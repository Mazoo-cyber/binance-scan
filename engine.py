"""
مسح كامل + بناء صفقات — v3
منهجية منطقة الدخول الجديدة:
  1) منطقة الدخول تُبنى على مستوى فعلي (حزمة) قريب من السعر: قاع/قمة تأرجح + EMA20/50/200 (4س/يومي)
     + قمة/قاع اليوم أو اليوم السابق + مستوى فيبوناتشي 0.5/0.618 للحركة الأخيرة.
  2) المسافة القصوى للمنطقة: ≤ 1.2 ATR(4س) عن السعر (قاعدة "لا تطارد").
  3) تصنيف احتمالية الوصول: A (≤0.5 ATR) · B (≤0.8 ATR) · C (≤1.2 ATR).
  4) الوقف = 0.45 ATR(4س) خلف حافة المنطقة (بلا محاذاة تزيد العدوانية) — يعطي مساحة تنفس.
  5) الأهداف = مستويات حقيقية (مقاومات/دعوم) أمام السعر، وإذا لم تكفِ تُمدَّد بمضاعفات ATR.
  6) الدرجة = اتجاه + بنية + قرب المستوى + السيولة + الزخم + RSI + براءة الفاندنغ/الأوي.
"""
import json, math, os, time, datetime as dt, concurrent.futures as cf
from core import (cached_get, klines, enrich, Coin, round_tick, fmt_price, BASE, CACHE)

RIYADH = dt.timezone(dt.timedelta(hours=3))
MIN_QV = 8.0          # مليون دولار
MAX_AGE = 30          # يوم
MIN_SCORE = 95
MIN_RR1, MIN_RR2 = 1.8, 2.6
MAX_DIST_ATR = 1.2    # لا تطارد
SIZE_USD = 1000.0


STABLE_BASES = {"USDC", "FDUSD", "TUSD", "USDP", "DAI", "USDE", "USD1", "USDS", "BUSD", "PYUSD", "RLUSD"}


# ------------------------------------------------------------------ universe
def load_universe():
    ei = cached_get("/v1/exchangeInfo", "exchangeInfo", ttl=6 * 3600)
    t24 = cached_get("/v1/ticker/24hr", "t24", ttl=300)
    prem = cached_get("/v1/premiumIndex", "prem", ttl=300)
    now = int(time.time() * 1000)
    info = {s["symbol"]: s for s in ei["symbols"]}
    td = {x["symbol"]: x for x in t24}
    pm = {x["symbol"]: x for x in prem}
    uni = []
    for sym, s in info.items():
        if s["contractType"] != "PERPETUAL" or s["quoteAsset"] != "USDT" or s["status"] != "TRADING":
            continue
        if not all(ord(ch) < 128 for ch in sym):
            continue
        if s.get("baseAsset") in STABLE_BASES:
            continue
        if sym not in td or sym not in pm:
            continue
        qv = float(td[sym]["quoteVolume"]) / 1e6
        age = (now - s["onboardDate"]) / 86400000
        if qv < MIN_QV or age < MAX_AGE:
            continue
        uni.append({"sym": sym, "qv": qv, "chg": float(td[sym]["priceChangePercent"]), "info": s,
                    "t24": td[sym], "prem": pm[sym]})
    uni.sort(key=lambda x: -x["chg"])
    top_up = [x["sym"] for x in uni[:40]]
    top_dn = [x["sym"] for x in uni[-40:]]
    return uni, top_up, top_dn, info, td, pm


def fetch_extras(symbols):
    """OI الحالي + OI قبل 4 ساعات (للمقارنة) + تمويل + عمق الدفتر."""
    out = {}

    def one(sym):
        r = {"oi": None, "oi_prev": None, "depth_ratio": None}
        try:
            r["oi"] = float(cached_get(f"/v1/openInterest?symbol={sym}", f"oi_{sym}", ttl=600)["openInterest"])
        except Exception:
            pass
        try:
            h = cached_get(f"/futures/data/openInterestHist?symbol={sym}&period=1h&limit=5", f"oih_{sym}", ttl=900)
            if h:
                r["oi_prev"] = float(h[0]["sumOpenInterest"])   # قبل 4 ساعات
        except Exception:
            pass
        return sym, r

    with cf.ThreadPoolExecutor(max_workers=10) as ex:
        for sym, r in ex.map(one, symbols):
            out[sym] = r
    return out


def is_asia_wick_window(now_riyadh=None):
    """نافذة الفجر الآسيوية (02:30 – 05:00 بتوقيت الرياض): تفعيل وضع اصطياد الذيل الآسيوي."""
    d = now_riyadh or dt.datetime.now(RIYADH)
    return (d.hour == 2 and d.minute >= 30) or d.hour in (3, 4)


# ------------------------------------------------------------------ levels
def _check_aligned_trend(k4, k1h, price, side, chg):
    """يتحقق مما إذا كانت العملة في ترند صحي قبل الانفجار ومتوافق بين 4س و1س (6% <= |chg| <= 22%)."""
    if not k1h or not k1h.get("ema20") or not k1h.get("ema50"):
        return False
    e20_4, e50_4 = k4["ema20"][-1], k4["ema50"][-1]
    e20_1h, e50_1h = k1h["ema20"][-1], k1h["ema50"][-1]
    if not (e20_4 and e50_4 and e20_1h and e50_1h):
        return False
    if side == "LONG":
        return (6.0 <= chg <= 22.0) and (price > e20_4 > e50_4) and (e20_1h > e50_1h)
    return (-22.0 <= chg <= -6.0) and (price < e20_4 < e50_4) and (e20_1h < e50_1h)


def _is_against_strong_trend(k4, k1h, price, side, chg):
    """قاعدة Trend is your friend: منع الوقوف عكس ترند قوي متوافق (|chg| >= 8% على 4س و1س)."""
    if not k1h or not k1h.get("ema20") or not k1h.get("ema50"):
        return False
    e20_4, e50_4 = k4["ema20"][-1], k4["ema50"][-1]
    e20_1h, e50_1h = k1h["ema20"][-1], k1h["ema50"][-1]
    if not (e20_4 and e50_4 and e20_1h and e50_1h):
        return False
    if side == "SHORT" and chg >= 8.0 and (price > e20_4 > e50_4) and (e20_1h > e50_1h):
        return True
    if side == "LONG" and chg <= -8.0 and (price < e20_4 < e50_4) and (e20_1h < e50_1h):
        return True
    return False


def cluster_levels(k4, k1, price, side, asia_wick=False, k1h=None, chg=0.0):
    """مصادر المستويات: قمم/قيعان تأرجح 4س، EMA20/50/200 على 4س واليومي، قمة/قاع اليوم واليوم السابق،
    بالإضافة لمرتكزات إعادة الاختبار السريعة (EMA9·4س + EMA20/50·1س + تأرجح 1س + فيبو موجة 48س) لعملات الترند النشط."""
    src = []

    def add(px, tag, w=1.0):
        if px and px > 0:
            src.append((px, tag, w))

    for i, v in k4["pl"][-8:]:
        add(v, "swing", 1.4)
    for i, v in k4["ph"][-8:]:
        add(v, "swing", 1.4)
    for nm in ("ema20", "ema50", "ema200"):
        add(k4[nm][-1], nm, 1.0)
    for nm in ("ema20", "ema50"):
        add(k1[nm][-1], nm + "d", 0.6)

    # في بداية اليوم الجديد (03:00 – 05:00) عمر الشمعة اليومية دقائق فقط، فنعتمد قمة/قاع اليوم المغلق للتو
    newborn_daily = asia_wick and len(k1.get("t", [])) > 1 and (time.time() * 1000 - k1["t"][-1]) < 3 * 3600 * 1000
    if newborn_daily:
        add(k1["h"][-2], "H_prev", 1.2)
        add(k1["l"][-2], "L_prev", 1.2)
        if len(k1["h"]) > 2:
            add(k1["h"][-3], "H_prev", 0.7)
            add(k1["l"][-3], "L_prev", 0.7)
    else:
        add(k1["h"][-1], "H_today", 1.2)
        add(k1["l"][-1], "L_today", 1.2)
        if len(k1["h"]) > 1:
            add(k1["h"][-2], "H_prev", 0.7)
            add(k1["l"][-2], "L_prev", 0.7)

    # فيبوناتشي للحركة الأخيرة (آخر 60 شمعة 4س)
    hi = max(k4["h"][-60:]); lo = min(k4["l"][-60:])
    if hi > lo:
        for f, nm in ((0.5, "fib50"), (0.618, "fib618"), (0.382, "fib382")):
            add(hi - (hi - lo) * f, nm, 0.5)

    weak_set = {"fib50", "fib618", "fib382", "ema20d", "ema50d"} if newborn_daily else {
        "fib50", "fib618", "fib382", "H_prev", "L_prev", "ema20d", "ema50d"
    }

    atr4 = k4["atr"][-1] or (price * 0.02)
    is_trend = _check_aligned_trend(k4, k1h, price, side, chg)
    tol = 0.0035
    if is_trend:
        tol = max(0.0035, min(0.16 * atr4 / price, 0.011))
        if k4.get("ema9") and k4["ema9"][-1]:
            add(k4["ema9"][-1], "ema9_4h", 1.1)
        add(k1h["ema20"][-1], "ema20_1h", 1.1)
        add(k1h["ema50"][-1], "ema50_1h", 0.9)
        for i, v in k1h["pl"][-8:]:
            add(v, "swing_1h", 1.1)
        for i, v in k1h["ph"][-8:]:
            add(v, "swing_1h", 1.1)
        hi12 = max(k4["h"][-12:]); lo12 = min(k4["l"][-12:])
        if hi12 > lo12:
            for f, nm in ((0.236, "ifib236"), (0.382, "ifib382"), (0.5, "ifib50")):
                px_f = (hi12 - (hi12 - lo12) * f) if side == "LONG" else (lo12 + (hi12 - lo12) * f)
                add(px_f, nm, 0.6)
        weak_set = weak_set | {"ifib236", "ifib382", "ifib50", "ema50_1h"}

    # تجميع
    src.sort(key=lambda x: x[0])
    groups = []
    for px, tag, w in src:
        placed = False
        for g in groups:
            if abs(px - g["px"]) / g["px"] <= tol:
                g["px"] = (g["px"] * g["w"] + px * w) / (g["w"] + w)
                g["w"] += w
                g["tags"].append(tag)
                placed = True
                break
        if not placed:
            groups.append({"px": px, "w": w, "tags": [tag]})
    out = []
    for g in groups:
        tags = sorted(set(g["tags"]))
        strong = [t for t in tags if t not in weak_set]
        n_src = len(tags)
        if n_src < 2:
            continue
        if side == "LONG" and g["px"] < price:
            out.append({"px": g["px"], "tags": tags, "n": n_src, "strong": len(strong), "w": g["w"]})
        if side == "SHORT" and g["px"] > price:
            out.append({"px": g["px"], "tags": tags, "n": n_src, "strong": len(strong), "w": g["w"]})
    if side == "LONG":
        out.sort(key=lambda x: -x["px"])
    else:
        out.sort(key=lambda x: x["px"])
    return out


def structure(k4, side):
    """بنية HH/HL أو LH/LL من آخر القمم/القيعان."""
    ph, pl = k4["ph"][-4:], k4["pl"][-4:]
    hh = len(ph) >= 2 and ph[-1][1] > ph[-2][1]
    hl = len(pl) >= 2 and pl[-1][1] > pl[-2][1]
    lh = len(ph) >= 2 and ph[-1][1] < ph[-2][1]
    ll = len(pl) >= 2 and pl[-1][1] < pl[-2][1]
    if side == "LONG":
        if hh and hl:
            return "صاعدة HH/HL", 1.0
        if hl:
            return "قيعان صاعدة", 0.6
        if lh and ll:
            return "هابطة LH/LL", -0.6
        return "عرضية", 0.0
    else:
        if lh and ll:
            return "هابطة LH/LL", 1.0
        if lh:
            return "قمم هابطة", 0.6
        if hh and hl:
            return "صاعدة HH/HL", -0.6
        return "عرضية", 0.0


def trend_dir(k4, k1):
    def g(k, name, i=-1):
        v = k.get(name)
        if not v:
            return None
        return v[i]
    c = k4["c"][-1]
    e20_4, e50_4, e200_4 = g(k4, "ema20"), g(k4, "ema50"), g(k4, "ema200")
    e20_1, e50_1 = g(k1, "ema20"), g(k1, "ema50")
    s = 0
    if e20_4:
        s += 1 if c > e20_4 else -1
    if e20_4 and e50_4:
        s += 1 if e20_4 > e50_4 else -1
    if e50_4 and e200_4:
        s += 1 if e50_4 > e200_4 else -1
    else:
        s += 1 if (e50_4 and c > e50_4) else (-1 if e50_4 else 0)
    s1 = 0
    c1 = k1["c"][-1]
    if e20_1:
        s1 += 1 if c1 > e20_1 else -1
    if e20_1 and e50_1:
        s1 += 1 if e20_1 > e50_1 else -1
    return s, s1


# ------------------------------------------------------------------ trade builder
def pick_cluster(clusters, price, atr4, side, min_dist_atr=0.0):
    """يختار أقرب حزمة مؤهلة للسعر (وليس الأقوى بعيداً) — جوهر إصلاح منطقة الدخول.
    - يجب أن تحتوي 2+ مصادر منها مصدر قوي واحد على الأقل.
    - سقف 1.0 ATR (المسافة إلى الحافة القريبة) — فوق ذلك تُعتبر بعيدة وتُستبعد.
    - في وضع اصطياد ذيل آسيا (02:30–05:00): يُفضَّل وجود مسافة دنيا ≥ 0.22 ATR لالتقاط الذيل.
    """
    cands = []
    for cl in clusters:
        if cl["n"] < 2 or cl["strong"] < 1:
            continue
        d = abs(price - cl["px"]) / atr4
        if min_dist_atr - 1e-9 <= d <= 1.0 + 1e-9:
            cands.append((d, cl))
    if not cands and min_dist_atr > 0:
        for cl in clusters:
            if cl["n"] < 2 or cl["strong"] < 1:
                continue
            d = abs(price - cl["px"]) / atr4
            if d <= 1.0 + 1e-9:
                cands.append((d, cl))
    if not cands:
        return None
    cands.sort(key=lambda x: x[0])
    near_d, near = cands[0]
    # إن كان الأقرب ضعيف المصادر وهناك حزمة أقوى بفارق بسيط (≤0.25 ATR) نأخذ الأقوى
    for d, cl in cands[1:]:
        if d - near_d > 0.25:
            break
        if cl["w"] >= near["w"] * 1.6 and cl["strong"] >= 2:
            return d, cl
    return near_d, near



def sr_levels(k4, k1, price, atr4):
    """أقرب 3 دعوم أسفل السعر + أقرب 3 مقاومات أعلاه (حزم + تأرجح + متوسطات)."""
    sup, res = [], []
    for c in cluster_levels(k4, k1, price, "LONG"):
        sup.append((c["px"], c["strong"] * 2 + c["n"]))
    for c in cluster_levels(k4, k1, price, "SHORT"):
        res.append((c["px"], c["strong"] * 2 + c["n"]))
    for i, v in k4["pl"][-8:]:
        if v < price:
            sup.append((v, 1))
    for i, v in k4["ph"][-8:]:
        if v > price:
            res.append((v, 1))
    for nm in ("ema20", "ema50", "ema200"):
        v = k4[nm][-1]
        if not v:
            continue
        (sup if v < price else res).append((v, 1))
    for nm in ("ema20", "ema50"):
        v = k1[nm][-1]
        if not v:
            continue
        (sup if v < price else res).append((v, 0.8))

    def dedup(arr, desc):
        arr.sort(key=lambda x: x[0], reverse=desc)
        out = []
        for px, w in arr:
            if all(abs(px - o) / o > 0.004 for o in out):
                out.append(px)
            if len(out) == 3:
                break
        return out

    supports = dedup(sup, True)     # الأقرب أولاً
    resistances = dedup(res, False)  # الأقرب أولاً
    while len(supports) < 3:
        supports.append((supports[-1] if supports else price) - 1.5 * atr4)
    while len(resistances) < 3:
        resistances.append((resistances[-1] if resistances else price) + 1.5 * atr4)
    return [round(x, 10) for x in supports], [round(x, 10) for x in resistances]


def build(coin, side, extra, asia_wick=None):
    k4, k1, k1h = coin.h4, coin.h1, getattr(coin, "m60", None)
    price = coin.last
    atr4 = k4["atr"][-1]
    if not atr4 or atr4 <= 0:
        return None
    if _is_against_strong_trend(k4, k1h, price, side, coin.chg):
        return None
    if asia_wick is None:
        asia_wick = is_asia_wick_window()
    atr_pct = atr4 / price * 100
    min_d_req = 0.22 if asia_wick else 0.0
    is_trend = _check_aligned_trend(k4, k1h, price, side, coin.chg)

    # أولاً: المحاولة بالمرتكزات الكلاسيكية (4س + يومي) لضمان عدم الانحياز للترند على حساب الصفقات البنيوية
    base_clusters = cluster_levels(k4, k1, price, side, asia_wick=asia_wick, k1h=None, chg=0.0)
    base_picked = pick_cluster(base_clusters, price, atr4, side, min_dist_atr=min_d_req)
    used_fast_trend = False
    if is_trend:
        tr_clusters = cluster_levels(k4, k1, price, side, asia_wick=asia_wick, k1h=k1h, chg=coin.chg)
        picked = pick_cluster(tr_clusters, price, atr4, side, min_dist_atr=min_d_req)
        used_fast_trend = base_picked is None
    else:
        picked = base_picked
    if not picked:
        return None
    best_d, best = picked
    lvl = best["px"]

    # عرض المنطقة: 0.35 ATR كحد أقصى، والحافة القريبة لا تتجاوز السعر
    # وفي نافذة الفجر الآسيوية (02:30–05:00): مسافة دنيا 0.22 ATR عن الافتتاح لاصطياد ذيل آسيا
    width = min(0.35 * atr4, 0.006 * price)
    min_gap = 0.22 * atr4 if asia_wick else 0.0
    if side == "LONG":
        e_hi = min(lvl + width * 0.55, price - min_gap)
        e_lo = e_hi - width
        stop = e_lo - 0.45 * atr4
        # حماية بنيوية: الوقف خلف أقرب قاع تأرجح ضمن 1.0 ATR (ليس في مهب الريح)
        cand = [v for i, v in k4["pl"][-8:] if v < e_lo and (e_lo - v) <= 1.0 * atr4]
        if cand:
            stop = min(stop, min(cand) - 0.15 * atr4)
        near_edge = e_hi
    else:
        e_lo = max(lvl - width * 0.55, price + min_gap)
        e_hi = e_lo + width
        stop = e_hi + 0.45 * atr4
        cand = [v for i, v in k4["ph"][-8:] if v > e_hi and (v - e_hi) <= 1.0 * atr4]
        if cand:
            stop = max(stop, max(cand) + 0.15 * atr4)
        near_edge = e_lo
    avg = (e_lo + e_hi) / 2
    risk_pct = abs(avg - stop) / avg * 100

    dist_atr = abs(price - near_edge) / atr4      # المسافة الحقيقية لأول لمسة (الحافة القريبة)
    dist_atr_mid = abs(price - avg) / atr4
    if dist_atr > 1.0 or risk_pct > 5.0 or risk_pct < 0.30 or atr_pct < 0.25:
        return None
    r = abs(avg - stop)
    if r <= 0:
        return None

    # ---------------- الأهداف: مستويات حقيقية أمام السعر (شاملة قمة/قاع 24س وتأرجحات 1س إن وُجدت)
    pool = []
    if side == "LONG":
        for cl in cluster_levels(k4, k1, price, "SHORT"):
            pool.append(cl["px"])
        for i, v in k4["ph"][-8:]:
            pool.append(v)
        if k1h:
            for i, v in k1h["ph"][-8:]:
                pool.append(v)
        if coin.high24:
            pool.append(coin.high24)
        pool = sorted([x for x in pool if x > avg + 0.55 * r])
    else:
        for cl in cluster_levels(k4, k1, price, "LONG"):
            pool.append(cl["px"])
        for i, v in k4["pl"][-8:]:
            pool.append(v)
        if k1h:
            for i, v in k1h["pl"][-8:]:
                pool.append(v)
        if coin.low24:
            pool.append(coin.low24)
        pool = sorted([x for x in pool if x < avg - 0.55 * r], reverse=True)
    uniq = []
    for x in pool:
        if not uniq or abs(x - uniq[-1]) / uniq[-1] > 0.004:
            uniq.append(x)

    need = (1.8, 2.6, 3.5)
    max_r_cap = (4.0, 5.8, 8.5)
    fallback_r = (2.1, 3.1, 4.4)
    tgts = []
    for kk in range(3):
        wantpx = avg + need[kk] * r if side == "LONG" else avg - need[kk] * r
        cappx = avg + max_r_cap[kk] * r if side == "LONG" else avg - max_r_cap[kk] * r
        pick = None
        for tp in uniq:
            ok = (wantpx <= tp <= cappx) if side == "LONG" else (cappx <= tp <= wantpx)
            if ok:
                pick = tp
                break
        if pick is None:
            ext = min(fallback_r[kk] * r, (1.0, 2.0, 3.1)[kk] * 2.2 * atr4)
            ext = max(ext, (need[kk] + 0.1) * r)
            pick = avg + ext if side == "LONG" else avg - ext
        if tgts:
            if side == "LONG" and pick <= tgts[-1]:
                pick = tgts[-1] + 0.75 * r
            if side == "SHORT" and pick >= tgts[-1]:
                pick = tgts[-1] - 0.75 * r
        tgts.append(pick)
    rr = [abs((t - avg) / r) for t in tgts]
    if rr[0] < MIN_RR1 or rr[1] < MIN_RR2:
        return None

    # ---------------- الدرجة
    score = 90.0
    notes = []
    tdir4, tdir1 = trend_dir(k4, k1)
    want = 1 if side == "LONG" else -1
    al4, al1 = tdir4 * want, tdir1 * want
    if al4 >= 3:
        score += 3; notes.append("اتجاه 4س قوي")
    elif al4 == 2:
        score += 1; notes.append("اتجاه 4س")
    elif al4 <= -1:
        score -= 3; notes.append("ضد اتجاه 4س")
    if al1 >= 2:
        score += 2
    elif al1 <= -2:
        score -= 2

    st, stw = structure(k4, side)
    score += 3 * stw
    if best["w"] >= 3.5 and best["strong"] >= 2:
        score += 4; notes.append("حزمة قوية")
    elif best["w"] >= 2.2:
        score += 2
    else:
        score -= 1

    if coin.qv >= 500:
        score += 3
    elif coin.qv >= 150:
        score += 2
    elif coin.qv >= 40:
        score += 1
    else:
        score -= 1

    mh, mhp = k4["macd_hist"][-1], k4["macd_hist"][-2]
    mom = 1 if (mh is not None and mhp is not None and mh > mhp) else -1
    if mom * want > 0:
        score += 2; notes.append("زخم مؤيد")
    else:
        score -= 1

    rsi4 = k4["rsi"][-1] or 50
    rsi1 = k1["rsi"][-1] or 50
    if side == "LONG":
        if rsi4 > 74 or rsi1 > 76:
            score -= 4; notes.append("RSI متطرف")
        elif rsi4 < 62:
            score += 1
    else:
        if rsi4 < 26 or rsi1 < 24:
            score -= 3; notes.append("RSI متطرف")
        elif rsi4 > 38:
            score += 1

    if abs(coin.funding) > 0.10:
        score -= 2; notes.append("فاندنغ شاذ")
    if is_trend:
        notes.append("ارتكاز ترند نشط")
    if asia_wick:
        notes.append("اصطياد ذيل آسيا")
    # مكافأة القرب (وزن أكبر مما كان) — وفي وضع ذيل آسيا نكافئ الشريط المثالي 0.25–0.60 ATR
    if asia_wick:
        score += max(0.0, 0.75 - abs(dist_atr - 0.38)) * 3.5
    else:
        score += max(0.0, 0.70 - dist_atr) * 4.0
    score = round(score, 1)
    # نختار من مرتكزات الترند السريع الصفقات القوية فقط (درجة A أو B: ≥ 99 نقطة) دون إغراق التقرير بصفقات ضعيفة
    if used_fast_trend and score < 99.0:
        return None
    grade = "A" if score >= 103 else ("B" if score >= 99 else "C")
    # تصنيف احتمالية الوصول مبني على قياس فعلي (1,728 عينة 4س على 32 عملة سائلة)
    if dist_atr <= 0.35:
        reach, reach_p = "A", 80
    elif dist_atr <= 0.65:
        reach, reach_p = "B", 68
    else:
        reach, reach_p = "C", 54

    qty = max(SIZE_USD / avg, coin.min_notional / avg) if avg > 0 else 0
    if coin.step > 0:
        qty = math.floor(qty / coin.step) * coin.step
    qty = round(qty, 8)

    return {
        "sym": coin.sym, "name": coin.name, "side": side, "price": price,
        "entry_lo": e_lo, "entry_hi": e_hi, "avg": avg, "stop": stop,
        "targets": tgts, "rr": rr, "risk_pct": risk_pct, "atr_pct": atr_pct, "atr4": atr4,
        "dist_atr": dist_atr, "dist_atr_mid": dist_atr_mid,
        "dist_pct": (near_edge / price - 1) * 100,
        "score": score, "grade": grade, "reach": reach, "reach_p": reach_p,
        "tags": best["tags"], "n_src": best["n"], "struct": st,
        "chg": coin.chg, "qv": coin.qv, "funding": coin.funding, "oi_chg": coin.oi_chg,
        "rsi4": rsi4, "rsi1": rsi1, "qty": qty, "notes": notes,
        "hi24": coin.high24, "lo24": coin.low24, "mark": coin.mark, "tick": coin.tick,
        "trend": al4, "is_trend": is_trend,
        "supports": sr_levels(k4, k1, price, atr4)[0],
        "resistances": sr_levels(k4, k1, price, atr4)[1],
    }


def analyze(sym, info, t24, prem, extra, k4raw=None, k1raw=None):
    oi, oi_prev = extra.get("oi"), extra.get("oi_prev")
    c = Coin(sym, info, t24, prem, oi, oi_prev)
    try:
        c.h4 = enrich(klines(sym, "4h", 500))
        c.h1 = enrich(klines(sym, "1d", 300))
        if abs(c.chg) >= 6.0:
            c.m60 = enrich(klines(sym, "1h", 160))
    except Exception:
        return []
    out = []
    for side in ("LONG", "SHORT"):
        t = build(c, side, extra)
        if t:
            out.append(t)
    return out


def build_explosion_candidate(coin, stage="radar", radar_ref=None):
    """يفحص إن كانت العملة مرشحة للانفجار مع الافتتاح اليومي، ويبني لها منطقة اصطياد ذيل آسيا."""
    k4, k1 = coin.h4, coin.h1
    price = coin.last
    hi24, lo24 = coin.high24, coin.low24
    atr4 = k4["atr"][-1] if k4 and k4.get("atr") else None
    e20 = k4["ema20"][-1] if k4 and k4.get("ema20") else None
    rsi4 = (k4["rsi"][-1] if k4 and k4.get("rsi") else None) or 50.0
    rsi1 = (k1["rsi"][-1] if k1 and k1.get("rsi") else None) or 50.0
    if not atr4 or atr4 <= 0 or hi24 <= lo24 or not e20:
        return None
    atr_pct = atr4 / price * 100.0
    if atr_pct < 0.35:
        return None

    pos24 = (price - lo24) / (hi24 - lo24)
    chg = coin.chg
    fund = coin.funding
    oi_chg = coin.oi_chg

    # في وضع التأكيد (02:45) لعملة رُصدت عند 23:05: نفحص هل حافظت على شروط القمة والتماسك؟
    if stage == "confirm" and radar_ref is not None:
        fail = []
        if pos24 < 0.74:
            fail.append(f"هبطت من القمة ({pos24*100:.0f}% من مدى 24س)")
        if price < radar_ref.get("price", price) * 0.985:
            fail.append("كسرت دعم التماسك منذ 23:05")
        if price <= e20:
            fail.append("أغلقت دون EMA20·4س")
        if fund > 0.028:
            fail.append(f"تضخم الفاندنغ ({fund:+.3f}%)")
        if rsi4 >= 78:
            fail.append(f"تشبع RSI ({rsi4:.0f})")
        if fail:
            return {
                "sym": coin.sym, "name": coin.name, "cancelled": True,
                "cancel_reason": " · ".join(fail),
                "price": price, "radar_price": radar_ref.get("price"),
                "pos24": round(pos24 * 100, 1), "chg": chg, "tick": coin.tick,
            }
    else:
        min_pos = 0.78 if stage == "confirm" else 0.72
        if pos24 < min_pos or not (1.0 <= chg <= 25.0) or price <= e20 or rsi4 >= 76 or fund > 0.025:
            return None
        if abs(coin.mark - price) / price * 100 > 0.5:
            return None
        if stage == "confirm" and oi_chg < 0.3:
            return None

    # تقييم قوة الزنبرك المضغوط
    sc = 92.0
    reasons = [f"تماسك قمة 24س ({pos24*100:.0f}%)"]
    sc += (pos24 - 0.70) * 20.0
    if fund < 0:
        sc += min(4.0, abs(fund) * 80.0 + 1.5)
        reasons.append(f"فاندنغ سالب ({fund:+.4f}% عصر بيع)")
    elif fund <= 0.008:
        sc += 1.0
        reasons.append("فاندنغ هادئ")
    if oi_chg >= 2.0:
        sc += 3.0
        reasons.append(f"تعبئة عقود ΔOI {oi_chg:+.2f}%")
    elif oi_chg >= 0.0:
        sc += 1.5
        reasons.append(f"ΔOI موجب ({oi_chg:+.2f}%)")
    else:
        sc -= 1.0
    rng2 = ((k4["h"][-1] - k4["l"][-1]) + (k4["h"][-2] - k4["l"][-2])) / (2.0 * atr4)
    if rng2 <= 0.95:
        sc += 2.0
        reasons.append("انكماش تذبذب")
    if coin.qv >= 50:
        sc += 1.5
    sc = round(sc, 1)
    if sc < 95.0:
        return None

    # منطقة اصطياد الذيل الآسيوي (0.28 – 0.62 ATR أسفل السعر)
    width = min(0.32 * atr4, 0.006 * price)
    clusters = cluster_levels(k4, k1, price, "LONG", asia_wick=True)
    anchor = None
    for cl in clusters:
        d = (price - cl["px"]) / atr4
        if 0.25 <= d <= 0.68:
            anchor = cl["px"]
            break
    if anchor is None and 0.25 <= (price - e20) / atr4 <= 0.68:
        anchor = e20
    if anchor is not None:
        e_hi = min(anchor + width * 0.45, price - 0.25 * atr4)
    else:
        e_hi = price - 0.30 * atr4
    e_lo = e_hi - width
    stop = e_lo - 0.45 * atr4
    cand_sl = [v for _, v in k4["pl"][-6:] if v < e_lo and (e_lo - v) <= 0.9 * atr4]
    if cand_sl:
        stop = min(stop, min(cand_sl) - 0.15 * atr4)
    avg = (e_lo + e_hi) / 2.0
    r = abs(avg - stop)
    risk_pct = r / avg * 100.0 if avg > 0 else 99
    if r <= 0 or risk_pct > 5.2:
        return None

    sups, ress = sr_levels(k4, k1, price, atr4)
    t1 = max(hi24 * 1.004, avg + 1.9 * r)
    t2 = max(ress[1] if len(ress) > 1 else 0, avg + 2.9 * r, t1 + 0.8 * r)
    t3 = max(ress[2] if len(ress) > 2 else 0, avg + 4.2 * r, t2 + 1.0 * r)
    tgts = [t1, t2, t3]
    rr = [round(abs(x - avg) / r, 2) for x in tgts]
    grade = "A" if sc >= 102 else ("B" if sc >= 98.5 else "C")
    qty = max(SIZE_USD / avg, coin.min_notional / avg) if avg > 0 else 0
    if coin.step > 0:
        qty = math.floor(qty / coin.step) * coin.step

    if stage == "confirm":
        st_label = "✅ مؤكدة — علّق Limit لصيد الذيل" if radar_ref else "🆕 برزت في 02:45 — علّق Limit"
    elif stage == "active":
        st_label = "🎯 مصيدة ذيل آسيا نشطة"
    else:
        st_label = "📡 رصد 23:05 — للمراقبة حتى 02:45"

    return {
        "sym": coin.sym, "name": coin.name, "side": "LONG", "cancelled": False,
        "stage": stage, "stage_label": st_label,
        "price": price, "radar_price": radar_ref.get("price") if radar_ref else price,
        "entry_lo": e_lo, "entry_hi": e_hi, "avg": avg, "stop": stop,
        "targets": tgts, "rr": rr, "risk_pct": risk_pct, "atr_pct": atr_pct, "atr4": atr4,
        "dist_atr": (price - e_hi) / atr4,
        "dist_pct": (e_hi / price - 1) * 100.0,
        "pos24": round(pos24 * 100.0, 1),
        "score": sc, "grade": grade, "reasons": reasons,
        "chg": chg, "qv": coin.qv, "funding": fund, "oi_chg": oi_chg,
        "rsi4": rsi4, "rsi1": rsi1, "qty": round(qty, 8),
        "hi24": hi24, "lo24": lo24, "tick": coin.tick,
        "supports": sups, "resistances": ress,
    }


def scan_explosions(uni=None, extras=None, stage="radar", prev_radar=None, max_workers=8):
    """يمسح الكون لإنتاج قائمة العملات القابلة للانفجار مع الافتتاح اليومي (بحد أقصى 6 عملات مركزة)."""
    if uni is None:
        uni, _, _, _, _, _ = load_universe()
    if extras is None:
        extras = fetch_extras([x["sym"] for x in uni])
    umap = {x["sym"]: x for x in uni}
    radar_map = {x["sym"]: x for x in (prev_radar or [])}
    target_syms = list(set(list(umap.keys()) + list(radar_map.keys())))
    active, cancelled = [], []

    def one(sym):
        u = umap.get(sym)
        if not u:
            return None
        ex = extras.get(sym, {})
        c = Coin(sym, u["info"], u["t24"], u["prem"], ex.get("oi"), ex.get("oi_prev"))
        try:
            c.h4 = enrich(klines(sym, "4h", 500))
            c.h1 = enrich(klines(sym, "1d", 300))
        except Exception:
            return None
        return build_explosion_candidate(c, stage=stage, radar_ref=radar_map.get(sym))

    with cf.ThreadPoolExecutor(max_workers=max_workers) as ex:
        for r in ex.map(one, target_syms):
            if not r:
                continue
            if r.get("cancelled"):
                cancelled.append(r)
            else:
                active.append(r)

    active.sort(key=lambda x: (-x["score"], -x["pos24"]))
    active = active[:6]
    return {"stage": stage, "ts": int(time.time() * 1000), "active": active, "cancelled": cancelled}


def scan(max_workers=8, verbose=True):
    uni, top_up, top_dn, info, td, pm = load_universe()
    syms = [x["sym"] for x in uni]
    if verbose:
        print(f"كون البحث: {len(syms)} عقد سيولة ≥ {MIN_QV}M$ | 40 صاعدة: {top_up[:5]}... | 40 هابطة: {top_dn[:5]}...")
    extras = fetch_extras(syms)
    umap = {x["sym"]: x for x in uni}
    trades = []
    done = 0

    def one(sym):
        u = umap[sym]
        return analyze(sym, u["info"], u["t24"], u["prem"], extras.get(sym, {}))

    with cf.ThreadPoolExecutor(max_workers=max_workers) as ex:
        for res in ex.map(one, syms):
            trades.extend(res)
            done += 1
            if verbose and done % 25 == 0:
                print(f"  ... {done}/{len(syms)}")
    # فلترة الدرجة والتمييز
    qualified = [t for t in trades if t["score"] >= MIN_SCORE]
    qualified.sort(key=lambda t: (-t["score"], t["dist_atr"]))
    # إزالة التكرار: صفقة واحدة لكل عملة (الأقوى)
    seen = {}
    for t in qualified:
        if t["sym"] not in seen:
            seen[t["sym"]] = t
    qualified = list(seen.values())

    # فحص العملات القابلة للانفجار وحفظها للتقرير ولمرحلة التأكيد (02:45)
    now_r = dt.datetime.now(RIYADH)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    radar_path = os.path.join(base_dir, "explosion_radar.json")
    exp_path = os.path.join(base_dir, "explosion_candidates.json")
    try:
        if now_r.hour in (22, 23, 0, 1):
            exp_data = scan_explosions(uni=uni, extras=extras, stage="radar", max_workers=max_workers)
            json.dump(exp_data["active"], open(radar_path, "w"), ensure_ascii=False, default=str)
            json.dump(exp_data, open(exp_path, "w"), ensure_ascii=False, default=str)
        elif now_r.hour in (2, 3, 4, 5, 6):
            prev_r = json.load(open(radar_path)) if os.path.exists(radar_path) else []
            stg = "confirm" if now_r.hour == 2 else "active"
            exp_data = scan_explosions(uni=uni, extras=extras, stage=stg, prev_radar=prev_r, max_workers=max_workers)
            json.dump(exp_data, open(exp_path, "w"), ensure_ascii=False, default=str)
        else:
            exp_data = scan_explosions(uni=uni, extras=extras, stage="radar", max_workers=max_workers)
            exp_data["stage"] = "daytime"
            json.dump(exp_data, open(exp_path, "w"), ensure_ascii=False, default=str)
    except Exception as e:
        if verbose:
            print("explosion scan warn:", e)

    return qualified, {"universe": len(syms), "top_up": top_up, "top_dn": top_dn,
                       "all": trades, "uni": uni, "extras": extras,
                       "ts": int(time.time() * 1000)}
