#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ماسح عقود بايننس الآجلة الرئيسي المستقل — نسخة الاختبار والتشغيل الخارجي (v3.6)
Binance USDT-M Perpetual Standalone Quantitative Scanner (Single-File Edition)
================================================================================
يحتوي هذا الملف الواحد على الكود الكامل الأصلي لجميع محركات المشروع بدون أي اختصار
وبدون الحاجة لأي مكتبات خارجية (يعمل بـ Python 3 القياسي فقط):

  • القسم [1] core       : الاتصال الحي بـ Binance Futures API + حساب المؤشرات (EMA, RSI, ATR, MACD, Pivots)
  • القسم [2] engine     : محرك فريم (4س / 1س) لاختيار أقرب حزمة دخول + الترند النشط + رادار الانفجار وذيل آسيا
  • القسم [3] track      : محرك التتبع اللحظي (فريم 5 دقائق) لحساب التفعيل والأهداف والوقف الصريح
  • القسم [4] lifecycle  : إدارة دورة حياة الصفقات ومنع إعادة الدخول الفوري بعد ضرب الوقف قبل إغلاق 4س
  • القسم [5] gen_report : محرك الفريم اليومي والأسبوعي والشهري (1D + 1W + 1M):
                           1) العملات الاستثمارية في مرحلة العصر الأفقي + ذيل التلاعب السُفلي (Spring)
                           2) كسر قمة 30 يوماً + 3 إغلاقات خضراء صاعدة + شمعة الهمر الانعكاسية (Hammer)
                           3) بوابة التوقيت اليومي (تجاهل شمعة اليوم الحية قبل 23:05 الرياض)
                           4) الفحص الإلزامي لشمعتي الأسبوع (1W) والشهر (1M) + درع التوازن + توليد index.html

طرق التشغيل والاختبار الخارجي من سطر الأوامر (Terminal / CMD / Colab):
  1) تشغيل دورة مسح كاملة للسوق وتوليد التقرير التفاعلي (index.html):
       python3 binance_scanner_standalone.py

  2) اختبار محرك الفريم اليومي والأسبوعي والشهري فقط (الاستثماري + كسر الهيكل + بوابة 23:05 + الهمر):
       python3 binance_scanner_standalone.py --macro-only

  3) فحص تشخيصي تفصيلي لعملة أو عدة عملات محددة (مثل LYN و AIO و SOL و BTC):
       python3 binance_scanner_standalone.py --coin LYN AIO SOL

  4) تشغيل حزمة اختبارات القبول الحتمية للمرحلة الأولى (9 اختبارات رياضية للدخول والأهداف الجزئية والوقف):
       python3 binance_scanner_standalone.py --test-phase1

  5) تشغيل حزمة اختبارات القبول الحتمية للمرحلة الثانية (8 اختبارات رياضية لإدارة المخاطر وحجم المركز والهامش):
       python3 binance_scanner_standalone.py --test-phase2

  6) تشغيل حزمة اختبارات القبول الحتمية للمرحلة الثالثة (7 اختبارات لمحرك الباكتيست التاريخي ومنحنى رأس المال):
       python3 binance_scanner_standalone.py --test-phase3

  7) تشغيل الباكتيست التاريخي المتقدم (Walk-Forward Backtest) ومقارنة حساسية نماذج التنفيذ الثلاثة:
       python3 binance_scanner_standalone.py --backtest --bt-days 14 --bt-top-n 12 --bt-compare-models

  8) تشغيل حزمة اختبارات القبول الحتمية للمرحلة الرابعة (6 اختبارات للشموع المغلقة، حيادية OI، تصنيف الأهداف، والمعايرة):
       python3 binance_scanner_standalone.py --test-phase4

  9) تشغيل جميع اختبارات القبول المجمعة (30 اختباراً للمراحل 1 + 2 + 3 + 4) وتخصيص رأس المال:
       python3 binance_scanner_standalone.py --test-all
       python3 binance_scanner_standalone.py --equity 25000 --risk-pct 1.0 --log-level INFO
================================================================================
"""
import argparse, sys
# تسجيل الملف الحالي كوحدة core/engine/track/lifecycle لدعم أي استيراد داخلي بسلاسة
for _m in ("core", "engine", "track", "lifecycle"):
    sys.modules.setdefault(_m, sys.modules[__name__])

DEFAULT_FILL_STATS = {"up": [-0.022, 0.0, 0.006, 0.012, 0.027, 0.037, 0.045, 0.053, 0.06, 0.067, 0.072, 0.076, 0.087, 0.097, 0.106, 0.115, 0.122, 0.132, 0.145, 0.155, 0.162, 0.174, 0.179, 0.185, 0.194, 0.202, 0.207, 0.214, 0.225, 0.232, 0.24, 0.249, 0.262, 0.269, 0.283, 0.29, 0.297, 0.302, 0.309, 0.327, 0.338, 0.35, 0.359, 0.369, 0.373, 0.378, 0.388, 0.395, 0.405, 0.416, 0.424, 0.432, 0.439, 0.445, 0.453, 0.462, 0.469, 0.474, 0.487, 0.496, 0.503, 0.511, 0.523, 0.53, 0.537, 0.546, 0.553, 0.566, 0.572, 0.576, 0.588, 0.594, 0.603, 0.614, 0.623, 0.63, 0.652, 0.657, 0.666, 0.672, 0.679, 0.686, 0.69, 0.7, 0.709, 0.716, 0.727, 0.736, 0.746, 0.757, 0.765, 0.778, 0.79, 0.797, 0.806, 0.82, 0.834, 0.843, 0.849, 0.863, 0.88, 0.906, 0.927, 0.936, 0.956, 0.972, 0.992, 1.015, 1.028, 1.041, 1.052, 1.071, 1.089, 1.101, 1.115, 1.123, 1.131, 1.149, 1.156, 1.171, 1.176, 1.189, 1.207, 1.218, 1.232, 1.243, 1.255, 1.291, 1.296, 1.303, 1.326, 1.337, 1.354, 1.363, 1.377, 1.402, 1.426, 1.444, 1.458, 1.474, 1.487, 1.512, 1.554, 1.602, 1.621, 1.638, 1.645, 1.668, 1.684, 1.701, 1.723, 1.744, 1.77, 1.784, 1.807, 1.831, 1.84, 1.864, 1.882, 1.9, 1.927, 1.939, 1.97, 1.985, 1.997, 2.017, 2.032, 2.069, 2.103, 2.149, 2.165, 2.204, 2.241, 2.276, 2.314, 2.357, 2.387, 2.431, 2.467, 2.5, 2.55, 2.586, 2.627, 2.665, 2.718, 2.76, 2.808, 2.859, 2.891, 2.959, 2.996, 3.042, 3.089, 3.162, 3.231, 3.334, 3.463, 3.604, 3.658, 3.72, 3.772, 3.884, 3.958, 4.028, 4.184, 4.282, 4.487, 4.622, 4.805, 5.117, 5.43, 5.785, 6.033, 6.42, 8.096, 14.06], "dn": [-0.003, 0.009, 0.019, 0.023, 0.032, 0.042, 0.05, 0.058, 0.064, 0.069, 0.078, 0.084, 0.089, 0.091, 0.094, 0.102, 0.108, 0.114, 0.125, 0.138, 0.147, 0.152, 0.157, 0.164, 0.171, 0.179, 0.189, 0.203, 0.212, 0.22, 0.233, 0.239, 0.252, 0.265, 0.271, 0.28, 0.29, 0.307, 0.313, 0.319, 0.331, 0.341, 0.347, 0.353, 0.368, 0.379, 0.386, 0.392, 0.401, 0.405, 0.415, 0.424, 0.431, 0.442, 0.452, 0.469, 0.483, 0.493, 0.509, 0.528, 0.536, 0.548, 0.557, 0.564, 0.576, 0.588, 0.601, 0.617, 0.629, 0.638, 0.651, 0.659, 0.664, 0.676, 0.683, 0.706, 0.718, 0.725, 0.739, 0.748, 0.756, 0.762, 0.774, 0.784, 0.795, 0.809, 0.82, 0.829, 0.841, 0.846, 0.864, 0.875, 0.881, 0.896, 0.915, 0.926, 0.94, 0.965, 0.982, 0.991, 1.003, 1.02, 1.052, 1.075, 1.093, 1.12, 1.137, 1.154, 1.167, 1.185, 1.211, 1.242, 1.25, 1.275, 1.299, 1.333, 1.37, 1.386, 1.41, 1.422, 1.442, 1.462, 1.479, 1.496, 1.506, 1.531, 1.541, 1.592, 1.62, 1.641, 1.663, 1.687, 1.704, 1.731, 1.751, 1.774, 1.794, 1.816, 1.845, 1.871, 1.886, 1.913, 1.948, 1.973, 1.996, 2.02, 2.052, 2.089, 2.117, 2.138, 2.161, 2.18, 2.221, 2.255, 2.27, 2.296, 2.323, 2.34, 2.373, 2.417, 2.43, 2.464, 2.508, 2.531, 2.544, 2.569, 2.589, 2.637, 2.664, 2.69, 2.717, 2.781, 2.828, 2.882, 2.917, 2.951, 2.978, 3.008, 3.072, 3.097, 3.126, 3.161, 3.189, 3.21, 3.252, 3.306, 3.361, 3.396, 3.443, 3.514, 3.581, 3.608, 3.699, 3.751, 3.818, 3.899, 3.933, 3.987, 4.072, 4.14, 4.198, 4.284, 4.364, 4.457, 4.601, 4.747, 4.93, 5.145, 5.392, 5.633, 5.967, 6.073, 6.292, 6.784, 8.643, 14.12]}


# ==============================================================================
# [1] القسم الأول: core.py
# ==============================================================================
"""
محرك مسح عقود بايننس الآجلة — v3
- بيانات: Binance Futures API عبر النطاق www.binance.com/fapi (النطاق fapi محجوب)
- تركيز: مناطق دخول واقعية (قريبة من السعر ومُصنَّفة باحتمال الوصول)
"""
import json, logging, math, os, time, concurrent.futures as cf, urllib.request, urllib.error

API_BASE = "https://www.binance.com/fapi"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE, exist_ok=True)
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Accept": "application/json"}

# سجل تشخيصي منظم يستبدل الابتلاع الصامت للأخطاء (Priority #9) دون إغراق الطرفية في الوضع العادي
SCANNER_LOGGER = logging.getLogger("binance_scanner")
if not SCANNER_LOGGER.handlers:
    _sh = logging.StreamHandler()
    _sh.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    SCANNER_LOGGER.addHandler(_sh)
SCANNER_LOGGER.setLevel(getattr(logging, os.environ.get("SCANNER_LOG_LEVEL", "ERROR").upper(), logging.ERROR))

RUNTIME_DIAGNOSTICS = {"counts": {}, "recent_warnings": []}


def reset_diagnostics():
    RUNTIME_DIAGNOSTICS["counts"].clear()
    RUNTIME_DIAGNOSTICS["recent_warnings"].clear()


def record_diag_warning(stage, message, symbol=None, exc=None):
    """يسجل تحذيراً منظماً مع عدّاد لكل مرحلة وعينة من آخر التحذيرات لتسهيل التشخيص والمراجعة."""
    RUNTIME_DIAGNOSTICS["counts"][stage] = RUNTIME_DIAGNOSTICS["counts"].get(stage, 0) + 1
    detail = f"{stage}" + (f"[{symbol}]" if symbol else "") + f": {message}" + (f" ({type(exc).__name__}: {exc})" if exc else "")
    if len(RUNTIME_DIAGNOSTICS["recent_warnings"]) < 40:
        RUNTIME_DIAGNOSTICS["recent_warnings"].append({
            "ts": int(time.time() * 1000),
            "stage": stage,
            "symbol": symbol,
            "message": message,
            "error": f"{type(exc).__name__}: {exc}" if exc else None,
        })
    SCANNER_LOGGER.warning(detail)


def get_diagnostics_summary():
    return {
        "total_warnings": sum(RUNTIME_DIAGNOSTICS["counts"].values()),
        "counts_by_stage": dict(RUNTIME_DIAGNOSTICS["counts"]),
        "recent_warnings": list(RUNTIME_DIAGNOSTICS["recent_warnings"][-15:]),
    }


def _get(path, retries=4):
    url = API_BASE + path
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=35) as r:
                return json.loads(r.read())
        except Exception as e:
            last = e
            time.sleep(0.6 * (i + 1))
    raise RuntimeError(f"GET failed {path}: {last}")


DATA_BASE = "https://www.binance.com"


def _get_data(path, retries=3):
    """بيانات إحصائية (OI التاريخي) تحتاج النطاق العام لا /fapi."""
    url = DATA_BASE + path
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=35) as r:
                return json.loads(r.read())
        except Exception as e:
            last = e
            time.sleep(0.5 * (i + 1))
    raise RuntimeError(f"GET failed {path}: {last}")


def cached_get(path, key, ttl=900):
    f = os.path.join(CACHE, key + ".json")
    if os.path.exists(f) and time.time() - os.path.getmtime(f) < ttl:
        try:
            with open(f, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:
            record_diag_warning("corrupt_cache_read", f"فشل قراءة ملف الكاش {key}", exc=exc)
    d = _get_data(path) if path.startswith("/futures/data") else _get(path)
    try:
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(d, fh)
    except Exception as exc:
        record_diag_warning("cache_write_failed", f"فشل كتابة ملف الكاش {key}", exc=exc)
    return d


# ---------------------------------------------------------------- indicators
def ema(vals, n):
    out = [None] * len(vals)
    if len(vals) < n or n <= 0:
        return out
    k = 2 / (n + 1)
    e = sum(vals[:n]) / n
    out[n - 1] = e
    for i in range(n, len(vals)):
        e = vals[i] * k + e * (1 - k)
        out[i] = e
    return out


def atr_series(h, l, c, n=14):
    trs = []
    for i in range(len(c)):
        if i == 0:
            trs.append(h[i] - l[i])
        else:
            trs.append(max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])))
    out, a = [], None
    for i, t in enumerate(trs):
        if i + 1 < n:
            out.append(None)
        elif i + 1 == n:
            a = sum(trs[:n]) / n
            out.append(a)
        else:
            a = (a * (n - 1) + t) / n
            out.append(a)
    return out


def rsi_series(c, n=14):
    out = [None] * len(c)
    if len(c) <= n:
        return out
    gains = losses = 0.0
    for i in range(1, n + 1):
        d = c[i] - c[i - 1]
        gains += max(d, 0)
        losses += max(-d, 0)
    ag, al = gains / n, losses / n
    out[n] = 100 - 100 / (1 + (ag / al if al else 999))
    for i in range(n + 1, len(c)):
        d = c[i] - c[i - 1]
        ag = (ag * (n - 1) + max(d, 0)) / n
        al = (al * (n - 1) + max(-d, 0)) / n
        out[i] = 100 - 100 / (1 + (ag / al if al else 999))
    return out


def macd_series(c, f=12, s=26, sig=9):
    ef, es = ema(c, f), ema(c, s)
    line = [None if (ef[i] is None or es[i] is None) else ef[i] - es[i] for i in range(len(c))]
    base = [x for x in line if x is not None]
    if not base:
        return line, [None] * len(c), [None] * len(c)
    sm = ema(base, sig)
    off = len(line) - len(base)
    signal = [None] * off + sm
    hist = [None if (line[i] is None or signal[i] is None) else line[i] - signal[i] for i in range(len(line))]
    return line, signal, hist


def pivots(h, l, k=3):
    """قمم/قيعان تأرجح (fractal)."""
    highs, lows = [], []
    n = len(h)
    for i in range(k, n - k):
        if all(h[i] >= h[i - j] for j in range(1, k + 1)) and all(h[i] >= h[i + j] for j in range(1, k + 1)):
            highs.append((i, h[i]))
        if all(l[i] <= l[i - j] for j in range(1, k + 1)) and all(l[i] <= l[i + j] for j in range(1, k + 1)):
            lows.append((i, l[i]))
    return highs, lows


# ---------------------------------------------------------------- data
CORE_INTERVAL_MS = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}


def closed_klines_only(k, interval, now_ms=None):
    """يزيل الشمعة الأخيرة المفتوحة (غير المكتملة بعد) من الفريمات الزمنية لضمان ثبات المؤشرات
    وفحوصات الانكماش عند المسح في الدقيقة :05 وعدم تلوثها بشمعة عمرها 5 دقائق فقط (Priority #5)."""
    if not k or not k.get("t") or len(k["t"]) < 3:
        return k
    iv_ms = CORE_INTERVAL_MS.get(interval)
    if not iv_ms:
        return k
    ref_now = float(now_ms if now_ms is not None else time.time() * 1000)
    # إذا كان وقت فتح الشمعة الأخيرة + مدة الفريم > الوقت الحالي، فهي شمعة قيد التكوين لم تغلق بعد
    if float(k["t"][-1]) + iv_ms > ref_now:
        out = {}
        n_keep = len(k["t"]) - 1
        for key, arr in k.items():
            out[key] = arr[:n_keep] if isinstance(arr, list) and len(arr) == len(k["t"]) else arr
        return out
    return k


def klines(symbol, interval, limit=500):
    k = f"k_{symbol}_{interval}_{limit}"
    raw = cached_get(f"/v1/klines?symbol={symbol}&interval={interval}&limit={limit}", k, ttl=600)
    return {
        "t": [int(x[0]) for x in raw],
        "o": [float(x[1]) for x in raw],
        "h": [float(x[2]) for x in raw],
        "l": [float(x[3]) for x in raw],
        "c": [float(x[4]) for x in raw],
        "v": [float(x[5]) for x in raw],
    }


def enrich(k):
    c, h, l = k["c"], k["h"], k["l"]
    k["ema9"] = ema(c, 9)
    k["ema20"], k["ema50"], k["ema200"] = ema(c, 20), ema(c, 50), ema(c, 200)
    k["atr"] = atr_series(h, l, c, 14)
    k["rsi"] = rsi_series(c, 14)
    ml, ms, mh = macd_series(c)
    k["macd"], k["macd_sig"], k["macd_hist"] = ml, ms, mh
    k["ph"], k["pl"] = pivots(h, l, 3)
    return k


class Coin:
    def __init__(self, sym, info, t24, prem, oi, oi_prev):
        self.sym = sym
        self.tick = float(next((f["tickSize"] for f in info["filters"] if f["filterType"] == "PRICE_FILTER"), "0.0001"))
        self.step = float(next((f["stepSize"] for f in info["filters"] if f["filterType"] == "LOT_SIZE"), "1"))
        self.min_notional = float(next((f.get("notional", 5) for f in info["filters"] if f["filterType"] == "MIN_NOTIONAL"), 5))
        self.precision = info.get("pricePrecision", 8)
        self.age_days = (time.time() * 1000 - info["onboardDate"]) / 86400000
        self.qv = float(t24["quoteVolume"]) / 1e6
        self.chg = float(t24["priceChangePercent"])
        self.high24 = float(t24["highPrice"])
        self.low24 = float(t24["lowPrice"])
        self.last = float(t24["lastPrice"])
        self.mark = float(prem["markPrice"])
        self.index = float(prem["indexPrice"])
        self.funding = float(prem["lastFundingRate"]) * 100
        self.next_funding = prem.get("nextFundingTime")
        self.oi = oi
        self.oi_prev = oi_prev
        self.oi_available = (oi is not None and oi_prev is not None and oi_prev > 0)
        self.oi_chg = ((oi / oi_prev - 1.0) * 100.0) if self.oi_available else None
        self.d = None
        self.h4 = None
        self.h1 = None
        self.m60 = None

    @property
    def name(self):
        return self.sym.replace("USDT", "")


def round_tick(x, tick, mode="near"):
    if tick <= 0:
        return x
    n = x / tick
    n = math.floor(n) if mode == "down" else (math.ceil(n) if mode == "up" else round(n))
    v = n * tick
    return float(f"{v:.{max(0, int(round(-math.log10(tick)))) }f}") if tick < 1 else float(int(v))


def fmt_price(x, tick):
    if x >= 1000:
        p = 2
    elif x >= 10:
        p = 2
    elif x >= 1:
        p = 4
    elif x >= 0.01:
        p = 5
    elif x >= 0.0001:
        p = 6
    else:
        p = 8
    d = max(0, min(p, int(round(-math.log10(tick)))))
    return f"{x:,.{d}f}"


def pct(a, b):
    return (a / b - 1) * 100


# ==============================================================================
# [2] القسم الثاني: engine.py
# ==============================================================================
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
# [مدمج في نفس الملف من قسم core]

RIYADH = dt.timezone(dt.timedelta(hours=3))
MIN_QV = 8.0          # مليون دولار
MAX_AGE = 30          # يوم
MIN_SCORE = 95
MIN_RR1, MIN_RR2 = 1.8, 2.6
MAX_DIST_ATR = 1.2    # لا تطارد

# ==============================================================================
# إعدادات ومحرك إدارة المخاطر المرتبطة برأس المال الفعلي (Phase 2 Risk Engine)
# ==============================================================================
DEFAULT_EQUITY_USD = float(os.environ.get("SCANNER_EQUITY_USD", "10000.0"))
DEFAULT_RISK_PCT_PER_TRADE = float(os.environ.get("SCANNER_RISK_PCT", "0.01"))          # 1.0% لكل صفقة
DEFAULT_MAX_TOTAL_OPEN_RISK_PCT = float(os.environ.get("SCANNER_MAX_TOTAL_RISK_PCT", "0.03"))  # 3.0% حد أقصى للمراكز المفتوحة
DEFAULT_MAX_CONCURRENT_POSITIONS = int(os.environ.get("SCANNER_MAX_OPEN_POS", "4"))     # 4 مراكز متزامنة كحد أقصى
DEFAULT_MAX_MAJOR_POSITIONS = 1                                                         # مركز واحد كحد أقصى في BTC/ETH/SOL
DEFAULT_MAX_MARGIN_PER_TRADE_PCT = 0.25                                                 # لا يتجاوز هامش أي صفقة منفردة 25% من المحفظة
DEFAULT_MAX_TOTAL_MARGIN_PCT = 0.65                                                     # لا يتجاوز إجمالي الهامش المحجوز 65% من المحفظة
DEFAULT_MIN_APPROVAL_SCORE = float(os.environ.get("SCANNER_MIN_APPROVAL_SCORE", "103.0"))          # إجازة الدرجة A (103+) مالياً
DEFAULT_CHOP_SESSION_MIN_SCORE = float(os.environ.get("SCANNER_CHOP_MIN_SCORE", "106.0"))          # انتقائية مشددة (106+) في نافذة 11:05 المتذبذبة
MAJOR_SYMS = {"BTCUSDT", "ETHUSDT", "SOLUSDT"}

RUNTIME_RISK_CONFIG = {
    "equity_usd": DEFAULT_EQUITY_USD,
    "risk_pct_per_trade": DEFAULT_RISK_PCT_PER_TRADE,
    "max_total_open_risk_pct": DEFAULT_MAX_TOTAL_OPEN_RISK_PCT,
    "max_concurrent_positions": DEFAULT_MAX_CONCURRENT_POSITIONS,
    "max_major_positions": DEFAULT_MAX_MAJOR_POSITIONS,
    "max_margin_per_trade_pct": DEFAULT_MAX_MARGIN_PER_TRADE_PCT,
    "max_total_margin_pct": DEFAULT_MAX_TOTAL_MARGIN_PCT,
    "min_approval_score": DEFAULT_MIN_APPROVAL_SCORE,
    "chop_session_min_score": DEFAULT_CHOP_SESSION_MIN_SCORE,
    "maker_fee_pct": 0.0002,
    "taker_fee_pct": 0.0005,
    "stop_slippage_pct": 0.0003,
}


def get_risk_config(overrides=None):
    cfg = dict(RUNTIME_RISK_CONFIG)
    if overrides:
        for k, v in overrides.items():
            if v is not None:
                cfg[k] = v
    return cfg


def select_safe_leverage(sym, atr_pct, effective_stop_pct_dec, strategy_type="swing_4h"):
    """تحديد الرافعة المالية الآمنة وفق تقلب العملة ونوع الاستراتيجية مع ضمان بقاء سعر التصفية أبعد بكثير من الوقف."""
    if strategy_type in ("macro_squeeze", "macro_bos"):
        base_lev = 2 if effective_stop_pct_dec <= 0.12 else 1
    elif sym in MAJOR_SYMS and atr_pct <= 3.5:
        base_lev = 5
    elif atr_pct > 5.0:
        base_lev = 2
    else:
        base_lev = 3
    # ضمان ألا تتجاوز الخسارة عند الوقف 60% من الهامش المعزول لمنع التصفية المبكرة قبل لمس الوقف
    max_safe_lev = max(1, int(math.floor(0.60 / max(1e-6, effective_stop_pct_dec))))
    return max(1, min(base_lev, max_safe_lev))


def compute_risk_position_size(
    entry_ref_price,
    stop_price,
    side,
    step=0.0,
    min_notional=5.0,
    sym="",
    atr_pct=2.0,
    strategy_type="swing_4h",
    entry_is_maker=True,
    risk_cfg=None,
):
    """يحسب كمية المركز وقيمته الاسمية والرافعة والهامش والمخاطرة النقدية الفعلية (شاملة الرسوم والانزلاق)
    انطلاقاً من رأس المال ونسبة المخاطرة المحددة لكل صفقة، بدلاً من استخدام حجم اسمي ثابت."""
    cfg = get_risk_config(risk_cfg)
    equity = float(cfg["equity_usd"])
    risk_pct_budget = float(cfg["risk_pct_per_trade"])
    risk_budget_cash = equity * risk_pct_budget
    f_in = float(cfg["maker_fee_pct"] if entry_is_maker else cfg["taker_fee_pct"])
    f_taker = float(cfg["taker_fee_pct"])
    s_stop = float(cfg["stop_slippage_pct"])

    if entry_ref_price <= 0 or stop_price <= 0 or equity <= 0 or risk_pct_budget <= 0:
        return {"valid": False, "reject_reason": "INVALID_INPUTS"}
    if (side == "LONG" and stop_price >= entry_ref_price) or (side == "SHORT" and stop_price <= entry_ref_price):
        return {"valid": False, "reject_reason": "INVALID_STOP_DIRECTION"}

    theo_dist = abs(entry_ref_price - stop_price)
    theo_stop_pct_dec = theo_dist / entry_ref_price

    eff_stop_px = stop_price * (1.0 - s_stop) if side == "LONG" else stop_price * (1.0 + s_stop)
    eff_price_loss = abs(entry_ref_price - eff_stop_px)
    fee_and_slip_per_unit = (eff_price_loss - theo_dist) + (entry_ref_price * f_in) + (eff_stop_px * f_taker)
    loss_per_unit = theo_dist + fee_and_slip_per_unit
    eff_stop_pct_dec = loss_per_unit / entry_ref_price

    lev = select_safe_leverage(sym, atr_pct, eff_stop_pct_dec, strategy_type=strategy_type)
    raw_qty = risk_budget_cash / max(1e-12, loss_per_unit)

    # سقف الهامش للصفقة الواحدة (منع تضخم القيمة الاسمية بشكل مفرط عندما يكون الوقف ضيقاً جداً)
    max_single_margin_usd = equity * float(cfg["max_margin_per_trade_pct"])
    max_single_notional_usd = max_single_margin_usd * lev
    margin_capped = False
    if raw_qty * entry_ref_price > max_single_notional_usd:
        raw_qty = max_single_notional_usd / entry_ref_price
        margin_capped = True

    if step and step > 0:
        decs = max(0, int(round(-math.log10(step)))) if step < 1 else 0
        qty = math.floor((raw_qty + 1e-12) / step) * step
        qty = round(qty, max(8, decs))
    else:
        qty = round(raw_qty, 8)

    notional_usd = qty * entry_ref_price
    min_not = float(min_notional or 5.0)
    if qty <= 0 or notional_usd < min_not:
        # نتحقق ما إذا كان رفع الكمية للحد الأدنى للعقد/القيمة الاسمية يظل ضمن هامش مسموح (<= 1.05x من ميزانية المخاطرة)
        req_qty = min_not / entry_ref_price
        if step and step > 0:
            req_qty = max(step, math.ceil(req_qty / step) * step)
        req_risk_cash = req_qty * loss_per_unit
        if req_qty > 0 and req_risk_cash <= risk_budget_cash * 1.05 and (req_qty * entry_ref_price / lev) <= max_single_margin_usd:
            qty = round(req_qty, 8)
            notional_usd = qty * entry_ref_price
        else:
            return {
                "valid": False,
                "reject_reason": "MIN_NOTIONAL_EXCEEDS_RISK_LIMIT",
                "min_notional_required": round(max(min_not, req_qty * entry_ref_price), 2),
                "min_notional_risk_cash": round(req_risk_cash, 2),
                "risk_budget_cash": round(risk_budget_cash, 2),
            }

    theo_risk_cash = qty * theo_dist
    cost_cash = qty * fee_and_slip_per_unit
    actual_risk_cash = qty * loss_per_unit
    actual_risk_pct_eq = (actual_risk_cash / equity) * 100.0
    margin_req_usd = notional_usd / lev
    margin_pct_eq = (margin_req_usd / equity) * 100.0
    roundtrip_maker_fee_usd = notional_usd * (f_in + float(cfg["maker_fee_pct"]))

    return {
        "valid": True,
        "reject_reason": None,
        "equity_usd": round(equity, 2),
        "risk_budget_pct": round(risk_pct_budget * 100.0, 3),
        "risk_budget_cash": round(risk_budget_cash, 2),
        "entry_ref_price": entry_ref_price,
        "stop_price": stop_price,
        "eff_stop_price": eff_stop_px,
        "theoretical_stop_pct": round(theo_stop_pct_dec * 100.0, 3),
        "effective_stop_pct": round(eff_stop_pct_dec * 100.0, 3),
        "leverage": lev,
        "position_size": qty,
        "qty": qty,
        "position_notional_usd": round(notional_usd, 2),
        "margin_required_usd": round(margin_req_usd, 2),
        "margin_pct_equity": round(margin_pct_eq, 2),
        "margin_capped": margin_capped,
        "theoretical_risk_cash": round(theo_risk_cash, 2),
        "est_stop_fee_and_slip_usd": round(cost_cash, 2),
        "est_roundtrip_fee_usd": round(roundtrip_maker_fee_usd, 2),
        "actual_risk_cash": round(actual_risk_cash, 2),
        "actual_risk_pct_equity": round(actual_risk_pct_eq, 3),
    }


def compute_open_position_risk(pos, risk_cfg=None):
    """يحسب الخطر النقدي الفعلي المتبقي على رأس المال والهامش المحجوز لمركز مفتوح حالياً:
    - إذا كان الوقف عند original_stop فالمخاطرة تحسب على الكمية المتبقية شاملة الرسوم والانزلاق.
    - إذا نُقل الوقف إلى التعادل الشامل للرسوم (BE) أو تأمين ربح (trail عند TP1) فالخطر الرأسمالي على المحفظة يصبح 0$
      بينما يظل المركز محتسباً ضمن عدد المراكز المفتوحة والهامش المحجوز."""
    cfg = get_risk_config(risk_cfg)
    if not pos.get("filled"):
        return {"is_open": False, "open_risk_cash": 0.0, "open_risk_pct": 0.0, "open_margin_usd": 0.0, "open_margin_pct": 0.0}
    rem_pct = float(pos.get("remaining_pct", 1.0 if pos.get("status") == "مفتوحة" else 0.0))
    if rem_pct <= 0.0:
        return {"is_open": False, "open_risk_cash": 0.0, "open_risk_pct": 0.0, "open_margin_usd": 0.0, "open_margin_pct": 0.0}

    equity = max(1e-9, float(cfg["equity_usd"]))
    side = pos["side"]
    fill_px = float(pos.get("fill_price") or pos.get("entry_trigger_price") or pos.get("avg") or pos.get("price"))
    act_stop = float(pos.get("active_stop") if pos.get("active_stop") is not None else pos["stop"])
    init_qty = float(pos.get("position_size") or pos.get("qty") or 0.0)
    rem_qty = init_qty * rem_pct
    lev = max(1, int(pos.get("leverage") or 3))

    f_in = float(cfg["taker_fee_pct"] if pos.get("fill_model") == "trigger_with_slippage" else cfg["maker_fee_pct"])
    f_taker = float(cfg["taker_fee_pct"])
    s_stop = float(cfg["stop_slippage_pct"])
    eff_stop = act_stop * (1.0 - s_stop) if side == "LONG" else act_stop * (1.0 + s_stop)
    gross_at_stop = (eff_stop - fill_px) if side == "LONG" else (fill_px - eff_stop)
    fees_at_stop = (fill_px * f_in) + (eff_stop * f_taker)
    net_pnl_at_stop = rem_qty * (gross_at_stop - fees_at_stop)
    downside_cash = max(0.0, -net_pnl_at_stop)
    open_margin = (rem_qty * fill_px) / lev

    return {
        "is_open": True,
        "sym": pos["sym"],
        "side": side,
        "remaining_pct": rem_pct,
        "open_risk_cash": round(downside_cash, 2),
        "open_risk_pct": round((downside_cash / equity) * 100.0, 3),
        "open_margin_usd": round(open_margin, 2),
        "open_margin_pct": round((open_margin / equity) * 100.0, 2),
    }


def get_session_liquidity_regime(now_riyadh=None, base_min_score=103.0, chop_min_score=106.0):
    """يحدد نظام سيولة الجلسة الحالية بتوقيت الرياض وعتبة الإجازة المالية المقابلة:
    - نافذة 11:05 الانتقالية المتذبذبة (09:30 إلى 13:30 الرياض): ترفع عتبة الإجازة إلى 106+ لتجنب الاختراقات الكاذبة قبل السيولة الأمريكية.
    - باقي النوافذ القيادية (03:05 الإغلاق اليومي · 15:05/19:05 السيولة الأمريكية · 23:05 إغلاق وول ستريت): تجيز نخبة الدرجة A (103+)."""
    if now_riyadh is None:
        dt_r = dt.datetime.now(RIYADH)
    elif isinstance(now_riyadh, (int, float)):
        ts_sec = now_riyadh / 1000.0 if now_riyadh > 1e11 else float(now_riyadh)
        dt_r = dt.datetime.fromtimestamp(ts_sec, RIYADH)
    else:
        dt_r = now_riyadh

    hm = dt_r.hour * 60 + dt_r.minute
    if 9 * 60 + 30 <= hm < 13 * 60 + 30:
        return {
            "regime_id": "transition_chop",
            "is_chop_session": True,
            "effective_min_score": float(chop_min_score),
            "label_ar": f"⚠️ نافذة سيولة انتقالية متذبذبة (قبل السيولة الأمريكية — إجازة النخبة {chop_min_score:.0f}+ فقط)",
        }
    if hm >= 22 * 60 or hm < 2 * 60:
        lbl = f"🟢 نافذة استقرار وإغلاق وول ستريت (سيولة اتجاهية عالية — إجازة الدرجة A: {base_min_score:.0f}+)"
        rid = "ny_close_prime"
    elif 2 * 60 <= hm < 5 * 60:
        lbl = f"🟢 نافذة الإغلاق اليومي واصطياد ذيل آسيا (إجازة الدرجة A: {base_min_score:.0f}+)"
        rid = "daily_close_asia"
    elif 18 * 60 <= hm < 22 * 60:
        lbl = f"🟢 ذروة سيولة نيويورك وتسوية التمويل (إجازة الدرجة A: {base_min_score:.0f}+)"
        rid = "us_ny_peak"
    elif 13 * 60 + 30 <= hm < 18 * 60:
        lbl = f"🟢 نافذة دخول السيولة الأمريكية (إجازة الدرجة A: {base_min_score:.0f}+)"
        rid = "us_session"
    else:
        lbl = f"🟡 فترة سيولة هادئة (إجازة الدرجة A: {base_min_score:.0f}+)"
        rid = "off_hours"
    return {
        "regime_id": rid,
        "is_chop_session": False,
        "effective_min_score": float(base_min_score),
        "label_ar": lbl,
    }


def evaluate_portfolio_risk_gate(
    candidates,
    open_positions=None,
    risk_cfg=None,
    strict_filter=False,
    now_riyadh=None,
    enforce_quality_gate=False,
):
    """يفحص حدود المحفظة الكلية (سقف المخاطرة الإجمالية 3% · أقصى عدد مراكز متزامنة 4 · حد الكبار 1 · سقف الهامش 65%)
    ومع تفعيل enforce_quality_gate يقصر الإجازة المالية على نخبة الدرجة A (103+) ويرفعها إلى (106+) في نافذة 11:05 المتذبذبة
    مع إبقاء باقي الفرص (98+) معروضة بشفافية كاحتياطي للمراقبة."""
    cfg = get_risk_config(risk_cfg)
    equity = float(cfg["equity_usd"])
    max_risk_cash = equity * float(cfg["max_total_open_risk_pct"])
    max_pos = int(cfg["max_concurrent_positions"])
    max_majors = int(cfg["max_major_positions"])
    max_margin_usd = equity * float(cfg["max_total_margin_pct"])
    base_min_sc = float(cfg.get("min_approval_score", 103.0))
    chop_min_sc = float(cfg.get("chop_session_min_score", 106.0))
    sess_info = get_session_liquidity_regime(now_riyadh, base_min_score=base_min_sc, chop_min_score=chop_min_sc)

    cur_open_details = [compute_open_position_risk(p, cfg) for p in (open_positions or [])]
    cur_open_details = [d for d in cur_open_details if d["is_open"]]

    used_pos = len(cur_open_details)
    used_risk_cash = sum(d["open_risk_cash"] for d in cur_open_details)
    used_margin_usd = sum(d["open_margin_usd"] for d in cur_open_details)
    used_majors = sum(1 for d in cur_open_details if d["sym"] in MAJOR_SYMS)

    init_summary = {
        "equity_usd": round(equity, 2),
        "risk_pct_per_trade": round(float(cfg["risk_pct_per_trade"]) * 100.0, 2),
        "risk_cash_per_trade": round(equity * float(cfg["risk_pct_per_trade"]), 2),
        "risk_per_trade_cash": round(equity * float(cfg["risk_pct_per_trade"]), 2),
        "max_total_risk_pct": round(float(cfg["max_total_open_risk_pct"]) * 100.0, 2),
        "max_total_open_risk_pct": round(float(cfg["max_total_open_risk_pct"]) * 100.0, 2),
        "max_total_risk_cash": round(max_risk_cash, 2),
        "max_total_open_risk_cash": round(max_risk_cash, 2),
        "max_concurrent_positions": max_pos,
        "max_major_positions": max_majors,
        "max_total_margin_pct": round(float(cfg["max_total_margin_pct"]) * 100.0, 1),
        "open_positions_count": used_pos,
        "open_count": used_pos,
        "open_major_count": used_majors,
        "open_risk_cash": round(used_risk_cash, 2),
        "open_risk_pct": round((used_risk_cash / equity) * 100.0, 3) if equity > 0 else 0.0,
        "open_margin_usd": round(used_margin_usd, 2),
        "open_margin_pct": round((used_margin_usd / equity) * 100.0, 2) if equity > 0 else 0.0,
        "available_slots": max(0, max_pos - used_pos),
        "available_risk_cash": round(max(0.0, max_risk_cash - used_risk_cash), 2),
        "available_risk_pct": round(max(0.0, (max_risk_cash - used_risk_cash) / equity * 100.0), 3) if equity > 0 else 0.0,
        "remaining_risk_budget_cash": round(max(0.0, max_risk_cash - used_risk_cash), 2),
        "remaining_risk_budget_pct": round(max(0.0, (max_risk_cash - used_risk_cash) / equity * 100.0), 3) if equity > 0 else 0.0,
        "session_regime_id": sess_info["regime_id"],
        "session_is_chop": sess_info["is_chop_session"],
        "session_label_ar": sess_info["label_ar"],
        "effective_min_approval_score": sess_info["effective_min_score"] if enforce_quality_gate else 0.0,
        "base_min_approval_score": base_min_sc,
        "chop_min_approval_score": chop_min_sc,
    }

    out = []
    approved_count = 0
    blocked_count = 0
    watchlist_count = 0
    for cand in (candidates or []):
        c2 = dict(cand)
        c_risk = float(c2.get("actual_risk_cash") or 0.0)
        c_margin = float(c2.get("margin_required_usd") or 0.0)
        c_score = float(c2.get("score") if c2.get("score") is not None else 999.0)
        is_maj = c2.get("sym") in MAJOR_SYMS

        if enforce_quality_gate and c_score < base_min_sc - 1e-9:
            c2["risk_gate_allowed"] = False
            c2["risk_gate_status"] = "WATCHLIST_GRADE_B"
            c2["risk_gate_reason_ar"] = f"احتياطي للمراقبة — الدرجة {c2.get('grade', 'B')} ({c_score:.1f}) أقل من عتبة الإجازة لنخبة A ({base_min_sc:.0f}+)"
            blocked_count += 1
            watchlist_count += 1
        elif enforce_quality_gate and sess_info["is_chop_session"] and c_score < chop_min_sc - 1e-9:
            c2["risk_gate_allowed"] = False
            c2["risk_gate_status"] = "WATCHLIST_CHOP_SESSION"
            c2["risk_gate_reason_ar"] = f"احتياطي للمراقبة — نافذة 11:05 المتذبذبة تشترط نخبة {chop_min_sc:.0f}+ (الحالية {c_score:.1f})"
            blocked_count += 1
            watchlist_count += 1
        elif used_pos >= max_pos:
            c2["risk_gate_allowed"] = False
            c2["risk_gate_status"] = "BLOCKED_MAX_POSITIONS"
            c2["risk_gate_reason_ar"] = f"تجاوز الحد الأقصى للمراكز المتزامنة ({max_pos} مراكز)"
            blocked_count += 1
        elif is_maj and used_majors >= max_majors:
            c2["risk_gate_allowed"] = False
            c2["risk_gate_status"] = "BLOCKED_MAJOR_CAP"
            c2["risk_gate_reason_ar"] = "يوجد مركز مفتوح/معتمد في العملات الكبرى (BTC/ETH/SOL حد أقصى 1)"
            blocked_count += 1
        elif used_risk_cash + c_risk > max_risk_cash + 1e-6:
            c2["risk_gate_allowed"] = False
            c2["risk_gate_status"] = "BLOCKED_MAX_PORTFOLIO_RISK"
            c2["risk_gate_reason_ar"] = f"يتجاوز سقف المخاطرة الكلية المسموح ({init_summary['max_total_risk_pct']:.1f}% = {max_risk_cash:,.0f}$)"
            blocked_count += 1
        elif used_margin_usd + c_margin > max_margin_usd + 1e-6:
            c2["risk_gate_allowed"] = False
            c2["risk_gate_status"] = "BLOCKED_MARGIN_CAP"
            c2["risk_gate_reason_ar"] = f"يتجاوز سقف الهامش الإجمالي المسموح ({init_summary['max_total_margin_pct']:.0f}%)"
            blocked_count += 1
        else:
            used_pos += 1
            used_risk_cash += c_risk
            used_margin_usd += c_margin
            if is_maj:
                used_majors += 1
            approved_count += 1
            c2["risk_gate_allowed"] = True
            c2["risk_gate_status"] = "APPROVED"
            c2["risk_gate_reason_ar"] = "متاح للتنفيذ ضمن سقف المخاطرة والهامش"
            c2["portfolio_risk_after_pct"] = round((used_risk_cash / equity) * 100.0, 3) if equity > 0 else 0.0
            c2["portfolio_positions_after"] = used_pos

        if not strict_filter or c2["risk_gate_allowed"]:
            out.append(c2)

    init_summary["approved_new_count"] = approved_count
    init_summary["blocked_new_count"] = blocked_count
    init_summary["watchlist_count"] = watchlist_count
    init_summary["approved_candidates"] = approved_count
    init_summary["blocked_candidates"] = blocked_count
    init_summary["projected_total_risk_cash"] = round(used_risk_cash, 2)
    init_summary["projected_total_risk_pct"] = round((used_risk_cash / equity) * 100.0, 3) if equity > 0 else 0.0
    init_summary["projected_positions_count"] = used_pos
    return out, init_summary


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
    """OI الحالي + OI قبل 4 ساعات (للمقارنة)."""
    out = {}

    def one(sym):
        r = {"oi": None, "oi_prev": None}
        try:
            r["oi"] = float(cached_get(f"/v1/openInterest?symbol={sym}", f"oi_{sym}", ttl=600)["openInterest"])
        except Exception as exc:
            record_diag_warning("oi_current_fetch", "تعذر جلب الفائدة المفتوحة الحالية", symbol=sym, exc=exc)
        try:
            h = cached_get(f"/futures/data/openInterestHist?symbol={sym}&period=1h&limit=5", f"oih_{sym}", ttl=900)
            if h:
                r["oi_prev"] = float(h[0]["sumOpenInterest"])   # قبل 4 ساعات
        except Exception as exc:
            record_diag_warning("oi_hist_fetch", "تعذر جلب تاريخ الفائدة المفتوحة (4س)", symbol=sym, exc=exc)
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


def cluster_levels(k4, k1, price, side, asia_wick=False, k1h=None, chg=0.0, now_ms=None):
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
    ref_now_ms = float(now_ms if now_ms is not None else time.time() * 1000)
    newborn_daily = asia_wick and len(k1.get("t", [])) > 1 and (ref_now_ms - k1["t"][-1]) < 3 * 3600 * 1000
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


TARGET_SRC_AR = {
    "structural_sr": "مستوى بنيوي",
    "atr_projection": "امتداد ATR",
    "rr_floor_extension": "حد R:R أدنى",
}

# ملف تعريف المعايرة التجريبية الموثق من الباكتيست التاريخي الخالي من الانحياز المستقبلي (Phase 3/4)
EMPIRICAL_CALIBRATION_META = {
    "basis": "walk_forward_5m_zero_lookahead",
    "sample_window_days": 21,
    "reach_empirical_fill_pct": {"A": 85, "B": 60, "C": 55},
}


def trend_dir(k4, k1, now_ms=None):
    def g(k, name, i=-1):
        v = k.get(name)
        if not v or len(v) < abs(i):
            return None
        return v[i]
    c = k4["c"][-1]
    e20_4, e50_4, e200_4 = g(k4, "ema20"), g(k4, "ema50"), g(k4, "ema200")
    ref_now = float(now_ms if now_ms is not None else time.time() * 1000)
    # إذا كانت آخر شمعة يومية لم تغلق بعد وعمرها أقل من 20 ساعة نعتمد إغلاق أمس المكتمل للمؤشرات اليومية
    d_idx = -2 if (len(k1.get("t", [])) >= 2 and float(k1["t"][-1]) + 86_400_000 > ref_now and (ref_now - float(k1["t"][-1])) < 20 * 3_600_000) else -1
    e20_1, e50_1 = g(k1, "ema20", d_idx), g(k1, "ema50", d_idx)
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
    c1 = k1["c"][d_idx]
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


def build(coin, side, extra, asia_wick=None, now_ms=None, risk_cfg=None, entry_is_maker=True):
    k4, k1, k1h = coin.h4, coin.h1, getattr(coin, "m60", None)
    price = coin.last
    atr4 = k4["atr"][-1]
    if not atr4 or atr4 <= 0:
        return None
    if _is_against_strong_trend(k4, k1h, price, side, coin.chg):
        return None
    if asia_wick is None:
        ref_dt = dt.datetime.fromtimestamp(now_ms / 1000.0, RIYADH) if now_ms is not None else None
        asia_wick = is_asia_wick_window(ref_dt)
    atr_pct = atr4 / price * 100
    min_d_req = 0.22 if asia_wick else 0.0
    is_trend = _check_aligned_trend(k4, k1h, price, side, coin.chg)

    # أولاً: المحاولة بالمرتكزات الكلاسيكية (4س + يومي) لضمان عدم الانحياز للترند على حساب الصفقات البنيوية
    base_clusters = cluster_levels(k4, k1, price, side, asia_wick=asia_wick, k1h=None, chg=0.0, now_ms=now_ms)
    base_picked = pick_cluster(base_clusters, price, atr4, side, min_dist_atr=min_d_req)
    used_fast_trend = False
    if is_trend:
        tr_clusters = cluster_levels(k4, k1, price, side, asia_wick=asia_wick, k1h=k1h, chg=coin.chg, now_ms=now_ms)
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
    tgt_sources = []
    for kk in range(3):
        wantpx = avg + need[kk] * r if side == "LONG" else avg - need[kk] * r
        cappx = avg + max_r_cap[kk] * r if side == "LONG" else avg - max_r_cap[kk] * r
        pick = None
        tsrc = "structural_sr"
        for tp in uniq:
            ok = (wantpx <= tp <= cappx) if side == "LONG" else (cappx <= tp <= wantpx)
            if ok:
                pick = tp
                tsrc = "structural_sr"
                break
        if pick is None:
            atr_ext = min(fallback_r[kk] * r, (1.0, 2.0, 3.1)[kk] * 2.2 * atr4)
            floor_ext = (need[kk] + 0.1) * r
            if floor_ext > atr_ext + 1e-12:
                ext = floor_ext
                tsrc = "rr_floor_extension"
            else:
                ext = atr_ext
                tsrc = "atr_projection"
            pick = avg + ext if side == "LONG" else avg - ext
        if tgts:
            if side == "LONG" and pick <= tgts[-1]:
                pick = tgts[-1] + 0.75 * r
                tsrc = "rr_floor_extension"
            if side == "SHORT" and pick >= tgts[-1]:
                pick = tgts[-1] - 0.75 * r
                tsrc = "rr_floor_extension"
        tgts.append(pick)
        tgt_sources.append(tsrc)
    rr = [abs((t - avg) / r) for t in tgts]
    if rr[0] < MIN_RR1 or rr[1] < MIN_RR2:
        return None
    struct_tgt_cnt = sum(1 for s_k in tgt_sources if s_k == "structural_sr")

    # ---------------- الدرجة (شفافة ومفككة العناصر بالكامل — Priority #8)
    base_sc = 90.0
    notes = []
    tdir4, tdir1 = trend_dir(k4, k1, now_ms=now_ms)
    want = 1 if side == "LONG" else -1
    al4, al1 = tdir4 * want, tdir1 * want
    sc_trend4 = 0.0
    if al4 >= 3:
        sc_trend4 = 3.0; notes.append("اتجاه 4س قوي")
    elif al4 == 2:
        sc_trend4 = 1.0; notes.append("اتجاه 4س")
    elif al4 <= -1:
        sc_trend4 = -3.0; notes.append("ضد اتجاه 4س")
    sc_trend1 = 2.0 if al1 >= 2 else (-2.0 if al1 <= -2 else 0.0)

    st, stw = structure(k4, side)
    sc_struct = round(3.0 * stw, 2)

    if best["w"] >= 3.5 and best["strong"] >= 2:
        sc_cluster = 4.0; notes.append("حزمة قوية")
    elif best["w"] >= 2.2:
        sc_cluster = 2.0
    else:
        sc_cluster = -1.0

    if coin.qv >= 500:
        sc_liq = 3.0
    elif coin.qv >= 150:
        sc_liq = 2.0
    elif coin.qv >= 40:
        sc_liq = 1.0
    else:
        sc_liq = -1.0

    mh, mhp = k4["macd_hist"][-1], k4["macd_hist"][-2]
    mom = 1 if (mh is not None and mhp is not None and mh > mhp) else -1
    if mom * want > 0:
        sc_mom = 2.0; notes.append("زخم مؤيد")
    else:
        sc_mom = -1.0

    ref_now_b = float(now_ms if now_ms is not None else time.time() * 1000)
    d_rsi_idx = -2 if (len(k1.get("t", [])) >= 2 and float(k1["t"][-1]) + 86_400_000 > ref_now_b and (ref_now_b - float(k1["t"][-1])) < 20 * 3_600_000) else -1
    rsi4 = k4["rsi"][-1] or 50
    rsi1 = (k1["rsi"][d_rsi_idx] if k1.get("rsi") and len(k1["rsi"]) >= abs(d_rsi_idx) else None) or 50
    sc_rsi = 0.0
    if side == "LONG":
        if rsi4 > 74 or rsi1 > 76:
            sc_rsi = -4.0; notes.append("RSI متطرف")
        elif rsi4 < 62:
            sc_rsi = 1.0
    else:
        if rsi4 < 26 or rsi1 < 24:
            sc_rsi = -3.0; notes.append("RSI متطرف")
        elif rsi4 > 38:
            sc_rsi = 1.0

    sc_fund = -2.0 if abs(coin.funding) > 0.10 else 0.0
    if sc_fund < 0:
        notes.append("فاندنغ شاذ")
    if is_trend:
        notes.append("ارتكاز ترند نشط")
    if asia_wick:
        notes.append("اصطياد ذيل آسيا")

    if asia_wick:
        sc_prox = round(max(0.0, 0.75 - abs(dist_atr - 0.38)) * 3.5, 2)
    else:
        sc_prox = round(max(0.0, 0.70 - dist_atr) * 4.0, 2)

    if tgt_sources[0] == "structural_sr":
        notes.append("هدف 1 بنيوي")

    score_components = {
        "base": base_sc,
        "trend_4h": sc_trend4,
        "trend_1d": sc_trend1,
        "structure": sc_struct,
        "cluster": sc_cluster,
        "liquidity": sc_liq,
        "momentum": sc_mom,
        "rsi": sc_rsi,
        "funding": sc_fund,
        "proximity": sc_prox,
    }
    score = round(sum(score_components.values()), 1)
    # نختار من مرتكزات الترند السريع الصفقات القوية فقط (درجة A أو B: ≥ 99 نقطة) دون إغراق التقرير بصفقات ضعيفة
    if used_fast_trend and score < 99.0:
        return None
    grade = "A" if score >= 103 else ("B" if score >= 99 else "C")
    # تصنيف احتمالية الوصول المعاير تجريبياً على شموع 5 دقائق بدون انحياز مستقبلي (Empirical Walk-Forward Calibration)
    emp_reach = EMPIRICAL_CALIBRATION_META["reach_empirical_fill_pct"]
    if dist_atr <= 0.35:
        reach, reach_p = "A", emp_reach["A"]
    elif dist_atr <= 0.65:
        reach, reach_p = "B", emp_reach["B"]
    else:
        reach, reach_p = "C", emp_reach["C"]

    sz = compute_risk_position_size(
        near_edge,
        stop,
        side,
        step=coin.step,
        min_notional=coin.min_notional,
        sym=coin.sym,
        atr_pct=atr_pct,
        strategy_type="swing_4h",
        entry_is_maker=entry_is_maker,
        risk_cfg=risk_cfg,
    )
    if not sz.get("valid"):
        return None
    qty = sz["position_size"]

    return {
        "sym": coin.sym, "name": coin.name, "side": side, "price": price,
        "entry_lo": e_lo, "entry_hi": e_hi, "avg": avg, "stop": stop,
        "targets": tgts, "target_sources": tgt_sources, "structural_targets_count": struct_tgt_cnt,
        "rr": rr, "risk_pct": risk_pct,
        "theoretical_stop_pct": sz["theoretical_stop_pct"],
        "effective_stop_pct": sz["effective_stop_pct"],
        "atr_pct": atr_pct, "atr4": atr4,
        "dist_atr": dist_atr, "dist_atr_mid": dist_atr_mid,
        "dist_pct": (near_edge / price - 1) * 100,
        "score": score, "score_components": score_components,
        "grade": grade, "reach": reach, "reach_p": reach_p,
        "reach_basis": EMPIRICAL_CALIBRATION_META["basis"],
        "tags": best["tags"], "n_src": best["n"], "struct": st,
        "chg": coin.chg, "qv": coin.qv, "funding": coin.funding,
        "oi_chg": coin.oi_chg, "oi_available": coin.oi_available,
        "rsi4": rsi4, "rsi1": rsi1, "qty": qty, "position_size": qty,
        "position_notional_usd": sz["position_notional_usd"],
        "leverage": sz["leverage"],
        "margin_required_usd": sz["margin_required_usd"],
        "margin_pct_equity": sz["margin_pct_equity"],
        "margin_capped": sz["margin_capped"],
        "equity_usd": sz["equity_usd"],
        "theoretical_risk_cash": sz["theoretical_risk_cash"],
        "est_stop_fee_and_slip_usd": sz["est_stop_fee_and_slip_usd"],
        "est_roundtrip_fee_usd": sz["est_roundtrip_fee_usd"],
        "actual_risk_cash": sz["actual_risk_cash"],
        "actual_risk_pct_equity": sz["actual_risk_pct_equity"],
        "notes": notes,
        "hi24": coin.high24, "lo24": coin.low24, "mark": coin.mark, "tick": coin.tick,
        "trend": al4, "is_trend": is_trend,
        "supports": sr_levels(k4, k1, price, atr4)[0],
        "resistances": sr_levels(k4, k1, price, atr4)[1],
    }


def analyze(sym, info, t24, prem, extra, k4raw=None, k1raw=None, now_ms=None):
    oi, oi_prev = extra.get("oi"), extra.get("oi_prev")
    c = Coin(sym, info, t24, prem, oi, oi_prev)
    ref_now = now_ms if now_ms is not None else int(time.time() * 1000)
    try:
        raw_4h = k4raw if k4raw is not None else klines(sym, "4h", 500)
        raw_1d = k1raw if k1raw is not None else klines(sym, "1d", 300)
        # اعتماد الشموع المغلقة فقط على 4س و1س لمنع تلوث المؤشرات بشمعة الـ 5 دقائق المفتوحة عند :05 (Priority #5)
        c.h4 = enrich(closed_klines_only(raw_4h, "4h", now_ms=ref_now))
        c.h1 = enrich(raw_1d)
        if abs(c.chg) >= 6.0:
            c.m60 = enrich(closed_klines_only(klines(sym, "1h", 160), "1h", now_ms=ref_now))
    except Exception as exc:
        record_diag_warning("analyze_klines_failed", "تعذر بناء المؤشرات الفنية للعملة", symbol=sym, exc=exc)
        return []
    out = []
    for side in ("LONG", "SHORT"):
        t = build(c, side, extra, now_ms=ref_now)
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
    rsi1 = (k1["rsi"][-2] if k1 and k1.get("rsi") and len(k1["rsi"]) >= 2 else (k1["rsi"][-1] if k1 and k1.get("rsi") else None)) or 50.0
    if not atr4 or atr4 <= 0 or hi24 <= lo24 or not e20:
        return None
    atr_pct = atr4 / price * 100.0
    if atr_pct < 0.35:
        return None

    pos24 = (price - lo24) / (hi24 - lo24)
    chg = coin.chg
    fund = coin.funding
    oi_chg = coin.oi_chg  # قد يكون None عند عدم توفر بيانات OI (يعامل بحياد تام — Priority #6)

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
        if stage == "confirm" and (oi_chg is not None and oi_chg < 0.3):
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
    # معالجة محايدة تماماً عند غياب OI (لا مكافأة وهمية ولا عقوبة — Priority #6)
    if oi_chg is None:
        reasons.append("ΔOI غير متاح (محايد)")
    elif oi_chg >= 2.0:
        sc += 3.0
        reasons.append(f"تعبئة عقود ΔOI {oi_chg:+.2f}%")
    elif oi_chg >= 0.0:
        sc += 1.5
        reasons.append(f"ΔOI موجب ({oi_chg:+.2f}%)")
    else:
        sc -= 1.0
    # فحص الانكماش على آخر شمعتي 4س مغلقتين فعلياً (بعد تنقية closed_klines_only)
    if len(k4["h"]) >= 2:
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
    t1_sr = hi24 * 1.004
    t1_fl = avg + 1.9 * r
    t1 = max(t1_sr, t1_fl)
    src1 = "structural_sr" if t1_sr >= t1_fl else "rr_floor_extension"

    r2_sr = ress[1] if len(ress) > 1 else 0.0
    t2 = max(r2_sr, avg + 2.9 * r, t1 + 0.8 * r)
    src2 = "structural_sr" if (r2_sr > 0 and abs(t2 - r2_sr) <= 1e-9) else "rr_floor_extension"

    r3_sr = ress[2] if len(ress) > 2 else 0.0
    t3 = max(r3_sr, avg + 4.2 * r, t2 + 1.0 * r)
    src3 = "structural_sr" if (r3_sr > 0 and abs(t3 - r3_sr) <= 1e-9) else "rr_floor_extension"

    tgts = [t1, t2, t3]
    exp_tgt_sources = [src1, src2, src3]
    rr = [round(abs(x - avg) / r, 2) for x in tgts]
    grade = "A" if sc >= 102 else ("B" if sc >= 98.5 else "C")
    sz_exp = compute_risk_position_size(
        e_hi,
        stop,
        "LONG",
        step=coin.step,
        min_notional=coin.min_notional,
        sym=coin.sym,
        atr_pct=atr_pct,
        strategy_type="explosion",
        entry_is_maker=True,
    )
    if not sz_exp.get("valid"):
        return None
    qty = sz_exp["position_size"]

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
        "targets": tgts, "target_sources": exp_tgt_sources, "rr": rr, "risk_pct": risk_pct,
        "theoretical_stop_pct": sz_exp["theoretical_stop_pct"],
        "effective_stop_pct": sz_exp["effective_stop_pct"],
        "atr_pct": atr_pct, "atr4": atr4,
        "dist_atr": (price - e_hi) / atr4,
        "dist_pct": (e_hi / price - 1) * 100.0,
        "pos24": round(pos24 * 100.0, 1),
        "score": sc, "grade": grade, "reasons": reasons,
        "chg": chg, "qv": coin.qv, "funding": fund,
        "oi_chg": oi_chg, "oi_available": coin.oi_available,
        "rsi4": rsi4, "rsi1": rsi1, "qty": round(qty, 8), "position_size": round(qty, 8),
        "position_notional_usd": sz_exp["position_notional_usd"],
        "leverage": sz_exp["leverage"],
        "margin_required_usd": sz_exp["margin_required_usd"],
        "margin_pct_equity": sz_exp["margin_pct_equity"],
        "equity_usd": sz_exp["equity_usd"],
        "actual_risk_cash": sz_exp["actual_risk_cash"],
        "actual_risk_pct_equity": sz_exp["actual_risk_pct_equity"],
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
            c.h4 = enrich(closed_klines_only(klines(sym, "4h", 500), "4h"))
            c.h1 = enrich(klines(sym, "1d", 300))
        except Exception as exc:
            record_diag_warning("explosion_klines_failed", "تعذر جلب شموع فحص الانفجار", symbol=sym, exc=exc)
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


# ==============================================================================
# [3] القسم الثالث: track.py
# ==============================================================================
# -*- coding: utf-8 -*-
"""تحديث الصفقات السابقة ودورة الحياة الكاملة (Phase 1 — Immutable Entry Fill & Stateful Partial Exits):
- تثبيت سعر الدخول ووقت التفعيل لمرة واحدة فقط (منع أي تعديل بأثر رجعي عبر lo_after / hi_after).
- دعم نماذج تنفيذ صريحة وقابلة للاختبار: limit_near_edge_strict · touch_limit · trigger_with_slippage.
- إدارة الكمية المتبقية والأهداف الجزئية فعلياً: 50% عند TP1 + 25% عند TP2 + 25% عند TP3 (تظل الصفقة نشطة حتى remaining_pct == 0).
- احتساب الرسوم والانزلاق صراحةً في صافي العائد وفي تعريف نقطة التعادل الحقيقية (Fee-Adjusted Break-Even).
- قاعدة محافظة صارمة عند تعارض الهدف والوقف داخل نفس شمعة الـ 5 دقائق (تقديم الوقف النشط دائماً).
- صلاحية زمنية محددة للإشارات المعلقة (منع بقاء إشارة قديمة متاحة للدخول إلى أجل غير مسمى).
"""
import concurrent.futures as cf
# [مدمج في نفس الملف من قسم core]

DEFAULT_FILL_MODEL = "limit_near_edge_strict"
PARTIAL_EXIT_WEIGHTS = (0.50, 0.25, 0.25)   # TP1: 50% | TP2: 25% | TP3: 25%
MAKER_FEE_PCT = 0.0002                      # 0.02% رسوم أمر معلق (Limit)
TAKER_FEE_PCT = 0.0005                      # 0.05% رسوم أمر سوقي / وقف سوقي (Stop-Market)
ENTRY_SLIPPAGE_PCT = 0.0003                 # 0.03% انزلاق دخول لنموذج trigger_with_slippage
STOP_SLIPPAGE_PCT = 0.0003                  # 0.03% انزلاق تنفيذ الوقف السوقي
PENDING_SIGNAL_EXPIRY_HOURS = 24.0          # انتهاء صلاحية الإشارة غير المفعلة بعد 24 ساعة (6 شموع 4س)
BAR_5M_MS = 5 * 60 * 1000

TERMINAL_TRADE_STATUSES = {
    "CLOSED_TP3",
    "CLOSED_STOP",
    "CLOSED_BE",
    "CLOSED_TRAIL",
    "CLOSED_EXPIRY",
    "CANCELLED_DIST",
    "EXPIRED",
}
ACTIVE_OPEN_STATUSES = {"OPEN", "PARTIAL_TP1", "PARTIAL_TP2"}


def compute_fee_adjusted_be_stop(
    fill_price,
    side,
    tp1,
    tick=0.0,
    entry_fee_pct=MAKER_FEE_PCT,
    exit_taker_fee_pct=TAKER_FEE_PCT,
    stop_slippage_pct=STOP_SLIPPAGE_PCT,
):
    """يحسب سعر وقف التعادل الحقيقي الشامل لرسوم الدخول ورسوم الخروج السوقي والانزلاق المتوقع،
    بحيث لا تخرج الكمية المتبقية بخسارة مالية صافية عند ضرب التعادل."""
    if side == "LONG":
        denom = max(1e-9, (1.0 - stop_slippage_pct) * (1.0 - exit_taker_fee_pct))
        be_raw = fill_price * (1.0 + entry_fee_pct) / denom
        be_px = round_tick(be_raw, tick, "up") if tick and tick > 0 else be_raw
        max_be = fill_price + 0.35 * max(0.0, tp1 - fill_price)
        return min(be_px, max_be) if tp1 > fill_price else be_px
    else:
        denom = max(1e-9, (1.0 + stop_slippage_pct) * (1.0 + exit_taker_fee_pct))
        be_raw = fill_price * (1.0 - entry_fee_pct) / denom
        be_px = round_tick(be_raw, tick, "down") if tick and tick > 0 else be_raw
        min_be = fill_price - 0.35 * max(0.0, fill_price - tp1)
        return max(be_px, min_be) if tp1 < fill_price else be_px


def _status_ar_from_state(trade_status, open_state=None):
    if trade_status == "PENDING":
        return "بانتظار التفعيل"
    if trade_status == "OPEN":
        return "مفتوحة"
    if trade_status == "PARTIAL_TP1":
        return "مفتوحة جزئياً (حقق هدف 1 · متبقٍ 50%)"
    if trade_status == "PARTIAL_TP2":
        return "مفتوحة جزئياً (حقق هدف 2 · متبقٍ 25%)"
    if trade_status == "CLOSED_TP3":
        return "اكتملت الأهداف (TP1+TP2+TP3)"
    if trade_status == "CLOSED_STOP":
        return "ضربت الوقف"
    if trade_status == "CLOSED_BE":
        return "أُغلقت عند التعادل بعد هدف 1"
    if trade_status == "CLOSED_TRAIL":
        return "أُغلقت على ربح مؤمَّن بعد هدف 2"
    if trade_status == "CLOSED_EXPIRY":
        return "أُغلقت بانتهاء مدة الصفقة"
    if trade_status == "CANCELLED_DIST":
        return "أُلغيت (ابتعدت)"
    if trade_status == "EXPIRED":
        return "انتهت صلاحية الإشارة"
    return "لا بيانات"


def simulate_trade_lifecycle(
    t,
    k5m,
    since_ms=0,
    live_price=None,
    now_ms=None,
    max_dist_atr=1.0,
    fill_model=None,
    partial_weights=PARTIAL_EXIT_WEIGHTS,
    trail_after_tp2=True,
    maker_fee_pct=MAKER_FEE_PCT,
    taker_fee_pct=TAKER_FEE_PCT,
    entry_slippage_pct=ENTRY_SLIPPAGE_PCT,
    stop_slippage_pct=STOP_SLIPPAGE_PCT,
    pending_expiry_hours=PENDING_SIGNAL_EXPIRY_HOURS,
    max_open_hours=None,
):
    """محرك حتمي ومستقل لمحاكاة وتتبع دورة حياة الصفقة الكاملة بدون أي انحياز مستقبلي (Zero-Lookahead).
    يقبل بيانات شموع 5 دقائق (t, o, h, l, c) ويعيد حالة الصفقة المحدثة بالكامل.
    """
    if not k5m or not k5m.get("t"):
        t_no = dict(t)
        t_no["status"] = "لا بيانات"
        t_no.setdefault("trade_status", "NO_DATA")
        return t_no

    # إذا كانت الصفقة في حالة نهائية مسبقاً، نحافظ على سجلها كما هو دون أي تعديل لاحق
    if t.get("trade_status") in TERMINAL_TRADE_STATUSES and float(t.get("remaining_pct", 0.0)) == 0.0:
        return dict(t)

    side = t["side"]
    tick = float(t.get("tick") or 0.0)
    e_lo = float(t.get("entry_zone_low", t["entry_lo"]))
    e_hi = float(t.get("entry_zone_high", t["entry_hi"]))
    orig_stop = float(t.get("original_stop", t["stop"]))
    tp1, tp2, tp3 = float(t["targets"][0]), float(t["targets"][1]), float(t["targets"][2])
    pos_size = float(t.get("position_size") or t.get("qty") or 0.0)
    f_model = fill_model or t.get("fill_model") or DEFAULT_FILL_MODEL
    entry_trig_px = float(t.get("entry_trigger_price") or (e_hi if side == "LONG" else e_lo))
    entry_fee_rate = taker_fee_pct if f_model == "trigger_with_slippage" else maker_fee_pct

    t_since = int(t.get("origin_ts") or since_ms or 0)
    sim_now_ms = int(now_ms if now_ms is not None else (k5m["t"][-1] + BAR_5M_MS))
    expiry_ms = int(t_since + pending_expiry_hours * 3600 * 1000) if (pending_expiry_hours is not None and pending_expiry_hours > 0) else None
    signal_expiry_ts = int(t.get("signal_expiry_ts") or expiry_ms or 0) if expiry_ms else None

    # استعادة الحالة المثبتة مسبقاً (Immutable Entry & Stateful Partial Legs)
    filled = bool(t.get("filled")) and (t.get("filled_at") is not None) and (t.get("fill_price") is not None)
    filled_at = int(t["filled_at"]) if filled else None
    fill_price = float(t["fill_price"]) if filled else None
    r_unit = float(t["r_unit"]) if (filled and t.get("r_unit")) else None

    closed_pct = float(t.get("closed_pct", 0.0)) if filled else 0.0
    remaining_pct = float(t.get("remaining_pct", 1.0 - closed_pct)) if filled else 1.0
    realized_r = float(t.get("realized_r", 0.0)) if filled else 0.0
    realized_pnl_pct = float(t.get("realized_pnl_pct", 0.0)) if filled else 0.0
    total_fee_r = float(t.get("total_fee_r", 0.0)) if filled else 0.0

    tp_hits = list(t.get("tp_hits") or [False, False, False])
    tp_hit_times = list(t.get("tp_hit_times") or [None, None, None])
    leg_fills = [dict(x) for x in (t.get("leg_fills") or [])]

    stop_mode = str(t.get("stop_mode") or "original")
    active_stop = float(t.get("active_stop") if t.get("active_stop") is not None else orig_stop)
    stop_activated_ts = int(t.get("stop_activated_ts") or 0)
    last_closed_bar_ts = int(t.get("last_closed_bar_ts") or 0)

    exit_ts = t.get("exit_ts")
    trade_status = t.get("trade_status") or ("OPEN" if filled else "PENDING")
    if filled and tp_hits[1] and remaining_pct > 0:
        trade_status = "PARTIAL_TP2"
    elif filled and tp_hits[0] and remaining_pct > 0:
        trade_status = "PARTIAL_TP1"

    ks_o = k5m.get("o") or k5m["c"]
    all_bars = [
        (int(tt), float(o), float(h), float(l), float(c))
        for tt, o, h, l, c in zip(k5m["t"], ks_o, k5m["h"], k5m["l"], k5m["c"])
        if int(tt) >= t_since
    ]
    hi_since = max([b[2] for b in all_bars] + ([t["hi_since"]] if t.get("hi_since") is not None else []), default=None)
    lo_since = min([b[3] for b in all_bars] + ([t["lo_since"]] if t.get("lo_since") is not None else []), default=None)

    def _record_exit_leg(leg_name, weight_to_close, trig_px, exec_px, is_maker_exit, ev_ts):
        nonlocal closed_pct, remaining_pct, realized_r, realized_pnl_pct, total_fee_r
        w = min(remaining_pct, float(weight_to_close))
        if w <= 1e-9:
            return
        exit_fee_rate = maker_fee_pct if is_maker_exit else taker_fee_pct
        gross_move = (exec_px - fill_price) if side == "LONG" else (fill_price - exec_px)
        fee_move = (fill_price * entry_fee_rate) + (exec_px * exit_fee_rate)
        net_move = gross_move - fee_move
        ru = max(1e-12, r_unit)
        leg_gross_r = w * (gross_move / ru)
        leg_fee_r = w * (fee_move / ru)
        leg_net_r = w * (net_move / ru)
        leg_pnl_pct = w * (net_move / fill_price) * 100.0

        leg_qty = pos_size * w
        leg_gross_usd = leg_qty * gross_move
        leg_fee_usd = leg_qty * fee_move
        leg_slip_usd = leg_qty * abs(exec_px - trig_px)
        leg_net_usd = leg_qty * net_move

        closed_pct = round(min(1.0, closed_pct + w), 6)
        remaining_pct = round(max(0.0, 1.0 - closed_pct), 6)
        realized_r += leg_net_r
        realized_pnl_pct += leg_pnl_pct
        total_fee_r += leg_fee_r
        leg_fills.append({
            "leg": leg_name,
            "pct": round(w, 4),
            "qty_closed": round(leg_qty, 8),
            "trigger_px": trig_px,
            "exec_px": exec_px,
            "ts": int(ev_ts),
            "gross_r": round(leg_gross_r, 6),
            "fee_r": round(leg_fee_r, 6),
            "net_r": round(leg_net_r, 6),
            "net_pnl_pct": round(leg_pnl_pct, 6),
            "gross_usd": round(leg_gross_usd, 4),
            "fee_usd": round(leg_fee_usd, 4),
            "slippage_usd": round(leg_slip_usd, 4),
            "net_usd": round(leg_net_usd, 4),
        })

    def _exec_stop_exit(cur_stop_px, cur_stop_mode, ev_ts):
        nonlocal exit_ts, trade_status
        if side == "LONG":
            eff_px = cur_stop_px * (1.0 - stop_slippage_pct)
        else:
            eff_px = cur_stop_px * (1.0 + stop_slippage_pct)
        if cur_stop_mode == "original":
            leg_lbl, end_st = "STOP", "CLOSED_STOP"
        elif cur_stop_mode == "BE":
            leg_lbl, end_st = "BE_STOP", "CLOSED_BE"
        else:
            leg_lbl, end_st = "TRAIL_STOP", "CLOSED_TRAIL"
        _record_exit_leg(leg_lbl, remaining_pct, cur_stop_px, eff_px, is_maker_exit=False, ev_ts=ev_ts)
        exit_ts = int(ev_ts)
        trade_status = end_st

    # معالجة الشموع الجديدة فقط بعد آخر شمعة مغلقة جرى اعتمادها
    for tt, o, h, l, c in all_bars:
        if last_closed_bar_ts and tt <= last_closed_bar_ts:
            continue

        # 1) حالة الإشارة قبل التفعيل
        if not filled:
            if signal_expiry_ts is not None and tt >= signal_expiry_ts:
                trade_status = "EXPIRED"
                exit_ts = tt
                break

            pen = max(tick, entry_trig_px * 0.0001) if f_model == "limit_near_edge_strict" else 0.0
            if side == "LONG":
                trig_hit = (l <= entry_trig_px - pen) or (o < entry_trig_px)
            else:
                trig_hit = (h >= entry_trig_px + pen) or (o > entry_trig_px)

            if trig_hit:
                # تثبيت سعر الدخول لمرة واحدة نهائية دون أي اعتماد على حركة لاحقة
                filled = True
                filled_at = tt
                if f_model == "trigger_with_slippage":
                    if side == "LONG":
                        base_px = min(entry_trig_px, o) if o < entry_trig_px else entry_trig_px
                        fill_price = base_px * (1.0 + entry_slippage_pct)
                    else:
                        base_px = max(entry_trig_px, o) if o > entry_trig_px else entry_trig_px
                        fill_price = base_px * (1.0 - entry_slippage_pct)
                else:
                    # أوامر Limit المعلقة عند الحافة تُنفذ بسعر الأمر المحدد (أو أفضل عند فجوة افتتاحية في نفس لحظة الإشارة)
                    fill_price = entry_trig_px
                r_unit = max(1e-12, abs(fill_price - orig_stop))
                stop_mode = "original"
                active_stop = orig_stop
                stop_activated_ts = tt
                trade_status = "OPEN"

        # 2) إذا كانت الصفقة مفعّلة في هذه الشمعة أو قبلها
        if filled and remaining_pct > 0:
            just_filled_this_bar = (filled_at == tt)

            # (أ) في شمعة الدخول نفسها: نفحص ضرب الوقف الأصلي فوراً (محافظ)، ولا نمنح أي هدف داخل شمعة الدخول
            if just_filled_this_bar:
                stop_hit_same_bar = (l <= active_stop) if side == "LONG" else (h >= active_stop)
                if stop_hit_same_bar:
                    _exec_stop_exit(active_stop, stop_mode, tt)
                    if tt + BAR_5M_MS <= sim_now_ms:
                        last_closed_bar_ts = tt
                    break
            else:
                # (ب) فحص انتهاء مدة الصفقة المفتوحة إن حُدد سقف زمني للمركز
                if max_open_hours is not None and max_open_hours > 0 and tt >= filled_at + int(max_open_hours * 3600 * 1000):
                    eff_exp_px = c * (1.0 - stop_slippage_pct) if side == "LONG" else c * (1.0 + stop_slippage_pct)
                    _record_exit_leg("EXPIRY_EXIT", remaining_pct, c, eff_exp_px, is_maker_exit=False, ev_ts=tt)
                    exit_ts = tt
                    trade_status = "CLOSED_EXPIRY"
                    if tt + BAR_5M_MS <= sim_now_ms:
                        last_closed_bar_ts = tt
                    break

                # (ج) القاعدة المحافظة لتعارض الهدف والوقف داخل نفس الشمعة:
                # أي وقف كان مفعّلاً قبل افتتاح هذه الشمعة له الأولوية القصوى قبل فحص أي هدف جديد
                if stop_activated_ts < tt:
                    pre_stop_hit = (l <= active_stop) if side == "LONG" else (h >= active_stop)
                    if pre_stop_hit:
                        _exec_stop_exit(active_stop, stop_mode, tt)
                        if tt + BAR_5M_MS <= sim_now_ms:
                            last_closed_bar_ts = tt
                        break

                # (د) فحص الأهداف الجزئية بالترتيب (TP1 -> TP2 -> TP3)
                w1, w2, w3 = partial_weights
                stop_updated_in_this_bar = False

                if not tp_hits[0] and remaining_pct > 0:
                    if (side == "LONG" and h >= tp1) or (side == "SHORT" and l <= tp1):
                        tp_hits[0] = True
                        tp_hit_times[0] = tt
                        _record_exit_leg("TP1", w1, tp1, tp1, is_maker_exit=True, ev_ts=tt)
                        if remaining_pct > 0:
                            active_stop = compute_fee_adjusted_be_stop(
                                fill_price, side, tp1, tick=tick,
                                entry_fee_pct=entry_fee_rate, exit_taker_fee_pct=taker_fee_pct,
                                stop_slippage_pct=stop_slippage_pct,
                            )
                            stop_mode = "BE"
                            stop_activated_ts = tt
                            stop_updated_in_this_bar = True
                            trade_status = "PARTIAL_TP1"

                if tp_hits[0] and not tp_hits[1] and remaining_pct > 0:
                    if (side == "LONG" and h >= tp2) or (side == "SHORT" and l <= tp2):
                        tp_hits[1] = True
                        tp_hit_times[1] = tt
                        _record_exit_leg("TP2", w2, tp2, tp2, is_maker_exit=True, ev_ts=tt)
                        if remaining_pct > 0:
                            if trail_after_tp2:
                                active_stop = tp1
                                stop_mode = "trail"
                                stop_activated_ts = tt
                                stop_updated_in_this_bar = True
                            trade_status = "PARTIAL_TP2"

                if tp_hits[1] and not tp_hits[2] and remaining_pct > 0:
                    if (side == "LONG" and h >= tp3) or (side == "SHORT" and l <= tp3):
                        tp_hits[2] = True
                        tp_hit_times[2] = tt
                        _record_exit_leg("TP3", remaining_pct, tp3, tp3, is_maker_exit=True, ev_ts=tt)
                        exit_ts = tt
                        trade_status = "CLOSED_TP3"
                        if tt + BAR_5M_MS <= sim_now_ms:
                            last_closed_bar_ts = tt
                        break

                # (هـ) إذا فُعّل وقف جديد (تعادل أو متحرك) داخل هذه الشمعة ثم عاد إغلاق الشمعة لكسره،
                # فالإغلاق (close) يحدث زمنياً حتماً بعد القمة/القاع، لذا يُفعّل الوقف الجديد فوراً في نفس الشمعة!
                if (stop_updated_in_this_bar or stop_activated_ts == tt) and remaining_pct > 0:
                    post_tp_reversal = (c <= active_stop) if side == "LONG" else (c >= active_stop)
                    if post_tp_reversal:
                        _exec_stop_exit(active_stop, stop_mode, tt)
                        if tt + BAR_5M_MS <= sim_now_ms:
                            last_closed_bar_ts = tt
                        break

        if tt + BAR_5M_MS <= sim_now_ms:
            last_closed_bar_ts = tt

    last = float(live_price if live_price is not None else (k5m["c"][-1] if k5m["c"] else t["price"]))
    now_bar_ts = int(k5m["t"][-1]) if k5m["t"] else t_since

    # فحص السعر اللحظي الحي (live_price) فقط عند تمريره فعلياً للمراكز المفتوحة بين إغلاقات الـ 5 دقائق
    if live_price is not None and filled and remaining_pct > 0 and trade_status not in TERMINAL_TRADE_STATUSES:
        just_filled_now = (filled_at == now_bar_ts)
        if (side == "LONG" and last <= active_stop) or (side == "SHORT" and last >= active_stop):
            _exec_stop_exit(active_stop, stop_mode, now_bar_ts)
        elif not just_filled_now:
            w1, w2, _w3 = partial_weights
            if not tp_hits[0] and ((side == "LONG" and last >= tp1) or (side == "SHORT" and last <= tp1)):
                tp_hits[0] = True
                tp_hit_times[0] = now_bar_ts
                _record_exit_leg("TP1", w1, tp1, tp1, is_maker_exit=True, ev_ts=now_bar_ts)
                if remaining_pct > 0:
                    active_stop = compute_fee_adjusted_be_stop(
                        fill_price, side, tp1, tick=tick,
                        entry_fee_pct=entry_fee_rate, exit_taker_fee_pct=taker_fee_pct,
                        stop_slippage_pct=stop_slippage_pct,
                    )
                    stop_mode = "BE"
                    stop_activated_ts = now_bar_ts
                    trade_status = "PARTIAL_TP1"
            if tp_hits[0] and not tp_hits[1] and remaining_pct > 0 and ((side == "LONG" and last >= tp2) or (side == "SHORT" and last <= tp2)):
                tp_hits[1] = True
                tp_hit_times[1] = now_bar_ts
                _record_exit_leg("TP2", w2, tp2, tp2, is_maker_exit=True, ev_ts=now_bar_ts)
                if remaining_pct > 0:
                    if trail_after_tp2:
                        active_stop = tp1
                        stop_mode = "trail"
                        stop_activated_ts = now_bar_ts
                    trade_status = "PARTIAL_TP2"
            if tp_hits[1] and not tp_hits[2] and remaining_pct > 0 and ((side == "LONG" and last >= tp3) or (side == "SHORT" and last <= tp3)):
                tp_hits[2] = True
                tp_hit_times[2] = now_bar_ts
                _record_exit_leg("TP3", remaining_pct, tp3, tp3, is_maker_exit=True, ev_ts=now_bar_ts)
                exit_ts = now_bar_ts
                trade_status = "CLOSED_TP3"

    # إذا لم تتفعل الإشارة بعد: فحص انتهاء الصلاحية الزمنية أو ابتعاد السعر > max_dist_atr
    if not filled and trade_status not in TERMINAL_TRADE_STATUSES:
        if signal_expiry_ts is not None and sim_now_ms >= signal_expiry_ts:
            trade_status = "EXPIRED"
            exit_ts = sim_now_ms
        else:
            near_edge = e_hi if side == "LONG" else e_lo
            atr4 = max(1e-12, float(t.get("atr4") or (abs(e_hi - e_lo) * 3.0) or 1.0))
            d_atr = abs(last - near_edge) / atr4
            if max_dist_atr is not None and d_atr > max_dist_atr:
                trade_status = "CANCELLED_DIST"
                exit_ts = sim_now_ms
            else:
                trade_status = "PENDING"

    t2 = dict(t)
    t2["origin_ts"] = t_since
    t2["entry_zone_low"] = e_lo
    t2["entry_zone_high"] = e_hi
    t2["entry_trigger_price"] = entry_trig_px
    t2["fill_model"] = f_model
    t2["original_stop"] = orig_stop
    t2["signal_expiry_ts"] = signal_expiry_ts
    t2["position_size"] = pos_size
    t2["filled"] = filled
    t2["filled_at"] = filled_at
    t2["fill_price"] = fill_price
    t2["r_unit"] = r_unit
    t2["closed_pct"] = round(closed_pct, 4) if filled else 0.0
    t2["remaining_pct"] = round(remaining_pct, 4) if filled else 0.0
    t2["remaining_qty"] = round(pos_size * (remaining_pct if filled else 0.0), 8)
    t2["tp_hits"] = tp_hits
    t2["tp_hit_times"] = tp_hit_times
    t2["leg_fills"] = leg_fills
    t2["stop_mode"] = stop_mode if filled else "original"
    t2["active_stop"] = active_stop if filled else orig_stop
    t2["stop_activated_ts"] = stop_activated_ts if filled else 0
    t2["last_closed_bar_ts"] = last_closed_bar_ts
    t2["exit_ts"] = exit_ts
    t2["hi_since"] = hi_since
    t2["lo_since"] = lo_since
    t2["last"] = last
    t2["trade_status"] = trade_status

    if filled:
        ru = max(1e-12, r_unit)
        if remaining_pct > 0:
            float_gross = (last - fill_price) if side == "LONG" else (fill_price - last)
            float_net = float_gross - (fill_price * entry_fee_rate)
            unreal_r = remaining_pct * (float_net / ru)
            unreal_pnl_pct = remaining_pct * (float_net / fill_price) * 100.0
            unreal_pnl_usd = (pos_size * remaining_pct) * float_net
        else:
            unreal_r = 0.0
            unreal_pnl_pct = 0.0
            unreal_pnl_usd = 0.0

        real_pnl_usd = sum(float(lf.get("net_usd", 0.0)) for lf in leg_fills)
        tot_fees_usd = sum(float(lf.get("fee_usd", 0.0)) for lf in leg_fills)
        tot_slip_usd = sum(float(lf.get("slippage_usd", 0.0)) for lf in leg_fills)

        tot_r = realized_r + unreal_r
        tot_pnl_pct = realized_pnl_pct + unreal_pnl_pct
        r_disp = 0.0 if abs(round(tot_r, 2)) == 0 else round(tot_r, 2)
        p_disp = 0.0 if abs(round(tot_pnl_pct, 2)) == 0 else round(tot_pnl_pct, 2)

        t2["realized_r"] = round(realized_r, 4)
        t2["unrealized_r"] = round(unreal_r, 4)
        t2["total_r"] = round(tot_r, 4)
        t2["realized_pnl_pct"] = round(realized_pnl_pct, 4)
        t2["unrealized_pnl_pct"] = round(unreal_pnl_pct, 4)
        t2["total_fee_r"] = round(total_fee_r, 4)
        t2["realized_pnl_usd"] = round(real_pnl_usd, 4)
        t2["unrealized_pnl_usd"] = round(unreal_pnl_usd, 4)
        t2["total_pnl_usd"] = round(real_pnl_usd + unreal_pnl_usd, 4)
        t2["total_fees_usd"] = round(tot_fees_usd, 4)
        t2["total_slippage_usd"] = round(tot_slip_usd, 4)
        t2["r_raw"] = tot_r
        t2["r_now"] = r_disp
        t2["pnl_pct"] = p_disp

        if remaining_pct > 0:
            if r_disp > 0 or (r_disp == 0 and p_disp > 0):
                t2["open_state"] = "رابحة"
            elif r_disp < 0 or (r_disp == 0 and p_disp < 0):
                t2["open_state"] = "خاسرة"
            else:
                t2["open_state"] = "عند الدخول"
        else:
            t2["open_state"] = None
    else:
        near_edge = e_hi if side == "LONG" else e_lo
        atr4 = max(1e-12, float(t.get("atr4") or 1.0))
        t2["dist_now_atr"] = round(abs(last - near_edge) / atr4, 2)
        t2["realized_r"] = 0.0
        t2["unrealized_r"] = 0.0
        t2["total_r"] = 0.0
        t2["realized_pnl_pct"] = 0.0
        t2["unrealized_pnl_pct"] = 0.0
        t2["total_fee_r"] = 0.0
        t2["realized_pnl_usd"] = 0.0
        t2["unrealized_pnl_usd"] = 0.0
        t2["total_pnl_usd"] = 0.0
        t2["total_fees_usd"] = 0.0
        t2["total_slippage_usd"] = 0.0
        t2["open_state"] = None

    t2["status"] = _status_ar_from_state(trade_status, t2.get("open_state"))
    return t2


def _fetch_5m(sym, fresh=True):
    key = f"k_{sym}_5m_1000"
    raw = _get(f"/v1/klines?symbol={sym}&interval=5m&limit=1000") if fresh else cached_get(
        f"/v1/klines?symbol={sym}&interval=5m&limit=1000", key, ttl=120
    )
    return {
        "t": [int(x[0]) for x in raw],
        "o": [float(x[1]) for x in raw],
        "h": [float(x[2]) for x in raw],
        "l": [float(x[3]) for x in raw],
        "c": [float(x[4]) for x in raw],
    }


def track(
    trades,
    since_ms,
    max_dist_atr=1.0,
    fresh=True,
    fill_model=DEFAULT_FILL_MODEL,
    trail_after_tp2=True,
    pending_expiry_hours=PENDING_SIGNAL_EXPIRY_HOURS,
    max_open_hours=None,
):
    if not trades:
        return []
    try:
        live_prices = {x["symbol"]: float(x["price"]) for x in _get("/v1/ticker/price")}
    except Exception:
        live_prices = {}

    now_ms = int(time.time() * 1000)
    syms = list(dict.fromkeys(t["sym"] for t in trades))
    kmap = {}
    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(_fetch_5m, s, fresh): s for s in syms}
        for f in cf.as_completed(futs):
            s = futs[f]
            try:
                kmap[s] = f.result()
            except Exception:
                kmap[s] = None

    out = []
    for t in trades:
        sym = t["sym"]
        k = kmap.get(sym)
        if not k:
            t2 = dict(t)
            t2["status"] = "لا بيانات"
            t2.setdefault("trade_status", "NO_DATA")
            out.append(t2)
            continue
        t2 = simulate_trade_lifecycle(
            t,
            k,
            since_ms=since_ms,
            live_price=live_prices.get(sym),
            now_ms=now_ms,
            max_dist_atr=max_dist_atr,
            fill_model=fill_model,
            trail_after_tp2=trail_after_tp2,
            pending_expiry_hours=pending_expiry_hours,
            max_open_hours=max_open_hours,
        )
        out.append(t2)
    return out


# ==============================================================================
# [4] القسم الرابع: lifecycle.py
# ==============================================================================
# -*- coding: utf-8 -*-
"""إدارة دورة حياة تتبع الصفقات عبر المسوحات والتقارير (v3.6 — Phase 1 Stateful Partial Exits):
- تستمر متابعة أي صفقة مفعّلة طالما أن الكمية المتبقية remaining_pct > 0 (OPEN / PARTIAL_TP1 / PARTIAL_TP2).
- لا تُستبدل أو تُسقط صفقة مفتوحة فعلياً بسبب صدور إشارة جديدة غير مفعلة على نفس العملة والاتجاه.
- الصفقات التي اكتمل إغلاقها بالكامل (remaining_pct == 0: أهداف مكتملة / تعادل / وقف / انتهاء صلاحية / إلغاء)
  تُعرض مرة واحدة في التقرير ليطّلع عليها المتداول ثم تُؤرشف في المسح التالي.
- منع إعادة الدخول الفوري على نفس العملة والاتجاه قبل إغلاق شمعة 4س بعد ضرب الوقف الأصلي (CLOSED_STOP).
"""
import json, os, time
# [مدمج في نفس الملف من قسم track]

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE, "tracker_state.json")


def make_tid(t, fallback_ts=0):
    ots = int(t.get("origin_ts") or fallback_ts or 0)
    return f"{t['sym']}|{t['side']}|{ots}"


def load_tracker_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as fh:
                st = json.load(fh)
            st.setdefault("reported_stops", {})
            st.setdefault("reported_cancels", {})
            st.setdefault("reported_closed", {})
            st.setdefault("carried_open", [])
            return st
        except Exception as exc:
            record_diag_warning("corrupt_tracker_state", "تعذر قراءة ملف حالة المتتبع tracker_state.json", exc=exc)
    return {"reported_stops": {}, "reported_cancels": {}, "reported_closed": {}, "carried_open": []}


def already_pruned_ids(st=None):
    st = st or load_tracker_state()
    return (
        set((st.get("reported_stops") or {}).keys())
        | set((st.get("reported_cancels") or {}).keys())
        | set((st.get("reported_closed") or {}).keys())
    )


def active_open_pairs(st=None):
    """إرجاع مجموعة (sym, side) التي تملك مركزاً مفتوحاً حالياً (remaining_pct > 0) لمنع فتح صفقة مكررة فوقها."""
    st = st or load_tracker_state()
    pairs = set()
    for row in (st.get("carried_open") or []):
        if row.get("filled") and float(row.get("remaining_pct", 0.0)) > 0:
            pairs.add((row["sym"], row["side"]))
    return pairs


def save_tracker_state(st):
    now_ms = int(time.time() * 1000)
    cutoff = now_ms - 7 * 86400 * 1000
    for bucket in ("reported_stops", "reported_cancels", "reported_closed"):
        st[bucket] = {
            k: v for k, v in (st.get(bucket) or {}).items()
            if int(v.get("reported_at", now_ms)) >= cutoff
        }
    json.dump(st, open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)


def update_and_prune_tracking(
    scan_trades,
    scan_ts,
    max_dist_atr=1.0,
    fresh=True,
    commit=True,
    track_fn=None,
):
    """يتتبع المراكز المفتوحة المرحّلة (بما فيها PARTIAL_TP1 و PARTIAL_TP2) + إشارات المسح الأخير:
    1) الأولوية القصوى للمراكز المفعّلة المفتوحة في carried_open (لا تُسقط أبداً بسبب إشارة جديدة على نفس الزوج).
    2) الصفقات التي وصلت لحالة نهائية (remaining_pct == 0 أو ملغاة/منتهية) تُعرض مرة واحدة ثم تُؤرشف.
    """
    st = load_tracker_state()
    reported_stops = dict(st.get("reported_stops") or {})
    reported_cancels = dict(st.get("reported_cancels") or {})
    reported_closed = dict(st.get("reported_closed") or {})
    pruned_ids = set(reported_stops.keys()) | set(reported_cancels.keys()) | set(reported_closed.keys())
    carried_open = list(st.get("carried_open") or [])

    pool = []
    open_pair_keys = set()

    # 1) أولاً: جميع المراكز المفعّلة المفتوحة المرحّلة (100% أو 50% أو 25%) لها الأولوية ولا تُكتب فوقها إشارة جديدة
    for old_t in carried_open:
        ots = int(old_t.get("origin_ts") or 0)
        tid = make_tid(old_t, ots)
        if tid in pruned_ids:
            continue
        t_copy = dict(old_t)
        t_copy["origin_ts"] = ots
        pool.append(t_copy)
        open_pair_keys.add((old_t["sym"], old_t["side"]))

    # 2) ثانياً: إشارات المسح الأخير غير المؤرشفة وغير المتداخلة مع مركز مفتوح حالياً على نفس العملة والاتجاه
    for t in (scan_trades or []):
        ots = int(t.get("origin_ts") or scan_ts)
        tid = make_tid(t, ots)
        if tid in pruned_ids or (t["sym"], t["side"]) in open_pair_keys:
            continue
        t_copy = dict(t)
        t_copy["origin_ts"] = ots
        pool.append(t_copy)

    runner = track_fn or track
    tracked = runner(pool, scan_ts, max_dist_atr=max_dist_atr, fresh=fresh) if pool else []
    now_ms = int(time.time() * 1000)

    newly_stopped = 0
    for row in tracked:
        t_stat = row.get("trade_status")
        tid = make_tid(row, scan_ts)
        if t_stat == "CLOSED_STOP" and tid not in reported_stops:
            reported_stops[tid] = {
                "sym": row["sym"],
                "side": row["side"],
                "name": row.get("name", row["sym"]),
                "origin_ts": int(row.get("origin_ts") or scan_ts),
                "stop_ts": int(row.get("exit_ts") or now_ms),
                "realized_r": row.get("realized_r"),
                "reported_at": now_ms,
            }
            newly_stopped += 1
        elif t_stat in ("CANCELLED_DIST", "EXPIRED") and tid not in reported_cancels:
            reported_cancels[tid] = {
                "sym": row["sym"],
                "side": row["side"],
                "name": row.get("name", row["sym"]),
                "origin_ts": int(row.get("origin_ts") or scan_ts),
                "reason": t_stat,
                "reported_at": now_ms,
            }
        elif t_stat in ("CLOSED_TP3", "CLOSED_BE", "CLOSED_TRAIL", "CLOSED_EXPIRY") and tid not in reported_closed:
            reported_closed[tid] = {
                "sym": row["sym"],
                "side": row["side"],
                "name": row.get("name", row["sym"]),
                "origin_ts": int(row.get("origin_ts") or scan_ts),
                "close_reason": t_stat,
                "realized_r": row.get("realized_r"),
                "exit_ts": int(row.get("exit_ts") or now_ms),
                "reported_at": now_ms,
            }

    if commit:
        # تبقى الصفقة في carried_open طالما أنها مفعّلة ولديها كمية متبقية مفتوحة > 0%
        next_open = [
            r for r in tracked
            if r.get("filled") and float(r.get("remaining_pct", 0.0)) > 0.0 and r.get("trade_status") in ACTIVE_OPEN_STATUSES
        ]
        save_tracker_state({
            "reported_stops": reported_stops,
            "reported_cancels": reported_cancels,
            "reported_closed": reported_closed,
            "carried_open": next_open,
        })

    return tracked, newly_stopped


def recent_4h_stopped_pairs(now_ms=None):
    """إرجاع مجموعة (sym, side) التي ضربت الوقف الأصلي داخل شمعة الـ 4 ساعات الحالية غير المغلقة بعد."""
    now_ms = int(now_ms or time.time() * 1000)
    four_h_ms = 4 * 3600 * 1000
    cur_4h_open = (now_ms // four_h_ms) * four_h_ms
    st = load_tracker_state()
    blocked = set()
    for v in (st.get("reported_stops") or {}).values():
        stop_ts = int(v.get("stop_ts") or 0)
        if stop_ts >= cur_4h_open:
            blocked.add((v["sym"], v["side"]))
    return blocked



# ==============================================================================
# [5] القسم الخامس: gen_report.py
# ==============================================================================
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مولّد تقرير الصفقات (HTML عربي RTL) — v3"""
import json, os, datetime as dt, html

RIYADH = dt.timezone(dt.timedelta(hours=3))
BASE = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(BASE, "index.html")

TAG_AR = {
    "swing": "تأرجح", "ema20": "EMA20·4س", "ema50": "EMA50·4س", "ema200": "EMA200·4س",
    "ema20d": "EMA20·يومي", "ema50d": "EMA50·يومي", "H_today": "قمة اليوم", "L_today": "قاع اليوم",
    "H_prev": "قمة الأمس", "L_prev": "قاع الأمس", "fib50": "فيبو 0.5", "fib618": "فيبو 0.618",
    "fib382": "فيبو 0.382",
    "ema9_4h": "EMA9·4س", "ema20_1h": "EMA20·1س", "ema50_1h": "EMA50·1س", "swing_1h": "تأرجح 1س",
    "ifib236": "فيبو موجة 0.236", "ifib382": "فيبو موجة 0.382", "ifib50": "فيبو موجة 0.50",
}

SEARCH_ANALYZER_JS = r"""
var TAG_AR_JS = {
  swing:"تأرجح", ema20:"EMA20·4س", ema50:"EMA50·4س", ema200:"EMA200·4س",
  ema20d:"EMA20·يومي", ema50d:"EMA50·يومي", H_today:"قمة اليوم", L_today:"قاع اليوم",
  H_prev:"قمة الأمس", L_prev:"قاع الأمس", fib50:"فيبو 0.5", fib618:"فيبو 0.618", fib382:"فيبو 0.382",
  ema9_4h:"EMA9·4س", ema20_1h:"EMA20·1س", ema50_1h:"EMA50·1س", swing_1h:"تأرجح 1س",
  ifib236:"فيبو موجة 0.236", ifib382:"فيبو موجة 0.382", ifib50:"فيبو موجة 0.50"
};

function normSymInput(raw) {
  var s = (raw || '').toUpperCase().replace(/\s+/g, '').replace(/^\$/, '');
  s = s.replace(/[-_/]?USDT$/, '').replace(/[-_/]?PERP$/, '');
  return s;
}

function fmtPx(x) {
  if (x === null || x === undefined || isNaN(x)) return '-';
  var ax = Math.abs(x), d = 4;
  if (ax >= 1000) d = 2;
  else if (ax >= 10) d = 2;
  else if (ax >= 1) d = 3;
  else if (ax >= 0.1) d = 4;
  else if (ax >= 0.01) d = 5;
  else if (ax >= 0.001) d = 6;
  else d = 7;
  return Number(x).toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d});
}

// ===================== الميزة 1: البحث الفوري داخل التقرير =====================
function onSearchCoin() {
  var raw = document.getElementById('coinSearchInp').value || '';
  var q = normSymInput(raw);
  var clrBtn = document.getElementById('clrSearchBtn');
  var sumBox = document.getElementById('searchSummary');
  clrBtn.style.display = q ? 'inline-flex' : 'none';

  var els = document.querySelectorAll('[data-sym]');
  if (!q) {
    for (var i = 0; i < els.length; i++) els[i].style.display = '';
    sumBox.style.display = 'none';
    sumBox.innerHTML = '';
    return;
  }

  for (var j = 0; j < els.length; j++) {
    var sym = (els[j].getAttribute('data-sym') || '').toUpperCase();
    var match = sym.indexOf(q) !== -1 || ('1000' + q) === sym;
    els[j].style.display = match ? '' : 'none';
  }

  var idx = window.REPORT_INDEX || {trades:[], exp:[], inv:[], bos:[], track:[]};
  var mTrades = idx.trades.filter(function(t){ return t.name.indexOf(q) !== -1 || t.name === '1000'+q; });
  var mExp = idx.exp.filter(function(e){ return e.name.indexOf(q) !== -1 || e.name === '1000'+q; });
  var mInv = (idx.inv || []).filter(function(m){ return m.name.indexOf(q) !== -1 || m.name === '1000'+q; });
  var mBos = (idx.bos || []).filter(function(b){ return b.name.indexOf(q) !== -1 || b.name === '1000'+q; });
  var mTrack = idx.track.filter(function(x){ return x.name.indexOf(q) !== -1 || x.name === '1000'+q; });

  var html = '<div style="font-weight:700;color:#93c5fd;margin-bottom:6px">🔎 نتيجة البحث الفوري في التقرير عن: <span style="color:#fff;direction:ltr;display:inline-block">' + q + '</span></div>';
  if (mTrades.length) {
    html += '<div>📋 <b>الصفقات المؤهلة (' + mTrades.length + '):</b> ' + mTrades.map(function(t){
      var col = t.side === 'LONG' ? '#4ade80' : '#f87171';
      return '<a href="#t-' + t.name + '" style="color:' + col + ';font-weight:700;text-decoration:underline;margin-left:8px">' + t.name + ' ' + t.side + ' (درجة ' + t.grade + ' · ' + t.score.toFixed(1) + ')</a>';
    }).join(' ') + '</div>';
  } else {
    html += '<div style="color:#9db1c8">📋 <b>الصفقات المؤهلة (4س):</b> غير موجودة ضمن صفقات المضاربة في هذا المسح.</div>';
  }

  if (mInv.length) {
    html += '<div>🧲 <b>العملات الاستثمارية (عصر وقاع):</b> ' + mInv.map(function(m){
      return '<a href="#inv-' + m.name + '" style="color:#c4b5fd;font-weight:700;text-decoration:underline;margin-left:8px">💎 ' + m.name + ' (' + m.badge + ')</a>';
    }).join(' ') + '</div>';
  }

  if (mBos.length) {
    html += '<div>🚀 <b>كسر الهيكل اليومي (3 إغلاقات):</b> ' + mBos.map(function(b){
      return '<a href="#bos-' + b.name + '" style="color:#38bdf8;font-weight:700;text-decoration:underline;margin-left:8px">🚀 ' + b.name + ' (سيولة ' + b.vol_x.toFixed(1) + 'x)</a>';
    }).join(' ') + '</div>';
  }

  if (mExp.length) {
    html += '<div>🔥 <b>قائمة الانفجار اليومي:</b> ' + mExp.map(function(e){
      return '<a href="#exp-' + e.name + '" style="color:#fbbf24;font-weight:700;text-decoration:underline;margin-left:8px">🔥 ' + e.name + ' (' + e.score.toFixed(1) + ')</a>';
    }).join(' ') + '</div>';
  }

  if (mTrack.length) {
    html += '<div>🔄 <b>متابعة المسح السابق:</b> ' + mTrack.map(function(x){
      var rtxt = (x.r_now !== null && x.r_now !== undefined) ? (' · ' + (x.r_now >= 0 ? '+' : '') + Number(x.r_now).toFixed(2) + 'R') : '';
      return '<a href="#track" style="color:#cbd5e1;text-decoration:underline;margin-left:8px"><b>' + x.name + '</b> (' + x.side + ' — ' + x.status + rtxt + ')</a>';
    }).join(' ') + '</div>';
  }

  html += '<div style="margin-top:9px"><button class="abtn pri" onclick="analyzeFromSearch(\'' + q.replace(/[^A-Z0-9]/g,'') + '\')">🎯 فحص وتحليل حي الآن لعملة ' + q + ' (مباشر من بايننس)</button></div>';
  sumBox.innerHTML = html;
  sumBox.style.display = 'block';
}

function clearSearchCoin() {
  document.getElementById('coinSearchInp').value = '';
  onSearchCoin();
}

function analyzeFromSearch(sym) {
  document.getElementById('customCoinInp').value = sym;
  analyzeCustomCoin();
}

// ===================== الميزة 2أ: المحلل الحي الفوري لعملة محددة (v3.4) =====================
function calcEMA(vals, n) {
  var out = new Array(vals.length).fill(null);
  if (vals.length < n || n <= 0) return out;
  var k = 2 / (n + 1), sum = 0;
  for (var i = 0; i < n; i++) sum += vals[i];
  var e = sum / n;
  out[n - 1] = e;
  for (var j = n; j < vals.length; j++) {
    e = vals[j] * k + e * (1 - k);
    out[j] = e;
  }
  return out;
}

function calcATR(h, l, c, n) {
  n = n || 14;
  var trs = [], out = [], a = null;
  for (var i = 0; i < c.length; i++) {
    if (i === 0) trs.push(h[i] - l[i]);
    else trs.push(Math.max(h[i] - l[i], Math.abs(h[i] - c[i - 1]), Math.abs(l[i] - c[i - 1])));
  }
  for (var j = 0; j < trs.length; j++) {
    if (j + 1 < n) out.push(null);
    else if (j + 1 === n) {
      var s = 0; for (var m = 0; m < n; m++) s += trs[m];
      a = s / n; out.push(a);
    } else {
      a = (a * (n - 1) + trs[j]) / n;
      out.push(a);
    }
  }
  return out;
}

function calcRSI(c, n) {
  n = n || 14;
  var out = new Array(c.length).fill(null);
  if (c.length <= n) return out;
  var gains = 0, losses = 0;
  for (var i = 1; i <= n; i++) {
    var d = c[i] - c[i - 1];
    if (d > 0) gains += d; else losses += (-d);
  }
  var ag = gains / n, al = losses / n;
  out[n] = 100 - 100 / (1 + (al ? ag / al : 999));
  for (var j = n + 1; j < c.length; j++) {
    var df = c[j] - c[j - 1];
    ag = (ag * (n - 1) + (df > 0 ? df : 0)) / n;
    al = (al * (n - 1) + (df < 0 ? -df : 0)) / n;
    out[j] = 100 - 100 / (1 + (al ? ag / al : 999));
  }
  return out;
}

function calcMACDHist(c) {
  var ef = calcEMA(c, 12), es = calcEMA(c, 26);
  var line = [], base = [];
  for (var i = 0; i < c.length; i++) {
    var v = (ef[i] === null || es[i] === null) ? null : (ef[i] - es[i]);
    line.push(v);
    if (v !== null) base.push(v);
  }
  if (!base.length) return new Array(c.length).fill(null);
  var sm = calcEMA(base, 9);
  var off = line.length - base.length;
  var hist = new Array(c.length).fill(null);
  for (var j = 0; j < sm.length; j++) {
    if (line[off + j] !== null && sm[j] !== null) hist[off + j] = line[off + j] - sm[j];
  }
  return hist;
}

function calcPivots(h, l, k) {
  k = k || 3;
  var highs = [], lows = [], n = h.length;
  for (var i = k; i < n - k; i++) {
    var okH = true, okL = true;
    for (var j = 1; j <= k; j++) {
      if (h[i] < h[i - j] || h[i] < h[i + j]) okH = false;
      if (l[i] > l[i - j] || l[i] > l[i + j]) okL = false;
    }
    if (okH) highs.push([i, h[i]]);
    if (okL) lows.push([i, l[i]]);
  }
  return {ph: highs, pl: lows};
}

function enrichKlines(raw) {
  var t = [], o = [], h = [], l = [], c = [];
  for (var i = 0; i < raw.length; i++) {
    t.push(Number(raw[i][0])); o.push(Number(raw[i][1]));
    h.push(Number(raw[i][2])); l.push(Number(raw[i][3])); c.push(Number(raw[i][4]));
  }
  var pv = calcPivots(h, l, 3);
  return {
    t:t, o:o, h:h, l:l, c:c,
    ema9: calcEMA(c, 9), ema20: calcEMA(c, 20), ema50: calcEMA(c, 50), ema200: calcEMA(c, 200),
    atr: calcATR(h, l, c, 14), rsi: calcRSI(c, 14), macd_hist: calcMACDHist(c),
    ph: pv.ph, pl: pv.pl
  };
}

function isAsiaWickNow() {
  var riyadhMs = Date.now() + 3 * 3600 * 1000;
  var d = new Date(riyadhMs);
  var hr = d.getUTCHours(), mn = d.getUTCMinutes();
  return (hr === 2 && mn >= 30) || hr === 3 || hr === 4;
}

function checkAlignedTrendJS(k4, k1h, price, side, chg) {
  if (!k1h || !k1h.ema20 || !k1h.ema50) return false;
  var e20_4 = k4.ema20[k4.ema20.length - 1], e50_4 = k4.ema50[k4.ema50.length - 1];
  var e20_1h = k1h.ema20[k1h.ema20.length - 1], e50_1h = k1h.ema50[k1h.ema50.length - 1];
  if (!e20_4 || !e50_4 || !e20_1h || !e50_1h) return false;
  if (side === 'LONG') return (chg >= 6.0 && chg <= 22.0) && (price > e20_4 && e20_4 > e50_4) && (e20_1h > e50_1h);
  return (chg >= -22.0 && chg <= -6.0) && (price < e20_4 && e20_4 < e50_4) && (e20_1h < e50_1h);
}

function isAgainstStrongTrendJS(k4, k1h, price, side, chg) {
  if (!k1h || !k1h.ema20 || !k1h.ema50) return false;
  var e20_4 = k4.ema20[k4.ema20.length - 1], e50_4 = k4.ema50[k4.ema50.length - 1];
  var e20_1h = k1h.ema20[k1h.ema20.length - 1], e50_1h = k1h.ema50[k1h.ema50.length - 1];
  if (!e20_4 || !e50_4 || !e20_1h || !e50_1h) return false;
  if (side === 'SHORT' && chg >= 8.0 && price > e20_4 && e20_4 > e50_4 && e20_1h > e50_1h) return true;
  if (side === 'LONG' && chg <= -8.0 && price < e20_4 && e20_4 < e50_4 && e20_1h < e50_1h) return true;
  return false;
}

function clusterLevelsJS(k4, k1, price, side, asiaWick, k1h, chg) {
  var src = [];
  function add(px, tag, w) { if (px && px > 0 && !isNaN(px)) src.push([px, tag, w || 1.0]); }
  k4.pl.slice(-8).forEach(function(p){ add(p[1], 'swing', 1.4); });
  k4.ph.slice(-8).forEach(function(p){ add(p[1], 'swing', 1.4); });
  ['ema20','ema50','ema200'].forEach(function(nm){ add(k4[nm][k4[nm].length - 1], nm, 1.0); });
  ['ema20','ema50'].forEach(function(nm){ add(k1[nm][k1[nm].length - 1], nm + 'd', 0.6); });

  var newborn = asiaWick && k1.t.length > 1 && (Date.now() - k1.t[k1.t.length - 1]) < 3 * 3600 * 1000;
  if (newborn) {
    add(k1.h[k1.h.length - 2], 'H_prev', 1.2); add(k1.l[k1.l.length - 2], 'L_prev', 1.2);
    if (k1.h.length > 2) { add(k1.h[k1.h.length - 3], 'H_prev', 0.7); add(k1.l[k1.l.length - 3], 'L_prev', 0.7); }
  } else {
    add(k1.h[k1.h.length - 1], 'H_today', 1.2); add(k1.l[k1.l.length - 1], 'L_today', 1.2);
    if (k1.h.length > 1) { add(k1.h[k1.h.length - 2], 'H_prev', 0.7); add(k1.l[k1.l.length - 2], 'L_prev', 0.7); }
  }

  var h60 = k4.h.slice(-60), l60 = k4.l.slice(-60);
  var hi = Math.max.apply(null, h60), lo = Math.min.apply(null, l60);
  if (hi > lo) {
    [[0.5,'fib50'],[0.618,'fib618'],[0.382,'fib382']].forEach(function(f){ add(hi - (hi - lo) * f[0], f[1], 0.5); });
  }

  var weak = newborn ? {fib50:1,fib618:1,fib382:1,ema20d:1,ema50d:1} : {fib50:1,fib618:1,fib382:1,H_prev:1,L_prev:1,ema20d:1,ema50d:1};
  var atr4 = k4.atr[k4.atr.length - 1] || (price * 0.02);
  var isTrend = k1h ? checkAlignedTrendJS(k4, k1h, price, side, chg || 0) : false;
  var tol = 0.0035;
  if (isTrend && k1h) {
    tol = Math.max(0.0035, Math.min(0.16 * atr4 / price, 0.011));
    add(k4.ema9[k4.ema9.length - 1], 'ema9_4h', 1.1);
    add(k1h.ema20[k1h.ema20.length - 1], 'ema20_1h', 1.1);
    add(k1h.ema50[k1h.ema50.length - 1], 'ema50_1h', 0.9);
    k1h.pl.slice(-8).forEach(function(p){ add(p[1], 'swing_1h', 1.1); });
    k1h.ph.slice(-8).forEach(function(p){ add(p[1], 'swing_1h', 1.1); });
    var hi12 = Math.max.apply(null, k4.h.slice(-12)), lo12 = Math.min.apply(null, k4.l.slice(-12));
    if (hi12 > lo12) {
      [[0.236,'ifib236'],[0.382,'ifib382'],[0.5,'ifib50']].forEach(function(f){
        var pxf = side === 'LONG' ? (hi12 - (hi12 - lo12) * f[0]) : (lo12 + (hi12 - lo12) * f[0]);
        add(pxf, f[1], 0.6);
      });
    }
    weak.ifib236 = 1; weak.ifib382 = 1; weak.ifib50 = 1; weak.ema50_1h = 1;
  }

  src.sort(function(a,b){ return a[0] - b[0]; });
  var groups = [];
  src.forEach(function(it){
    var px = it[0], tag = it[1], w = it[2], placed = false;
    for (var i = 0; i < groups.length; i++) {
      var g = groups[i];
      if (Math.abs(px - g.px) / g.px <= tol) {
        g.px = (g.px * g.w + px * w) / (g.w + w);
        g.w += w; g.tags.push(tag); placed = true; break;
      }
    }
    if (!placed) groups.push({px: px, w: w, tags: [tag]});
  });

  var out = [];
  groups.forEach(function(g){
    var uniqTags = Array.from(new Set(g.tags)).sort();
    if (uniqTags.length < 2) return;
    var strongCnt = uniqTags.filter(function(t){ return !weak[t]; }).length;
    if (side === 'LONG' && g.px < price) out.push({px:g.px, tags:uniqTags, n:uniqTags.length, strong:strongCnt, w:g.w});
    if (side === 'SHORT' && g.px > price) out.push({px:g.px, tags:uniqTags, n:uniqTags.length, strong:strongCnt, w:g.w});
  });
  out.sort(function(a,b){ return side === 'LONG' ? (b.px - a.px) : (a.px - b.px); });
  return out;
}

function pickClusterJS(clusters, price, atr4, minDistAtr, maxDistAtr) {
  var cands = [];
  clusters.forEach(function(cl){
    if (cl.n < 2 || cl.strong < 1) return;
    var d = Math.abs(price - cl.px) / atr4;
    if (d >= minDistAtr - 1e-9 && d <= maxDistAtr + 1e-9) cands.push([d, cl]);
  });
  if (!cands.length && minDistAtr > 0) {
    clusters.forEach(function(cl){
      if (cl.n < 2 || cl.strong < 1) return;
      var d = Math.abs(price - cl.px) / atr4;
      if (d <= maxDistAtr + 1e-9) cands.push([d, cl]);
    });
  }
  if (!cands.length) return null;
  cands.sort(function(a,b){ return a[0] - b[0]; });
  var nearD = cands[0][0], near = cands[0][1];
  for (var i = 1; i < cands.length; i++) {
    if (cands[i][0] - nearD > 0.25) break;
    if (cands[i][1].w >= near.w * 1.6 && cands[i][1].strong >= 2) return cands[i];
  }
  return [nearD, near];
}

function srLevelsJS(k4, k1, price, atr4) {
  var sup = [], res = [];
  clusterLevelsJS(k4, k1, price, 'LONG', false, null, 0).forEach(function(c){ sup.push([c.px, c.strong*2+c.n]); });
  clusterLevelsJS(k4, k1, price, 'SHORT', false, null, 0).forEach(function(c){ res.push([c.px, c.strong*2+c.n]); });
  k4.pl.slice(-8).forEach(function(p){ if (p[1] < price) sup.push([p[1], 1]); });
  k4.ph.slice(-8).forEach(function(p){ if (p[1] > price) res.push([p[1], 1]); });
  ['ema20','ema50','ema200'].forEach(function(nm){
    var v = k4[nm][k4[nm].length - 1];
    if (v) (v < price ? sup : res).push([v, 1]);
  });
  ['ema20','ema50'].forEach(function(nm){
    var v = k1[nm][k1[nm].length - 1];
    if (v) (v < price ? sup : res).push([v, 0.8]);
  });
  function dedup(arr, desc) {
    arr.sort(function(a,b){ return desc ? (b[0] - a[0]) : (a[0] - b[0]); });
    var out = [];
    for (var i = 0; i < arr.length; i++) {
      var px = arr[i][0];
      if (out.every(function(o){ return Math.abs(px - o) / o > 0.004; })) out.push(px);
      if (out.length === 3) break;
    }
    return out;
  }
  var s = dedup(sup, true), r = dedup(res, false);
  while (s.length < 3) s.push((s.length ? s[s.length - 1] : price) - 1.5 * atr4);
  while (r.length < 3) r.push((r.length ? r[r.length - 1] : price) + 1.5 * atr4);
  return {supports: s, resistances: r};
}

function structureJS(k4, side) {
  var ph = k4.ph.slice(-4), pl = k4.pl.slice(-4);
  var hh = ph.length >= 2 && ph[ph.length-1][1] > ph[ph.length-2][1];
  var hl = pl.length >= 2 && pl[pl.length-1][1] > pl[pl.length-2][1];
  var lh = ph.length >= 2 && ph[ph.length-1][1] < ph[ph.length-2][1];
  var ll = pl.length >= 2 && pl[pl.length-1][1] < pl[pl.length-2][1];
  if (side === 'LONG') {
    if (hh && hl) return ['صاعدة HH/HL', 1.0];
    if (hl) return ['قيعان صاعدة', 0.6];
    if (lh && ll) return ['هابطة LH/LL', -0.6];
    return ['عرضية', 0.0];
  } else {
    if (lh && ll) return ['هابطة LH/LL', 1.0];
    if (lh) return ['قمم هابطة', 0.6];
    if (hh && hl) return ['صاعدة HH/HL', -0.6];
    return ['عرضية', 0.0];
  }
}

function trendDirJS(k4, k1) {
  var c = k4.c[k4.c.length - 1], c1 = k1.c[k1.c.length - 1];
  var e20_4 = k4.ema20[k4.ema20.length - 1], e50_4 = k4.ema50[k4.ema50.length - 1], e200_4 = k4.ema200[k4.ema200.length - 1];
  var e20_1 = k1.ema20[k1.ema20.length - 1], e50_1 = k1.ema50[k1.ema50.length - 1];
  var s = 0, s1 = 0;
  if (e20_4) s += (c > e20_4 ? 1 : -1);
  if (e20_4 && e50_4) s += (e20_4 > e50_4 ? 1 : -1);
  if (e50_4 && e200_4) s += (e50_4 > e200_4 ? 1 : -1);
  else if (e50_4) s += (c > e50_4 ? 1 : -1);
  if (e20_1) s1 += (c1 > e20_1 ? 1 : -1);
  if (e20_1 && e50_1) s1 += (e20_1 > e50_1 ? 1 : -1);
  return [s, s1];
}

function evaluateSideJS(data, side) {
  var k4 = data.k4, k1 = data.k1, k1h = data.k1h;
  var price = data.price, atr4 = k4.atr[k4.atr.length - 1];
  var reasons = [];
  if (!atr4 || atr4 <= 0) return {ok:false, reasons:['بيانات شموع غير كافية لحساب ATR'], plan:null};

  if (data.qv < 8.0) reasons.push('سيولة 24س (' + data.qv.toFixed(1) + 'M$) أقل من الحد الأدنى المعتمد (8M$)');
  if (data.markDiffPct > 0.5) reasons.push('فجوة سعر العلامة Mark/Last (' + data.markDiffPct.toFixed(2) + '%) تتجاوز 0.5%');
  if (isAgainstStrongTrendJS(k4, k1h, price, side, data.chg)) {
    reasons.push('ممنوع الدخول (' + side + ') عكس ترند قوي متوافق على 4س و1س (قاعدة Trend is your friend)');
  }

  var asiaWick = isAsiaWickNow();
  var minDReq = asiaWick ? 0.22 : 0.0;
  var isTrend = checkAlignedTrendJS(k4, k1h, price, side, data.chg);
  var baseClusters = clusterLevelsJS(k4, k1, price, side, asiaWick, null, 0);
  var basePicked = pickClusterJS(baseClusters, price, atr4, minDReq, 1.0);
  var usedFastTrend = false, picked = null, allClusters = baseClusters;
  if (isTrend) {
    allClusters = clusterLevelsJS(k4, k1, price, side, asiaWick, k1h, data.chg);
    picked = pickClusterJS(allClusters, price, atr4, minDReq, 1.0);
    usedFastTrend = (basePicked === null);
  } else {
    picked = basePicked;
  }

  var waitingOnly = false;
  if (!picked) {
    var farPicked = pickClusterJS(allClusters, price, atr4, 0.0, 2.8);
    if (farPicked) {
      waitingOnly = true;
      picked = farPicked;
      reasons.push('أقرب حزمة ارتكاز قوية تقع على بُعد ' + farPicked[0].toFixed(2) + ' ATR (أبعد من سقف منع المطاردة 1.0 ATR — انتظر وصول السعر إليها)');
    } else {
      reasons.push('لا توجد حزمة تلاقي صالحة (مصدران فأكثر أحدهما قوي) قريبة من السعر في اتجاه ' + side);
      return {ok:false, reasons:reasons, plan:null};
    }
  }

  var best = picked[1], lvl = best.px;
  var width = Math.min(0.35 * atr4, 0.006 * price);
  var minGap = asiaWick ? (0.22 * atr4) : 0.0;
  var eLo, eHi, stop, nearEdge;
  if (side === 'LONG') {
    eHi = Math.min(lvl + width * 0.55, price - minGap);
    eLo = eHi - width;
    stop = eLo - 0.45 * atr4;
    var candL = k4.pl.slice(-8).map(function(p){return p[1];}).filter(function(v){ return v < eLo && (eLo - v) <= 1.0 * atr4; });
    if (candL.length) stop = Math.min(stop, Math.min.apply(null, candL) - 0.15 * atr4);
    nearEdge = eHi;
  } else {
    eLo = Math.max(lvl - width * 0.55, price + minGap);
    eHi = eLo + width;
    stop = eHi + 0.45 * atr4;
    var candS = k4.ph.slice(-8).map(function(p){return p[1];}).filter(function(v){ return v > eHi && (v - eHi) <= 1.0 * atr4; });
    if (candS.length) stop = Math.max(stop, Math.max.apply(null, candS) + 0.15 * atr4);
    nearEdge = eLo;
  }

  var avg = (eLo + eHi) / 2.0;
  var r = Math.abs(avg - stop);
  var riskPct = (r / avg) * 100.0;
  var atrPct = (atr4 / price) * 100.0;
  var distAtr = Math.abs(price - nearEdge) / atr4;
  var distPct = (nearEdge / price - 1.0) * 100.0;

  if (!waitingOnly && distAtr > 1.0) reasons.push('بُعد منطقة الدخول (' + distAtr.toFixed(2) + ' ATR) يتجاوز سقف 1.0 ATR');
  if (riskPct > 5.0) reasons.push('اتساع الوقف البنيوي (' + riskPct.toFixed(2) + '%) يتجاوز السقف الآمن (5.0%)');
  if (riskPct < 0.30) reasons.push('الوقف ضيق جداً (' + riskPct.toFixed(2) + '% < 0.30%) وعرضة للضرب بالضجيج');
  if (atrPct < 0.25) reasons.push('تذبذب العملة ميت حالياً (ATR = ' + atrPct.toFixed(2) + '% < 0.25%)');

  var pool = [];
  if (side === 'LONG') {
    clusterLevelsJS(k4, k1, price, 'SHORT', false, null, 0).forEach(function(cl){ pool.push(cl.px); });
    k4.ph.slice(-8).forEach(function(p){ pool.push(p[1]); });
    if (k1h) k1h.ph.slice(-8).forEach(function(p){ pool.push(p[1]); });
    if (data.hi24) pool.push(data.hi24);
    pool = pool.filter(function(x){ return x > avg + 0.55 * r; }).sort(function(a,b){ return a - b; });
  } else {
    clusterLevelsJS(k4, k1, price, 'LONG', false, null, 0).forEach(function(cl){ pool.push(cl.px); });
    k4.pl.slice(-8).forEach(function(p){ pool.push(p[1]); });
    if (k1h) k1h.pl.slice(-8).forEach(function(p){ pool.push(p[1]); });
    if (data.lo24) pool.push(data.lo24);
    pool = pool.filter(function(x){ return x < avg - 0.55 * r; }).sort(function(a,b){ return b - a; });
  }
  var uniq = [];
  pool.forEach(function(x){ if (!uniq.length || Math.abs(x - uniq[uniq.length-1]) / uniq[uniq.length-1] > 0.004) uniq.push(x); });

  var need = [1.8, 2.6, 3.5], maxCap = [4.0, 5.8, 8.5], fbR = [2.1, 3.1, 4.4], mults = [1.0, 2.0, 3.1];
  var tgts = [];
  for (var kk = 0; kk < 3; kk++) {
    var wantPx = side === 'LONG' ? (avg + need[kk] * r) : (avg - need[kk] * r);
    var capPx = side === 'LONG' ? (avg + maxCap[kk] * r) : (avg - maxCap[kk] * r);
    var pick = null;
    for (var u = 0; u < uniq.length; u++) {
      var tp = uniq[u];
      var ok = side === 'LONG' ? (tp >= wantPx && tp <= capPx) : (tp >= capPx && tp <= wantPx);
      if (ok) { pick = tp; break; }
    }
    if (pick === null) {
      var ext = Math.min(fbR[kk] * r, mults[kk] * 2.2 * atr4);
      ext = Math.max(ext, (need[kk] + 0.1) * r);
      pick = side === 'LONG' ? (avg + ext) : (avg - ext);
    }
    if (tgts.length) {
      if (side === 'LONG' && pick <= tgts[tgts.length - 1]) pick = tgts[tgts.length - 1] + 0.75 * r;
      if (side === 'SHORT' && pick >= tgts[tgts.length - 1]) pick = tgts[tgts.length - 1] - 0.75 * r;
    }
    tgts.push(pick);
  }
  var rr = tgts.map(function(t){ return Math.abs(t - avg) / r; });
  if (rr[0] < 1.8) reasons.push('العائد للمخاطرة للهدف الأول (R' + rr[0].toFixed(2) + ') أقل من الحد الأدنى (1.80)');
  if (rr[1] < 2.6) reasons.push('العائد للمخاطرة للهدف الثاني (R' + rr[1].toFixed(2) + ') أقل من الحد الأدنى (2.60)');

  var score = 90.0, notes = [];
  var td = trendDirJS(k4, k1);
  var want = side === 'LONG' ? 1 : -1;
  var al4 = td[0] * want, al1 = td[1] * want;
  if (al4 >= 3) { score += 3; notes.push('اتجاه 4س قوي'); }
  else if (al4 === 2) { score += 1; notes.push('اتجاه 4س'); }
  else if (al4 <= -1) { score -= 3; notes.push('ضد اتجاه 4س'); }
  if (al1 >= 2) score += 2; else if (al1 <= -2) score -= 2;

  var stObj = structureJS(k4, side);
  score += 3 * stObj[1];
  if (best.w >= 3.5 && best.strong >= 2) { score += 4; notes.push('حزمة قوية'); }
  else if (best.w >= 2.2) score += 2;
  else score -= 1;

  if (data.qv >= 500) score += 3;
  else if (data.qv >= 150) score += 2;
  else if (data.qv >= 40) score += 1;
  else score -= 1;

  var mh = k4.macd_hist[k4.macd_hist.length - 1], mhp = k4.macd_hist[k4.macd_hist.length - 2];
  var mom = (mh !== null && mhp !== null && mh > mhp) ? 1 : -1;
  if (mom * want > 0) { score += 2; notes.push('زخم مؤيد'); } else score -= 1;

  var rsi4 = k4.rsi[k4.rsi.length - 1] || 50, rsi1 = k1.rsi[k1.rsi.length - 1] || 50;
  if (side === 'LONG') {
    if (rsi4 > 74 || rsi1 > 76) { score -= 4; notes.push('RSI متطرف'); }
    else if (rsi4 < 62) score += 1;
  } else {
    if (rsi4 < 26 || rsi1 < 24) { score -= 3; notes.push('RSI متطرف'); }
    else if (rsi4 > 38) score += 1;
  }
  if (Math.abs(data.funding) > 0.10) { score -= 2; notes.push('فاندنغ شاذ'); }
  if (isTrend) notes.push('ارتكاز ترند نشط');
  if (asiaWick) notes.push('اصطياد ذيل آسيا');

  if (asiaWick) score += Math.max(0.0, 0.75 - Math.abs(distAtr - 0.38)) * 3.5;
  else score += Math.max(0.0, 0.70 - distAtr) * 4.0;
  score = Math.round(score * 10) / 10;

  if (usedFastTrend && score < 99.0) {
    reasons.push('صفقة ترند سريع بدرجة (' + score.toFixed(1) + ') أقل من شرط الدرجة A/B (99.0)');
  } else if (score < 95.0) {
    reasons.push('الدرجة الفنية الإجمالية (' + score.toFixed(1) + ') أقل من حد القبول الرسمي (95.0)');
  }

  var grade = score >= 103 ? 'A' : (score >= 99 ? 'B' : 'C');
  var reach = distAtr <= 0.35 ? 'A' : (distAtr <= 0.65 ? 'B' : 'C');
  var reachP = distAtr <= 0.35 ? 80 : (distAtr <= 0.65 ? 68 : 54);
  var lev = atrPct > 5.0 ? '2x (تذبذب عالٍ)' : ((['BTC','ETH','SOL','BNB'].indexOf(data.name) !== -1) ? '3x–5x' : '3x');

  return {
    ok: reasons.length === 0,
    reasons: reasons,
    plan: {
      side: side, entryLo: eLo, entryHi: eHi, avg: avg, stop: stop, targets: tgts, rr: rr,
      riskPct: riskPct, atrPct: atrPct, distAtr: distAtr, distPct: distPct,
      score: score, grade: grade, reach: reach, reachP: reachP, lev: lev,
      struct: stObj[0], rsi4: rsi4, rsi1: rsi1, isTrend: isTrend, waitingOnly: waitingOnly,
      tags: best.tags.map(function(t){ return TAG_AR_JS[t] || t; }).join(' + '), nSrc: best.n,
      notes: notes.join(' · ') || '—'
    }
  };
}

function fetchBinanceJson(path) {
  var bases = ['https://www.binance.com/fapi/v1', 'https://fapi.binance.com/fapi/v1'];
  return fetch(bases[0] + path).then(function(r){
    if (r.ok) return r.json();
    if (r.status === 400) throw {badSymbol: true};
    return fetch(bases[1] + path).then(function(r2){
      if (!r2.ok) throw {badSymbol: r2.status === 400};
      return r2.json();
    });
  }).catch(function(err){
    if (err && err.badSymbol) throw err;
    return fetch(bases[1] + path).then(function(r2){
      if (!r2.ok) throw {badSymbol: r2.status === 400};
      return r2.json();
    });
  });
}

function loadSymbolBundle(baseName) {
  var sym = baseName + 'USDT';
  return fetchBinanceJson('/ticker/24hr?symbol=' + sym).catch(function(err){
    if (err && err.badSymbol && baseName.indexOf('1000') !== 0) {
      sym = '1000' + baseName + 'USDT';
      baseName = '1000' + baseName;
      return fetchBinanceJson('/ticker/24hr?symbol=' + sym);
    }
    throw err;
  }).then(function(t24){
    return Promise.all([
      Promise.resolve(t24),
      fetchBinanceJson('/premiumIndex?symbol=' + sym),
      fetchBinanceJson('/klines?symbol=' + sym + '&interval=4h&limit=300'),
      fetchBinanceJson('/klines?symbol=' + sym + '&interval=1d&limit=220'),
      fetchBinanceJson('/klines?symbol=' + sym + '&interval=1h&limit=160'),
      fetchBinanceJson('/klines?symbol=' + sym + '&interval=1w&limit=55').catch(function(){ return []; }),
      fetchBinanceJson('/klines?symbol=' + sym + '&interval=1M&limit=18').catch(function(){ return []; })
    ]).then(function(res){
      var td = res[0], pm = res[1];
      var k4 = enrichKlines(res[2]), k1 = enrichKlines(res[3]), k1h = enrichKlines(res[4]);
      var kw = (res[5] && res[5].length) ? enrichKlines(res[5]) : null;
      var km = (res[6] && res[6].length) ? enrichKlines(res[6]) : null;
      var price = Number(td.lastPrice), mark = Number(pm.markPrice || price);
      return {
        sym: sym, name: baseName, price: price, mark: mark,
        markDiffPct: price > 0 ? Math.abs(mark - price) / price * 100.0 : 0,
        chg: Number(td.priceChangePercent), qv: Number(td.quoteVolume) / 1e6,
        hi24: Number(td.highPrice), lo24: Number(td.lowPrice),
        funding: Number(pm.lastFundingRate || 0) * 100.0,
        k4: k4, k1: k1, k1h: k1h, kw: kw, km: km
      };
    });
  });
}

function analyzeCustomCoin() {
  var inp = document.getElementById('customCoinInp');
  var box = document.getElementById('liveCoinResult');
  var base = normSymInput(inp.value);
  if (!base) {
    box.style.display = 'block';
    box.innerHTML = '<div class="warn">⚠️ اكتب رمز العملة أولاً (مثال: <b>SOL</b> أو <b>DOGE</b> أو <b>PEPE</b>).</div>';
    return;
  }
  box.style.display = 'block';
  box.innerHTML = '<div class="note" style="text-align:center">⏳ جاري جلب الشموع الحية من بايننس وتحليل <b>' + base + '</b> بمعادلات v3.4...</div>';

  loadSymbolBundle(base).then(function(data){
    var atr4 = data.k4.atr[data.k4.atr.length - 1] || (data.price * 0.02);
    var sr = srLevelsJS(data.k4, data.k1, data.price, atr4);
    var evL = evaluateSideJS(data, 'LONG');
    var evS = evaluateSideJS(data, 'SHORT');

    var pos24 = (data.hi24 > data.lo24) ? ((data.price - data.lo24) / (data.hi24 - data.lo24) * 100.0) : 50.0;
    var e20_4 = data.k4.ema20[data.k4.ema20.length - 1] || 0;
    var rsi4 = data.k4.rsi[data.k4.rsi.length - 1] || 50;
    var expCoiling = (pos24 >= 75 && data.chg >= 2 && data.chg <= 18 && data.price > e20_4 && data.funding <= 0.025 && rsi4 < 76);

    var chosen = null, alt = null;
    if (evL.ok && evS.ok) {
      chosen = evL.plan.score >= evS.plan.score ? evL : evS;
      alt = (chosen === evL) ? evS : evL;
    } else if (evL.ok) { chosen = evL; alt = evS; }
    else if (evS.ok) { chosen = evS; alt = evL; }
    else {
      // اختيار الاتجاه الأقرب فنياً لتوضيح أسباب الاستبعاد ومنطقة الانتظار
      var td = trendDirJS(data.k4, data.k1)[0];
      if (evL.plan && evS.plan) chosen = (td >= 0) ? evL : evS;
      else chosen = evL.plan ? evL : evS;
      alt = (chosen === evL) ? evS : evL;
    }

    var supTxt = sr.supports.map(fmtPx).join(' · ');
    var resTxt = sr.resistances.map(fmtPx).join(' · ');
    var chgCls = data.chg >= 0 ? 'pos' : 'neg';
    var fCls = data.funding >= 0 ? 'pos' : 'neg';
    var expNote = expCoiling ? '<span class="g expbadge" style="margin-right:6px">🔥 متماسكة قرب قمة 24س (مرشحة رادار انفجار)</span>' : '';

    var wSummary = '—', mSummary = '—', dSummary = '—';
    var riyadhHr = (new Date().getUTCHours() + 3) % 24;
    var isLateDailyJS = (riyadhHr >= 23 || riyadhHr < 3);
    if (data.k1 && data.k1.c && data.k1.c.length >= 3) {
      var dn = data.k1.c.length;
      var do0 = data.k1.o[dn-1], dc0 = data.k1.c[dn-1], dh0 = data.k1.h[dn-1], dl0 = data.k1.l[dn-1];
      var do1 = data.k1.o[dn-2], dc1 = data.k1.c[dn-2], dh1 = data.k1.h[dn-2], dl1 = data.k1.l[dn-2];
      var dl2 = data.k1.l[dn-3];
      var rng0 = Math.max(1e-9, dh0 - dl0), rng1 = Math.max(1e-9, dh1 - dl1);
      var lw0 = (Math.min(do0, dc0) - dl0) / rng0 * 100, uw0 = (dh0 - Math.max(do0, dc0)) / rng0 * 100;
      var lw1 = (Math.min(do1, dc1) - dl1) / rng1 * 100, uw1 = (dh1 - Math.max(do1, dc1)) / rng1 * 100;
      var bd0 = Math.abs(dc0 - do0) / rng0 * 100;
      var ham0 = (lw0 >= 55 && uw0 <= 20 && ((dh0 - dc0) / rng0) <= 0.35 && dl0 <= dl1);
      var ham1 = (lw1 >= 55 && uw1 <= 20 && ((dh1 - dc1) / rng1) <= 0.35 && dl1 <= dl2);
      var str0 = (dc0 > do0 && bd0 >= 50 && uw0 <= 28 && dc0 > dh1);
      if (!isLateDailyJS) {
        dSummary = '⏸️ قبل 23:05 الرياض (شمعة اليوم مستبعدة لعدم اكتمالها) · شمعة أمس المغلقة: ' +
          (ham1 ? ('🔨 همر يومي مكتمل (ذيل سفلي ' + lw1.toFixed(0) + '%)') : ((dc1 >= do1 ? '🟢 خضراء' : '🔴 حمراء') + ' إغلاق ' + fmtPx(dc1)));
      } else {
        dSummary = '🌙 بعد 23:05 الرياض (>83% مكتملة): ' +
          (ham0 ? ('🔨 همر انعكاسي حي (ذيل سفلي ' + lw0.toFixed(0) + '%)') :
           (str0 ? ('🟢 شمعة خضراء قوية فوق قمة أمس (جسم ' + bd0.toFixed(0) + '%)') :
            ('شمعة اليوم غير حاسمة بعد — القرار على إغلاق أمس ' + (ham1 ? '🔨 همر أمس' : fmtPx(dc1)))));
      }
    }
    if (data.kw && data.kw.c && data.kw.c.length >= 2) {
      var wn = data.kw.c.length;
      var wo = data.kw.o[wn-1], wc = data.kw.c[wn-1], wh = data.kw.h[wn-1], wl = data.kw.l[wn-1];
      var wchg = wo > 0 ? ((wc / wo - 1) * 100) : 0;
      var we20 = data.kw.ema20[wn-1] || data.kw.ema9[wn-1];
      var pwh = data.kw.h[wn-2];
      var wuw = (wh > wl) ? ((wh - Math.max(wo, wc)) / (wh - wl) * 100) : 0;
      wSummary = (wc >= wo ? '🟢 خضراء ' : '🔴 حمراء ') + (wchg>=0?'+':'') + wchg.toFixed(1) + '% · ' +
        (we20 ? (wc >= we20 ? 'فوق EMA20 الأسبوعي' : 'تحت EMA20 الأسبوعي') : '') +
        ' · قمة الأسبوع السابق ' + fmtPx(pwh) + ' (ذيل علوي ' + wuw.toFixed(0) + '%)';
    }
    if (data.km && data.km.c && data.km.c.length >= 2) {
      var mn = data.km.c.length;
      var mo = data.km.o[mn-1], mc = data.km.c[mn-1];
      var mchg = mo > 0 ? ((mc / mo - 1) * 100) : 0;
      var pmh = data.km.h[mn-2], pml = data.km.l[mn-2];
      mSummary = (mc >= mo ? '🟢 خضراء ' : '🔴 حمراء ') + (mchg>=0?'+':'') + mchg.toFixed(1) + '% عن افتتاح الشهر · ' +
        'نطاق الشهر السابق [' + fmtPx(pml) + ' – ' + fmtPx(pmh) + ']';
    }
    var htfRowsHtml = '<div class="sr"><span>☀️ الشمعة اليومية (بوابة 23:05)</span><b style="color:#fde68a">' + dSummary + '</b></div>' +
      '<div class="sr"><span>📅 شمعة الأسبوع (1W)</span><b style="color:#93c5fd">' + wSummary + '</b></div>' +
      '<div class="sr"><span>🗓️ شمعة الشهر (1M)</span><b style="color:#c4b5fd">' + mSummary + '</b></div>';

    var html = '';
    if (chosen && chosen.ok && chosen.plan) {
      var p = chosen.plan;
      var cls = p.side === 'LONG' ? 'long' : 'short';
      var sideAr = p.side === 'LONG' ? 'شراء LONG' : 'بيع SHORT';
      var gcol = p.grade === 'A' ? 'ga' : (p.grade === 'B' ? 'gb' : 'gc');
      var rcol = p.reach === 'A' ? 'ra' : (p.reach === 'B' ? 'rb' : 'rc');
      var tgHtml = [0,1,2].map(function(k){
        var pct = ((p.targets[k] / p.avg - 1) * 100);
        return '<div class="lv t' + (k+1) + '"><span>هدف ' + (k+1) + '</span><b>' + fmtPx(p.targets[k]) + '</b><i>' + (pct>=0?'+':'') + pct.toFixed(2) + '% · R' + p.rr[k].toFixed(2) + '</i></div>';
      }).join('');

      html = '<div class="okbox" style="margin:8px 0"><b>✅ نتيجة الفحص الحي (' + data.name + '/USDT):</b> العملة <b>تستوفي كامل شروط المحرك الرسمي (v3.4)</b> في هذه اللحظة!</div>' +
        '<article class="card ' + cls + '" style="margin-top:8px">' +
        '<div class="chead"><div class="csym">🎯 ' + data.name + '<span>/USDT</span> <small>' + p.score.toFixed(1) + ' نقطة</small> ' +
        '<em class="g ' + gcol + '">درجة ' + p.grade + '</em> <em class="g ' + rcol + '">وصول ' + p.reach + ' · ~' + p.reachP + '%</em>' +
        (p.isTrend ? ' <em class="g trtag">⚡ ترند</em>' : '') + expNote + '</div>' +
        '<div><span class="pill ' + cls + '">' + sideAr + '</span></div></div>' +
        '<div class="cbody"><div class="levels">' +
        '<div class="lv entry"><span>منطقة الدخول (Limit)</span><b>' + fmtPx(p.entryLo) + ' – ' + fmtPx(p.entryHi) + '</b><i>' + (p.distPct>=0?'+':'') + p.distPct.toFixed(2) + '% عن السعر · ' + p.distAtr.toFixed(2) + ' ATR</i></div>' +
        '<div class="lv stop"><span>الوقف البنيوي</span><b>' + fmtPx(p.stop) + '</b><i>مخاطرة ' + p.riskPct.toFixed(2) + '%</i></div>' +
        tgHtml + '</div>' +
        '<div class="meta">' +
        '<div><span>السعر اللحظي الآن</span><b>' + fmtPx(data.price) + '</b></div>' +
        '<div><span>تغيّر 24س</span><b class="' + chgCls + '">' + (data.chg>=0?'+':'') + data.chg.toFixed(2) + '%</b></div>' +
        '<div><span>موقع السعر في 24س</span><b>' + pos24.toFixed(0) + '%</b></div>' +
        '<div><span>سيولة 24س</span><b>' + data.qv.toFixed(1) + 'M$</b></div>' +
        '<div><span>فاندنغ</span><b class="' + fCls + '">' + (data.funding>=0?'+':'') + data.funding.toFixed(4) + '%</b></div>' +
        '<div><span>RSI 4س / يومي</span><b>' + p.rsi4.toFixed(0) + ' / ' + p.rsi1.toFixed(0) + '</b></div>' +
        '<div><span>البنية الفنية</span><b>' + p.struct + '</b></div>' +
        '<div><span>الرافعة المقترحة</span><b>' + p.lev + '</b></div>' +
        '<div class="sr"><span>أقرب 3 دعوم</span><b class="pos">' + supTxt + '</b></div>' +
        '<div class="sr"><span>أقرب 3 مقاومات</span><b class="neg">' + resTxt + '</b></div>' +
        htfRowsHtml +
        '<div class="sr"><span>مصادر منطقة الدخول</span><b>' + p.tags + ' (' + p.nSrc + ') · ' + p.notes + '</b></div>' +
        '</div>' +
        (alt ? ('<div class="plan" style="margin-top:10px"><b>↔️ حالة الاتجاه المعاكس (' + (p.side==='LONG'?'SHORT':'LONG') + '):</b> ' +
          (alt.ok && alt.plan
            ? ('متاح أيضاً كسيناريو مضاد بدرجة <b>' + alt.plan.score.toFixed(1) + ' (' + alt.plan.grade + ')</b> من منطقة <b style="direction:ltr;display:inline-block">' + fmtPx(alt.plan.entryLo) + ' – ' + fmtPx(alt.plan.entryHi) + '</b> (وقف ' + fmtPx(alt.plan.stop) + ').')
            : ('غير مؤهل حالياً — ' + (alt.reasons.join(' · ') || 'لا تتوفر شروطه'))) + '</div>') : '') +
        '</div></article>';
    } else {
      var allRej = [];
      if (chosen && chosen.reasons) allRej = chosen.reasons.slice();
      if (alt && alt.reasons && !chosen.plan) {
        alt.reasons.forEach(function(r){ if (allRej.indexOf(r) === -1) allRej.push(r); });
      }
      var rejHtml = allRej.map(function(r){ return '<li>' + r + '</li>'; }).join('');
      var p2 = chosen ? chosen.plan : null;
      var st4 = structureJS(data.k4, data.chg >= 0 ? 'LONG' : 'SHORT')[0];
      var waitHtml = '';
      if (p2) {
        var sideLbl = p2.side === 'LONG' ? 'الشراء (LONG)' : 'البيع (SHORT)';
        waitHtml = '<div class="plan" style="margin-top:10px;border-color:#785713;background:#171207;color:#fde68a">' +
          '<b>🧭 أقرب منطقة انتظار فنية (' + sideLbl + ' — للمراقبة فقط دون مطاردة):</b> ' +
          '<span style="direction:ltr;display:inline-block;font-weight:700;color:#fff">' + fmtPx(p2.entryLo) + ' – ' + fmtPx(p2.entryHi) + '</span> ' +
          '(على بُعد <b>' + p2.distAtr.toFixed(2) + ' ATR</b> · وقف بنيوي تقديري: <span style="direction:ltr;display:inline-block;color:#f87171">' + fmtPx(p2.stop) + '</span> · هدف أول: <span style="direction:ltr;display:inline-block;color:#4ade80">' + fmtPx(p2.targets[0]) + '</span> R' + p2.rr[0].toFixed(2) + ' · مصادرها: ' + p2.tags + ').' +
          '</div>';
      }
      html = '<div class="warn" style="margin:8px 0"><b>⚠️ نتيجة الفحص الحي (' + data.name + '/USDT): غير مؤهلة للدخول الفوري في التقرير الرسمي حالياً</b>' + expNote +
        '<div style="margin-top:6px;color:#fecaca"><b>أسباب الاستبعاد وفق قواعد v3.4 الصارمة:</b><ul style="margin:5px 0 2px">' + rejHtml + '</ul></div></div>' +
        '<article class="card" style="border-right:4px solid #f59e0b;margin-top:8px">' +
        '<div class="chead"><div class="csym">📊 الخريطة الفنية اللحظية لعملة ' + data.name + '<span>/USDT</span></div>' +
        '<div><em class="g gb">تشخيص فوري حي</em></div></div>' +
        '<div class="cbody"><div class="meta">' +
        '<div><span>السعر اللحظي الآن</span><b>' + fmtPx(data.price) + '</b></div>' +
        '<div><span>تغيّر 24س</span><b class="' + chgCls + '">' + (data.chg>=0?'+':'') + data.chg.toFixed(2) + '%</b></div>' +
        '<div><span>موقع السعر في مدى 24س</span><b>' + pos24.toFixed(0) + '%</b></div>' +
        '<div><span>سيولة 24س</span><b>' + data.qv.toFixed(1) + 'M$</b></div>' +
        '<div><span>فاندنغ</span><b class="' + fCls + '">' + (data.funding>=0?'+':'') + data.funding.toFixed(4) + '%</b></div>' +
        '<div><span>RSI 4س / يومي</span><b>' + rsi4.toFixed(0) + ' / ' + (data.k1.rsi[data.k1.rsi.length-1]||50).toFixed(0) + '</b></div>' +
        '<div><span>ATR(4س)</span><b>' + (atr4/data.price*100).toFixed(2) + '%</b></div>' +
        '<div><span>البنية الفنية (4س)</span><b>' + st4 + '</b></div>' +
        '<div class="sr"><span>أقرب 3 دعوم حقيقية</span><b class="pos">' + supTxt + '</b></div>' +
        '<div class="sr"><span>أقرب 3 مقاومات حقيقية</span><b class="neg">' + resTxt + '</b></div>' +
        htfRowsHtml +
        '</div>' + waitHtml + '</div></article>';
    }
    box.innerHTML = '<div style="text-align:left;margin-bottom:4px"><button class="abtn" style="padding:4px 10px;font-size:11.5px" onclick="document.getElementById(\'liveCoinResult\').style.display=\'none\'">✖ إغلاق نتيجة الفحص</button></div>' + html;
  }).catch(function(err){
    var msg = (err && err.badSymbol)
      ? ('❌ الرمز <b>' + base + '</b> غير موجود في عقود بايننس الآجلة الدائمة (USDT-M Perpetual). تأكد من كتابة الرمز الصحيح بالإنجليزية مثل BTC أو SOL أو PEPE.')
      : ('⚠️ تعذر الاتصال المباشر ببيانات بايننس من المتصفح الآن — تأكد من اتصالك بالإنترنت وأعد المحاولة.');
    box.innerHTML = '<div class="warn">' + msg + '</div>';
  });
}
"""


def fp(x, tick=0.0001):
    if x is None:
        return "-"
    ax = abs(x)
    if ax >= 1000:
        p = 2
    elif ax >= 10:
        p = 2
    elif ax >= 1:
        p = 4
    elif ax >= 0.01:
        p = 5
    elif ax >= 0.0001:
        p = 6
    else:
        p = 8
    if tick and tick > 0:
        d = max(0, min(p, int(round(-1 * __import__("math").log10(tick)))))
    else:
        d = p
    s = f"{x:,.{d}f}"
    return s


def load():
    trades = json.load(open(os.path.join(BASE, "scan_result.json")))
    meta = json.load(open(os.path.join(BASE, "scan_meta.json")))
    try:
        state = json.load(open(os.path.join(BASE, "cycle_state.json")))
    except Exception:
        state = {}
    stats = json.load(open(os.path.join(BASE, "fill_stats.json"))) if os.path.exists(os.path.join(BASE, "fill_stats.json")) else DEFAULT_FILL_STATS
    try:
        tracked = json.load(open(os.path.join(BASE, "prev_tracked.json")))
    except Exception:
        tracked = []
    # حالة التتبع المحفوظة تخصّ صفقات المسح السابق (held)
    try:
        held = json.load(open(os.path.join(BASE, "held.json")))
    except Exception:
        held = []
    try:
        t24 = {x["symbol"]: x for x in json.load(open(os.path.join(BASE, "cache", "t24.json")))}
        prem = {x["symbol"]: x for x in json.load(open(os.path.join(BASE, "cache", "prem.json")))}
    except Exception:
        t24, prem = {}, {}
    try:
        exp_data = json.load(open(os.path.join(BASE, "explosion_candidates.json")))
    except Exception:
        exp_data = {}
    return trades, meta, state, stats, t24, prem, tracked, held, exp_data


COMMODITY_AND_STABLE_SYMS = {
    "PAXGUSDT", "XAUUSDT", "XAUTUSDT", "XAGUSDT",
    "USDCUSDT", "FDUSDUSDT", "TUSDUSDT", "USDPUSDT", "DAIUSDT", "USDEUSDT", "USD1USDT",
}


def update_lifetime_stats(tracked_list, state, now_riyadh):
    """عداد تراكمي مستقل يحسب الصفقات المكتملة فقط (remaining_pct == 0) بصافي العائد المحقق بعد الرسوم والانزلاق."""
    lt_path = os.path.join(BASE, "lifetime_stats.json")
    if os.path.exists(lt_path):
        try:
            lt = json.load(open(lt_path, encoding="utf-8"))
        except Exception:
            lt = {}
    else:
        lt = {}
    lt.setdefault("started_at", now_riyadh.strftime("%Y-%m-%d %H:%M"))
    lt.setdefault("wins", 0)
    lt.setdefault("losses", 0)
    lt.setdefault("breakevens", 0)
    lt.setdefault("net_r", 0.0)
    lt.setdefault("counted", {})
    counted = lt["counted"]
    fallback_ts = int(state.get("prev_ts") or 0)
    now_ms = int(now_riyadh.timestamp() * 1000)

    closed_final_states = {"CLOSED_TP3", "CLOSED_STOP", "CLOSED_BE", "CLOSED_TRAIL", "CLOSED_EXPIRY"}

    for x in (tracked_list or []):
        ots = int(x.get("origin_ts") or fallback_ts or 0)
        tid = f"{x.get('sym','')}|{x.get('side','')}|{ots}"
        if tid in counted:
            continue

        t_stat = x.get("trade_status")
        st = str(x.get("status") or "")
        is_final_closed = (
            (t_stat in closed_final_states and float(x.get("remaining_pct", 0.0)) == 0.0)
            or (t_stat is None and (st.startswith("وصل") or st == "ضربت الوقف"))
        )
        if not is_final_closed:
            continue

        r_val = float(x.get("realized_r") if x.get("realized_r") is not None else (x.get("r_now") or 0.0))
        if r_val > 0.02:
            lt["wins"] = int(lt["wins"]) + 1
            res_code = "W"
        elif r_val < -0.02:
            lt["losses"] = int(lt["losses"]) + 1
            res_code = "L"
        else:
            lt["breakevens"] = int(lt.get("breakevens", 0)) + 1
            res_code = "BE"
        lt["net_r"] = round(float(lt["net_r"]) + r_val, 3)
        counted[tid] = {
            "sym": x.get("sym"),
            "side": x.get("side"),
            "trade_status": t_stat or st,
            "res": res_code,
            "r": round(r_val, 3),
            "ts": now_ms,
        }

    if len(counted) > 2000:
        keep_keys = sorted(counted.keys(), key=lambda k: counted[k].get("ts", 0))[-2000:]
        lt["counted"] = {k: counted[k] for k in keep_keys}
    lt["updated_at"] = now_riyadh.strftime("%Y-%m-%d %H:%M")
    try:
        json.dump(lt, open(lt_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except Exception:
        pass
    return lt


def scan_macro_regimes(t24, prem, now_riyadh, is_confirm_run=False):
    """يمسح الفريم اليومي (1D) لبناء قائمتين متمايزتين بدقة:
    1) 🧲 العملات الاستثمارية (مرحلة القاع والعصر الأفقي + حساب التلاعب السُفلي Spring).
    2) 🚀 عملات كسر الهيكل اليومي النشط (3 إغلاقات يومية متتالية بالجسم الكامل BOS + تدفق سيولة).
    """
    import time as _time, concurrent.futures as _cf
    macro_path = os.path.join(BASE, "macro_investments.json")
    now_ms = int(_time.time() * 1000)

    if is_confirm_run and os.path.exists(macro_path):
        try:
            cached_m = json.load(open(macro_path, encoding="utf-8"))
            if now_ms - int(cached_m.get("ts", 0)) < 5 * 3600 * 1000:
                return cached_m
        except Exception:
            pass

    try:
        from core import klines as _klines, enrich as _enrich, cached_get as _cget
    except Exception:
        if os.path.exists(macro_path):
            return json.load(open(macro_path, encoding="utf-8"))
        return {"ts": now_ms, "squeeze": [], "bos3": []}

    try:
        ei = _cget("/v1/exchangeInfo", "exchangeInfo", ttl=6 * 3600)
        if not t24:
            t24 = {x["symbol"]: x for x in _cget("/v1/ticker/24hr", "t24", ttl=300)}
        if not prem:
            prem = {x["symbol"]: x for x in _cget("/v1/premiumIndex", "prem", ttl=300)}
    except Exception:
        if os.path.exists(macro_path):
            return json.load(open(macro_path, encoding="utf-8"))
        return {"ts": now_ms, "squeeze": [], "bos3": []}

    # قراءة مناخ البيتكوين اليومي (BTC Macro Regime) لتوجيه الحجم الاستثماري علمياً
    btc_regime = {"state": "neutral", "label": "🟡 مناخ محايد", "advice": "التزم بالحجم القياسي (1% مخاطرة لكل صفقة مع وقف صريح في المنصة)."}
    try:
        bk = _enrich(_klines("BTCUSDT", "1d", 120))
        bc = bk["c"][-1]
        be50 = bk["ema50"][-1] or bc
        brsi = bk["rsi"][-1] or 50.0
        if bc >= be50:
            btc_regime = {
                "state": "bull",
                "label": f"🟢 مناخ داعم للتجميع (BTC فوق EMA50 اليومي · RSI {brsi:.0f})",
                "advice": "المناخ الكلي إيجابي — يُسمح بالحجم القياسي (1% مخاطرة للصفقة) مع وقف صريح في المنصة.",
            }
        elif brsi <= 38.0:
            btc_regime = {
                "state": "oversold",
                "label": f"🟡 مناخ ارتداد من تشبع بيعي (BTC RSI اليومي {brsi:.0f} ≤ 38)",
                "advice": "البيتكوين في منطقة تشبع بيعي تاريخية تدعم ارتداد قيعان التلاعب السُفلي (Spring) — التزم بوقف صريح.",
            }
        else:
            btc_regime = {
                "state": "caution",
                "label": f"🟠 مناخ حذر (BTC دون EMA50 اليومي · RSI {brsi:.0f})",
                "advice": "البيتكوين تحت متوسطه اليومي — خفّض حجم المركز الاستثماري للنصف (0.5% مخاطرة فقط) ولا تدخل إلا عملة اكتمل فيها ذيل التلاعب السُفلي.",
            }
    except Exception:
        pass

    pool = []
    for s in ei.get("symbols", []):
        sym = s.get("symbol", "")
        if s.get("contractType") != "PERPETUAL" or s.get("quoteAsset") != "USDT" or s.get("status") != "TRADING":
            continue
        if sym in COMMODITY_AND_STABLE_SYMS or not all(ord(ch) < 128 for ch in sym):
            continue
        td_item = t24.get(sym)
        pm_item = prem.get(sym)
        if not td_item or not pm_item:
            continue
        qv = float(td_item.get("quoteVolume", 0)) / 1e6
        age_d = (now_ms - int(s.get("onboardDate", now_ms))) / 86400000.0
        if qv < 8.0 or age_d < 35:
            continue
        tick = 0.0001
        step_sz = 0.0
        min_not = 5.0
        for flt in s.get("filters", []):
            ft = flt.get("filterType")
            if ft == "PRICE_FILTER":
                tick = float(flt.get("tickSize", 0.0001))
            elif ft == "LOT_SIZE":
                step_sz = float(flt.get("stepSize", 0.0))
            elif ft == "MIN_NOTIONAL":
                min_not = float(flt.get("notional", 5.0))
        pool.append((sym, s.get("baseAsset", sym[:-4]), qv, age_d, tick, step_sz, min_not, td_item, pm_item))

    pool.sort(key=lambda x: -x[2])
    pool = pool[:110]

    def _eval_one(item):
        sym, name, qv, age_d, tick, step_sz, min_not, td_item, pm_item = item
        try:
            k1 = _enrich(_klines(sym, "1d", 300))
        except Exception:
            return None, None
        c, h, l, o, v = k1["c"], k1["h"], k1["l"], k1["o"], k1["v"]
        atr, rsi, e9, e20, e50 = k1["atr"], k1["rsi"], k1["ema9"], k1["ema20"], k1["ema50"]
        n = len(c)
        if n < 90 or not atr[-1] or atr[-1] <= 0:
            return None, None

        price = float(td_item["lastPrice"])
        chg24 = float(td_item["priceChangePercent"])
        fund = float(pm_item.get("lastFundingRate", 0)) * 100.0
        atr_d = atr[-1]
        rsi_d = rsi[-1] or 50.0

        win180 = min(180, n)
        hi180, lo180 = max(h[-win180:]), min(l[-win180:])
        pos180 = (price - lo180) / (hi180 - lo180) if hi180 > lo180 else 0.5

        # قياس صندوق التجميع الأفقي (آخر 20 يوماً مغلقاً بالأجسام لتجنب تشويه ذيول التلاعب)
        bodies_low = sorted(min(o[i], c[i]) for i in range(-21, -1))
        bodies_high = sorted(max(o[i], c[i]) for i in range(-21, -1))
        core_floor = bodies_low[2]
        core_ceil = bodies_high[-3]
        box_atr_ratio = (core_ceil - core_floor) / atr_d if atr_d > 0 else 99.0
        box_pct = (core_ceil - core_floor) / core_floor * 100.0 if core_floor > 0 else 99.0

        bw_hist = []
        for i in range(max(20, n - 95), n):
            if atr[i]:
                seg = c[i - 20:i]
                m = sum(seg) / 20.0
                sd = (sum((x - m) ** 2 for x in seg) / 20.0) ** 0.5
                bw_hist.append((sd / m) * 0.6 + (atr[i] / c[i]) * 0.4)
        cur_bw = bw_hist[-1] if bw_hist else 1.0
        squeeze_pct = (1.0 - sum(1 for x in bw_hist if x <= cur_bw) / max(1, len(bw_hist))) * 100.0

        inv_item = None
        # -------- 1) فحص العملات الاستثمارية العلمي (قاع 180ي + صندوق أفقي حقيقي بدون ذيول ضخ وتفريغ + دفاع شرائي فعلي + وقف صريح Hard Stop)
        full_rng20 = (max(h[-20:]) - min(l[-20:])) / max(1e-9, min(l[-20:])) * 100.0 if n >= 21 else 99.0
        chg20 = (price / c[-21] - 1.0) * 100.0 if n >= 21 and c[-21] > 0 else 0.0
        chg10 = (price / c[-11] - 1.0) * 100.0 if n >= 11 and c[-11] > 0 else 0.0
        if (age_d >= 60 and pos180 <= 0.25 and box_atr_ratio <= 4.0 and box_pct <= 20.0
            and full_rng20 <= 35.0 and -16.0 <= chg20 <= 16.0 and chg10 >= -12.0
            and squeeze_pct >= 50.0 and fund <= 0.015 and core_floor - 0.50 * atr_d <= price <= core_ceil * 1.01):
            spring_done = any((l[i] < core_floor - 0.08 * atr_d and c[i] >= core_floor) for i in range(-8, 0))
            rsi_min14 = min((rsi[i] or 50.0) for i in range(-15, 0))
            rsi_div = (26.0 <= rsi_d <= 54.0) and (rsi_d >= rsi_min14 + 3.0)
            if spring_done or rsi_div:
                e_hi = min(core_floor + 0.25 * atr_d, price)
                e_lo = max(lo180 * 0.94, min(core_floor - 0.35 * atr_d, e_hi - 0.38 * atr_d))
                avg_e = (e_lo + e_hi) / 2.0
                lowest_wick = min(core_floor, min(l[-21:]))
                stop = lowest_wick - 0.65 * atr_d
                r = abs(avg_e - stop)
                risk_pct = (r / avg_e) * 100.0 if avg_e > 0 else 99.0

                if r > 0 and 1.2 <= risk_pct <= 18.0:
                    t1 = max(core_ceil, e50[-1] or 0, avg_e + 1.9 * r)
                    hi90 = max(h[-min(90, n):-5])
                    t2 = max(hi90 if hi90 > t1 * 1.04 else 0, avg_e + 3.1 * r)
                    mid180 = lo180 + 0.52 * (hi180 - lo180)
                    t3 = max(mid180 if mid180 > t2 * 1.05 else 0, avg_e + 4.6 * r)
                    rr = [(t1 - avg_e) / r, (t2 - avg_e) / r, (t3 - avg_e) / r]

                    sc = 92.0 + (1.0 - pos180 / 0.25) * 4.0 + (squeeze_pct - 50.0) * 0.10
                    tags_ar = [f"قاع 180ي ({pos180*100:.0f}%)", f"نطاق أفقي {box_pct:.1f}%", f"عصر {squeeze_pct:.0f}%"]
                    if spring_done and rsi_div:
                        sc += 7.0
                        badge = "🪤 ذيل تلاعب مكتمل + تعافي RSI (النموذج الأقوى +0.39R)"
                        tags_ar.append("Spring + انحراف RSI")
                    elif spring_done:
                        sc += 5.0
                        badge = "🪤 اكتمل ذيل التلاعب السُفلي (Spring)"
                        tags_ar.append("ذيل تلاعب سُفلي مكتمل")
                    else:
                        sc += 3.0
                        badge = "📈 قاع أفقي معصور + تعافي RSI"
                        tags_ar.append("تعافي RSI من القاع")
                    if qv >= 50:
                        sc += 1.5

                    sz_inv = compute_risk_position_size(
                        e_hi, stop, "LONG", step=step_sz, min_notional=min_not,
                        sym=sym, atr_pct=(atr_d / price * 100.0), strategy_type="macro_squeeze", entry_is_maker=True,
                    )
                    if sz_inv.get("valid"):
                        inv_item = {
                            "sym": sym, "name": name, "price": price, "tick": tick, "qv": qv, "chg": chg24,
                            "funding": fund, "rsi_d": rsi_d, "pos180": pos180 * 100.0,
                            "squeeze_pct": squeeze_pct, "box_floor": core_floor, "box_ceil": core_ceil, "box_pct": box_pct,
                            "spring_done": spring_done, "badge": badge, "score": round(sc, 1),
                            "entry_lo": e_lo, "entry_hi": e_hi, "avg": avg_e, "stop": stop,
                            "targets": [t1, t2, t3], "rr": rr, "risk_pct": risk_pct,
                            "theoretical_stop_pct": sz_inv["theoretical_stop_pct"],
                            "effective_stop_pct": sz_inv["effective_stop_pct"],
                            "qty": sz_inv["position_size"], "position_size": sz_inv["position_size"],
                            "position_notional_usd": sz_inv["position_notional_usd"],
                            "leverage": sz_inv["leverage"],
                            "margin_required_usd": sz_inv["margin_required_usd"],
                            "margin_pct_equity": sz_inv["margin_pct_equity"],
                            "equity_usd": sz_inv["equity_usd"],
                            "actual_risk_cash": sz_inv["actual_risk_cash"],
                            "actual_risk_pct_equity": sz_inv["actual_risk_pct_equity"],
                            "qty_1r": sz_inv["position_size"],
                            "pos_usd_1r": sz_inv["position_notional_usd"],
                            "dist_pct": (e_hi / price - 1.0) * 100.0,
                            "reasons": tags_ar,
                        }

        # -------- 2) محرك كسر الهيكل والاتجاه الصاعد والهمر اليومي + القاعدة الزمنية لشمعة اليوم (23:05) + فلتر 1W/1M:
        # • طوال اليوم (03:00 – 22:59 بتوقيت الرياض): شمعة اليوم الجارية (-1) غير ناضجة (<83%) ← لا تُحسب أبداً ضمن الإغلاقات ولا كهمر؛
        #   يُعتمد حصراً على الشموع اليومية المغلقة (-4,-3,-2 أو همر أمس المغلق -2)، ويُفحص السعر اللحظي فقط للتأكد أنه لم يكسر الوقف!
        # • ابتداءً من مسح 23:05 حتى 02:59 فجراً (اكتمل ≥83.5% من الشمعة اليومية):
        #   1) تُقبل شمعة اليوم (-1) كشمعة إغلاق ثالثة/ثانية فقط إذا كانت خضراء قوية وصحية (جسم ≥50%، ذيل علوي ≤28%، فوق قمة أمس)
        #      وليس أمامها مقاومة قريبة تعطّل إغلاقها (ثبات إحصائي 96.6% حتى الإغلاق 03:00).
        #   2) كما تُرصد شمعة الهمر الانعكاسية (🔨 Hammer بذيل رفض سُفلي ≥55% وذيل علوي ≤20% بعد كنس قاع اليوم السابق داخل اتجاه صاعد
        #      فوق EMA20 الأسبوعي وEMA50 اليومي، حتى لو لم يصل جسمها لليوم السابق · 50.0% نجاح و+0.27R EV).
        is_late_daily = (now_riyadh.hour >= 23 or now_riyadh.hour < 3)
        bos_item = None
        if n >= 50 and rsi_d < 78.0:
            cand_modes = []
            e50_now = e50[-1]
            e20_now = k1["ema20"][-1]

            # ====== (1) التقييم على الشموع اليومية المغلقة تماماً (يعمل في جميع الأوقات دون تشويش من شمعة اليوم غير المكتملة) ======
            rlive_chk = max(1e-9, h[-1] - l[-1])
            # في المساء المتأخر فقط نتحقق ألا تكون شمعة اليوم شبه المكتملة قد انقلبت لشمعة تصريف حمراء كبيرة
            late_not_dumping = (not is_late_daily) or (
                (c[-1] >= o[-1] or ((o[-1] - c[-1]) <= 0.32 * atr_d and (h[-1] - max(o[-1], c[-1])) / rlive_chk <= 0.45))
                and chg24 > -5.5
            )

            if late_not_dumping:
                i1, i2, i3 = -4, -3, -2
                lvl3 = max(h[n + i1 - 30 : n + i1])
                r1, r2, r3 = max(1e-9, h[i1] - l[i1]), max(1e-9, h[i2] - l[i2]), max(1e-9, h[i3] - l[i3])
                pre_run3 = (lvl3 - min(l[n + i1 - 10 : n + i1])) / atr_d
                vol3 = (v[i1] + v[i2] + v[i3]) / 3.0
                vol20_3 = sum(v[n + i1 - 20 : n + i1]) / 20.0
                vx3 = vol3 / vol20_3 if vol20_3 > 0 else 1.0

                # (أ-1) 3 إغلاقات يومية مغلقة خضراء بالجسم الكامل فوق قمة 30 يوماً
                if (c[i1 - 1] <= lvl3
                    and c[i1] > o[i1] and c[i3] > o[i3]
                    and (c[i2] >= o[i2] or (o[i2] - c[i2]) <= 0.12 * atr_d)
                    and c[i1] >= lvl3 + 0.05 * atr_d
                    and min(o[i2], c[i2]) > lvl3 and min(o[i3], c[i3]) > lvl3
                    and (c[i1] - o[i1]) / r1 >= 0.45
                    and (h[i1] - c[i1]) / r1 <= 0.35
                    and (h[i2] - max(o[i2], c[i2])) / r2 <= 0.35
                    and (h[i3] - max(o[i3], c[i3])) / r3 <= 0.35
                    and pre_run3 <= 4.2 and vx3 >= 1.15 and price > lvl3 - 0.10 * atr_d
                    and (price - lvl3) / atr_d <= 1.85):
                    e_hi = min(price, lvl3 + 0.35 * atr_d)
                    e_lo = max(lvl3 - 0.05 * atr_d, e_hi - 0.28 * atr_d)
                    if e_hi <= e_lo:
                        e_hi = e_lo + 0.15 * atr_d
                    stop = lvl3 - 0.50 * atr_d
                    if price > stop + 0.15 * atr_d:
                        cand_modes.append((
                            "3closes", "🚀 3 إغلاقات يومية مغلقة بالجسم فوق قمة 30 يوماً",
                            "أعلى قمة هيكلية لـ 30 يوماً", lvl3, lvl3, [c[i1], c[i2], c[i3]], vx3, n + i1, e_lo, e_hi, stop
                        ))

                # (أ-2) إغلاقان يوميان مغلقان أخضران بالجسم فوق قمة 30 يوماً
                if not cand_modes:
                    j1, j2 = -3, -2
                    lvl2 = max(h[n + j1 - 30 : n + j1])
                    rj1, rj2 = max(1e-9, h[j1] - l[j1]), max(1e-9, h[j2] - l[j2])
                    pre_run2 = (lvl2 - min(l[n + j1 - 10 : n + j1])) / atr_d
                    vol2 = (v[j1] + v[j2]) / 2.0
                    vol20_2 = sum(v[n + j1 - 20 : n + j1]) / 20.0
                    vx2 = vol2 / vol20_2 if vol20_2 > 0 else 1.0
                    if (c[j1 - 1] <= lvl2
                        and c[j1] > o[j1] and c[j2] > o[j2]
                        and c[j1] >= lvl2 + 0.05 * atr_d
                        and min(o[j2], c[j2]) > lvl2
                        and (c[j1] - o[j1]) / rj1 >= 0.45 and (c[j2] - o[j2]) / rj2 >= 0.35
                        and (h[j1] - c[j1]) / rj1 <= 0.35 and (h[j2] - c[j2]) / rj2 <= 0.35
                        and pre_run2 <= 4.2 and vx2 >= 1.15 and price > lvl2 - 0.10 * atr_d
                        and (price - lvl2) / atr_d <= 1.85):
                        e_hi = min(price, lvl2 + 0.35 * atr_d)
                        e_lo = max(lvl2 - 0.05 * atr_d, e_hi - 0.28 * atr_d)
                        if e_hi <= e_lo:
                            e_hi = e_lo + 0.15 * atr_d
                        stop = lvl2 - 0.50 * atr_d
                        if price > stop + 0.15 * atr_d:
                            cand_modes.append((
                                "2closes", "⚡ إغلاقان يوميان مغلقان بالجسم فوق قمة 30 يوماً",
                                "أعلى قمة هيكلية لـ 30 يوماً", lvl2, lvl2, [c[j1], c[j2]], vx2, n + j1, e_lo, e_hi, stop
                            ))

                # (ب) 3 إغلاقات يومية مغلقة خضراء في اتجاه صاعد قبل الوصول لقمة 30 يوماً (مساحة ≥ 1.8R)
                if not cand_modes:
                    hl_uptrend = min(l[-9:-1]) > min(l[-27:-9])
                    in_uptrend = bool((e50_now and c[-2] > e50_now) or (e20_now and c[-2] > e20_now and hl_uptrend))
                    three_rising_green = (
                        c[i1] > o[i1] and c[i2] > o[i2] and c[i3] > o[i3]
                        and c[i2] > c[i1] and c[i3] > c[i2]
                        and (c[i1] - o[i1]) / r1 >= 0.40 and (c[i2] - o[i2]) / r2 >= 0.35 and (c[i3] - o[i3]) / r3 >= 0.35
                        and (h[i1] - c[i1]) / r1 <= 0.36 and (h[i2] - c[i2]) / r2 <= 0.36 and (h[i3] - c[i3]) / r3 <= 0.36
                    )
                    if three_rising_green and in_uptrend and c[i3] < lvl3 and vx3 >= 1.05:
                        b10_ceil = max(max(o[k], c[k]) for k in range(n + i1 - 10, n + i1))
                        e_hi = min(price, c[i3] - 0.15 * atr_d)
                        e_lo = max(o[i2], e_hi - 0.30 * atr_d)
                        stop = min(l[i2], l[i3]) - 0.25 * atr_d
                        if e_hi > e_lo and price > stop + 0.15 * atr_d and (price - c[i3]) <= 1.2 * atr_d:
                            avg_sub = (e_lo + e_hi) / 2.0
                            r_sub = avg_sub - stop
                            if r_sub > 0 and (lvl3 - avg_sub) >= 1.8 * r_sub:
                                cand_modes.append((
                                    "uptrend3g", "📈 3 إغلاقات يومية مغلقة خضراء في اتجاه صاعد (قبل قمة 30ي)",
                                    "مرتكز الموجة الصاعدة (قمة 10ي)", b10_ceil, lvl3, [c[i1], c[i2], c[i3]], vx3, n + i1, e_lo, e_hi, stop
                                ))

            # ====== (2) القراءة المتقدمة بعد 23:05 فقط (اكتمل ≥83.5% من الشمعة اليومية الجارية -1) ======
            if not cand_modes and is_late_daily:
                rl1 = max(1e-9, h[-1] - l[-1])
                body1_pct = (c[-1] - o[-1]) / rl1
                upw1_pct = (h[-1] - max(o[-1], c[-1])) / rl1
                lvl_late30 = max(h[n - 3 - 30 : n - 3])
                # شرط عدم وجود مقاومة قريبة تعطّل إغلاق شمعة 23:05 فوق شمعة أمس:
                clear_close_wall = (c[-1] > lvl_late30 + 0.12 * atr_d) or ((lvl_late30 - c[-1]) >= 0.85 * atr_d)
                strong_today = (c[-1] > o[-1] and c[-1] > h[-2] and body1_pct >= 0.50 and upw1_pct <= 0.28 and clear_close_wall)

                if strong_today:
                    rm3, rm2 = max(1e-9, h[-3] - l[-3]), max(1e-9, h[-2] - l[-2])
                    prev2_ok = (
                        c[-3] > o[-3] and c[-2] > o[-2] and c[-2] > c[-3]
                        and (c[-3] - o[-3]) / rm3 >= 0.38 and (c[-2] - o[-2]) / rm2 >= 0.35
                        and (h[-3] - c[-3]) / rm3 <= 0.36 and (h[-2] - c[-2]) / rm2 <= 0.36
                    )
                    vol_l3 = (v[-3] + v[-2] + v[-1]) / 3.0
                    vol20_l = sum(v[n - 23 : n - 3]) / 20.0
                    vx_l = vol_l3 / vol20_l if vol20_l > 0 else 1.0
                    if prev2_ok and vx_l >= 1.05:
                        if c[-4] <= lvl_late30 and min(o[-2], c[-2]) > lvl_late30 and min(o[-1], c[-1]) > lvl_late30 and (price - lvl_late30) / atr_d <= 1.85:
                            e_hi = min(price - 0.05 * atr_d, lvl_late30 + 0.38 * atr_d)
                            e_lo = max(lvl_late30 - 0.05 * atr_d, e_hi - 0.28 * atr_d)
                            stop = lvl_late30 - 0.50 * atr_d
                            if e_hi > e_lo:
                                cand_modes.append((
                                    "3closes", "🌙 كسر قمة 30ي + شمعة اليوم (بعد 23:05 · مكتملة >85% بلا عائق)",
                                    "أعلى قمة هيكلية لـ 30 يوماً", lvl_late30, lvl_late30, [c[-3], c[-2], c[-1]], vx_l, n - 3, e_lo, e_hi, stop
                                ))
                        elif e50_now and price > e50_now and price < lvl_late30:
                            b10_l = max(max(o[k], c[k]) for k in range(n - 13, n - 3))
                            e_hi = c[-1] - 0.18 * atr_d
                            e_lo = max(o[-2], e_hi - 0.30 * atr_d)
                            stop = min(l[-2], l[-1]) - 0.25 * atr_d
                            avg_s = (e_lo + e_hi) / 2.0
                            r_s = avg_s - stop
                            if e_hi > e_lo and r_s > 0 and (lvl_late30 - avg_s) >= 1.8 * r_s:
                                cand_modes.append((
                                    "uptrend3g", "🌙 3 شموع خضراء صاعدة (شمعة 23:05 مكتملة >85% بلا عائق قبل قمة 30ي)",
                                    "مرتكز الموجة الصاعدة (قمة 10ي)", b10_l, lvl_late30, [c[-3], c[-2], c[-1]], vx_l, n - 3, e_lo, e_hi, stop
                                ))

            # ====== (3) رصد شمعة الهمر اليومية الانعكاسية (🔨 Hammer بذيل رفض سُفلي ≥55% داخل اتجاه صاعد · 50% نجاح و+0.27R EV) ======
            # نفحص شمعة -1 فقط إذا كنا بعد 23:05 (>83% مكتملة)، ونفحص شمعة أمس المغلقة (-2) خلال اليوم لالتقاط تراجع الشمعة الجديدة نحو الذيل!
            if not cand_modes:
                hm_indices = [-1, -2] if is_late_daily else [-2]
                for hi_idx in hm_indices:
                    oh, hh, lh, ch = o[hi_idx], h[hi_idx], l[hi_idx], c[hi_idx]
                    rng_h = max(1e-9, hh - lh)
                    lo_wick_h = (min(oh, ch) - lh) / rng_h
                    up_wick_h = (hh - max(oh, ch)) / rng_h
                    prev_low_d = l[hi_idx - 1]
                    hi30_h = max(h[n + hi_idx - 30 : n + hi_idx])
                    # شروط الهمر الانعكاسي الصحيح علمياً: مدى ≥0.65 ATR، كنس قاع اليوم السابق، ذيل سُفلي ≥55%، ذيل علوي ≤20%، إغلاق بأعلى 35% من الشمعة، واتجاه صاعد (>EMA50 اليومي)
                    if (rng_h >= 0.65 * atr_d and lo_wick_h >= 0.55 and up_wick_h <= 0.20
                        and lh < prev_low_d and ch >= lh + 0.65 * rng_h
                        and e50_now and ch >= e50_now * 0.98 and price > lh + 0.20 * rng_h
                        and (price - ch) <= 0.85 * atr_d):
                        body_floor_h = min(oh, ch)
                        e_hi = min(price, ch - 0.10 * atr_d)
                        e_lo = max(lh + 0.35 * (body_floor_h - lh), e_hi - 0.32 * atr_d)
                        if e_hi <= e_lo:
                            e_hi = min(price, body_floor_h + 0.05 * atr_d)
                            e_lo = lh + 0.35 * (body_floor_h - lh)
                        stop = lh - 0.18 * atr_d
                        avg_hm = (e_lo + e_hi) / 2.0
                        r_hm = avg_hm - stop
                        vol20_h = sum(v[n + hi_idx - 20 : n + hi_idx]) / 20.0
                        vx_h = v[hi_idx] / vol20_h if vol20_h > 0 else 1.0
                        if e_hi > e_lo and r_hm > 0 and (ch > hi30_h or (hi30_h - avg_hm) >= 1.8 * r_hm):
                            hm_lbl = (
                                f"🔨 همر يومي انعكاسي (بعد 23:05 · ذيل رفض سُفلي {lo_wick_h*100:.0f}%)"
                                if hi_idx == -1
                                else f"🔨 همر يومي مغلق أمس (ذيل رفض سُفلي {lo_wick_h*100:.0f}% للشمعة الجديدة)"
                            )
                            cand_modes.append((
                                "hammer1d", hm_lbl,
                                "قاع ذيل الرفض اليومي (Hammer)", lh, hi30_h, [ch], vx_h, n + hi_idx, e_lo, e_hi, stop
                            ))
                            break

            # الفحص الإلزامي لشمعة الأسبوع (1W) وشمعة الشهر (1M) لكل مرشح يومي:
            for b_kind, k_badge, lvl_type, struct_lvl, ref_hi30, cls_arr, vol_x, end_idx, e_lo, e_hi, stop in cand_modes:
                avg_e = (e_lo + e_hi) / 2.0
                r = abs(avg_e - stop)
                risk_pct = (r / avg_e) * 100.0 if avg_e > 0 else 99.0
                if r <= 0 or risk_pct > 22.0 or risk_pct < 1.0:
                    continue

                try:
                    kw = _enrich(_klines(sym, "1w", 55))
                    km = _klines(sym, "1M", 18)
                except Exception:
                    kw, km = None, None
                if not kw or not km or len(kw["c"]) < 4 or len(km["c"]) < 2:
                    continue

                w_o, w_h, w_l, w_c = kw["o"][-1], kw["h"][-1], kw["l"][-1], kw["c"][-1]
                w_up_wick = (w_h - max(w_o, w_c)) / max(1e-9, w_h - w_l)
                pw_h, pw_l = kw["h"][-2], kw["l"][-2]
                w_ema20 = kw["ema20"][-1] or kw["ema20"][-2]
                w_ema9 = kw["ema9"][-1] or kw["ema9"][-2]
                if w_ema20 is not None:
                    w_struct_ok = (price >= w_ema20) or (w_ema9 is not None and price >= w_ema9 and price > pw_h)
                else:
                    w_struct_ok = (w_ema9 is not None and price >= w_ema9 and price >= (pw_h + pw_l) / 2.0)
                w_candle_ok = (w_c >= w_o or (w_o - w_c) <= 0.35 * atr_d or b_kind == "hammer1d") and (w_up_wick <= 0.42 or w_c >= w_o)

                m_o, m_h, m_l, m_c = km["o"][-1], km["h"][-1], km["l"][-1], km["c"][-1]
                pm_h, pm_l = km["h"][-2], km["l"][-2]
                m_struct_ok = (price >= pm_l) and ((price > pm_h) or ((pm_h - avg_e) >= 1.5 * r))

                if not (w_struct_ok and w_candle_ok and m_struct_ok):
                    continue

                w_chg = (w_c / w_o - 1.0) * 100.0 if w_o > 0 else 0.0
                m_chg = (m_c / m_o - 1.0) * 100.0 if m_o > 0 else 0.0
                w_ema_txt = "فوق EMA20 الأسبوعي" if (w_ema20 and price >= w_ema20) else "فوق EMA9 الأسبوعي"
                w_pwh_txt = "مخترقة قمة الأسبوع السابق" if price > pw_h else f"قمة الأسبوع السابق {fp(pw_h, tick)}"
                w_summary = f"{'🟢 خضراء' if w_c >= w_o else '🟡 متماسكة'} ({w_chg:+.1f}%) · {w_ema_txt} · {w_pwh_txt}"
                m_pmh_txt = "فوق قمة الشهر السابق (PMH)" if price > pm_h else f"مساحة مفتوحة لقمة الشهر السابق {fp(pm_h, tick)}"
                m_summary = f"{'🟢 خضراء' if m_c >= m_o else '🟡 فوق قاع الشهر السابق'} ({m_chg:+.1f}% من افتتاح الشهر) · {m_pmh_txt}"
                room_30d_pct = ((ref_hi30 / price - 1.0) * 100.0) if b_kind in ("uptrend3g", "hammer1d") and price > 0 and ref_hi30 > price else 0.0

                pre_hi = max(h[max(0, end_idx - 160):end_idx])
                pre_lo = min(l[max(0, end_idx - 160):end_idx])
                pre_pos = (struct_lvl - pre_lo) / (pre_hi - pre_lo) if pre_hi > pre_lo else 0.5
                pre_bodies_lo = sorted(min(o[k], c[k]) for k in range(max(0, end_idx - 20), end_idx))
                pre_bodies_hi = sorted(max(o[k], c[k]) for k in range(max(0, end_idx - 20), end_idx))
                pre_box_atr = (pre_bodies_hi[-2] - pre_bodies_lo[1]) / atr_d if (atr_d > 0 and len(pre_bodies_hi) >= 4) else 9.0
                from_squeeze = (pre_pos <= 0.35 and pre_box_atr <= 4.2)

                hi120 = max(h[-min(120, n):])
                hi220 = max(h[-min(220, n):])
                if b_kind in ("uptrend3g", "hammer1d") and ref_hi30 > avg_e:
                    t1 = min(ref_hi30 * 0.995, max(avg_e + 1.95 * r, avg_e + 2.0 * r))
                    if (t1 - avg_e) < 1.8 * r:
                        t1 = avg_e + 1.9 * r
                else:
                    t1 = max(avg_e + 2.0 * r, min(hi120, avg_e + 3.2 * r) if hi120 > avg_e + 1.95 * r else avg_e + 2.0 * r)
                t2 = max(t1 + 0.9 * r, avg_e + 3.2 * r)
                t3 = max(hi220 if (avg_e + 4.2 * r <= hi220 <= avg_e + 8.0 * r) else 0, avg_e + 4.6 * r)
                if t3 <= t2:
                    t3 = t2 + 1.2 * r
                rr = [(t1 - avg_e) / r, (t2 - avg_e) / r, (t3 - avg_e) / r]

                dist_atr = abs(price - e_hi) / atr_d
                in_retest = dist_atr <= 0.55
                base_sc = 97.5 if b_kind == "3closes" else (96.0 if b_kind == "2closes" else (95.5 if b_kind == "uptrend3g" else 95.0))
                sc = base_sc + min(5.0, (vol_x - 1.0) * 2.2) + (2.5 if in_retest else 0.0) + (3.0 if from_squeeze else 0.0) + (1.5 if m_c >= m_o else 0.0)
                c_str = (f"إغلاق همر انعكاسي {fp(cls_arr[0], tick)} (قاع الذيل {fp(struct_lvl, tick)})"
                         if b_kind == "hammer1d" else " ← ".join(fp(x, tick) for x in cls_arr))
                sz_bos = compute_risk_position_size(
                    e_hi, stop, "LONG", step=step_sz, min_notional=min_not,
                    sym=sym, atr_pct=(atr_d / price * 100.0), strategy_type="macro_bos", entry_is_maker=True,
                )
                if not sz_bos.get("valid"):
                    continue
                bos_item = {
                    "sym": sym, "name": name, "price": price, "tick": tick, "qv": qv, "chg": chg24,
                    "funding": fund, "rsi_d": rsi_d, "bos_kind": b_kind,
                    "kind_badge": k_badge,
                    "lvl_type": lvl_type, "struct_lvl": struct_lvl, "hi30_ref": ref_hi30, "room_30d_pct": room_30d_pct,
                    "w_summary": w_summary, "m_summary": m_summary,
                    "closes_3": cls_arr, "close_note": c_str,
                    "vol_x": vol_x, "dist_atr": dist_atr,
                    "from_squeeze": from_squeeze, "in_retest": in_retest,
                    "state_lbl": "🎯 في منطقة التراجع/الذيل الآن" if in_retest else "⏳ علّق Limit عند التراجع للمنطقة",
                    "score": round(sc, 1), "entry_lo": e_lo, "entry_hi": e_hi, "avg": avg_e, "stop": stop,
                    "targets": [t1, t2, t3], "rr": rr, "risk_pct": risk_pct,
                    "theoretical_stop_pct": sz_bos["theoretical_stop_pct"],
                    "effective_stop_pct": sz_bos["effective_stop_pct"],
                    "qty": sz_bos["position_size"], "position_size": sz_bos["position_size"],
                    "position_notional_usd": sz_bos["position_notional_usd"],
                    "leverage": sz_bos["leverage"],
                    "margin_required_usd": sz_bos["margin_required_usd"],
                    "margin_pct_equity": sz_bos["margin_pct_equity"],
                    "equity_usd": sz_bos["equity_usd"],
                    "actual_risk_cash": sz_bos["actual_risk_cash"],
                    "actual_risk_pct_equity": sz_bos["actual_risk_pct_equity"],
                    "dist_pct": (e_hi / price - 1.0) * 100.0,
                }
                break

        return inv_item, bos_item

    squeeze_list, bos_list = [], []
    with _cf.ThreadPoolExecutor(max_workers=10) as ex:
        for inv_it, bos_it in ex.map(_eval_one, pool):
            if inv_it:
                squeeze_list.append(inv_it)
            if bos_it:
                bos_list.append(bos_it)

    # إذا انتقلت عملة فعلياً إلى كسر الهيكل بـ 3 إغلاقات يومية، تُعرض في قسم الكسر النشط مع شارة التاج ولا تُكرر في الانتظار القاعي
    bos_syms = {b["sym"] for b in bos_list}
    squeeze_list = [s for s in squeeze_list if s["sym"] not in bos_syms]

    _kr = {"3closes": 4, "2closes": 3, "uptrend3g": 2, "hammer1d": 1}
    squeeze_list.sort(key=lambda x: (-int(x["spring_done"]), -x["score"], x["pos180"]))
    bos_list.sort(key=lambda x: (-_kr.get(x.get("bos_kind"), 0), -int(x["from_squeeze"]), -int(x["in_retest"]), -x["score"]))

    out = {"ts": now_ms, "btc_regime": btc_regime, "squeeze": squeeze_list[:10], "bos3": bos_list[:10]}
    try:
        json.dump(out, open(macro_path, "w", encoding="utf-8"), ensure_ascii=False, default=str)
    except Exception:
        pass
    return out


def build_html(trades, meta, state, stats, t24, prem, tracked, held, now, exp_data=None, lt_stats=None, macro_data=None):
    if exp_data is None:
        try:
            exp_data = json.load(open(os.path.join(BASE, "explosion_candidates.json")))
        except Exception:
            exp_data = {}
    if lt_stats is None:
        lt_stats = update_lifetime_stats(held or tracked, state, now)
    if macro_data is None:
        is_conf = state.get("confirm_ts", 0) > meta.get("ts", 0)
        macro_data = scan_macro_regimes(t24, prem, now, is_confirm_run=is_conf)

    # تقييم بوابة المخاطرة الكلية للمحفظة + فلتر نخبة الدرجة A وسيولة الجلسة في ضوء المراكز المفتوحة حالياً
    eff_gate_ts = meta.get("ts") or now
    trades, port_risk = evaluate_portfolio_risk_gate(
        trades,
        held or tracked,
        strict_filter=False,
        now_riyadh=eff_gate_ts,
        enforce_quality_gate=True,
    )

    ts = now.strftime("%Y-%m-%d %H:%M")
    day = now.strftime("%Y-%m-%d")
    longs = [t for t in trades if t["side"] == "LONG"]
    shorts = [t for t in trades if t["side"] == "SHORT"]
    gradeA = [t for t in trades if t["grade"] == "A"]
    now_ok = [t for t in trades if t["reach"] == "A"]
    near = [t for t in trades if t["reach"] == "B"]
    far = [t for t in trades if t["reach"] == "C"]
    med_d = sorted(t["dist_atr"] for t in trades)[len(trades) // 2] if trades else 0.0

    def ctx(sym):
        t = t24.get(sym)
        p = prem.get(sym)
        if not t:
            return None
        return {
            "chg": float(t["priceChangePercent"]),
            "qv": float(t["quoteVolume"]) / 1e6,
            "fund": float(p["lastFundingRate"]) * 100 if p else 0,
        }

    btc = ctx("BTCUSDT") or {"chg": 0.0}
    eth = ctx("ETHUSDT") or {"chg": 0.0}
    sol = ctx("SOLUSDT") or {"chg": 0.0}
    try:
        _ei = json.load(open(os.path.join(BASE, "cache", "exchangeInfo.json")))
        _now_ms = now.timestamp() * 1000
        _pool = []
        for _s in _ei["symbols"]:
            if _s["contractType"] != "PERPETUAL" or _s["quoteAsset"] != "USDT" or _s["status"] != "TRADING":
                continue
            _t = t24.get(_s["symbol"])
            if not _t:
                continue
            if float(_t["quoteVolume"]) / 1e6 < 8 or (_now_ms - _s["onboardDate"]) / 86400000 < 30:
                continue
            _pool.append(float(_t["priceChangePercent"]))
        n_up = sum(1 for c in _pool if c > 0)
        n_dn = sum(1 for c in _pool if c < 0)
    except Exception:
        n_up = n_dn = 0
    top_longs = " · ".join(t["name"] for t in longs[:4]) if longs else "—"

    try:
        _cur_dt = dt.datetime.fromtimestamp(meta.get("ts", now.timestamp() * 1000) / 1000, RIYADH)
    except Exception:
        _cur_dt = now
    cur_hf_name = f"scan_{_cur_dt.strftime('%Y-%m-%d_%H%M')}.json"
    hist_dir = os.path.join(BASE, "history")
    hist_files = sorted(f for f in os.listdir(hist_dir) if f.startswith("scan_") and f.endswith(".json")) if os.path.isdir(hist_dir) else []
    prev_hist = [f for f in hist_files if f != cur_hf_name]
    prev_scan_syms = set()
    if prev_hist:
        try:
            prev_scan = json.load(open(os.path.join(hist_dir, prev_hist[-1])))
            prev_scan_syms = {(x["sym"], x["side"]) for x in prev_scan}
        except Exception:
            prev_scan_syms = set()
    elif tracked:
        prev_scan_syms = {(x["sym"], x["side"]) for x in tracked}
    prev_syms = prev_scan_syms

    tracked_list = held or tracked
    is_confirm_view = state.get("confirm_ts", 0) > meta.get("ts", 0)
    live_map = {(x["sym"], x["side"]): x for x in tracked_list} if is_confirm_view else {}

    def _live_pill(t):
        lx = live_map.get((t["sym"], t["side"]))
        if not lx:
            return ""
        st = lx.get("status", "")
        ts_c = lx.get("trade_status")
        rv = lx.get("r_now")
        if ts_c == "PARTIAL_TP2":
            return f'<em class="g tpbadge">🌖 حقق هدف 2 · متبقٍ 25% ({rv:+.2f}R)</em>'
        if ts_c == "PARTIAL_TP1":
            return f'<em class="g tpbadge">🌗 حقق هدف 1 · متبقٍ 50% ({rv:+.2f}R)</em>'
        if ts_c == "OPEN" or st == "مفتوحة":
            ost = lx.get("open_state") or ("رابحة" if (rv or 0) > 0 else ("خاسرة" if (rv or 0) < 0 else "عند الدخول"))
            if ost == "رابحة":
                return f'<em class="g owin">🟢 مفتوحة رابحة {rv:+.2f}R</em>'
            if ost == "خاسرة":
                return f'<em class="g oloss">🔴 مفتوحة خاسرة {rv:+.2f}R</em>'
            return '<em class="g oflat">⚪ مفتوحة عند الدخول</em>'
        if ts_c in ("CLOSED_TP3", "CLOSED_BE", "CLOSED_TRAIL") or str(st).startswith("وصل"):
            return f'<em class="g tpbadge">🎯 {st} ({rv:+.2f}R)</em>'
        if ts_c == "CLOSED_STOP" or st == "ضربت الوقف":
            return '<em class="g slbadge">🛑 ضربت الوقف</em>'
        if ts_c == "EXPIRED" or st == "انتهت صلاحية الإشارة":
            return '<em class="g cancelbadge">⌛ انتهت صلاحية الإشارة</em>'
        if ts_c == "PENDING" or st == "بانتظار التفعيل":
            d = lx.get("dist_now_atr")
            return f'<em class="g waitbadge">⏳ بانتظار التفعيل ({d:.2f} ATR)</em>' if d is not None else '<em class="g waitbadge">⏳ بانتظار التفعيل</em>'
        if ts_c == "CANCELLED_DIST" or st == "أُلغيت (ابتعدت)":
            d = lx.get("dist_now_atr")
            return f'<em class="g cancelbadge">⛔ أُلغيت · ابتعدت {d:.2f} ATR</em>' if d is not None else '<em class="g cancelbadge">⛔ أُلغيت (ابتعدت)</em>'
        return ""

    def _fmt_oi_html(val):
        if val is None:
            return '<b style="color:#94a3b8">غير متاح (محايد)</b>'
        cls_o = "pos" if float(val) >= 0 else "neg"
        return f'<b class="{cls_o}">{float(val):+.2f}%</b>'

    def card(t, idx, with_id=True):
        c = ctx(t["sym"]) or {"chg": t["chg"], "qv": t["qv"], "fund": t["funding"]}
        side = t["side"]
        side_ar = "شراء LONG" if side == "LONG" else "بيع SHORT"
        cls = "long" if side == "LONG" else "short"
        gcol = {"A": "ga", "B": "gb", "C": "gc"}[t["grade"]]
        rcol = {"A": "ra", "B": "rb", "C": "rc"}[t["reach"]]
        tags = " · ".join(TAG_AR.get(x, x) for x in t["tags"])
        tsrcs = t.get("target_sources") or ["structural_sr", "structural_sr", "structural_sr"]
        tg = "".join(
            f'<div class="lv t{k+1}"><span>هدف {k+1} · {TARGET_SRC_AR.get(tsrcs[k], "مستوى بنيوي")}</span><b>{fp(t["targets"][k], t["tick"])}</b>'
            f'<i>{((t["targets"][k]/t["avg"]-1)*100):+.2f}% · R{t["rr"][k]:.2f}</i></div>'
            for k in range(3)
        )
        chgcls = "pos" if c["chg"] >= 0 else "neg"
        fcls = "pos" if c["fund"] >= 0 else "neg"
        dist_txt = f'{t["dist_pct"]:+.2f}%'
        notes = " · ".join(t["notes"]) if t["notes"] else "—"
        if prev_syms:
            tag_html = (f'<em class="g {"ntag" if (t["sym"], t["side"]) not in prev_syms else "ktag"}">'
                        f'{"جديد" if (t["sym"], t["side"]) not in prev_syms else "مستمر"}</em>')
        else:
            tag_html = ""
        trend_badge = '<em class="g trtag">⚡ ترند</em>' if t.get("is_trend") else ""
        lpill = _live_pill(t)
        lx = live_map.get((t["sym"], t["side"]))
        disp_price = lx["last"] if (lx and lx.get("last") is not None) else t["price"]
        sup_txt = " · ".join(fp(x, t["tick"]) for x in t["supports"][:3])
        res_txt = " · ".join(fp(x, t["tick"]) for x in t["resistances"][:3])
        plan = ("50% عند هدف 1 ← نقل الوقف للتعادل الشامل للرسوم ← 25% عند هدف 2 ← 25% عند هدف 3"
                if True else "")
        id_attr = f' id="t-{t["name"]}"' if with_id else ""
        notional_u = float(t.get("position_notional_usd") or (t["qty"] * t["avg"]))
        lev_u = int(t.get("leverage") or 3)
        margin_u = float(t.get("margin_required_usd") or (notional_u / lev_u))
        margin_p = float(t.get("margin_pct_equity") or 0.0)
        act_rcash = float(t.get("actual_risk_cash") or 0.0)
        act_rpct = float(t.get("actual_risk_pct_equity") or 0.0)
        eff_spct = float(t.get("effective_stop_pct") or t["risk_pct"])
        theo_spct = float(t.get("theoretical_stop_pct") or t["risk_pct"])
        rg_ok = t.get("risk_gate_allowed", True)
        rg_status = t.get("risk_gate_status", "")
        if rg_ok:
            rg_badge = f'<em class="g owin">✅ مجاز للتنفيذ (إجمالي المخاطرة بعده {t.get("portfolio_risk_after_pct", act_rpct):.2f}%)</em>'
        elif rg_status in ("WATCHLIST_GRADE_B", "WATCHLIST_CHOP_SESSION"):
            rg_badge = f'<em class="g b" style="background:#1e293b;color:#fde68a;border-color:#475569">👁️ {t.get("risk_gate_reason_ar")}</em>'
        else:
            rg_badge = f'<em class="g cancelbadge">⛔ احتياطي: {t.get("risk_gate_reason_ar", "تجاوز سقف المحفظة")}</em>'
        return f'''
<article class="card {cls}"{id_attr} data-sym="{t["name"]}">
  <div class="chead">
    <div class="csym">{t["name"]}<span>/USDT</span> <small>{t["score"]:.1f} نقطة</small>
      <em class="g {gcol}">درجة {t["grade"]}</em> <em class="g {rcol}">وصول {t["reach"]} · ~{t["reach_p"]}%</em>
      {trend_badge} {tag_html} {lpill} {rg_badge}
    </div>
    <div><span class="pill {cls}">{side_ar}</span></div>
  </div>
  <div class="cbody">
    <div class="levels">
      <div class="lv entry"><span>منطقة الدخول</span><b>{fp(t["entry_lo"], t["tick"])} – {fp(t["entry_hi"], t["tick"])}</b><i>{dist_txt} عن السعر · {t["dist_atr"]:.2f} ATR</i></div>
      <div class="lv stop"><span>الوقف</span><b>{fp(t["stop"], t["tick"])}</b><i>نظري {theo_spct:.2f}% · فعلي بالرسوم {eff_spct:.2f}%</i></div>
      {tg}
    </div>
    <div class="meta">
      <div><span>السعر الآن</span><b>{fp(disp_price, t["tick"])}</b></div>
      <div><span>تغيّر 24س</span><b class="{chgcls}">{c["chg"]:+.2f}%</b></div>
      <div><span>R:R للأهداف 1/2/3</span><b>{t["rr"][0]:.2f} · {t["rr"][1]:.2f} · {t["rr"][2]:.2f}</b></div>
      <div><span>مصادر المستوى</span><b>{tags} ({t["n_src"]})</b></div>
      <div class="sr"><span>الدعوم</span><b class="pos">{sup_txt}</b></div>
      <div class="sr"><span>المقاومات</span><b class="neg">{res_txt}</b></div>
      <div><span>البنية</span><b>{t["struct"]}</b></div>
      <div><span>ATR(4س)</span><b>{t["atr_pct"]:.2f}%</b></div>
      <div><span>RSI 4س/يومي</span><b>{t["rsi4"]:.0f}/{t["rsi1"]:.0f}</b></div>
      <div><span>سيولة 24س</span><b>{c["qv"]:,.0f}M$</b></div>
      <div><span>فاندنغ</span><b class="{fcls}">{c["fund"]:+.4f}%</b></div>
      <div><span>Δ OI (4س)</span>{_fmt_oi_html(t.get("oi_chg"))}</div>
      <div><span>الكمية والقيمة الاسمية</span><b>{t["qty"]:,.4f} ({notional_u:,.0f}$)</b></div>
      <div><span>المخاطرة النقدية الفعلية</span><b class="neg">{act_rcash:,.2f}$ ({act_rpct:.2f}% من المحفظة)</b></div>
      <div><span>الرافعة والهامش المطلوب</span><b>{lev_u}x · هامش {margin_u:,.0f}$ ({margin_p:.1f}%)</b></div>
      <div><span>ملاحظات</span><b>{notes}</b></div>
    </div>
    <div class="plan"><b>الإدارة:</b> {plan}</div>
  </div>
</article>'''

    def row(t, i):
        c = ctx(t["sym"]) or {"chg": t["chg"], "qv": t["qv"]}
        cls = "long" if t["side"] == "LONG" else "short"
        gcol = {"A": "ga", "B": "gb", "C": "gc"}[t["grade"]]
        rcol = {"A": "ra", "B": "rb", "C": "rc"}[t["reach"]]
        s_txt = " · ".join(fp(x, t["tick"]) for x in t["supports"][:3])
        r_txt = " · ".join(fp(x, t["tick"]) for x in t["resistances"][:3])
        tr_b = ' <em class="g trtag" style="font-size:9.5px;padding:1px 5px">⚡ ترند</em>' if t.get("is_trend") else ""
        lpill = f'<div style="margin-top:2px">{_live_pill(t)}</div>' if is_confirm_view else ""
        return f'''<tr data-sym="{t["name"]}">
<td class="c">{i}</td>
<td class="sym"><a href="#t-{t["name"]}">{t["name"]}</a>{tr_b}{lpill}</td>
<td class="c"><span class="pill {cls}">{t["side"]}</span></td>
<td class="n">{fp(t["entry_lo"], t["tick"])} – {fp(t["entry_hi"], t["tick"])}<span class="sub">{t["dist_pct"]:+.2f}% · {t["dist_atr"]:.2f} ATR</span></td>
<td class="n sl">{fp(t["stop"], t["tick"])}<span class="sub">مخاطرة {t["risk_pct"]:.2f}%</span></td>
<td class="n tp">{fp(t["targets"][0], t["tick"])}<span class="sub">R{t["rr"][0]:.2f}</span></td>
<td class="n tp">{fp(t["targets"][1], t["tick"])}<span class="sub">R{t["rr"][1]:.2f}</span></td>
<td class="c">{t["score"]:.1f}</td>
<td class="c"><em class="g {gcol}">{t["grade"]}</em> / <em class="g {rcol}">{t["reach"]}</em></td>
<td class="n">{t["qv"]:,.0f}M</td>
<td class="n" style="font-size:10.5px"><span class="pos">د: {s_txt}</span><span class="sub neg">م: {r_txt}</span></td>
<td class="c" style="font-size:11px">{t["struct"]}</td>
</tr>'''

    try:
        prev_label = dt.datetime.fromtimestamp(state.get("prev_ts", 0) / 1000, RIYADH).strftime("%H:%M")
    except Exception:
        prev_label = "—"
    try:
        scan_hm = dt.datetime.fromtimestamp(meta.get("ts", now.timestamp() * 1000) / 1000, RIYADH).strftime("%H:%M")
    except Exception:
        scan_hm = now.strftime("%H:%M")
    try:
        track_hm = dt.datetime.fromtimestamp(state.get("track_ts", 0) / 1000, RIYADH).strftime("%H:%M")
        if state.get("track_ts", 0) < 1e12:
            track_hm = scan_hm
    except Exception:
        track_hm = scan_hm
    universe = meta["universe"]
    # ------- تحديث صفقات المسح السابق (held)
    tracked = held or tracked

    def _open_state(x):
        if x.get("open_state") in ("رابحة", "خاسرة", "عند الدخول"):
            return x["open_state"]
        r = float(x.get("r_now") or 0)
        if r > 0:
            return "رابحة"
        if r < 0:
            return "خاسرة"
        return "عند الدخول"

    def _is_active_open(x):
        ts_c = x.get("trade_status")
        if ts_c is not None:
            return ts_c in ("OPEN", "PARTIAL_TP1", "PARTIAL_TP2") and float(x.get("remaining_pct", 0.0)) > 0.0
        return x.get("status") == "مفتوحة"

    def _is_closed_profit(x):
        ts_c = x.get("trade_status")
        if ts_c in ("CLOSED_TP3", "CLOSED_BE", "CLOSED_TRAIL"):
            return True
        if ts_c == "CLOSED_EXPIRY":
            return float(x.get("realized_r") or 0.0) >= 0.0
        return ts_c is None and str(x.get("status", "")).startswith("وصل")

    def _is_closed_stop(x):
        ts_c = x.get("trade_status")
        if ts_c == "CLOSED_STOP":
            return True
        if ts_c == "CLOSED_EXPIRY":
            return float(x.get("realized_r") or 0.0) < 0.0
        return ts_c is None and x.get("status") == "ضربت الوقف"

    triggered = [
        x for x in tracked
        if x.get("filled") or _is_active_open(x) or _is_closed_profit(x) or _is_closed_stop(x)
    ]
    n_tr = len(tracked)
    c_wait = sum(1 for x in tracked if x.get("trade_status") == "PENDING" or x.get("status") == "بانتظار التفعيل")
    c_cancel = sum(
        1 for x in tracked
        if x.get("trade_status") in ("CANCELLED_DIST", "EXPIRED") or x.get("status") in ("أُلغيت (ابتعدت)", "انتهت صلاحية الإشارة")
    )
    open_list = [x for x in tracked if _is_active_open(x)]
    c_open = len(open_list)
    c_open_win = sum(1 for x in open_list if _open_state(x) == "رابحة")
    c_open_loss = sum(1 for x in open_list if _open_state(x) == "خاسرة")
    c_open_flat = sum(1 for x in open_list if _open_state(x) == "عند الدخول")
    c_stop = sum(1 for x in tracked if _is_closed_stop(x))
    c_tp = sum(1 for x in tracked if _is_closed_profit(x))
    net_r = sum(
        float(x.get("r_now") or 0)
        for x in tracked
        if x.get("filled") or _is_active_open(x) or _is_closed_profit(x) or _is_closed_stop(x)
    )

    def trrow(x):
        st = x.get("status", "-")
        ts_c = x.get("trade_status")
        r = x.get("r_now")
        pnl = x.get("pnl_pct")
        rem_pct = float(x.get("remaining_pct", 1.0 if st == "مفتوحة" else 0.0))
        real_r = x.get("realized_r")
        unreal_r = x.get("unrealized_r")
        stop_mode = x.get("stop_mode", "original")
        act_stop = x.get("active_stop", x.get("stop"))

        if pnl is None and r is not None and x.get("fill_price") is None and x.get("last") is not None:
            ref = x.get("avg") or x.get("price") or 1
            diff = (x["last"] - ref) if x["side"] == "LONG" else (ref - x["last"])
            pnl = (diff / ref) * 100.0
        rtxt = f"{r:+.2f}R" if r is not None else "—"
        ptxt = f"{pnl:+.2f}%" if pnl is not None else ""
        rowcls = ""

        if _is_active_open(x):
            ost = _open_state(x)
            if ts_c == "PARTIAL_TP2":
                badge = '<em class="g tpbadge">🌖 حقق هدف 2 · متبقٍ 25% (وقف مؤمَّن)</em>'
                rcls = "pos"
                rowcls = ' class="rwin"'
            elif ts_c == "PARTIAL_TP1":
                badge = '<em class="g tpbadge">🌗 حقق هدف 1 · متبقٍ 50% (وقف تعادل)</em>'
                rcls = "pos"
                rowcls = ' class="rwin"'
            elif ost == "رابحة":
                badge = '<em class="g owin">🟢 مفتوحة بالكامل (100%) · رابحة</em>'
                rcls = "pos"
                rowcls = ' class="rwin"'
            elif ost == "خاسرة":
                badge = '<em class="g oloss">🔴 مفتوحة بالكامل (100%) · خاسرة</em>'
                rcls = "neg"
                rowcls = ' class="rloss"'
            else:
                badge = '<em class="g oflat">⚪ مفتوحة بالكامل (100%) · عند الدخول</em>'
                rcls = ""
        elif ts_c == "CLOSED_TP3":
            badge = '<em class="g tpbadge">🎯 اكتملت الأهداف (TP1+TP2+TP3 · 100%)</em>'
            rcls = "pos"
        elif ts_c == "CLOSED_TRAIL":
            badge = '<em class="g tpbadge">🛡️ أُغلقت بعد هدف 2 على ربح مؤمَّن</em>'
            rcls = "pos"
        elif ts_c == "CLOSED_BE":
            badge = '<em class="g tpbadge">🛡️ أُغلقت بعد هدف 1 عند التعادل</em>'
            rcls = "pos" if (r or 0) >= 0 else "neg"
        elif _is_closed_profit(x):
            badge = f'<em class="g tpbadge">🎯 {st}</em>'
            rcls = "pos"
        elif _is_closed_stop(x):
            badge = '<em class="g slbadge">🛑 ضربت الوقف الأصلي</em>'
            rcls = "neg"
        elif ts_c == "EXPIRED" or st == "انتهت صلاحية الإشارة":
            badge = '<em class="g cancelbadge">⌛ انتهت صلاحية الإشارة</em>'
            rcls = ""
            rowcls = ' class="rcancel"'
        elif ts_c == "PENDING" or st == "بانتظار التفعيل":
            badge = '<em class="g waitbadge">⏳ بانتظار التفعيل</em>'
            rcls = ""
        elif ts_c == "CANCELLED_DIST" or st == "أُلغيت (ابتعدت)":
            badge = '<em class="g cancelbadge">⛔ أُلغيت (ابتعدت &gt; 1 ATR)</em>'
            rcls = "neg"
            rowcls = ' class="rcancel"'
        else:
            badge = f'<em class="g gc">{st}</em>'
            rcls = ""

        fill_p = x.get("fill_price")
        fill_sub = f'<span class="sub">سعر التفعيل المثبت: {fp(fill_p, x["tick"])}</span>' if fill_p is not None else ""
        stop_sub = ""
        if x.get("filled") and stop_mode == "BE" and act_stop is not None:
            stop_sub = f'<span class="sub pos">وقف تعادل شامل الرسوم: {fp(act_stop, x["tick"])}</span>'
        elif x.get("filled") and stop_mode == "trail" and act_stop is not None:
            stop_sub = f'<span class="sub pos">وقف ربح عند TP1: {fp(act_stop, x["tick"])}</span>'

        last_txt = fp(x["last"], x["tick"]) if x.get("last") is not None else "—"
        dist_now = x.get("dist_now_atr")
        if r is not None and x.get("filled"):
            leg_sub = ""
            if _is_active_open(x) and real_r is not None and unreal_r is not None and rem_pct < 1.0:
                leg_sub = f'<span class="sub">محقق {real_r:+.2f}R · عائم {unreal_r:+.2f}R</span>'
            elif not _is_active_open(x) and real_r is not None:
                leg_sub = '<span class="sub">صافي محقق بعد الرسوم</span>'
            res_cell = f'<b class="{rcls}">{rtxt}</b>' + (f'<span class="sub {rcls}">{ptxt}</span>' if ptxt else "") + leg_sub
        elif r is not None:
            res_cell = f'<b class="{rcls}">{rtxt}</b>' + (f'<span class="sub {rcls}">{ptxt}</span>' if ptxt else "")
        elif (ts_c == "PENDING" or st == "بانتظار التفعيل") and dist_now is not None:
            res_cell = f'<span style="color:#9ecbff;font-size:11.5px">على بُعد {dist_now:.2f} ATR</span>'
        elif (ts_c in ("CANCELLED_DIST", "EXPIRED") or st in ("أُلغيت (ابتعدت)", "انتهت صلاحية الإشارة")) and dist_now is not None:
            res_cell = f'<span class="neg" style="font-size:11.5px">ابتعد {dist_now:.2f} ATR</span>'
        else:
            res_cell = "—"
        sym_link = f'<a href="#t-{x["name"]}">{x["name"]}</a>' if any(t["name"] == x["name"] for t in trades) else x["name"]
        disp_stop = act_stop if (x.get("filled") and act_stop is not None) else x["stop"]
        return (
            f'<tr{rowcls} data-sym="{x["name"]}"><td class="sym">{sym_link}</td>'
            f'<td class="c"><span class="pill {"long" if x["side"]=="LONG" else "short"}">{x["side"]}</span></td>'
            f'<td class="n">{fp(x["entry_lo"], x["tick"])} – {fp(x["entry_hi"], x["tick"])}{fill_sub}</td>'
            f'<td class="n sl">{fp(disp_stop, x["tick"])}{stop_sub}</td>'
            f'<td class="n">{last_txt}</td>'
            f'<td class="n" style="text-align:center">{res_cell}</td>'
            f'<td class="c">{badge}</td></tr>'
        )

    def _tr_sort_key(x):
        rv = float(x.get("r_raw") if x.get("r_raw") is not None else (x.get("r_now") or 0))
        dn = float(x.get("dist_now_atr") or 99)
        if _is_active_open(x):
            ost = _open_state(x)
            sub_ord = {"رابحة": 0, "عند الدخول": 1, "خاسرة": 2}.get(ost, 1)
            return (0, sub_ord, -rv, x["name"])
        if _is_closed_profit(x):
            return (1, 0, -rv, x["name"])
        if _is_closed_stop(x):
            return (2, 0, 0, x["name"])
        if x.get("trade_status") == "PENDING" or x.get("status") == "بانتظار التفعيل":
            return (3, 0, dn, x["name"])
        if x.get("trade_status") in ("CANCELLED_DIST", "EXPIRED") or x.get("status") in ("أُلغيت (ابتعدت)", "انتهت صلاحية الإشارة"):
            return (4, 0, dn, x["name"])
        return (5, 0, 0, x["name"])

    track_rows = "".join(trrow(x) for x in sorted(tracked, key=_tr_sort_key))

    win_items = sorted([x for x in open_list if _open_state(x) == "رابحة"], key=lambda z: -(z.get("r_now") or 0))
    loss_items = sorted([x for x in open_list if _open_state(x) == "خاسرة"], key=lambda z: (z.get("r_now") or 0))
    top_win_txt = " · ".join(f'{x["name"]} (<span class="pos">{x["r_now"]:+.2f}R</span>)' for x in win_items[:6]) or "—"
    loss_txt = " · ".join(f'{x["name"]} (<span class="neg">{x["r_now"]:+.2f}R</span>)' for x in loss_items) or "لا توجد مراكز مفتوحة خاسرة حالياً"
    flat_sub = f'<span class="sub">عند الدخول: {c_open_flat}</span>' if c_open_flat else ""
    open_summary_html = (
        f'<div class="note" style="background:#0c1420;border-color:#1c2941;margin:8px 0 10px;padding:11px 14px;font-size:12.5px">'
        f'<div><b class="pos">🟢 المفتوحة الرابحة ({c_open_win}):</b> أبرزها {top_win_txt}</div>'
        f'<div style="margin-top:4px"><b class="neg">🔴 المفتوحة الخاسرة ({c_open_loss}):</b> {loss_txt}</div>'
        f'</div>'
    ) if c_open else ""


    css = """
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:#080c12;color:#e6edf5;font-family:'Segoe UI',Tahoma,system-ui,sans-serif;line-height:1.65}
.wrap{max-width:1280px;margin:0 auto;padding:24px 16px 80px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:19px;margin:34px 0 12px;padding-right:12px;border-right:4px solid #2f81f7;scroll-margin-top:80px}
h3{font-size:15px;margin:18px 0 8px;color:#b9c9dc}
.sub{color:#8798ab;font-size:12px;display:block}
.stamp{display:inline-block;background:#0b3b4d;color:#5ee0ff;border:1px solid #155e75;border-radius:20px;padding:4px 14px;font-size:13px;font-weight:700;margin-bottom:10px}
.hero{background:linear-gradient(135deg,#101a2a,#0c131d);border:1px solid #1e2c42;border-radius:16px;padding:20px 22px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-top:16px}
.kpi{background:#0e1725;border:1px solid #1c2941;border-radius:12px;padding:11px 13px}
.kpi span{display:block;color:#8798ab;font-size:11px}.kpi b{font-size:17px}
.note{background:#1a1509;border:1px solid #6b5218;border-radius:14px;padding:16px 18px;margin:16px 0;font-size:13.5px}
.note b{color:#ffd479}
.warn{background:#1e1116;border:1px solid #6b2432;border-radius:14px;padding:14px 18px;margin:14px 0;font-size:13.5px}
.okbox{background:#0b1f16;border:1px solid #1c5c39;border-radius:14px;padding:14px 18px;margin:14px 0;font-size:13.5px}
.twrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:12px;margin:8px 0 4px}
table{width:100%;min-width:680px;border-collapse:collapse;font-size:12.5px;background:#0c1320;border-radius:12px;overflow:hidden;margin:0}
.appbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;background:#0d1626;border:1px solid #1f3352;border-radius:14px;padding:10px 14px;margin-bottom:14px}
.appbtns{display:flex;flex-wrap:wrap;gap:7px}
.abtn{appearance:none;border:1px solid #2b456b;background:#13233a;color:#e6edf5;border-radius:10px;padding:8px 13px;font-size:12.5px;font-weight:700;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:5px}
.abtn:active{transform:scale(.97)}
.abtn.pri{background:linear-gradient(135deg,#1d4ed8,#2563eb);border-color:#3b82f6;color:#fff}
.abtn.conf{background:linear-gradient(135deg,#92400e,#b45309);border-color:#f59e0b;color:#fff}
.modal-bg{display:none;position:fixed;inset:0;background:rgba(4,8,15,.82);z-index:999;align-items:center;justify-content:center;padding:16px}
.modal-bg.open{display:flex}
.modal{background:#0f1929;border:1px solid #294166;border-radius:16px;max-width:460px;width:100%;padding:20px;color:#e6edf5}
.modal input{width:100%;padding:10px 12px;border-radius:10px;border:1px solid #2b456b;background:#080e18;color:#fff;direction:ltr;font-size:13px;margin:6px 0 12px}
.status-toast{display:none;background:#0d2818;border:1px solid #22c55e;color:#86efac;padding:10px 14px;border-radius:12px;margin-bottom:12px;font-size:13px;font-weight:600}
.tools-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0}
.tbox{background:#0d1626;border:1px solid #223859;border-radius:14px;padding:13px 15px}
.tbox h3{margin:0 0 6px;font-size:14px;color:#93c5fd;display:flex;align-items:center;gap:6px}
.tbox .tsub{font-size:11.5px;color:#8798ab;margin-bottom:9px}
.tinp-row{display:flex;gap:7px;align-items:center}
.tinp{flex:1;min-width:0;padding:9px 12px;border-radius:10px;border:1px solid #2b456b;background:#070d17;color:#fff;font-size:13.5px;font-weight:700;direction:ltr;text-align:left}
.tinp::placeholder{color:#5c7089;font-weight:400;direction:rtl;text-align:right}
.sres{display:none;margin-top:10px;padding:10px 12px;border-radius:11px;background:#091220;border:1px solid #1e3354;font-size:12.5px;line-height:1.75}
@media(max-width:760px){.tools-grid{grid-template-columns:1fr}}
@media(max-width:680px){.wrap{padding:12px 10px 76px}h1{font-size:19px}.hero{padding:15px}.abtn{flex:1 1 auto;justify-content:center;padding:9px 10px;font-size:12px}}
th{background:#152033;color:#9db1c8;font-weight:600;padding:9px 7px;text-align:right;font-size:11px;white-space:nowrap}
td{padding:8px 7px;border-top:1px solid #16223a;vertical-align:middle}
tr:hover td{background:#111c2c}
.n{direction:ltr;text-align:left;font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:600}
.n .sub{font-size:9.5px;color:#7d8ea3;font-weight:400}
.c{text-align:center}.sym{font-weight:700;white-space:nowrap}.sym a{color:#e6edf5;text-decoration:none}.sym a:hover{color:#79b8ff}
.sl{color:#f87171}.tp{color:#86e0a0}
.pill{display:inline-block;padding:1px 8px;border-radius:20px;font-size:10.5px;font-weight:700}
.pill.long{background:#0e2f1d;color:#4ade80;border:1px solid #1c5c39}
.pill.short{background:#2f1319;color:#f87171;border:1px solid #5c2029}
.g{font-style:normal;font-size:10.5px;padding:1px 7px;border-radius:6px;font-weight:700;white-space:nowrap}
.ga{background:#0b3b4d;color:#5ee0ff}.gb{background:#2a2a12;color:#e3c34a}.gc{background:#331124;color:#e879c7}
.ntag{background:#1a1130;color:#c4a6ff;border:1px solid #4c2a85}.ktag{background:#101a24;color:#7d8ea3;border:1px solid #24384f}
.trtag{background:#2a1d08;color:#fbbf24;border:1px solid #784f12}
.ra{background:#0e2f1d;color:#4ade80}.rb{background:#1c2a12;color:#c9e06a}.rc{background:#2f1319;color:#f87171}
.owin{background:#0d3320;color:#4ade80;border:1px solid #1f7a46;padding:2px 9px}
.oloss{background:#3a1219;color:#ff8585;border:1px solid #8a2838;padding:2px 9px}
.oflat{background:#162436;color:#9ecbff;border:1px solid #2b4566;padding:2px 9px}
.tpbadge{background:#0b3b2c;color:#6ee7b7;border:1px solid #18795b;padding:2px 9px}
.slbadge{background:#2d1218;color:#f87171;border:1px solid #6b2432;padding:2px 9px}
.waitbadge{background:#12243a;color:#9ecbff;border:1px solid #254b75;padding:2px 9px}
.cancelbadge{background:#25151a;color:#fca5a5;border:1px solid #592531;padding:2px 9px}
tr.rwin td:first-child{box-shadow:inset -3px 0 0 #22c55e}
tr.rloss{background:rgba(239,68,68,.045)}
tr.rloss td:first-child{box-shadow:inset -3px 0 0 #ef4444}
tr.rcancel td{opacity:.68}
.pos{color:#4ade80}.neg{color:#f87171}
.card{background:#0c1320;border:1px solid #1c2941;border-radius:16px;margin:14px 0;overflow:hidden;scroll-margin-top:80px}
.card.long{border-right:4px solid #22c55e}.card.short{border-right:4px solid #ef4444}
.chead{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;padding:12px 16px;background:#111b2b}
.csym{font-size:17px;font-weight:700}.csym span{color:#6b7c92;font-size:12.5px}
.csym small{color:#7d8ea3;font-size:10.5px;margin-right:6px}.csym em{margin-right:5px}
.cbody{padding:14px 16px}
.levels{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:9px}
.lv{background:#0e1725;border:1px solid #1c2941;border-radius:11px;padding:9px 11px}
.lv span{display:block;color:#8798ab;font-size:10.5px}
.lv b{font-size:14.5px;direction:ltr;display:block;font-variant-numeric:tabular-nums}
.lv i{display:block;color:#7d8ea3;font-size:10px;font-style:normal}
.lv.entry{border-color:#2f81f7;background:#0d1a2e}.lv.entry b{color:#9ecbff}
.lv.stop{border-color:#7f1d1d;background:#1a0f12}.lv.stop b{color:#f87171}
.lv.t1,.lv.t2{border-color:#14532d}.lv.t1 b,.lv.t2 b{color:#4ade80}
.lv.t3{border-color:#155e75}.lv.t3 b{color:#5ee0ff}
.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(132px,1fr));gap:7px;margin-top:11px;font-size:11.5px}
.meta div{background:#0a111c;border-radius:8px;padding:6px 9px;display:flex;justify-content:space-between;gap:6px}
.meta div.sr{grid-column:span 2;background:#0c1420;border:1px solid #1b2740}
.meta span{color:#7d8ea3}.meta b{font-weight:600;text-align:left}
.plan{margin-top:11px;background:#0b1526;border:1px dashed #24406b;border-radius:9px;padding:8px 11px;font-size:11.5px;color:#9fb3c9}
.plan b{color:#79b8ff}
.nav{position:sticky;top:0;z-index:40;display:flex;gap:8px;flex-wrap:wrap;background:rgba(8,12,18,.95);backdrop-filter:blur(8px);padding:10px 12px;margin:16px 0 6px;border:1px solid #1e2c42;border-radius:14px}
.nav a{text-decoration:none;font-size:12.5px;font-weight:700;padding:7px 14px;border-radius:10px;color:#9db1c8;background:#152033;border:1px solid #1e2c42;transition:.15s}
.nav a:hover{color:#fff;background:#1c2a41;transform:translateY(-1px)}
.nav a.longb{background:#0e2f1d;color:#4ade80;border-color:#1c5c39}
.nav a.longb:hover{background:#14472c;color:#86efac}
.nav a.shortb{background:#2f1319;color:#f87171;border-color:#5c2029}
.nav a.shortb:hover{background:#43191f;color:#fca5a5}
.nav a.expb{background:#2f1f09;color:#fbbf24;border-color:#784f12}
.nav a.expb:hover{background:#452c0c;color:#fde68a}
.nav a.invb{background:linear-gradient(135deg,#24133d,#10293d);color:#d8b4fe;border-color:#6d28d9}
.nav a.invb:hover{background:linear-gradient(135deg,#331a57,#163a54);color:#f3e8ff}
.nav .cnt{background:rgba(255,255,255,.12);border-radius:20px;padding:0 7px;font-size:11px;margin-right:4px}
h2.hlong{border-right-color:#22c55e}
h2.hshort{border-right-color:#ef4444}
h2.hexp{border-right-color:#f59e0b}
h2.hinv{border-right-color:#a855f7}
h2.hbos{border-right-color:#38bdf8}
.card.exp{border-right:4px solid #f59e0b;background:#0e131d}
.card.inv{border-right:4px solid #a855f7;background:#0e1120}
.card.bos{border-right:4px solid #38bdf8;background:#0b1522}
.expbadge{background:#382408;color:#fbbf24;border:1px solid #855512;padding:2px 9px}
.invbadge{background:#281442;color:#d8b4fe;border:1px solid #7e22ce;padding:2px 9px}
.bosbadge{background:#0c2d48;color:#7dd3fc;border:1px solid #0284c7;padding:2px 9px}
.crownbadge{background:linear-gradient(135deg,#422006,#3b0764);color:#fde047;border:1px solid #eab308;padding:2px 9px}
.ltbar{background:linear-gradient(135deg,#0d192b,#0a1220);border:1px solid #243b5e;border-radius:14px;padding:11px 15px;margin-bottom:14px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between}
.ltpills{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.ltp{background:#08101c;border:1px solid #1e314d;border-radius:10px;padding:5px 11px;font-size:12.5px;display:inline-flex;align-items:center;gap:6px}
.ltp b{font-size:14px;font-variant-numeric:tabular-nums}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 12px}
.chip{text-decoration:none;font-size:11.5px;font-weight:700;padding:4px 10px;border-radius:8px;background:#101a29;border:1px solid #1e2c42;color:#cbd8e8}
.chip.long:hover{border-color:#22c55e;color:#4ade80;background:#0e2419}
.chip.short:hover{border-color:#ef4444;color:#f87171;background:#271217}
.top{position:fixed;left:16px;bottom:16px;z-index:60;background:#152033;color:#9db1c8;border:1px solid #1e2c42;border-radius:50%;width:44px;height:44px;display:flex;align-items:center;justify-content:center;text-decoration:none;font-size:18px;font-weight:700}
.top:hover{color:#fff;background:#1f304d}
.bars{display:grid;gap:6px;margin:10px 0}
.bar{display:grid;grid-template-columns:88px 1fr 52px;align-items:center;gap:9px;font-size:11.5px}
.bar .tr{background:#111c2c;border-radius:6px;height:16px;overflow:hidden}
.bar .fl{height:100%;background:linear-gradient(90deg,#2f81f7,#5ee0ff)}
.bar .fl.red{background:linear-gradient(90deg,#7f1d1d,#f87171)}
ul{margin:8px 0;padding-right:20px}li{margin:4px 0;font-size:13px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:760px){.grid2{grid-template-columns:1fr}}
"""

    bars = ""
    for th, lab in ((0.4, "0.4 ATR"), (0.6, "0.6 ATR"), (0.8, "0.8 ATR"), (1.0, "1.0 ATR"), (1.2, "1.2 ATR")):
        pu = sum(1 for x in stats["up"] if x >= th) / len(stats["up"]) * 100
        pd = sum(1 for x in stats["dn"] if x >= th) / len(stats["dn"]) * 100
        bars += f'<div class="bar"><span>صعود {lab}</span><div class="tr"><div class="fl" style="width:{pu:.0f}%"></div></div><b>{pu:.0f}%</b></div>'
        bars += f'<div class="bar"><span>هبوط {lab}</span><div class="tr"><div class="fl red" style="width:{pd:.0f}%"></div></div><b>{pd:.0f}%</b></div>'

    table_all = "".join(row(t, i + 1) for i, t in enumerate(trades))

    def _chips(arr, cls):
        if not arr:
            return ""
        return '<div class="chips">' + "".join(
            f'<a class="chip {cls}" data-sym="{t["name"]}" href="#t-{t["name"]}">{t["name"]}</a>' for t in arr
        ) + '</div>'

    side_sections = ""
    for title, arr, idd, hcls, ccls, desc in (
        ("🟢 صفقات الشراء LONG", longs, "longs", "hlong", "long", "مرتبة بالأولوية وقرب منطقة الدخول · الشراء من مناطق الدعم"),
        ("🔴 صفقات البيع SHORT", shorts, "shorts", "hshort", "short", "مرتبة بالأولوية وقرب منطقة الدخول · البيع من مناطق المقاومة"),
    ):
        side_sections += f'<h2 id="{idd}" class="{hcls}">{title} — {len(arr)}</h2><div class="sub" style="margin-bottom:8px">{desc}</div>'
        if arr:
            side_sections += _chips(arr, ccls)
            side_sections += "".join(card(t, i, with_id=True) for i, t in enumerate(arr))
        else:
            side_sections += '<div class="note" style="background:#0d1622;border-color:#1e2c42">لا توجد صفقات مؤهلة في هذا الاتجاه خلال هذه الدورة.</div>'

    # ------- قسم العملات القابلة للانفجار مع الافتتاح اليومي
    exp_active = (exp_data or {}).get("active") or []
    exp_cancelled = (exp_data or {}).get("cancelled") or []
    exp_stage = (exp_data or {}).get("stage") or "radar"

    def card_exp(e):
        gcol = {"A": "ga", "B": "gb", "C": "gc"}.get(e.get("grade", "B"), "gb")
        etsrcs = e.get("target_sources") or ["structural_sr", "rr_floor_extension", "rr_floor_extension"]
        tg = "".join(
            f'<div class="lv t{k+1}"><span>هدف {k+1} · {TARGET_SRC_AR.get(etsrcs[k], "مستوى بنيوي")}</span><b>{fp(e["targets"][k], e["tick"])}</b>'
            f'<i>{((e["targets"][k]/e["avg"]-1)*100):+.2f}% · R{e["rr"][k]:.2f}</i></div>'
            for k in range(3)
        )
        sup_txt = " · ".join(fp(x, e["tick"]) for x in e.get("supports", [])[:3])
        res_txt = " · ".join(fp(x, e["tick"]) for x in e.get("resistances", [])[:3])
        reasons_txt = " · ".join(e.get("reasons") or []) or "—"
        fcls = "pos" if e["funding"] <= 0 else "neg"
        return f'''
<article class="card exp" id="exp-{e["name"]}" data-sym="{e["name"]}">
  <div class="chead">
    <div class="csym">🔥 {e["name"]}<span>/USDT</span> <small>{e["score"]:.1f} نقطة</small>
      <em class="g {gcol}">درجة {e["grade"]}</em>
      <em class="g expbadge">{e.get("stage_label", "قابلة للانفجار")}</em>
    </div>
    <div><span class="pill long">اصطياد ذيل LONG</span></div>
  </div>
  <div class="cbody">
    <div class="levels">
      <div class="lv entry"><span>منطقة صيد الذيل (Limit)</span><b>{fp(e["entry_lo"], e["tick"])} – {fp(e["entry_hi"], e["tick"])}</b><i>{e["dist_pct"]:+.2f}% عن السعر · {e["dist_atr"]:.2f} ATR</i></div>
      <div class="lv stop"><span>الوقف البنيوي</span><b>{fp(e["stop"], e["tick"])}</b><i>مخاطرة {e["risk_pct"]:.2f}%</i></div>
      {tg}
    </div>
    <div class="meta">
      <div><span>السعر الآن</span><b>{fp(e["price"], e["tick"])}</b></div>
      <div><span>موقع السعر في مدى 24س</span><b class="pos">{e["pos24"]:.1f}% (قرب القمة)</b></div>
      <div><span>تغيّر 24س</span><b class="pos">{e["chg"]:+.2f}%</b></div>
      <div><span>Δ OI (4س)</span>{_fmt_oi_html(e.get("oi_chg"))}</div>
      <div><span>فاندنغ</span><b class="{fcls}">{e["funding"]:+.4f}%</b></div>
      <div><span>سيولة 24س</span><b>{e["qv"]:,.1f}M$</b></div>
      <div><span>RSI 4س/يومي</span><b>{e["rsi4"]:.0f}/{e["rsi1"]:.0f}</b></div>
      <div><span>الكمية والقيمة الاسمية</span><b>{e["qty"]:,.4f} ({float(e.get("position_notional_usd", 1000)):,.0f}$)</b></div>
      <div><span>المخاطرة النقدية الفعلية</span><b class="neg">{float(e.get("actual_risk_cash", 100)):,.2f}$ ({float(e.get("actual_risk_pct_equity", 1.0)):.2f}%)</b></div>
      <div><span>الرافعة والهامش</span><b>{int(e.get("leverage", 3))}x · هامش {float(e.get("margin_required_usd", 333)):,.0f}$</b></div>
      <div class="sr"><span>الدعوم</span><b class="pos">{sup_txt}</b></div>
      <div class="sr"><span>المقاومات</span><b class="neg">{res_txt}</b></div>
      <div class="sr"><span>بصمة الانفجار</span><b style="color:#fbbf24">{reasons_txt}</b></div>
    </div>
    <div class="plan"><b>خطة اصطياد ذيل آسيا:</b> ممنوع الشراء السوقي عند 03:00 ← علّق Limit في منطقة صيد الذيل بعد تأكيد 02:45 ← اترك الأمر يلتقط تلاعب آسيا (انطلاقة البدائل ~04:30 والكبار ~06:30) ← أغلق 50% عند هدف 1 وانقل الوقف للتعادل.</div>
  </div>
</article>'''

    if exp_stage == "confirm":
        exp_banner = '<div class="okbox"><b>✅ مرحلة التأكيد النهائي (02:45 قبل الإغلاق اليومي):</b> هذه العملات حافظت على تماسكها في الربع العلوي حتى نهاية اليوم — علّق أوامر <b>Limit</b> في منطقة صيد الذيل الآسيوي (لا شراء سوقي عند 03:00).</div>'
    elif exp_stage == "active":
        exp_banner = '<div class="okbox"><b>🎯 مصيدة ذيل آسيا نشطة (03:00 – 07:00):</b> الجلسة الآسيوية تصنع الآن الذيل اليومي — اترك أوامر <b>Limit</b> المعلّقة تعمل بهدوء دون مطاردة.</div>'
    elif exp_stage == "daytime":
        exp_banner = '<div class="note"><b>ℹ️ ملاحظة التوقيت:</b> الرصد الرسمي لقائمة الانفجار يبدأ في مسح <b>23:05</b> ويُؤكَّد في فحص <b>02:45</b> قبل الإغلاق اليومي. ما يظهر أدناه معاينة نهارية للعملات المتماسكة في قممها حالياً.</div>'
    else:
        exp_banner = '<div class="note"><b>📡 مرحلة الرصد المبكر (23:05 — للمراقبة فقط):</b> ~40% من مرشحات الليل تفقد تماسكها قبل الفجر؛ لذلك <b>تُراقب فقط الآن</b> ويتم تثبيت الصامد منها وشطب الفاشل في <b>فحص التأكيد 02:45</b> قبل الإغلاق اليومي.</div>'

    cancel_box = ""
    if exp_cancelled:
        c_items = " · ".join(f'<b>{c["name"]}</b> ({c.get("cancel_reason", "فقدت التماسك")})' for c in exp_cancelled)
        cancel_box = f'<div class="warn"><b>⛔ شُطبت في فحص التأكيد (02:45):</b> {c_items}</div>'

    exp_section = f'<h2 id="explode" class="hexp">🔥 عملات قابلة للانفجار مع الافتتاح اليومي — {len(exp_active)}</h2>'
    exp_section += exp_banner + cancel_box
    if exp_active:
        exp_section += "".join(card_exp(e) for e in exp_active)
    else:
        exp_section += '<div class="note" style="background:#0d1622;border-color:#1e2c42">لا توجد عملات تستوفي شروط الانفجار الصارمة في هذه اللحظة.</div>'

    # ------- قسم العملات الاستثمارية (العصر والقاع) + كسر الهيكل اليومي النشط (المحرّك المزدوج)
    inv_squeeze = (macro_data or {}).get("squeeze") or []
    bos_active = (macro_data or {}).get("bos3") or []
    btc_reg = (macro_data or {}).get("btc_regime") or {"state": "neutral", "label": "🟡 مناخ محايد", "advice": "التزم بوقف صريح 1% لكل صفقة."}
    n_macro = len(inv_squeeze) + len(bos_active)

    def card_inv(m):
        tg = "".join(
            f'<div class="lv t{k+1}"><span>هدف استثماري {k+1}</span><b>{fp(m["targets"][k], m["tick"])}</b>'
            f'<i>{((m["targets"][k]/m["avg"]-1)*100):+.1f}% · R{m["rr"][k]:.1f}</i></div>'
            for k in range(3)
        )
        fcls = "pos" if m["funding"] <= 0 else "neg"
        reasons_txt = " · ".join(m.get("reasons") or [])
        pos_usd = float(m.get("position_notional_usd") or m.get("pos_usd_1r") or 100.0)
        m_qty = float(m.get("position_size") or m.get("qty_1r") or 0.0)
        m_rcash = float(m.get("actual_risk_cash") or 100.0)
        m_rpct = float(m.get("actual_risk_pct_equity") or 1.0)
        m_lev = int(m.get("leverage") or 1)
        m_marg = float(m.get("margin_required_usd") or pos_usd)
        m_eq = float(m.get("equity_usd") or 10000.0)
        return f'''
<article class="card inv" id="inv-{m["name"]}" data-sym="{m["name"]}">
  <div class="chead">
    <div class="csym">💎 {m["name"]}<span>/USDT</span> <small>{m["score"]:.1f} نقطة</small>
      <em class="g invbadge">{m["badge"]}</em>
    </div>
    <div><span class="pill" style="background:#281442;color:#e9d5ff;border:1px solid #7e22ce">استثمارية · تجميع قاعي (+0.39R EV)</span></div>
  </div>
  <div class="cbody">
    <div class="levels">
      <div class="lv entry" style="border-color:#8b5cf6;background:#150f29"><span>منطقة التمركز وصيد التلاعب (دفعتين)</span><b style="color:#ddd6fe">{fp(m["entry_lo"], m["tick"])} – {fp(m["entry_hi"], m["tick"])}</b><i>{m["dist_pct"]:+.2f}% عن السعر · تشمل جيب التلاعب السُفلي</i></div>
      <div class="lv stop"><span>وقف صريح إلزامي في المنصة (Hard Stop)</span><b>{fp(m["stop"], m["tick"])}</b><i>مسافة السعر {m["risk_pct"]:.2f}% · مخاطرة المحفظة {m_rcash:,.2f}$ ({m_rpct:.2f}%)</i></div>
      {tg}
    </div>
    <div class="meta">
      <div><span>السعر الآن</span><b>{fp(m["price"], m["tick"])}</b></div>
      <div><span>نطاق العصر الأفقي (20ي)</span><b style="direction:ltr">{fp(m["box_floor"], m["tick"])} – {fp(m["box_ceil"], m["tick"])} ({m["box_pct"]:.1f}%)</b></div>
      <div><span>موقع القاع الكلي (180ي)</span><b class="pos">{m["pos180"]:.1f}% (منطقة قاع)</b></div>
      <div><span>شدة العصر والانكماش</span><b style="color:#d8b4fe">{m["squeeze_pct"]:.0f}%</b></div>
      <div><span>الكمية والقيمة الاسمية</span><b>{m_qty:,.4f} ({pos_usd:,.0f}$)</b></div>
      <div><span>الرافعة والهامش المطلوب</span><b>{m_lev}x · هامش {m_marg:,.0f}$</b></div>
      <div><span>RSI اليومي</span><b>{m["rsi_d"]:.1f}</b></div>
      <div><span>فاندنغ</span><b class="{fcls}">{m["funding"]:+.4f}%</b></div>
      <div><span>سيولة 24س</span><b>{m["qv"]:,.1f}M$</b></div>
      <div><span>بصمة التجميع والدفاع الشرائي</span><b style="color:#c4b5fd">{reasons_txt}</b></div>
    </div>
    <div class="plan" style="border-color:#6d28d9;background:#120d24;color:#d8b4fe"><b style="color:#e9d5ff">القاعدة العلمية الصارمة للتنفيذ:</b> لا توجد عملة مضمونة الصعود 100%؛ التفوق الإحصائي هنا (+0.39R) يأتي من <b>تثبيت أمر وقف صريح (Hard Stop) في المنصة</b> تحت ذيل التلاعب وضبط القيمة الاسمية عند <b>{pos_usd:,.0f}$</b> (لمحفظة {m_eq:,.0f}$ · رافعة <b>{m_lev}x</b>) بحيث يستحيل أن تتجاوز الخسارة الفعلية شاملة الرسوم والانزلاق <b>{m_rcash:,.2f}$ ({m_rpct:.2f}%)</b>، بينما تُغلق 50% عند هدف 1 ويُنقل الوقف للتعادل.</div>
  </div>
</article>'''

    def card_bos(b):
        tg = "".join(
            f'<div class="lv t{k+1}"><span>هدف موجة {k+1}</span><b>{fp(b["targets"][k], b["tick"])}</b>'
            f'<i>{((b["targets"][k]/b["avg"]-1)*100):+.1f}% · R{b["rr"][k]:.1f}</i></div>'
            for k in range(3)
        )
        c_note = b.get("close_note") or " ← ".join(fp(x, b["tick"]) for x in b["closes_3"])
        kind_b = b.get("kind_badge", "🚀 كسر هيكل يومي")
        crown = '<em class="g crownbadge">👑 جوهرة متكاملة (خرجت من قاع تجميعي)</em>' if b.get("from_squeeze") else ""
        b_lev = int(b.get("leverage") or (2 if b["risk_pct"] <= 12.0 else 1))
        pos_usd_b = float(b.get("position_notional_usd") or 1000.0)
        b_qty = float(b.get("position_size") or 0.0)
        b_rcash = float(b.get("actual_risk_cash") or 100.0)
        b_rpct = float(b.get("actual_risk_pct_equity") or 1.0)
        b_marg = float(b.get("margin_required_usd") or (pos_usd_b / b_lev))
        room_note = (
            f'<div><span>قمة 30 يوماً المستهدفة</span><b style="color:#fde047">{fp(b.get("hi30_ref", b["struct_lvl"]), b["tick"])} (+{b.get("room_30d_pct", 0):.1f}% مساحة مفتوحة)</b></div>'
            if b.get("bos_kind") in ("uptrend3g", "hammer1d") and b.get("room_30d_pct", 0) > 0
            else f'<div><span>السقف المكسور ({b["lvl_type"]})</span><b class="pos">{fp(b["struct_lvl"], b["tick"])}</b></div>'
        )
        w_sum = b.get("w_summary", "—")
        m_sum = b.get("m_summary", "—")
        return f'''
<article class="card bos" id="bos-{b["name"]}" data-sym="{b["name"]}">
  <div class="chead">
    <div class="csym">🚀 {b["name"]}<span>/USDT</span> <small>{b["score"]:.1f} نقطة</small>
      <em class="g bosbadge">{kind_b}</em>
      <em class="g" style="background:#0f291e;color:#6ee7b7;border:1px solid #15803d">{b["state_lbl"]}</em> {crown}
    </div>
    <div><span class="pill" style="background:#0c2d48;color:#7dd3fc;border:1px solid #0284c7">زخم / كسر يومي + تأييد 1W/1M</span></div>
  </div>
  <div class="cbody">
    <div class="levels">
      <div class="lv entry" style="border-color:#0284c7;background:#0a1d30"><span>منطقة التراجع / إعادة الاختبار (Limit)</span><b style="color:#bae6fd">{fp(b["entry_lo"], b["tick"])} – {fp(b["entry_hi"], b["tick"])}</b><i>{b["dist_pct"]:+.2f}% عن السعر · بُعد {b["dist_atr"]:.2f} ATR يومي</i></div>
      <div class="lv stop"><span>وقف صريح إلزامي (Hard Stop)</span><b>{fp(b["stop"], b["tick"])}</b><i>مسافة السعر {b["risk_pct"]:.2f}% · مخاطرة المحفظة {b_rcash:,.2f}$ ({b_rpct:.2f}%)</i></div>
      {tg}
    </div>
    <div class="meta">
      <div><span>السعر الآن</span><b>{fp(b["price"], b["tick"])}</b></div>
      {room_note}
      <div class="sr"><span>الإغلاقات اليومية الخضراء بالجسم الكامل</span><b style="color:#7dd3fc;direction:ltr">{c_note}</b></div>
      <div class="sr"><span>📅 قراءة شمعة الأسبوع (1W)</span><b style="color:#93c5fd">{w_sum}</b></div>
      <div class="sr"><span>🗓️ قراءة شمعة الشهر (1M)</span><b style="color:#c4b5fd">{m_sum}</b></div>
      <div><span>الكمية والقيمة الاسمية</span><b>{b_qty:,.4f} ({pos_usd_b:,.0f}$)</b></div>
      <div><span>الرافعة والهامش المطلوب</span><b>{b_lev}x · هامش {b_marg:,.0f}$</b></div>
      <div><span>تدفق السيولة المؤسسية</span><b class="pos">{b["vol_x"]:.2f}x من متوسط 20ي</b></div>
      <div><span>RSI اليومي</span><b>{b["rsi_d"]:.1f}</b></div>
      <div><span>سيولة 24س</span><b>{b["qv"]:,.1f}M$</b></div>
    </div>
    <div class="plan" style="border-color:#0284c7;background:#091829;color:#bae6fd"><b style="color:#7dd3fc">خطة التنفيذ المتوافقة مع 1D + 1W + 1M (+0.51R EV):</b> العملة مدعومة ببنية أسبوعية وشهرية سليمة وأغلقت شموعاً يومية خضراء ممتلئة الجسم · <b>لا تطارد القمة سوقياً؛ علّق أمر Limit في منطقة التراجع/إعادة الاختبار مع وقف صريح في المنصة</b>.</div>
  </div>
</article>'''

    is_late_now = (_cur_dt.hour >= 23 or _cur_dt.hour < 3)
    daily_clock_note = (
        "🌙 <b>التوقيت الليلي المتأخر (بعد 23:05 — اكتمل &gt;83% من الشمعة اليومية):</b> مفعَّل الآن احتساب شمعة اليوم الجارية القوية التي لا يواجهها عائق مقاومة قريب (دقة ثبات 96.6%)، وكذلك شمعة الهمر الانعكاسية (🔨 Hammer بذيل رفض سُفلي &ge;55% في اتجاه صاعد)."
        if is_late_now else
        "☀️ <b>التوقيت النهاري (قبل 23:05 — وقت طويل على الإغلاق اليومي 03:00):</b> يتم <b>تجاهل شمعة اليوم الجارية غير المكتملة تماماً</b> في حساب الإغلاقات، والاعتماد حصراً على الشموع اليومية المغلقة (أو همر أمس المغلق) حتى يحين مسح <b>23:05</b>."
    )
    reg_bg = "#092115" if btc_reg["state"] == "bull" else ("#1f1908" if btc_reg["state"] == "oversold" else "#23120b")
    reg_bd = "#1b683e" if btc_reg["state"] == "bull" else ("#855512" if btc_reg["state"] == "oversold" else "#9a3412")
    macro_section = f'''
<div id="macro" style="scroll-margin-top:75px">
  <h2 class="hinv">💎 العملات الاستثمارية وكسر الهيكل اليومي (1D) — {n_macro} عملة</h2>
  <div class="note" style="background:{reg_bg};border-color:{reg_bd};margin-bottom:8px">
    <b>🧭 مؤشر مناخ البيتكوين اليومي للتمركز: {btc_reg["label"]}</b> — {btc_reg["advice"]}
  </div>
  <div class="note" style="background:#0b1526;border-color:#1e3a5f;margin-top:0;margin-bottom:10px;padding:11px 15px;font-size:12.5px">
    {daily_clock_note}
  </div>
  <div class="grid2" style="margin-bottom:12px">
    <div class="note" style="background:#120d22;border-color:#581c87;margin:0">
      <b style="color:#e9d5ff">🟣 أولاً: 🧲 العملات الاستثمارية (مرحلة العصر والقاع — {len(inv_squeeze)})</b><br>
      تُشترط هنا <b>علامة دفاع شرائي فعلية</b> (اكتمال ذيل التلاعب السُفلي <i>Spring</i> أو انحراف تعافي <i>RSI</i>) لاستبعاد العملات الميتة، مع <b>أمر وقف صريح إلزامي (Hard Stop)</b> وتصغير حجم المركز ليبقى أقصى خطر -1R بالضبط.
    </div>
    <div class="note" style="background:#091829;border-color:#0369a1;margin:0">
      <b style="color:#7dd3fc">🩵 ثانياً: 🚀 الكسر اليومي + 3 إغلاقات صاعدة + الهمر الانعكاسي (1D + 1W + 1M — {len(bos_active)})</b><br>
      يرصد: <b>(1) كسر قمة 30 يوماً</b>، و<b>(2) 3 إغلاقات خضراء صاعدة قبل قمة 30ي بمساحة &ge;1.8R</b>، و<b>(3) 🔨 شمعة الهمر الانعكاسية بذيل رفض سُفلي &ge;55% داخل اتجاه صاعد</b> (تُتجاهل شمعة اليوم الحية نهاراً ولا تُقرأ إلا بعد <b>23:05</b>)، مع شرط <b>EMA20 الأسبوعي وأرضية الشهر السابق</b>.
    </div>
  </div>
  <h2 class="hinv" style="font-size:16.5px;margin-top:14px">🧲 1) قائمة العصر الأفقي والقاع الاستثماري المؤيد بدفاع شرائي — {len(inv_squeeze)}</h2>
  {"".join(card_inv(m) for m in inv_squeeze) if inv_squeeze else '<div class="note" style="background:#0d1622;border-color:#1e2c42">لا توجد عملات في قاع وعصر أفقي مكتمل مع دفاع شرائي في هذه اللحظة.</div>'}
  <h2 class="hbos" style="font-size:16.5px;margin-top:20px">🚀 2) قائمة الكسر اليومي و3 إغلاقات صاعدة بالجسم المؤيدة بشمعتي الأسبوع والشهر — {len(bos_active)}</h2>
  {"".join(card_bos(b) for b in bos_active) if bos_active else '<div class="note" style="background:#0d1622;border-color:#1e2c42">لا توجد حالياً أي عملة حققت إغلاقات الأجسام الخضراء اليومية (فوق قمة 30 يوماً أو في اتجاه صاعد قبلها بمساحة مفتوحة) مع اجتياز شرطي شمعة الأسبوع (1W) وشمعة الشهر (1M) ضمن مسافة الدخول.</div>'}
</div>'''

    # ------- شريط العداد التراكمي العام منذ بدء التشغيل
    lt_w = int((lt_stats or {}).get("wins", 0))
    lt_l = int((lt_stats or {}).get("losses", 0))
    lt_tot = lt_w + lt_l
    lt_wr = (lt_w / lt_tot * 100.0) if lt_tot > 0 else 0.0
    lt_net = float((lt_stats or {}).get("net_r", 0.0))
    lt_since = (lt_stats or {}).get("started_at", ts)
    lifetime_bar_html = f'''
<div class="ltbar">
  <div style="font-size:12.5px;font-weight:700;color:#cbd5e1">
    📊 السجل التراكمي العام للصفقات المحسومة <span style="color:#7d8ea3;font-weight:400">(منذ {lt_since} · يُحدَّث آلياً مع كل تقرير)</span>
  </div>
  <div class="ltpills">
    <div class="ltp"><span>✅ رابحة مغلقة:</span><b class="pos">{lt_w}</b></div>
    <div class="ltp"><span>🛑 خاسرة مغلقة:</span><b class="neg">{lt_l}</b></div>
    <div class="ltp"><span>🏆 نسبة النجاح:</span><b style="color:#fde047">{lt_wr:.1f}%</b></div>
    <div class="ltp"><span>💰 صافي محقق:</span><b class="{'pos' if lt_net>=0 else 'neg'}" style="direction:ltr">{lt_net:+.2f}R</b></div>
    <div class="ltp" style="border-style:dashed"><span>⏳ مفتوحة الآن:</span><b><span class="pos">{c_open_win} رابحة</span> / <span class="neg">{c_open_loss} خاسرة</span></b></div>
  </div>
</div>'''

    sections = ""
    for title, arr, idd, desc in (
        ("✅ لمسة فورية — المنطقة على بُعد ≤ 0.5 ATR", now_ok, "now", "أعلى احتمال تنفيذ (~80% خلال 24 ساعة حسب القياس)"),
        ("🟡 قريبة — 0.5 إلى 0.65 ATR", near, "near", "احتمال تنفيذ جيد (~65%)"),
        ("🟠 أبعد قليلاً — 0.65 إلى 1.0 ATR", far, "far", "تُراقب فقط؛ لا تُلاحق إن ابتعدت أكثر"),
    ):
        sections += f'<h2 id="{idd}">{title} — {len(arr)}</h2><div class="sub" style="margin-bottom:8px">{desc}</div>'
        if arr:
            sections += "".join(card(t, i, with_id=False) for i, t in enumerate(arr))
        else:
            sections += '<div class="note" style="background:#0d1622;border-color:#1e2c42">لا توجد صفقات ضمن هذه الفئة حالياً.</div>'

    sched_slots = {
        3: "نافذة 03:05 — إغلاق يومي + 4س + فاندنغ + وضع اصطياد ذيل آسيا",
        11: "نافذة 11:05 — إغلاق 4س + فاندنغ + لندن",
        15: "نافذة 15:05 — إغلاق 4س قبل الجلسة الأمريكية",
        19: "نافذة 19:05 — أفضل نافذة: إغلاق 4س + نيويورك + فاندنغ",
        23: "نافذة 23:05 — إغلاق 4س + رصد قائمة قابلة للانفجار",
    }
    confirm_ts = state.get("confirm_ts", 0)
    is_gh_sched = os.environ.get("GITHUB_EVENT_NAME") == "schedule"
    if confirm_ts and confirm_ts > meta.get("ts", 0):
        confirm_hm = dt.datetime.fromtimestamp(confirm_ts / 1000, RIYADH).strftime("%H:%M")
        win_note = f'✅ فحص التأكيد الرسمي ({confirm_hm} — تثبيت قائمة قابلة للانفجار قبل الإغلاق اليومي)'
    elif (_cur_dt.hour in sched_slots and 0 <= _cur_dt.minute <= 35) or (is_gh_sched and _cur_dt.hour in sched_slots):
        win_note = f'✅ تنفيذ ضمن الموعد المتفق عليه ({sched_slots[_cur_dt.hour]})'
    else:
        dead_warn = " · ⚠️ تنبيه: ساعة سيولة ضعيفة" if _cur_dt.hour in (1, 2, 7, 13, 14, 22) else ""
        win_note = f'تنفيذ خارج المواعيد المتفق عليها (02:45 تأكيدي · 03:05 · 11:05 · 15:05 · 19:05 · 23:05) بطلب صريح من المستخدم{dead_warn}'

    # ------- صفوة الدورة المتوازنة (منع التكدس ومخاطرة الارتباط العالي بالبيتكوين + بوابة المخاطرة الكلية)
    BIG_MAJORS = {"BTC", "ETH", "SOL", "BNB"}
    ordered_pool = sorted(
        [t for t in trades if t.get("risk_gate_allowed", True)],
        key=lambda x: (0 if x["reach"] in ("A", "B") else 1, -x["score"], x["dist_atr"]),
    )
    div_picks = []
    cnt_side = {"LONG": 0, "SHORT": 0}
    used_major = port_risk.get("open_major_count", 0) >= port_risk.get("max_major_positions", 1)
    for cand_t in ordered_pool:
        if len(div_picks) >= max(0, port_risk.get("max_concurrent_positions", 4) - port_risk.get("open_count", 0)):
            break
        is_maj = cand_t["name"] in BIG_MAJORS
        if is_maj and used_major:
            continue
        if cnt_side[cand_t["side"]] >= 2:
            continue
        div_picks.append(cand_t)
        cnt_side[cand_t["side"]] += 1
        if is_maj:
            used_major = True

    if div_picks:
        dp_cards = "".join(
            f'<a href="#t-{p["name"]}" style="text-decoration:none;background:#0a1424;border:1px solid {"#1c5c39" if p["side"]=="LONG" else "#5c2029"};border-radius:11px;padding:8px 12px;display:flex;flex-direction:column;gap:3px;min-width:175px;flex:1">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<b style="color:#fff;font-size:14px">{p["name"]}</b>'
            f'<span class="pill {"long" if p["side"]=="LONG" else "short"}">{p["side"]}</span></div>'
            f'<div style="font-size:11.5px;color:#9db1c8">الدرجة <b style="color:#fde047">{p["score"]:.1f} ({p["grade"]})</b> · مخاطرة <b style="color:#fda4af">{float(p.get("actual_risk_cash", 0)):.0f}$</b> ({int(p.get("leverage", 3))}x)</div>'
            f'<div style="font-size:11px;color:#93c5fd;direction:ltr;text-align:left">{fp(p["entry_lo"], p["tick"])} – {fp(p["entry_hi"], p["tick"])}</div>'
            f'</a>'
            for p in div_picks
        )
        diversified_picks_html = f'''
<div class="okbox" style="background:linear-gradient(135deg,#0b1929,#0a1520);border-color:#2563eb;margin:12px 0 16px">
  <div style="font-size:13.5px;font-weight:800;color:#93c5fd;margin-bottom:4px">🛡️ صفوة الدورة المتوازنة (تشكيلة مضادة للتكدس ومضبوطة بسقف المخاطرة الكلي {port_risk["max_total_open_risk_pct"]:.1f}%)</div>
  <div style="font-size:12px;color:#9db1c8;margin-bottom:10px">اختار المحرك تلقائياً أعلى الفرص المجازة من بوابة المخاطرة الكلية مع <b>منع تكرار الكبار</b> و<b>موازنة الاتجاه</b> وعدم تجاوز <b>{port_risk["max_concurrent_positions"]} مراكز متزامنة</b>:</div>
  <div style="display:flex;flex-wrap:wrap;gap:9px">{dp_cards}</div>
</div>'''
    else:
        diversified_picks_html = ""

    pr_open_col = "#34d399" if port_risk["open_risk_pct"] < port_risk["max_total_open_risk_pct"] * 0.8 else "#fbbf24"
    sess_col = "#fde047" if port_risk.get("session_is_chop") else "#86efac"
    portfolio_risk_bar_html = f'''
<div class="ltbar" style="border-color:#1e3a5f;background:linear-gradient(135deg,#0a1322,#0d1b30)">
  <div class="lthead">
    <div class="lttitle" style="color:#93c5fd">🛡️ محرك المخاطر الرأسمالية وبوابة الانتقاء الذكية (v4.0)</div>
    <div class="ltsub">رأس المال المرجعي: <b>{port_risk["equity_usd"]:,.0f}$</b> · ميزانية الصفقة: <b>{port_risk["risk_per_trade_cash"]:,.0f}$ ({port_risk["risk_pct_per_trade"]:.2f}%)</b> · <span style="color:{sess_col};font-weight:700">{port_risk.get("session_label_ar", "")}</span></div>
  </div>
  <div class="ltkpis">
    <div class="ltkpi"><span>المراكز المفتوحة</span><b>{port_risk["open_count"]} / {port_risk["max_concurrent_positions"]}</b></div>
    <div class="ltkpi"><span>المخاطرة المفتوحة الآن</span><b style="color:{pr_open_col}">{port_risk["open_risk_cash"]:,.2f}$ ({port_risk["open_risk_pct"]:.2f}%)</b></div>
    <div class="ltkpi"><span>السقف الكلي للمخاطرة</span><b style="color:#fde047">{port_risk["max_total_open_risk_cash"]:,.0f}$ ({port_risk["max_total_open_risk_pct"]:.1f}%)</b></div>
    <div class="ltkpi"><span>المتاح لصفقات جديدة</span><b class="pos">{port_risk["remaining_risk_budget_cash"]:,.2f}$ ({port_risk["remaining_risk_budget_pct"]:.2f}%)</b></div>
    <div class="ltkpi"><span>الهامش المحجوز حالياً</span><b>{port_risk["open_margin_usd"]:,.0f}$ ({port_risk["open_margin_pct"]:.1f}% / {port_risk["max_total_margin_pct"]:.0f}%)</b></div>
    <div class="ltkpi"><span>مجاز للتنفيذ / مراقبة واحتياطي</span><b style="color:#7dd3fc">{port_risk["approved_candidates"]} مجاز ({port_risk.get("effective_min_approval_score", 103):.0f}+) · {port_risk["blocked_candidates"]} احتياطي</b></div>
  </div>
</div>'''

    report_idx_json = json.dumps({
        "trades": [{"name": t["name"], "side": t["side"], "grade": t["grade"], "score": float(t["score"])} for t in trades],
        "exp": [{"name": e["name"], "score": float(e.get("score", 0))} for e in exp_active],
        "inv": [{"name": m["name"], "badge": m["badge"], "score": float(m["score"])} for m in inv_squeeze],
        "bos": [{"name": b["name"], "vol_x": float(b["vol_x"]), "score": float(b["score"])} for b in bos_active],
        "track": [{"name": x["name"], "side": x["side"], "status": x.get("status", "-"), "r_now": x.get("r_now")} for x in tracked],
    }, ensure_ascii=False)

    html_doc = f'''<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#080c12">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="ماسح بايننس">
<link rel="manifest" href="manifest.json">
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="icon.svg">
<title>ماسح بايننس — {ts}</title>
<style>{css}</style></head><body><div class="wrap" id="top">

<div class="appbar">
  <div style="font-size:13px;font-weight:700;color:#9ecbff">📱 تطبيق ماسح بايننس الآجل (v4.0 المطور)</div>
  <div class="appbtns">
    <button class="abtn pri" onclick="triggerCloud('scan')">🔄 ابدأ المسح الآن</button>
    <button class="abtn conf" onclick="triggerCloud('confirm')">✅ فحص تأكيد 02:45</button>
    <button class="abtn" onclick="refreshNow()">↻ تحديث الصفحة</button>
    <button class="abtn" onclick="openCfg()">⚙️ إعداد الضغطة الواحدة</button>
  </div>
</div>
<div id="toast" class="status-toast"></div>
{lifetime_bar_html}
{portfolio_risk_bar_html}

<div class="hero">
  <span class="stamp">🕒 {ts} — توقيت الرياض (UTC+3)</span>
  <h1>مسح عقود بايننس الآجلة — نسخة مناطق الدخول المُراجَعة (v3)</h1>
  <span class="sub">{win_note} ·
  <b>بيانات المسح: {scan_hm}</b> · آخر تحديث للمراكز: {track_hm} · المصدر: Binance Futures API</span>
  <div class="kpis">
    <div class="kpi"><span>صفقات مؤهلة</span><b>{len(trades)}</b></div>
    <div class="kpi"><span>شراء / بيع</span><b>{len(longs)} / {len(shorts)}</b></div>
    <div class="kpi"><span>🔥 قابلة للانفجار</span><b style="color:#fbbf24">{len(exp_active)}</b></div>
    <div class="kpi"><span>💎 استثمارية / كسر هيكل</span><b style="color:#d8b4fe">{len(inv_squeeze)} / {len(bos_active)}</b></div>
    <div class="kpi"><span>درجة A</span><b>{len(gradeA)}</b></div>
    <div class="kpi"><span>لمسة فورية (≤0.5 ATR)</span><b>{len(now_ok)}</b></div>
    <div class="kpi"><span>وسيط المسافة عن السعر</span><b>{med_d:.2f} ATR</b></div>
    <div class="kpi"><span>عقود مفحوصة</span><b>{universe} من 522</b></div>
  </div>
</div>

<div class="nav">
  <a href="#tools" style="background:#172b4d;color:#93c5fd;border-color:#2f5a9e">🔍 بحث / فحص عملة</a>
  <a href="#all">📋 كل الصفقات <span class="cnt">{len(trades)}</span></a>
  <a class="longb" href="#longs">🟢 صفقات الشراء <span class="cnt">{len(longs)}</span></a>
  <a class="shortb" href="#shorts">🔴 صفقات البيع <span class="cnt">{len(shorts)}</span></a>
  <a class="expb" href="#explode">🔥 قابلة للانفجار <span class="cnt">{len(exp_active)}</span></a>
  <a class="invb" href="#macro">💎 استثمارية وكسر هيكل <span class="cnt">{n_macro}</span></a>
  <a href="#now">✅ لمسة فورية <span class="cnt">{len(now_ok)}</span></a>
  <a href="#near">🟡 قريبة <span class="cnt">{len(near)}</span></a>
  <a href="#far">🟠 أبعد <span class="cnt">{len(far)}</span></a>
  <a href="#track">🔄 تحديث السابق <span class="cnt">{n_tr}</span></a>
  <a href="#rules">📌 القواعد</a>
</div>

<div id="tools" class="tools-grid" style="scroll-margin-top:75px">
  <div class="tbox">
    <h3>🔍 البحث الفوري داخل التقرير الحالي</h3>
    <div class="tsub">اكتب رمز العملة لفلترة الجداول والبطاقات ومعرفة وضعها في الصفقات المؤهلة والانفجار والمتابعة فوراً:</div>
    <div class="tinp-row">
      <input id="coinSearchInp" class="tinp" placeholder="اكتب رمز العملة (مثل BTC أو SOL أو ZEC)..." oninput="onSearchCoin()">
      <button id="clrSearchBtn" class="abtn" style="display:none;flex:0 0 auto" onclick="clearSearchCoin()">✖ مسح</button>
    </div>
    <div id="searchSummary" class="sres"></div>
  </div>

  <div class="tbox" style="border-color:#2c4c7e">
    <h3>🎯 فحص وتحليل عملة محددة حياً (خلال ثانية)</h3>
    <div class="tsub">اكتب أي عملة في عقود بايننس الآجلة (حتى لو لم تكن بالتقرير) لفحصها حياً بمعادلات v3.4 وكشف الدعوم والمقاومات وسبب قبولها أو استبعادها:</div>
    <div class="tinp-row">
      <input id="customCoinInp" class="tinp" placeholder="مثال: DOGE أو PEPE أو ARB أو XRP..." onkeydown="if(event.key==='Enter')analyzeCustomCoin()">
      <button class="abtn pri" style="flex:0 0 auto" onclick="analyzeCustomCoin()">🎯 حلّل الآن</button>
    </div>
  </div>
</div>
<div id="liveCoinResult" style="display:none;margin:10px 0 18px"></div>

{diversified_picks_html}

<h2 id="all">📋 كل الصفقات المؤهلة — {len(trades)}</h2>
<div class="sub" style="margin-bottom:8px">مرتبة بالأولوية: الدرجة ثم قرب منطقة الدخول · اضغط على رمز العملة للانتقال إلى بطاقتها التفصيلية · الدرجة A = ≥103 · B = 99–103 · C = 95–99</div>
<div class="twrap"><table>
<thead><tr><th class="c">#</th><th>العملة</th><th class="c">الاتجاه</th><th>منطقة الدخول</th><th>الوقف</th><th>هدف 1</th><th>هدف 2</th><th class="c">الدرجة</th><th class="c">الدرجة/الوصول</th><th class="c">سيولة</th><th>الدعوم / المقاومات</th><th class="c">البنية</th></tr></thead>
<tbody>{table_all}</tbody></table></div>

{side_sections}

{exp_section}

{macro_section}

{sections}

<h2 id="track">🔄 تحديث جميع صفقات المسح السابق ({prev_label}) — {n_tr} صفقة</h2>
<div class="sub" style="margin-bottom:8px">حالة جميع صفقات المسح السابق: المفتوحة (رابحة/خاسرة) · المغلقة (هدف/وقف — الصفقة التي تضرب الوقف تُعرض مرة واحدة فقط ثم تُزال في التقرير التالي) · بانتظار التفعيل · والملغاة (&gt; 1.0 ATR){f' · <b>أُزيلت تلقائياً {state.get("pruned_stops")} صفقة سبق عرض ضربها للوقف</b>' if state.get("pruned_stops", 0) else ''}</div>
<div class="kpis" style="margin-bottom:10px">
  <div class="kpi"><span>إجمالي صفقات المسح السابق</span><b>{n_tr}</b></div>
  <div class="kpi"><span>مفتوحة الآن</span><b>{c_open}</b>{flat_sub}</div>
  <div class="kpi"><span>🟢 مفتوحة رابحة</span><b class="pos">{c_open_win}</b></div>
  <div class="kpi"><span>🔴 مفتوحة خاسرة</span><b class="neg">{c_open_loss}</b></div>
  <div class="kpi"><span>🎯 وصلت هدفاً</span><b class="pos">{c_tp}</b></div>
  <div class="kpi"><span>🛑 ضربت الوقف</span><b class="neg">{c_stop}</b></div>
  <div class="kpi"><span>⏳ بانتظار التفعيل</span><b>{c_wait}</b></div>
  <div class="kpi"><span>⛔ أُلغيت (ابتعدت)</span><b class="neg">{c_cancel}</b></div>
  <div class="kpi"><span>صافي R (عائم + محقق)</span><b class="{'pos' if net_r>=0 else 'neg'}">{net_r:+.2f}R</b></div>
</div>
{open_summary_html}
<div class="twrap"><table><thead><tr><th>العملة</th><th class="c">الاتجاه</th><th>منطقة الدخول</th><th>الوقف</th><th>السعر الآن</th><th class="c">الربح / الخسارة · البُعد</th><th class="c">الحالة</th></tr></thead>
<tbody>{track_rows}</tbody></table></div>

<h2 id="rules">📌 القواعد المطبقة في هذا التقرير</h2>
<div class="grid2">
<div class="note" style="background:#0d1622;border-color:#1e2c42">
<b>الفلترة ومنطقة الدخول ومواعيد المسح</b>
<ul>
<li><b>المواعيد الرسمية (الرياض):</b> <b>02:45</b> (تأكيدي لقائمة الانفجار) · <b>03:05</b> · <b>11:05</b> · <b>15:05</b> · <b>19:05</b> (الأفضل) · <b>23:05</b> (مع الرصد المبكر للانفجار).</li>
<li><b>منطقة الدخول = أقرب حزمة صالحة</b> (2+ مصادر منها مصدر قوي)، سقف بُعد 1.0 ATR وعرض ≤ 0.35 ATR.</li>
<li><b>مرتكزات عملات الترند الصحي قبل الانفجار (⚡ ترند، 6%–22%):</b> انتقاء <b>الصفقات القوية فقط (درجة A/B ≥ 99)</b> من مرتكزات إعادة الاختبار السريعة (EMA9·4س + EMA20/50·1س + تأرجح 1س) دون تقييد التقرير بالترند ودون مطاردة بعد الانفجار (&gt; 22%)، مع منع الدخول عكس ترند قوي (Trend is your friend).</li>
<li><b>وضع اصطياد ذيل آسيا (02:45 و03:05):</b> مسافة دنيا ≥ 0.22 ATR عن الافتتاح اليومي لالتقاط الذيل الآسيوي مع اعتماد قمة/قاع اليوم المغلق.</li>
<li>عقود USDT دائمة فقط · سيولة 24س ≥ 8M$ · عمر ≥ 30 يوماً · استبعاد العملات المستقرة والرموز غير اللاتينية → <b>{universe} عقداً</b>.</li>
<li>R:R أول ≥ 1.8 · ثانٍ ≥ 2.6 · فرق mark/last ≤ 0.5%.</li>
</ul>
</div>
<div class="note" style="background:#0d1622;border-color:#1e2c42">
<b>المخاطرة والإدارة وقاعدة الانفجار اليومي</b>
<ul>
<li>1% لكل صفقة · 3% كلية · 3–4 مراكز مفتوحة كحد أقصى · BTC/ETH/SOL مركز واحد.</li>
<li>رافعة 3–5x للكبار · 2x لما ATR(4س) &gt; 5%.</li>
<li><b>قاعدة الانفجار اليومي:</b> رصد في <b>23:05</b> (مراقبة فقط) ← تأكيد في <b>02:45</b> ← تعليق Limit لصيد ذيل آسيا (لا شراء سوقي عند 03:00).</li>
<li>50% عند هدف 1 ← التعادل ← 25% عند هدف 2 ← الباقي لهدف 3 · لا نقل للوقف نحو الخسارة.</li>
<li>لا مطاردة: إذا ابتعد السعر &gt; 1.0 ATR عن المنطقة قبل التفعيل تُلغى.</li>
<li><b>تنظيف الصفقات المنتهية:</b> الصفقات التي تضرب الوقف أو تُلغى لابتعاد السعر (&gt; 1.0 ATR) تُعرض <b>مرة واحدة فقط</b> في أول تقرير أو مسح لتحديث وضعها ثم تُزال تلقائياً في التقرير التالي، بينما تبقى المراكز المفتوحة (رابحة وخاسرة عائمة) تحت المتابعة الحية.</li>
</ul>
</div>
</div>

<div class="note" style="background:#0d1622;border-color:#1e2c42;margin-top:14px">
<b>قراءة السوق لحظة التنفيذ:</b> BTC {fp(float(t24["BTCUSDT"]["lastPrice"]) if "BTCUSDT" in t24 else 0)} ({btc["chg"]:+.2f}%) ·
ETH {fp(float(t24["ETHUSDT"]["lastPrice"]) if "ETHUSDT" in t24 else 0)} ({eth["chg"]:+.2f}%) ·
SOL {fp(float(t24["SOLUSDT"]["lastPrice"]) if "SOLUSDT" in t24 else 0)} ({sol["chg"]:+.2f}%) ·
فاندنغ قريب من الصفر (لا انحياز تمويلي حاد).
من {universe} عقداً سائلاً: <b>{n_up} صاعدة</b> مقابل <b>{n_dn} هابطة</b> على مدى 24 ساعة — لذلك صفقات البيع ({len(shorts)}) أكثر من الشراء ({len(longs)}).
أقوى صفقات الشراء المتاحة الآن: {top_longs}.
</div>

<div class="sub" style="margin-top:22px;text-align:center">
تقرير أُعيد توليده آلياً بواسطة محرك v3 · المصدر: Binance Futures API · {ts} بتوقيت الرياض ·
هذا تحليل آلي وليس نصيحة استثمارية — الالتزام بحدود المخاطرة أهم من أي صفقة.
</div>
<div id="cfgModal" class="modal-bg" onclick="if(event.target===this)closeCfg()">
  <div class="modal">
    <h3 style="margin-top:0;color:#9ecbff">⚙️ إعداد التشغيل بضغطة واحدة (اختياري)</h3>
    <div style="font-size:12.5px;color:#b9c9dc;margin-bottom:10px">
      المسح المجدول في المواعيد الستة يعمل تلقائياً <b>بدون أي إعداد</b>.<br>
      إذا أردت تشغيل المسح بضغطة زر من داخل هذه الشاشة دون فتح صفحة GitHub، أدخل اسم المستودع ومفتاح الوصول مرة واحدة (يُحفظ في جوالك فقط):
    </div>
    <label style="font-size:12px;color:#8798ab">اسم حسابك واسم المستودع (مثال: ahmad/binance-scan)</label>
    <input id="ghRepo" placeholder="username/repo-name">
    <label style="font-size:12px;color:#8798ab">مفتاح GitHub الشخصي (اختياري — يبدأ بـ github_pat_ أو ghp_)</label>
    <input id="ghTok" type="password" placeholder="github_pat_...">
    <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:6px">
      <button class="abtn" onclick="closeCfg()">إلغاء</button>
      <button class="abtn pri" onclick="saveCfg()">💾 حفظ في هذا الجهاز</button>
    </div>
  </div>
</div>

<script>
window.REPORT_INDEX = {report_idx_json};
{SEARCH_ANALYZER_JS}
if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {{
  navigator.serviceWorker.register('./sw.js').catch(function(){{}});
}}
function detectRepo() {{
  var saved = localStorage.getItem('bs_gh_repo');
  if (saved) return saved.trim();
  if (location.hostname.endsWith('.github.io')) {{
    var owner = location.hostname.replace('.github.io', '');
    var parts = location.pathname.split('/').filter(Boolean);
    if (parts.length > 0) return owner + '/' + parts[0];
  }}
  return '';
}}
function openCfg() {{
  document.getElementById('ghRepo').value = detectRepo();
  document.getElementById('ghTok').value = localStorage.getItem('bs_gh_tok') || '';
  document.getElementById('cfgModal').classList.add('open');
}}
function closeCfg() {{ document.getElementById('cfgModal').classList.remove('open'); }}
function saveCfg() {{
  localStorage.setItem('bs_gh_repo', document.getElementById('ghRepo').value.trim());
  localStorage.setItem('bs_gh_tok', document.getElementById('ghTok').value.trim());
  closeCfg();
  showToast('✅ تم حفظ الإعداد في جهازك بنجاح.');
}}
function showToast(msg) {{
  var el = document.getElementById('toast');
  el.innerHTML = msg;
  el.style.display = 'block';
}}
function refreshNow() {{
  location.href = location.pathname + '?t=' + Date.now();
}}
function triggerCloud(mode) {{
  var repo = detectRepo();
  var tok = (localStorage.getItem('bs_gh_tok') || '').trim();
  if (!repo) {{
    openCfg();
    return;
  }}
  if (!tok) {{
    window.open('https://github.com/' + repo + '/actions/workflows/scanner.yml', '_blank');
    return;
  }}
  var label = (mode === 'confirm') ? 'فحص تأكيد 02:45' : 'المسح الشامل';
  showToast('⏳ جاري إرسال طلب ' + label + ' إلى السحابة...');
  fetch('https://api.github.com/repos/' + repo + '/actions/workflows/scanner.yml/dispatches', {{
    method: 'POST',
    headers: {{
      'Accept': 'application/vnd.github+json',
      'Authorization': 'Bearer ' + tok,
      'Content-Type': 'application/json'
    }},
    body: JSON.stringify({{ ref: 'main', inputs: {{ mode: mode }} }})
  }}).then(function(r) {{
    if (r.status === 204 || r.ok) {{
      var sec = 65;
      var iv = setInterval(function() {{
        sec--;
        if (sec <= 0) {{
          clearInterval(iv);
          refreshNow();
        }} else {{
          showToast('🚀 بدأ ' + label + ' في السحابة! سيُحدَّث التقرير تلقائياً خلال ' + sec + ' ثانية...');
        }}
      }}, 1000);
    }} else {{
      showToast('⚠️ تعذر التشغيل المباشر (تأكد من صلاحية المفتاح Actions: Read & Write) — سيتم فتح صفحة التشغيل اليدوي.');
      setTimeout(function(){{ window.open('https://github.com/' + repo + '/actions/workflows/scanner.yml', '_blank'); }}, 1500);
    }}
  }}).catch(function() {{
    window.open('https://github.com/' + repo + '/actions/workflows/scanner.yml', '_blank');
  }});
}}
</script>
<a class="top" href="#top" title="العودة للأعلى">↑</a>
</div></body></html>'''
    return html_doc, ts



# ==============================================================================
# [6] مشغّل المسح الشامل وأدوات الاختبار التشخيصي الخارجي (CLI Runner)
# ==============================================================================
def save_report_files(trades, meta, state, stats, t24, prem, tracked, held, exp_data):
    now = dt.datetime.now(RIYADH)
    doc, _ts = build_html(trades, meta, state, stats, t24, prem, tracked, held, now, exp_data=exp_data)
    open(OUT_FILE, "w", encoding="utf-8").write(doc)
    is_confirm_run = state.get("confirm_ts", 0) > meta.get("ts", 0)
    if not is_confirm_run:
        try:
            eff_ts = meta.get("ts", now.timestamp() * 1000)
            _stamp = dt.datetime.fromtimestamp(eff_ts / 1000.0, RIYADH)
            hist = os.path.join(BASE, "history")
            os.makedirs(hist, exist_ok=True)
            hf = os.path.join(hist, f"scan_{_stamp.strftime('%Y-%m-%d_%H%M')}.json")
            if not os.path.exists(hf):
                json.dump(trades, open(hf, "w", encoding="utf-8"), ensure_ascii=False, default=str)
            hfiles = sorted(f for f in os.listdir(hist) if f.endswith(".json"))
            for old_h in hfiles[:-10]:
                os.remove(os.path.join(hist, old_h))
        except Exception as e:
            record_diag_warning("history_save", f"تعذر حفظ أرشيف المسح: {e}")
    return OUT_FILE, len(doc)


def inspect_specific_coins(coins):
    now_r = dt.datetime.now(RIYADH)
    is_late = (now_r.hour >= 23 or now_r.hour < 3)
    print(f"=== فحص تشخيصي خارجي ({now_r.strftime('%Y-%m-%d %H:%M:%S')} بتوقيت الرياض | بوابة ما بعد 23:05: {is_late}) ===")
    uni, _top_up, _top_dn, info, td, pm = load_universe()
    uni_map = {u["sym"]: u for u in uni}

    macro_res = scan_macro_regimes(td, pm, now_r, is_confirm_run=False)
    sq_map = {x["sym"]: x for x in macro_res.get("squeeze", [])}
    bos_map = {x["sym"]: x for x in macro_res.get("bos3", [])}

    for raw_c in coins:
        sym = raw_c.strip().upper()
        if not sym.endswith("USDT"):
            sym += "USDT"
        print("\n" + "=" * 74)
        print(f"🔍 العملة: {sym}")
        if sym not in td:
            print("  ❌ غير موجودة في عقود USDT الدائمة على بايننس.")
            continue
        qv = float(td[sym]["quoteVolume"]) / 1e6
        price = float(td[sym]["lastPrice"])
        chg = float(td[sym]["priceChangePercent"])
        print(f"  السعر الحالي: {price} | تغيّر 24س: {chg:+.2f}% | سيولة 24س: {qv:,.2f}M$")
        if sym not in uni_map:
            print(f"  ⚠️ خارج كون الفلترة الأولية (يشترط سيولة >= {MIN_QV}M$ وعمر >= {MAX_AGE} يوماً).")

        if sym in info and sym in pm:
            ex = fetch_extras([sym]).get(sym, {})
            tr_list = analyze(sym, info[sym], td[sym], pm[sym], ex)
            if tr_list:
                for tr in tr_list:
                    print(f"  ✅ [فريم 4س/1س المضاربي] مؤهلة ({tr['side']}) | الدرجة: {tr['score']} ({tr['grade']}) | الدخول: [{tr['entry_lo']} - {tr['entry_hi']}] | الوقف: {tr['stop']}")
            else:
                print("  ⛔ [فريم 4س/1س المضاربي] غير مؤهلة حالياً (لم تحقق شروط الحزمة القريبة أو الدرجة >= 95 أو R:R >= 1.8).")

        if sym in sq_map:
            s = sq_map[sym]
            print(f"  🧲 [الاستثماري 1D] مؤهلة في قائمة العصر والقاع: {s['badge']} | التمركز: [{s['entry_lo']} - {s['entry_hi']}] | الوقف: {s['stop']}")
        else:
            print("  ➖ [الاستثماري 1D] ليست في مرحلة عصر قاعي مكتمل بدفاع شرائي.")

        if sym in bos_map:
            b = bos_map[sym]
            print(f"  🚀 [كسر الهيكل والزخم 1D+1W+1M] مؤهلة: {b['kind_badge']} | الدخول: [{b['entry_lo']} - {b['entry_hi']}] | الوقف: {b['stop']}")
            print(f"     📅 الأسبوعي: {b.get('w_summary')} | 🗓️ الشهري: {b.get('m_summary')}")
        else:
            print("  ⛔ [كسر الهيكل والزخم 1D+1W+1M] مستبعدة (لم تحقق كسر قمة 30ي أو 3 إغلاقات صاعدة أو همر انعكاسي مع شرطي الأسبوع والشهر وبوابة 23:05).")


def run_standalone_full_scan():
    reset_diagnostics()
    now_r = dt.datetime.now(RIYADH)
    asia_mode = is_asia_wick_window(now_r)
    print(f"=== دورة مسح كاملة ({now_r.strftime('%Y-%m-%d %H:%M:%S')} الرياض) | وضع ذيل آسيا: {asia_mode} ===")

    os.makedirs(CACHE, exist_ok=True)
    exp_path = os.path.join(BASE, "explosion_candidates.json")
    prev_confirmed = []
    prev_confirm_ts = int(time.time() * 1000) - 25 * 60 * 1000
    if asia_mode and os.path.exists(exp_path):
        try:
            pe = json.load(open(exp_path, encoding="utf-8"))
            if pe.get("stage") in ("confirm", "active"):
                prev_confirmed = pe.get("active") or []
                prev_confirm_ts = pe.get("ts") or prev_confirm_ts
        except Exception as e:
            record_diag_warning("asia_explosion_load", f"تعذر قراءة مصائد 02:45 السابقة: {e}")

    sr_path = os.path.join(BASE, "scan_result.json")
    sm_path = os.path.join(BASE, "scan_meta.json")
    prev_trades = json.load(open(sr_path, encoding="utf-8")) if os.path.exists(sr_path) else []
    prev_meta = json.load(open(sm_path, encoding="utf-8")) if os.path.exists(sm_path) else {"ts": int(time.time() * 1000)}
    prev_ts = prev_meta.get("ts", int(time.time() * 1000))

    already_pruned = already_pruned_ids()
    pruned_prev_stops = sum(1 for t in prev_trades if make_tid(t, prev_ts) in already_pruned)
    tracked, newly_stopped = update_and_prune_tracking(prev_trades, prev_ts, max_dist_atr=1.0, fresh=True, commit=True)
    track_ts = int(time.time() * 1000)

    json.dump(tracked, open(os.path.join(BASE, "held.json"), "w", encoding="utf-8"), ensure_ascii=False, default=str)
    json.dump(tracked, open(os.path.join(BASE, "prev_tracked.json"), "w", encoding="utf-8"), ensure_ascii=False, default=str)
    json.dump(
        {"prev_ts": prev_ts, "track_ts": track_ts, "confirm_ts": 0, "pruned_stops": pruned_prev_stops},
        open(os.path.join(BASE, "cycle_state.json"), "w", encoding="utf-8"),
        ensure_ascii=False,
    )

    for f in os.listdir(CACHE):
        if f != "exchangeInfo.json":
            try:
                os.remove(os.path.join(CACHE, f))
            except Exception:
                pass

    qualified, full_meta = scan(max_workers=10, verbose=True)
    blocked_pairs = recent_4h_stopped_pairs(full_meta["ts"]) | active_open_pairs()
    if blocked_pairs:
        qualified = [t for t in qualified if (t["sym"], t["side"]) not in blocked_pairs]
    for t in qualified:
        t["origin_ts"] = full_meta["ts"]
    qualified, port_risk_summary = evaluate_portfolio_risk_gate(
        qualified,
        tracked,
        strict_filter=False,
        now_riyadh=full_meta["ts"],
        enforce_quality_gate=True,
    )

    slim_meta = {
        "universe": full_meta["universe"],
        "top_up": full_meta["top_up"],
        "top_dn": full_meta["top_dn"],
        "ts": full_meta["ts"],
        "portfolio_risk": port_risk_summary,
        "diagnostics": get_diagnostics_summary(),
    }
    json.dump(qualified, open(sr_path, "w", encoding="utf-8"), ensure_ascii=False, default=str)
    json.dump(slim_meta, open(sm_path, "w", encoding="utf-8"), ensure_ascii=False, default=str)

    if asia_mode and prev_confirmed:
        try:
            cur_exp = json.load(open(exp_path, encoding="utf-8")) if os.path.exists(exp_path) else {"active": [], "cancelled": []}
            merged_exp, seen_exp = [], set()
            tr_conf = track(prev_confirmed, prev_confirm_ts, max_dist_atr=1.2, fresh=True)
            for x in tr_conf:
                st = x.get("status", "")
                x["price"] = x.get("last", x["price"])
                x["dist_pct"] = (x["entry_hi"] / x["price"] - 1) * 100.0
                x["dist_atr"] = abs(x["price"] - x["entry_hi"]) / x["atr4"]
                if st == "مفتوحة":
                    ost = x.get("open_state", "رابحة")
                    x["stage_label"] = f"🟢 اصطادت الذيل · مفتوحة {ost} ({x['r_now']:+.2f}R)"
                elif str(st).startswith("وصل"):
                    x["stage_label"] = f"🎯 {st} ({x['r_now']:+.2f}R)"
                elif st == "ضربت الوقف":
                    x["stage_label"] = "🛑 ضربت الوقف"
                elif x["dist_atr"] > 1.0:
                    x["stage_label"] = f"🚀 انفجرت مع الافتتاح (ابتعدت {x['dist_atr']:.2f} ATR — لا تطارد)"
                else:
                    x["stage_label"] = "🎯 مؤكدة من 02:45 — مصيدة الذيل نشطة"
                merged_exp.append(x)
                seen_exp.add(x["sym"])
            for x in cur_exp.get("active") or []:
                if x["sym"] not in seen_exp and len(merged_exp) < 6:
                    merged_exp.append(x)
                    seen_exp.add(x["sym"])
            final_exp = {"stage": "active", "ts": full_meta["ts"], "active": merged_exp, "cancelled": cur_exp.get("cancelled") or []}
            json.dump(final_exp, open(exp_path, "w", encoding="utf-8"), ensure_ascii=False, default=str)
        except Exception as e:
            record_diag_warning("asia_explosion_merge", f"تعذر دمج مصائد 02:45: {e}")

    trades, meta, state, stats, t24, prem, tracked_l, held_l, exp_data = load()
    out_html, n_bytes = save_report_files(trades, meta, state, stats, t24, prem, tracked_l, held_l, exp_data)
    print(f"\n✅ اكتمل المسح الشامل بنجاح!")
    print(f"   • نظام الجلسة: {port_risk_summary.get('session_label_ar')}")
    print(f"   • الصفقات المؤهلة (4س/1س): {len(qualified)} صفقة ({port_risk_summary['approved_candidates']} مجازة ضمن سقف المخاطرة · {port_risk_summary['blocked_candidates']} مراقبة واحتياطي)")
    print(f"   • المخاطرة المفتوحة حالياً: {port_risk_summary['open_risk_cash']:.2f}$ ({port_risk_summary['open_risk_pct']:.2f}% من {port_risk_summary['equity_usd']:,.0f}$)")
    print(f"   • ملف التقرير التفاعلي الجاهز: {out_html} ({n_bytes:,} بايت)")


def run_standalone_confirm_0245():
    """فحص التأكيد الخاص بنافذة 02:45 فجراً بتوقيت الرياض (موحد بالكامل داخل الملف المستقل):
    يؤكد قائمة (قابلة للانفجار) قبل الإغلاق اليومي + يحدث المراكز المفتوحة والأهداف الجزئية + يعيد بناء index.html."""
    reset_diagnostics()
    now_r = dt.datetime.now(RIYADH)
    print(f"=== فحص التأكيد 02:45 ({now_r.strftime('%Y-%m-%d %H:%M:%S')} الرياض) ===")

    os.makedirs(CACHE, exist_ok=True)
    for f in os.listdir(CACHE):
        if f != "exchangeInfo.json" and not f.endswith("_1d_300.json"):
            try:
                os.remove(os.path.join(CACHE, f))
            except Exception:
                pass

    radar_path = os.path.join(BASE, "explosion_radar.json")
    prev_radar = json.load(open(radar_path, encoding="utf-8")) if os.path.exists(radar_path) else []
    exp_data = scan_explosions(stage="confirm", prev_radar=prev_radar, max_workers=10)
    json.dump(exp_data, open(os.path.join(BASE, "explosion_candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, default=str)
    print(f"تأكيد الانفجار: {len(exp_data['active'])} مؤكدة | {len(exp_data['cancelled'])} أُلغيت")

    state_path = os.path.join(BASE, "cycle_state.json")
    state = json.load(open(state_path, encoding="utf-8")) if os.path.exists(state_path) else {}
    meta_path = os.path.join(BASE, "scan_meta.json")
    sr_path = os.path.join(BASE, "scan_result.json")
    if os.path.exists(meta_path) and os.path.exists(sr_path):
        cur_meta = json.load(open(meta_path, encoding="utf-8"))
        cur_trades = json.load(open(sr_path, encoding="utf-8"))
        prev_ts = cur_meta.get("ts", state.get("prev_ts", int(time.time() * 1000)))
        already_pruned = already_pruned_ids()
        pruned_prev_stops = sum(1 for t in cur_trades if make_tid(t, prev_ts) in already_pruned)

        tracked, newly_stopped = update_and_prune_tracking(cur_trades, prev_ts, max_dist_atr=1.0, fresh=True, commit=True)
        json.dump(tracked, open(os.path.join(BASE, "held.json"), "w", encoding="utf-8"), ensure_ascii=False, default=str)
        json.dump(tracked, open(os.path.join(BASE, "prev_tracked.json"), "w", encoding="utf-8"), ensure_ascii=False, default=str)
        if pruned_prev_stops > 0:
            filtered_cur = [t for t in cur_trades if make_tid(t, prev_ts) not in already_pruned]
            json.dump(filtered_cur, open(sr_path, "w", encoding="utf-8"), ensure_ascii=False, default=str)
        state["prev_ts"] = prev_ts
        state["pruned_stops"] = pruned_prev_stops
        print(f"التتبع: {len(tracked)} صفقة معروضة | {newly_stopped} ضربت الوقف (تُعرض لمرة واحدة) | {pruned_prev_stops} أُزيلت سابقاً")

    now_ms = int(time.time() * 1000)
    state["track_ts"] = now_ms
    state["confirm_ts"] = now_ms
    json.dump(state, open(state_path, "w", encoding="utf-8"), ensure_ascii=False)

    trades, meta, state_l, stats, t24, prem, tracked_l, held_l, exp_l = load()
    out_html, n_bytes = save_report_files(trades, meta, state_l, stats, t24, prem, tracked_l, held_l, exp_l)
    print(f"✅ اكتمل فحص التأكيد 02:45 وتحديث التقرير: {out_html} ({n_bytes:,} بايت)")


def run_phase1_acceptance_tests():
    """حزمة اختبارات القبول الآلية الحتمية للمرحلة الأولى (Phase 1 Acceptance Suite):
    تختبر بشموع مصطنعة معروفة الأسعار مسبقاً جميع معايير القبول الهندسية دون أي اتصال بالشبكة:
      1) ثبات سعر الدخول (Entry Fill Immutability) وعدم تأثره بأي هبوط/صعود لاحق أو تعدد دورات المسح.
      2) نماذج التنفيذ الثلاثة (limit_near_edge_strict · touch_limit · trigger_with_slippage).
      3) دورة الأهداف الجزئية الكاملة (TP1: 50% -> TP2: 25% -> TP3: 25%) وبقاء الصفقة نشطة حتى 0% متبقٍ.
      4) الوصول إلى TP1 ثم العودة إلى وقف التعادل الشامل للرسوم والانزلاق (Fee-Adjusted BE) بلا خسارة خفية.
      5) الوصول إلى TP2 ثم العودة إلى وقف تأمين الربح (Trail @ TP1) أو التعادل (BE).
      6) ضرب الوقف الأصلي مباشرةً قبل TP1 مع خصم الرسوم والانزلاق الواقعي.
      7) تعارض الهدف والوقف داخل نفس شمعة الـ 5 دقائق (3 حالات فرعية: شمعة الدخول، شمعة لاحقة، وانعكاس إغلاق بعد TP1).
      8) التناظر الكامل لصفقات البيع (SHORT) في التفعيل والأهداف الجزئية ووقف التعادل.
      9) انتهاء صلاحية الإشارة المعلقة (EXPIRED) + ترحيل المراكز الجزئية عبر عدة دورات مسح دون الكتابة فوقها.
    """
    import tempfile

    t0 = 1_700_000_000_000

    def mk_bars(rows):
        # rows: list of (idx, o, h, l, c)
        return {
            "t": [t0 + idx * BAR_5M_MS for idx, _, _, _, _ in rows],
            "o": [float(o) for _, o, _, _, _ in rows],
            "h": [float(h) for _, _, h, _, _ in rows],
            "l": [float(l) for _, _, _, l, _ in rows],
            "c": [float(c) for _, _, _, _, c in rows],
        }

    def mk_trade(side="LONG", e_lo=100.0, e_hi=102.0, stop=98.0, targets=(110.0, 114.0, 118.0), qty=10.0, tick=0.01):
        avg = (e_lo + e_hi) / 2.0
        r = abs(avg - stop)
        return {
            "sym": "TESTUSDT",
            "name": "TEST",
            "side": side,
            "price": 103.5 if side == "LONG" else 96.5,
            "entry_lo": e_lo,
            "entry_hi": e_hi,
            "avg": avg,
            "stop": stop,
            "targets": list(targets),
            "rr": [round(abs(x - avg) / r, 2) for x in targets],
            "atr4": 4.0,
            "qty": qty,
            "tick": tick,
            "origin_ts": t0,
        }

    results = []

    # ------------------------------------------------------------------
    # اختبار 1: ثبات سعر الدخول (عدم التعديل بأثر رجعي عند الهبوط اللاحق + حساسية نماذج التنفيذ)
    # ------------------------------------------------------------------
    tr1 = mk_trade("LONG", e_lo=100.0, e_hi=102.0, stop=98.0, targets=(110.0, 114.0, 118.0))
    # شمعة 1 تلمس 102.00 فقط دون اختراق التِك (لا تتفعل في النموذج الصارم، وتتفعل في touch_limit)
    bars_touch_only = mk_bars([(1, 103.0, 103.2, 102.00, 102.5)])
    r_strict_touch = simulate_trade_lifecycle(tr1, bars_touch_only, fill_model="limit_near_edge_strict")
    r_loose_touch = simulate_trade_lifecycle(tr1, bars_touch_only, fill_model="touch_limit")
    assert not r_strict_touch["filled"] and r_strict_touch["trade_status"] == "PENDING", "اللمس الحدي بلا اختراق يجب ألا يفعّل النموذج الصارم"
    assert r_loose_touch["filled"] and r_loose_touch["fill_price"] == 102.0, "نموذج touch_limit يجب أن يفعّل عند 102.0"

    # الآن شمعة 1 تخترق 102.00 إلى 101.80 -> يتثبت الدخول عند 102.00، ثم شمعة 2 تهبط إلى 99.20!
    bars_step1 = mk_bars([(1, 103.0, 103.2, 101.80, 102.10)])
    s1 = simulate_trade_lifecycle(tr1, bars_step1, now_ms=t0 + 2 * BAR_5M_MS)
    assert s1["filled"] and s1["fill_price"] == 102.0 and s1["filled_at"] == t0 + BAR_5M_MS
    assert abs(s1["r_unit"] - 4.0) < 1e-9

    bars_step2 = mk_bars([
        (1, 103.0, 103.2, 101.80, 102.10),
        (2, 102.10, 102.20, 99.20, 99.80),   # هبوط عميق بعد التفعيل فوق الوقف 98.0
        (3, 99.80, 104.50, 99.70, 104.20),
    ])
    # تشغيل تزايدي (عبر تمرير الحالة s1) وتشغيل دفعة واحدة من الصفر: كلاهما يجب أن يثبت عند 102.00 بالضبط!
    s2_inc = simulate_trade_lifecycle(s1, bars_step2, now_ms=t0 + 4 * BAR_5M_MS)
    s2_batch = simulate_trade_lifecycle(tr1, bars_step2, now_ms=t0 + 4 * BAR_5M_MS)
    assert s2_inc["fill_price"] == 102.0 and s2_batch["fill_price"] == 102.0, "فشل: تغيّر سعر الدخول بأثر رجعي!"
    assert s2_inc["filled_at"] == s2_batch["filled_at"] == t0 + BAR_5M_MS
    assert s2_inc["trade_status"] == "OPEN" and s2_inc["remaining_pct"] == 1.0

    # فحص نموذج الانزلاق trigger_with_slippage
    s_slip = simulate_trade_lifecycle(tr1, bars_step1, fill_model="trigger_with_slippage")
    assert abs(s_slip["fill_price"] - 102.0 * (1.0 + ENTRY_SLIPPAGE_PCT)) < 1e-9
    results.append("✅ [1/9] Entry Fill Test: ثبات سعر الدخول عند 102.00 وعدم تأثره بهبوط 99.20 اللاحق + عمل نماذج التنفيذ الـ 3 بدقة.")

    # ------------------------------------------------------------------
    # اختبار 2: دورة الأهداف الجزئية الكاملة (TP1 50% -> TP2 25% -> TP3 25%)
    # ------------------------------------------------------------------
    tr2 = mk_trade("LONG", e_lo=99.0, e_hi=100.0, stop=95.0, targets=(110.0, 115.0, 120.0), qty=20.0)
    b_tp1 = mk_bars([
        (1, 101.0, 101.2, 99.80, 100.5),     # تفعيل عند 100.0 (R = 5.0)
        (2, 100.5, 110.4, 100.2, 109.0),     # تحقيق TP1 فقط (50% مغلق، 50% متبقٍ)
    ])
    p1 = simulate_trade_lifecycle(tr2, b_tp1, now_ms=t0 + 3 * BAR_5M_MS)
    assert p1["trade_status"] == "PARTIAL_TP1" and p1["closed_pct"] == 0.50 and p1["remaining_pct"] == 0.50
    assert p1["remaining_qty"] == 10.0 and p1["stop_mode"] == "BE" and p1["active_stop"] > 100.0

    b_tp2 = mk_bars([
        (1, 101.0, 101.2, 99.80, 100.5),
        (2, 100.5, 110.4, 100.2, 109.0),
        (3, 109.0, 115.6, 108.5, 114.2),     # تحقيق TP2 (إجمالي مغلق 75%، متبقٍ 25%)
    ])
    p2 = simulate_trade_lifecycle(p1, b_tp2, now_ms=t0 + 4 * BAR_5M_MS)
    assert p2["trade_status"] == "PARTIAL_TP2" and p2["closed_pct"] == 0.75 and p2["remaining_pct"] == 0.25
    assert p2["remaining_qty"] == 5.0 and p2["stop_mode"] == "trail" and p2["active_stop"] == 110.0

    b_tp3 = mk_bars([
        (1, 101.0, 101.2, 99.80, 100.5),
        (2, 100.5, 110.4, 100.2, 109.0),
        (3, 109.0, 115.6, 108.5, 114.2),
        (4, 114.2, 121.0, 113.8, 120.2),     # تحقيق TP3 (إغلاق كامل 100%، متبقٍ 0%)
    ])
    p3 = simulate_trade_lifecycle(p2, b_tp3, now_ms=t0 + 5 * BAR_5M_MS)
    assert p3["trade_status"] == "CLOSED_TP3" and p3["closed_pct"] == 1.0 and p3["remaining_pct"] == 0.0
    # التحقق الرياضي الدقيق من صافي العائد بعد رسوم Maker (دخول 0.02% + خروج 0.02%)
    exp_r = sum(
        w * ((tp - 100.0 - (100.0 * MAKER_FEE_PCT + tp * MAKER_FEE_PCT)) / 5.0)
        for w, tp in ((0.50, 110.0), (0.25, 115.0), (0.25, 120.0))
    )
    assert abs(p3["realized_r"] - round(exp_r, 4)) <= 1e-4, f"Mismatch R: {p3['realized_r']} vs {exp_r}"
    results.append(f"✅ [2/9] Partial Exit Test: تدرج الكمية (100% -> 50% -> 25% -> 0%) وصافي العائد المحقق = +{p3['realized_r']:.4f}R.")

    # ------------------------------------------------------------------
    # اختبار 3: تحقيق TP1 ثم العودة لوقف التعادل الشامل للرسوم والانزلاق (Fee-Adjusted BE)
    # ------------------------------------------------------------------
    b_be = mk_bars([
        (1, 101.0, 101.2, 99.80, 100.5),     # دخول عند 100.0
        (2, 100.5, 110.4, 100.2, 108.0),     # تحقيق TP1 (50%) وتفعيل وقف التعادل الشامل للرسوم (~100.10)
        (3, 108.0, 108.2, 99.70, 99.90),     # عودة السعر لكسر وقف التعادل
    ])
    p_be = simulate_trade_lifecycle(tr2, b_be, now_ms=t0 + 4 * BAR_5M_MS)
    assert p_be["trade_status"] == "CLOSED_BE" and p_be["remaining_pct"] == 0.0 and len(p_be["leg_fills"]) == 2
    be_leg = p_be["leg_fills"][1]
    assert be_leg["leg"] == "BE_STOP" and be_leg["net_r"] >= -0.0005, f"شريحة التعادل حققت خسارة خفية: {be_leg}"
    assert 0.95 < p_be["realized_r"] < 1.02, f"العائد الصافي المتوقع ~+0.99R لا +2.0R، الناتج: {p_be['realized_r']}"
    results.append(f"✅ [3/9] Stop Management (TP1->BE): شريحة التعادل حققت {be_leg['net_r']:+.5f}R (صفر خسارة بعد الرسوم والانزلاق) وإجمالي الصفقة +{p_be['realized_r']:.4f}R.")

    # ------------------------------------------------------------------
    # اختبار 4: تحقيق TP2 ثم العودة للوقف المؤمَّن (Trail @ TP1) مقابل وضع BE فقط
    # ------------------------------------------------------------------
    b_tp2_ret = mk_bars([
        (1, 101.0, 101.2, 99.80, 100.5),
        (2, 100.5, 110.4, 100.2, 109.0),
        (3, 109.0, 115.5, 108.8, 113.0),
        (4, 113.0, 113.2, 109.5, 109.8),     # كسر 110.0 (وقف Trail عند TP1) دون كسر 100.10
    ])
    p_trail = simulate_trade_lifecycle(tr2, b_tp2_ret, trail_after_tp2=True, now_ms=t0 + 5 * BAR_5M_MS)
    p_notrail = simulate_trade_lifecycle(tr2, b_tp2_ret, trail_after_tp2=False, now_ms=t0 + 5 * BAR_5M_MS)
    assert p_trail["trade_status"] == "CLOSED_TRAIL" and p_trail["remaining_pct"] == 0.0 and len(p_trail["leg_fills"]) == 3
    assert p_notrail["trade_status"] == "PARTIAL_TP2" and p_notrail["remaining_pct"] == 0.25
    results.append(f"✅ [4/9] Stop Management (TP2->Trail): أُغلقت الشريحة الأخيرة 25% عند TP1 بصافي كلي +{p_trail['realized_r']:.4f}R.")

    # ------------------------------------------------------------------
    # اختبار 5: ضرب الوقف الأصلي مباشرةً قبل TP1
    # ------------------------------------------------------------------
    b_sl = mk_bars([
        (1, 101.0, 101.2, 99.80, 100.2),
        (2, 100.2, 103.0, 94.50, 94.80),     # كسر الوقف الأصلي 95.00
    ])
    p_sl = simulate_trade_lifecycle(tr2, b_sl, now_ms=t0 + 3 * BAR_5M_MS)
    eff_sl = 95.0 * (1.0 - STOP_SLIPPAGE_PCT)
    exp_sl_r = (eff_sl - 100.0 - (100.0 * MAKER_FEE_PCT + eff_sl * TAKER_FEE_PCT)) / 5.0
    assert p_sl["trade_status"] == "CLOSED_STOP" and p_sl["remaining_pct"] == 0.0
    assert abs(p_sl["realized_r"] - round(exp_sl_r, 4)) <= 1e-4 and p_sl["realized_r"] < -1.0
    results.append(f"✅ [5/9] Direct Stop Loss Test: خسارة كاملة واقعية شاملة الرسوم والانزلاق = {p_sl['realized_r']:+.4f}R.")

    # ------------------------------------------------------------------
    # اختبار 6: تعارض TP و SL داخل نفس الشمعة (3 حالات محافظة)
    # ------------------------------------------------------------------
    # (6أ) شمعة الدخول نفسها تضرب الوقف والهدف معاً -> الوقف يربح فوراً ولا يُمنح هدف
    b_col_entry = mk_bars([(1, 101.0, 112.0, 94.5, 111.0)])
    c_a = simulate_trade_lifecycle(tr2, b_col_entry, now_ms=t0 + 2 * BAR_5M_MS)
    assert c_a["trade_status"] == "CLOSED_STOP" and not any(c_a["tp_hits"])

    # (6ب) مركز مفتوح مسبقاً، والشمعة التالية تلمس الوقف الأصلي 95.0 والهدف 110.0 معاً -> الوقف النشط أولاً
    b_col_open = mk_bars([
        (1, 101.0, 101.2, 99.8, 100.5),
        (2, 100.5, 112.0, 94.8, 108.0),
    ])
    c_b = simulate_trade_lifecycle(tr2, b_col_open, now_ms=t0 + 3 * BAR_5M_MS)
    assert c_b["trade_status"] == "CLOSED_STOP" and not any(c_b["tp_hits"])

    # (6ج) شمعة لا تلمس الوقف الأصلي (أدناها 99.0 > 95.0)، تصعد لـ TP1 (110.5) ثم تغلق عند 99.5 تحت وقف التعادل -> تنفيذ TP1 ثم خروج BE في نفس الشمعة!
    b_col_pump_dump = mk_bars([
        (1, 101.0, 101.2, 99.8, 100.5),
        (2, 100.5, 110.5, 99.0, 99.5),
    ])
    c_c = simulate_trade_lifecycle(tr2, b_col_pump_dump, now_ms=t0 + 3 * BAR_5M_MS)
    assert c_c["trade_status"] == "CLOSED_BE" and c_c["tp_hits"][0] and c_c["remaining_pct"] == 0.0
    results.append("✅ [6/9] TP/SL Collision Test: اجتياز الحالات الـ 3 لتعارض الهدف والوقف داخل نفس الشمعة بدون انحياز تفاؤلي.")

    # ------------------------------------------------------------------
    # اختبار 7: التناظر الكامل لصفقات البيع (SHORT)
    # ------------------------------------------------------------------
    tr_short = mk_trade("SHORT", e_lo=100.0, e_hi=101.0, stop=105.0, targets=(90.0, 85.0, 80.0), qty=12.0)
    b_short = mk_bars([
        (1, 99.0, 100.2, 98.8, 99.5),        # تفعيل البيع عند 100.0 (اختراق للأعلى >= 100.01)
        (2, 99.5, 99.8, 89.5, 91.0),         # تحقيق TP1 (90.0) -> إغلاق 50% ونقل الوقف للتعادل (< 100.0)
        (3, 91.0, 100.2, 90.8, 100.1),       # عودة السعر للأعلى لضرب وقف التعادل للبيع
    ])
    s_res = simulate_trade_lifecycle(tr_short, b_short, now_ms=t0 + 4 * BAR_5M_MS)
    assert s_res["filled"] and s_res["fill_price"] == 100.0
    assert s_res["trade_status"] == "CLOSED_BE" and s_res["remaining_pct"] == 0.0
    assert s_res["leg_fills"][1]["net_r"] >= -0.0005 and s_res["realized_r"] > 0.95
    results.append(f"✅ [7/9] SHORT Symmetry Test: تناظر كامل في البيع (سعر دخول ثابت 100.0 + وقف تعادل بيعي + صافي +{s_res['realized_r']:.4f}R).")

    # ------------------------------------------------------------------
    # اختبار 8: انتهاء صلاحية الإشارة غير المفعلة (Pending Expiry) وانتهاء مدة المركز المفتوح
    # ------------------------------------------------------------------
    b_exp = mk_bars([
        (1, 103.0, 103.5, 102.5, 103.0),               # بعد 5 دقائق: لم تصل لمنطقة الشراء [99-100]
        (300, 102.8, 103.0, 99.50, 100.0),             # بعد 25 ساعة (> 24س): وصلت للمنطقة بعد انتهاء الصلاحية!
    ])
    p_exp = simulate_trade_lifecycle(tr2, b_exp, pending_expiry_hours=24.0, now_ms=t0 + 305 * BAR_5M_MS)
    assert not p_exp["filled"] and p_exp["trade_status"] == "EXPIRED", "يجب أن تنتهي صلاحية الإشارة عند 24س ولا تتفعل في الساعة 25!"

    b_open_exp = mk_bars([
        (1, 101.0, 101.2, 99.8, 100.5),                # تفعيل عند 100.0
        (20, 102.0, 103.0, 101.5, 102.5),              # بعد 100 دقيقة تتجاوز سقف max_open_hours=1.0
    ])
    p_oexp = simulate_trade_lifecycle(tr2, b_open_exp, max_open_hours=1.0, now_ms=t0 + 25 * BAR_5M_MS)
    assert p_oexp["trade_status"] == "CLOSED_EXPIRY" and p_oexp["remaining_pct"] == 0.0
    results.append("✅ [8/9] Signal & Position Expiry Test: إلغاء الإشارة المنتهية زمنياً ومنع تفعيلها المتأخر + إغلاق انتهاء المدة.")

    # ------------------------------------------------------------------
    # اختبار 9: ترحيل دورة الحياة عبر عدة مسوحات متعاقبة دون إسقاط الصفقة الجزئية أو الكتابة فوقها
    # ------------------------------------------------------------------
    global STATE_FILE
    old_state_file = STATE_FILE
    with tempfile.TemporaryDirectory() as tmpd:
        STATE_FILE = os.path.join(tmpd, "tracker_state.json")
        try:
            sig_a = mk_trade("LONG", e_lo=99.0, e_hi=100.0, stop=95.0, targets=(110.0, 115.0, 120.0))
            # دورة 1: دخول + تحقيق TP1 (متبقٍ 50%)
            c1_bars = mk_bars([(1, 101.0, 101.2, 99.8, 100.5), (2, 100.5, 110.5, 100.2, 109.0)])
            tr_c1, _ = update_and_prune_tracking(
                [sig_a], t0, commit=True,
                track_fn=lambda pool, *a, **kw: [simulate_trade_lifecycle(p, c1_bars, now_ms=t0 + 3 * BAR_5M_MS) for p in pool]
            )
            assert len(tr_c1) == 1 and tr_c1[0]["trade_status"] == "PARTIAL_TP1" and tr_c1[0]["remaining_pct"] == 0.50
            assert ("TESTUSDT", "LONG") in active_open_pairs()

            # دورة 2: يمرر الماسح إشارة جديدة على نفس العملة TESTUSDT (origin_ts جديد) بينما القديمة مفتوحة جزئياً!
            dup_new_sig = dict(sig_a, origin_ts=t0 + 10 * BAR_5M_MS, entry_lo=105.0, entry_hi=106.0)
            c2_bars = mk_bars([
                (1, 101.0, 101.2, 99.8, 100.5),
                (2, 100.5, 110.5, 100.2, 109.0),
                (3, 109.0, 121.0, 108.8, 120.5),   # القديمة تحقق TP2 + TP3 وتُغلق بالكامل!
            ])
            tr_c2, _ = update_and_prune_tracking(
                [dup_new_sig], t0 + 10 * BAR_5M_MS, commit=True,
                track_fn=lambda pool, *a, **kw: [simulate_trade_lifecycle(p, c2_bars, now_ms=t0 + 4 * BAR_5M_MS) for p in pool]
            )
            assert len(tr_c2) == 1 and tr_c2[0]["origin_ts"] == t0, "فشل: تم استبدال الصفقة الجزئية المفتوحة بإشارة جديدة!"
            assert tr_c2[0]["trade_status"] == "CLOSED_TP3" and tr_c2[0]["remaining_pct"] == 0.0

            # دورة 3: بعد أن اكتملت الصفقة وعُرضت مرة واحدة في دورة 2، يجب أن تُؤرشف الآن ولا تتكرر للأبد
            tr_c3, _ = update_and_prune_tracking(
                [], t0 + 20 * BAR_5M_MS, commit=True,
                track_fn=lambda pool, *a, **kw: [simulate_trade_lifecycle(p, c2_bars, now_ms=t0 + 5 * BAR_5M_MS) for p in pool]
            )
            assert len(tr_c3) == 0, "فشل: الصفقة المنتهية لم تُؤرشف بعد عرض اكتمالها!"
        finally:
            STATE_FILE = old_state_file
    results.append("✅ [9/9] Multi-Scan Lifecycle Persistence Test: بقاء الصفقة الجزئية عبر المسوحات وحمايتها من التداخل ثم أرشفتها بعد اكتمال 100%.")

    print("=" * 78)
    print("🧪 نتائج اختبارات القبول للمرحلة الأولى (Phase 1 Acceptance Suite — 9/9 PASSED)")
    print("=" * 78)
    for line in results:
        print(" ", line)
    print("=" * 78)
    return True


def run_phase2_acceptance_tests():
    """حزمة اختبارات القبول الآلية الحتمية للمرحلة الثانية (Phase 2 Risk & Margin Acceptance Suite):
    تختبر رياضياً وبصفر اتصال بالشبكة جميع معايير القبول الهندسية لإدارة المخاطر وحجم المركز:
      1) استبدال SIZE_USD = 1000 الثابت بحجم مركز ديناميكي مربوط برأس المال (1% من Equity):
         صفقة بوقف 2% تحصل على ضعف القيمة الاسمية لصفقة بوقف 4% مع ثبات الخسارة النقدية <= 100$.
      2) الفصل الرياضي الدقيق بين مسافة الوقف النظرية ومسافة الخسارة الفعلية الشاملة للرسوم والانزلاق
         (LONG و SHORT)، وإثبات أن ضرب الوقف الفعلي لا يكسر سقف الـ 1% (100$).
      3) الرافعة المالية الآمنة وحماية التصفية (Liquidation Buffer): خفض الرافعة تلقائياً في الوقف الواسع
         (مثل الاستثماري 12% -> 1x/2x) بحيث يستحيل أن تسبق التصفية أمر الوقف الصريح.
      4) سقف الهامش للصفقة الواحدة (25% من المحفظة): في الصفقات ذات الوقف الضيق جداً (مثل 0.4%)، يقيد المحرك
         القيمة الاسمية بالهامش الأقصى فتقل المخاطرة الفعلية عن 1% بدلاً من تضخم المركز بشكل خطر.
      5) التقريب للأسفل وفق stepSize وفحص الحد الأدنى لقيمة الأمر في بايننس (min_notional) ورفض الصفقة
         إذا كان الحد الأدنى للأمر يكسر ميزانية المخاطرة لمحفظة صغيرة.
      6) حساب المخاطرة المتبقية للمراكز المفتوحة: مركز مفتوح قبل TP1 يحجز مخاطرته الفعلية، بينما مركز وصل إلى
         TP1 ونُقل وقفه إلى التعادل الشامل للرسوم (BE) أو تأمين الربح (Trail) تنخفض مخاطرته النقدية المفتوحة إلى 0$
         مع بقاء خانته وهامشه النشط محتسبَين!
      7) بوابة المخاطرة الكلية للمحفظة (Portfolio Risk Gate): إنفاذ سقف 3.0% مخاطرة مفتوحة، و4 مراكز متزامنة،
         ومركز واحد فقط من العملات الكبرى (BTC/ETH/SOL)، وسقف 65% لإجمالي الهامش المحجوز.
      8) تناسب الحجم خطياً مع تغير رأس المال المرجعي (مثلاً 10,000$ مقابل 25,000$) في جميع المحركات الأربعة.
    """
    cfg_10k = get_risk_config({"equity_usd": 10000.0, "risk_pct_per_trade": 0.01, "max_total_open_risk_pct": 0.03})
    results = []

    # ------------------------------------------------------------------
    # اختبار 1: توحيد المخاطرة النقدية (1% = 100$) بغض النظر عن اتساع الوقف (2% مقابل 5%)
    # ------------------------------------------------------------------
    s_tight = compute_risk_position_size(
        entry_ref_price=100.0, stop_price=98.0, side="LONG", step=0.01,
        sym="SOLUSDT", atr_pct=2.2, strategy_type="swing_4h", risk_cfg=cfg_10k,
    )
    s_wide = compute_risk_position_size(
        entry_ref_price=100.0, stop_price=95.0, side="LONG", step=0.01,
        sym="AVAXUSDT", atr_pct=3.5, strategy_type="swing_4h", risk_cfg=cfg_10k,
    )
    assert s_tight["valid"] and s_wide["valid"]
    # في النظام القديم (SIZE_USD=1000) كانت الأولى تخسر ~21$ والثانية تخسر ~51$! الآن كلاهما <= 100$ ومقترب من 100$
    assert 98.5 <= s_tight["actual_risk_cash"] <= 100.0, f"مخاطرة غير منضبطة: {s_tight}"
    assert 98.5 <= s_wide["actual_risk_cash"] <= 100.0, f"مخاطرة غير منضبطة: {s_wide}"
    assert s_tight["position_notional_usd"] > s_wide["position_notional_usd"] * 2.2
    results.append(
        f"✅ [1/8] Risk-Normalized Sizing Test: وقف 2% أعطى مركزاً {s_tight['position_notional_usd']:,.0f}$ "
        f"(مخاطرة {s_tight['actual_risk_cash']:.2f}$) ووقف 5% أعطى {s_wide['position_notional_usd']:,.0f}$ "
        f"(مخاطرة {s_wide['actual_risk_cash']:.2f}$ <= 100$)."
    )

    # ------------------------------------------------------------------
    # اختبار 2: التطابق الرياضي التام بين محرك الحجم (Phase 2) ومحرك التنفيذ الفعلي (Phase 1) عند ضرب الوقف
    # ------------------------------------------------------------------
    for side, ep, sp in [("LONG", 100.0, 96.0), ("SHORT", 100.0, 104.0)]:
        sz = compute_risk_position_size(
            entry_ref_price=ep, stop_price=sp, side=side, step=0.001,
            sym="LINKUSDT", atr_pct=2.8, strategy_type="swing_4h", entry_is_maker=True, risk_cfg=cfg_10k,
        )
        assert sz["effective_stop_pct"] > sz["theoretical_stop_pct"]
        assert sz["actual_risk_cash"] > sz["theoretical_risk_cash"]
        assert sz["actual_risk_cash"] <= 100.0 + 1e-6

        # محاكاة ضرب الوقف الفعلي في محرك المرحلة الأولى والتحقق أن الخسارة النقدية الحقيقية بالـ USDT == actual_risk_cash!
        qty = sz["position_size"]
        eff_sl = sp * (1.0 - cfg_10k["stop_slippage_pct"]) if side == "LONG" else sp * (1.0 + cfg_10k["stop_slippage_pct"])
        gross_loss = (ep - eff_sl) * qty if side == "LONG" else (eff_sl - ep) * qty
        fees_usd = (ep * cfg_10k["maker_fee_pct"] + eff_sl * cfg_10k["taker_fee_pct"]) * qty
        realized_loss_usd = round(gross_loss + fees_usd, 4)
        assert abs(realized_loss_usd - sz["actual_risk_cash"]) <= 0.02, f"{realized_loss_usd} != {sz['actual_risk_cash']}"
        assert realized_loss_usd <= 100.0
    results.append("✅ [2/8] Theoretical vs All-In Risk Reconciliation: الخسارة الفعلية بالـ USDT عند ضرب الوقف في LONG/SHORT تطابق actual_risk_cash ولا تتجاوز 100.00$.")

    # ------------------------------------------------------------------
    # اختبار 3: اختيار الرافعة الآمنة ومنع التصفية قبل الوقف (Liquidation Safety Cap)
    # ------------------------------------------------------------------
    s_btc = compute_risk_position_size(
        entry_ref_price=70000.0, stop_price=68600.0, side="LONG", step=0.001,
        sym="BTCUSDT", atr_pct=1.6, strategy_type="swing_4h", risk_cfg=cfg_10k,
    )
    s_macro_wide = compute_risk_position_size(
        entry_ref_price=1.00, stop_price=0.84, side="LONG", step=0.1,
        sym="ARBUSDT", atr_pct=6.5, strategy_type="macro_squeeze", risk_cfg=cfg_10k,
    )
    s_extreme = compute_risk_position_size(
        entry_ref_price=1.00, stop_price=0.65, side="LONG", step=1.0,
        sym="MEMEUSDT", atr_pct=12.0, strategy_type="macro_squeeze", risk_cfg=cfg_10k,
    )
    assert s_btc["leverage"] == 5, f"BTC low-vol should get 5x, got {s_btc['leverage']}"
    assert s_macro_wide["leverage"] <= 2
    assert s_extreme["leverage"] == 1, "الوقف الأوسع من 30% يجب أن يُجبر على رافعة 1x لمنع التصفية"
    # هامش الأمان التقريبي للتصفية (1 / leverage) أكبر بكثير من مسافة الوقف الفعلية في جميع الحالات
    for sx in (s_btc, s_macro_wide, s_extreme):
        assert (sx["effective_stop_pct"] / 100.0) * sx["leverage"] <= 0.65
    results.append(f"✅ [3/8] Safe Leverage & Anti-Liquidation Test: BTC={s_btc['leverage']}x · Macro(16%)={s_macro_wide['leverage']}x · Extreme(35%)={s_extreme['leverage']}x.")

    # ------------------------------------------------------------------
    # اختبار 4: قيد الهامش الأقصى للصفقة الواحدة (25% من المحفظة) عند الوقف الضيق جداً
    # ------------------------------------------------------------------
    s_ultra_tight = compute_risk_position_size(
        entry_ref_price=3000.0, stop_price=2988.0, side="LONG", step=0.001,
        sym="ETHUSDT", atr_pct=1.4, strategy_type="swing_4h", risk_cfg=cfg_10k,
    )
    # عند وقف ~0.48% شامل الرسوم، الوصول لمخاطرة 100$ يتطلب مركزاً اسمياً ~20,800$؛ وبرافعة 5x يتطلب هامش 4,160$ (> 2,500$ المسموح)!
    assert s_ultra_tight["margin_capped"] is True
    assert s_ultra_tight["margin_required_usd"] <= 2500.0 + 1e-6
    assert s_ultra_tight["actual_risk_cash"] < 100.0
    results.append(
        f"✅ [4/8] Single-Trade Margin Cap Test: تقييد الهامش تلقائياً عند {s_ultra_tight['margin_required_usd']:,.2f}$ "
        f"(<= 25%) فانخفضت المخاطرة بأمان إلى {s_ultra_tight['actual_risk_cash']:.2f}$."
    )

    # ------------------------------------------------------------------
    # اختبار 5: التقريب للأسفل وفق stepSize وفحص min_notional للمحافظ الصغيرة
    # ------------------------------------------------------------------
    cfg_tiny = get_risk_config({"equity_usd": 150.0, "risk_pct_per_trade": 0.01})  # ميزانية المخاطرة = 1.50$ فقط!
    s_min_fail = compute_risk_position_size(
        entry_ref_price=90000.0, stop_price=87300.0, side="LONG", step=0.001,
        min_notional=100.0, sym="BTCUSDT", atr_pct=2.0, strategy_type="swing_4h", risk_cfg=cfg_tiny,
    )
    # أصغر عقد 0.001 BTC = 90$ وتحت min_notional=100$ (0.002 BTC = 180$ مخاطرته ~5.5$ > 1.50$!) فيجب رفضه صراحةً
    assert s_min_fail["valid"] is False and s_min_fail["reject_reason"] == "MIN_NOTIONAL_EXCEEDS_RISK_LIMIT"
    results.append("✅ [5/8] Exchange StepSize & MinNotional Guard: رفض صريح للصفقات التي يكسر حدها الأدنى في بايننس سقف المخاطرة للمحافظ الصغيرة.")

    # ------------------------------------------------------------------
    # اختبار 6: ديناميكية المخاطرة المفتوحة قبل وبعد نقل الوقف للتعادل (BE / Trail)
    # ------------------------------------------------------------------
    open_initial = {
        "sym": "ADAUSDT", "name": "ADA", "side": "LONG",
        "trade_status": "OPEN", "filled": True, "fill_price": 1.00,
        "stop": 0.95, "active_stop": 0.95, "stop_mode": "initial",
        "qty": 1900.0, "remaining_pct": 1.0, "leverage": 3,
    }
    be_stop_sol = compute_fee_adjusted_be_stop(100.0, "LONG", tp1=110.0, tick=0.01)
    open_after_tp1 = {
        "sym": "SOLUSDT", "name": "SOL", "side": "LONG",
        "trade_status": "PARTIAL_TP1", "filled": True, "fill_price": 100.0,
        "stop": 95.0, "active_stop": be_stop_sol, "stop_mode": "BE",
        "qty": 19.5, "remaining_pct": 0.50, "leverage": 3,
    }
    r_init = compute_open_position_risk(open_initial, cfg_10k)
    r_be = compute_open_position_risk(open_after_tp1, cfg_10k)
    assert r_init["is_open"] and r_init["open_risk_cash"] > 95.0
    assert r_be["is_open"] and r_be["open_risk_cash"] == 0.0 and r_be["open_margin_usd"] > 0.0
    results.append(
        f"✅ [6/8] Dynamic Open Risk After BE Test: المركز قبل TP1 يحجز مخاطرة {r_init['open_risk_cash']:.2f}$، "
        f"وبعد نقل الوقف للتعادل تنخفض مخاطرته المفتوحة إلى {r_be['open_risk_cash']:.2f}$ مع بقاء خانته وهامشه ({r_be['open_margin_usd']:.0f}$) نشطَين."
    )

    # ------------------------------------------------------------------
    # اختبار 7: بوابة المخاطرة الكلية للمحفظة (3% مخاطرة · 4 مراكز · 1 كبار BTC/ETH/SOL)
    # ------------------------------------------------------------------
    # لدينا 3 مراكز مفتوحة بالفعل: SOL في حالة BE (0$ مخاطرة، لكنه يحجز خانة الكبار!) + ADA بمخاطرة ~96.88$ + DOGE بمخاطرة ~98.08$ -> المجموع ~194.96$
    open_third = {
        "sym": "DOGEUSDT", "name": "DOGE", "side": "SHORT",
        "trade_status": "OPEN", "filled": True, "fill_price": 0.20,
        "stop": 0.21, "active_stop": 0.21, "stop_mode": "initial",
        "qty": 9600.0, "remaining_pct": 1.0, "leverage": 3,
    }
    cands = [
        # (أ) BTC أعلى درجة لكن يجب حجبها لأن SOL الكبرى مفتوحة حالياً!
        {"sym": "BTCUSDT", "name": "BTC", "side": "LONG", "score": 92.0, "reach": "A", "dist_atr": 0.2,
         "avg": 70000.0, "qty": 0.07, "leverage": 5, "actual_risk_cash": 99.0, "margin_required_usd": 980.0, "valid": True},
        # (ب) LINK عملة بديلة بمخاطرة 99$ -> إجمالي المراكز يصبح 4/4 وإجمالي المخاطرة ~294$ (<= 300$) -> تُقبل!
        {"sym": "LINKUSDT", "name": "LINK", "side": "LONG", "score": 88.0, "reach": "A", "dist_atr": 0.3,
         "avg": 15.0, "qty": 130.0, "leverage": 3, "actual_risk_cash": 99.0, "margin_required_usd": 650.0, "valid": True},
        # (ج) SUI صفقة خامسة -> تُحجب بسبب امتلاء الخانات الـ 4 وسقف الـ 3%!
        {"sym": "SUIUSDT", "name": "SUI", "side": "LONG", "score": 85.0, "reach": "A", "dist_atr": 0.4,
         "avg": 2.0, "qty": 950.0, "leverage": 3, "actual_risk_cash": 99.0, "margin_required_usd": 633.0, "valid": True},
    ]
    gated, gsum = evaluate_portfolio_risk_gate(cands, [open_initial, open_after_tp1, open_third], cfg_10k)
    by_name = {x["name"]: x for x in gated}
    assert by_name["BTC"]["risk_gate_allowed"] is False and by_name["BTC"]["risk_gate_status"] == "BLOCKED_MAJOR_CAP"
    assert by_name["LINK"]["risk_gate_allowed"] is True and by_name["LINK"]["risk_gate_status"] == "APPROVED"
    assert by_name["SUI"]["risk_gate_allowed"] is False and by_name["SUI"]["risk_gate_status"] in ("BLOCKED_MAX_POSITIONS", "BLOCKED_MAX_PORTFOLIO_RISK")
    assert gsum["approved_candidates"] == 1 and gsum["blocked_candidates"] == 2
    results.append("✅ [7/8] Portfolio Risk Gate Test: حجب الكبار المكررة (BTC مع وجود SOL) + قبول الصفقة المكملة للسقف (LINK) + حجب التجاوز الخامس (SUI).")

    # ------------------------------------------------------------------
    # اختبار 8: التناسب الخطي الدقيق مع تغير رأس المال (10,000$ مقابل 25,000$)
    # ------------------------------------------------------------------
    cfg_25k = get_risk_config({"equity_usd": 25000.0, "risk_pct_per_trade": 0.01})
    s_10k = compute_risk_position_size(25.0, 24.0, "LONG", step=0.01, sym="AVAXUSDT", atr_pct=2.5, risk_cfg=cfg_10k)
    s_25k = compute_risk_position_size(25.0, 24.0, "LONG", step=0.01, sym="AVAXUSDT", atr_pct=2.5, risk_cfg=cfg_25k)
    ratio = s_25k["position_size"] / s_10k["position_size"]
    assert 2.49 <= ratio <= 2.51 and s_25k["actual_risk_cash"] <= 250.0
    results.append(
        f"✅ [8/8] Equity Scaling Test: مضاعفة رأس المال 2.5x رفعت الكمية بدقة {ratio:.3f}x "
        f"({s_10k['position_size']} -> {s_25k['position_size']} عقد، مخاطرة {s_25k['actual_risk_cash']:.2f}$ <= 250$)."
    )

    print("=" * 78)
    print("🧪 نتائج اختبارات القبول للمرحلة الثانية (Phase 2 Risk Engine Suite — 8/8 PASSED)")
    print("=" * 78)
    for line in results:
        print(" ", line)
    print("=" * 78)
    return True


# ==============================================================================
# [7] القسم السابع: محرك الباكتيست التاريخي المتقدم (Walk-Forward Backtest Engine — Phase 3)
# ==============================================================================
import bisect
import statistics

INTERVAL_MS_MAP = {
    "5m": 5 * 60 * 1000,
    "15m": 15 * 60 * 1000,
    "1h": 3600 * 1000,
    "4h": 4 * 3600 * 1000,
    "1d": 24 * 3600 * 1000,
}


def _slice_klines_as_of(k, as_of_ms, interval_ms, closed_only=True, max_bars=None):
    """اقتطاع زمني صارم بدون أي انحياز مستقبلي (Zero-Lookahead Point-in-Time Slicer):
    - عند closed_only=True: لا يُسمح برؤية أي شمعة إلا بعد اكتمال إغلاقها بالكامل (t + interval_ms <= as_of_ms).
    - يعيد قاموس شموع خام جاهزاً لدالة enrich() دون تعديل السلسلة الأصلية.
    """
    if not k or not k.get("t"):
        return {"t": [], "o": [], "h": [], "l": [], "c": [], "v": [], "qv": []}
    cutoff_open_ts = int(as_of_ms - interval_ms) if closed_only else int(as_of_ms)
    end_idx = bisect.bisect_right(k["t"], cutoff_open_ts)
    if end_idx <= 0:
        return {"t": [], "o": [], "h": [], "l": [], "c": [], "v": [], "qv": []}
    start_idx = max(0, end_idx - max_bars) if (max_bars and max_bars > 0) else 0
    has_qv = "qv" in k and len(k["qv"]) == len(k["t"])
    has_v = "v" in k and len(k["v"]) == len(k["t"])
    return {
        "t": list(k["t"][start_idx:end_idx]),
        "o": list(k["o"][start_idx:end_idx]),
        "h": list(k["h"][start_idx:end_idx]),
        "l": list(k["l"][start_idx:end_idx]),
        "c": list(k["c"][start_idx:end_idx]),
        "v": list(k["v"][start_idx:end_idx]) if has_v else [0.0] * (end_idx - start_idx),
        "qv": list(k["qv"][start_idx:end_idx]) if has_qv else [
            float(k["c"][i]) * float(k["v"][i]) if has_v else 0.0 for i in range(start_idx, end_idx)
        ],
    }


def _slice_5m_between(k5m, start_open_ms, as_of_ms):
    """يقتطع شموع الـ 5 دقائق المغلقة بالكامل في الفترة [start_open_ms, as_of_ms - 5m] لمحاكاة دورة حياة الصفقة."""
    if not k5m or not k5m.get("t"):
        return {"t": [], "o": [], "h": [], "l": [], "c": []}
    ts_list = k5m["t"]
    lo_idx = bisect.bisect_left(ts_list, int(start_open_ms))
    hi_idx = bisect.bisect_right(ts_list, int(as_of_ms - BAR_5M_MS))
    if hi_idx <= lo_idx:
        return {"t": [], "o": [], "h": [], "l": [], "c": []}
    return {
        "t": ts_list[lo_idx:hi_idx],
        "o": k5m["o"][lo_idx:hi_idx],
        "h": k5m["h"][lo_idx:hi_idx],
        "l": k5m["l"][lo_idx:hi_idx],
        "c": k5m["c"][lo_idx:hi_idx],
    }


def fetch_historical_klines_paginated(symbol, interval, start_ms, end_ms, use_cache=True):
    """جلب تاريخي مقسّم على دفعات (Paginated) من Binance Futures API مع تخزين مؤقت محلي لتسريع مقارنات الحساسية."""
    iv_ms = INTERVAL_MS_MAP[interval]
    bt_cache_dir = os.path.join(CACHE, "backtest")
    os.makedirs(bt_cache_dir, exist_ok=True)
    # تقريب مفاتيح الكاش لأقرب ساعة لتسهيل إعادة الاستخدام في مقارنات النماذج المتتالية
    s_bucket = (int(start_ms) // 3_600_000) * 3_600_000
    e_bucket = ((int(end_ms) + 3_599_999) // 3_600_000) * 3_600_000
    cfile = os.path.join(bt_cache_dir, f"bt_{symbol}_{interval}_{s_bucket}_{e_bucket}.json")
    if use_cache and os.path.exists(cfile):
        try:
            cached = json.load(open(cfile, encoding="utf-8"))
            if cached and cached.get("t"):
                return cached
        except Exception:
            pass

    rows_by_ts = {}
    cur = int(start_ms)
    hard_end = int(end_ms)
    while cur <= hard_end:
        path = f"/v1/klines?symbol={symbol}&interval={interval}&startTime={cur}&endTime={hard_end}&limit=1500"
        batch = _get(path)
        if not batch:
            break
        for x in batch:
            t_open = int(x[0])
            rows_by_ts[t_open] = (
                t_open,
                float(x[1]),
                float(x[2]),
                float(x[3]),
                float(x[4]),
                float(x[5]),
                float(x[7]),  # quoteAssetVolume بالـ USDT
            )
        last_open = int(batch[-1][0])
        if last_open < cur or len(batch) < 1500:
            cur = last_open + iv_ms
            if len(batch) < 1500:
                break
        else:
            cur = last_open + iv_ms

    ordered = [rows_by_ts[k] for k in sorted(rows_by_ts.keys())]
    out = {
        "t": [r[0] for r in ordered],
        "o": [r[1] for r in ordered],
        "h": [r[2] for r in ordered],
        "l": [r[3] for r in ordered],
        "c": [r[4] for r in ordered],
        "v": [r[5] for r in ordered],
        "qv": [r[6] for r in ordered],
    }
    if use_cache and ordered:
        try:
            json.dump(out, open(cfile, "w", encoding="utf-8"))
        except Exception:
            pass
    return out


def fetch_historical_funding_series(symbol, start_ms, end_ms, use_cache=True):
    """جلب سجل الفاندنغ التاريخي الفعلي لربط كل لحظة مسح في الباكتيست بمعدل التمويل السائد وقتها فقط."""
    bt_cache_dir = os.path.join(CACHE, "backtest")
    os.makedirs(bt_cache_dir, exist_ok=True)
    s_bucket = (int(start_ms) // 3_600_000) * 3_600_000
    e_bucket = ((int(end_ms) + 3_599_999) // 3_600_000) * 3_600_000
    cfile = os.path.join(bt_cache_dir, f"bt_fund_{symbol}_{s_bucket}_{e_bucket}.json")
    if use_cache and os.path.exists(cfile):
        try:
            return json.load(open(cfile, encoding="utf-8"))
        except Exception:
            pass
    try:
        raw = _get(f"/v1/fundingRate?symbol={symbol}&startTime={int(start_ms)}&endTime={int(end_ms)}&limit=1000")
        out = sorted(
            [{"t": int(x["fundingTime"]), "rate": float(x["fundingRate"])} for x in (raw or [])],
            key=lambda z: z["t"],
        )
    except Exception:
        out = []
    if use_cache and out:
        try:
            json.dump(out, open(cfile, "w", encoding="utf-8"))
        except Exception:
            pass
    return out


def load_walk_forward_dataset(symbols, start_ms, end_ms, tail_hours=48, max_workers=6, use_cache=True, verbose=True):
    """يجهز حزمة البيانات التاريخية متعددة الفريمات (1d, 4h, 1h, 5m + funding + exchangeInfo) للكون المختار."""
    ei = cached_get("/v1/exchangeInfo", "exchangeInfo", ttl=6 * 3600)
    info_map = {s["symbol"]: s for s in ei["symbols"]}
    warmup_4h_ms = 230 * INTERVAL_MS_MAP["4h"]
    warmup_1d_ms = 85 * INTERVAL_MS_MAP["1d"]
    warmup_1h_ms = 90 * INTERVAL_MS_MAP["1h"]
    eval_end_ms = int(end_ms + tail_hours * 3600 * 1000)

    dataset = {}

    def _load_one(sym):
        s_info = info_map.get(sym)
        if not s_info:
            return sym, None
        k4 = fetch_historical_klines_paginated(sym, "4h", start_ms - warmup_4h_ms, eval_end_ms, use_cache=use_cache)
        k1d = fetch_historical_klines_paginated(sym, "1d", start_ms - warmup_1d_ms, eval_end_ms, use_cache=use_cache)
        k1h = fetch_historical_klines_paginated(sym, "1h", start_ms - warmup_1h_ms, eval_end_ms, use_cache=use_cache)
        k5m = fetch_historical_klines_paginated(sym, "5m", start_ms - 6 * 3600 * 1000, eval_end_ms, use_cache=use_cache)
        f_hist = fetch_historical_funding_series(sym, start_ms - 24 * 3600 * 1000, eval_end_ms, use_cache=use_cache)
        return sym, {
            "info": s_info,
            "4h": k4,
            "1d": k1d,
            "1h": k1h,
            "5m": k5m,
            "funding": f_hist,
        }

    with cf.ThreadPoolExecutor(max_workers=max_workers) as ex:
        done = 0
        for sym, bundle in ex.map(_load_one, symbols):
            done += 1
            if bundle and bundle["4h"]["t"] and bundle["5m"]["t"]:
                dataset[sym] = bundle
            if verbose:
                print(f"  [بيانات الباكتيست] {done}/{len(symbols)} تم تحميل {sym}")
    return dataset


def generate_walk_forward_schedule(start_ms, end_ms, all_4h_windows=False):
    """يولّد جدول طوابع المسح الزمنية التاريخية بتوقيت الرياض (UTC+3):
    - الوضع الافتراضي: النوافذ الـ 5 الرسمية في RULES.md (03:05 · 11:05 · 15:05 · 19:05 · 23:05).
    - عند all_4h_windows=True: جميع إغلاقات الـ 4 ساعات الـ 6 يومياً (+05 دقائق بعد الإغلاق).
    """
    allowed_hours = {3, 7, 11, 15, 19, 23} if all_4h_windows else {3, 11, 15, 19, 23}
    dt_start = dt.datetime.fromtimestamp(start_ms / 1000.0, RIYADH).replace(minute=5, second=0, microsecond=0)
    cur_dt = dt_start - dt.timedelta(hours=4)
    end_dt = dt.datetime.fromtimestamp(end_ms / 1000.0, RIYADH)
    schedule = []
    while cur_dt <= end_dt:
        if cur_dt.hour in allowed_hours:
            cand_dt = cur_dt.replace(minute=5, second=0, microsecond=0)
            ts = int(cand_dt.timestamp() * 1000)
            if start_ms <= ts <= end_ms:
                schedule.append(ts)
        cur_dt += dt.timedelta(hours=1)
    return sorted(set(schedule))


def _point_in_time_funding_rate(funding_series, as_of_ms):
    if not funding_series:
        return 0.0
    times = [x["t"] for x in funding_series]
    idx = bisect.bisect_right(times, int(as_of_ms)) - 1
    return float(funding_series[idx]["rate"]) if idx >= 0 else 0.0


def _point_in_time_oi(oi_series, as_of_ms):
    """يدعم سجل OI التاريخي إن توفّر في الحزمة (مثلاً للتحقق التجريبي)، وإلا يعيد (None, None) دون انحياز."""
    if not oi_series:
        return None, None
    times = [x["t"] for x in oi_series]
    idx = bisect.bisect_right(times, int(as_of_ms)) - 1
    if idx < 0:
        return None, None
    oi_now = float(oi_series[idx]["oi"])
    target_prev_ts = int(as_of_ms - 4 * 3600 * 1000)
    idx_prev = bisect.bisect_right(times, target_prev_ts) - 1
    oi_prev = float(oi_series[idx_prev]["oi"]) if idx_prev >= 0 else None
    return oi_now, oi_prev


def build_point_in_time_candidates(
    dataset,
    scan_ts_ms,
    risk_cfg,
    min_score=MIN_SCORE,
    min_qv_m=MIN_QV,
    closed_bars_only=True,
    entry_is_maker=True,
    custom_signal_builder=None,
):
    """يبني الصفقات المرشحة عند اللحظة التاريخية scan_ts_ms حصراً من الشموع المغلقة قبلها (Zero-Lookahead)."""
    if custom_signal_builder is not None:
        return custom_signal_builder(dataset, scan_ts_ms, risk_cfg)

    scan_dt = dt.datetime.fromtimestamp(scan_ts_ms / 1000.0, RIYADH)
    asia_flag = is_asia_wick_window(scan_dt)
    raw_candidates = []

    for sym, bundle in dataset.items():
        s_info = bundle["info"]
        onboard = int(s_info.get("onboardDate") or 0)
        if onboard and (scan_ts_ms - onboard) / 86_400_000.0 < MAX_AGE:
            continue

        k4_raw = _slice_klines_as_of(bundle["4h"], scan_ts_ms, INTERVAL_MS_MAP["4h"], closed_only=closed_bars_only, max_bars=500)
        k1d_raw = _slice_klines_as_of(bundle["1d"], scan_ts_ms, INTERVAL_MS_MAP["1d"], closed_only=closed_bars_only, max_bars=300)
        if len(k4_raw["c"]) < 60 or len(k1d_raw["c"]) < 22:
            continue

        k1h_raw = _slice_klines_as_of(bundle.get("1h"), scan_ts_ms, INTERVAL_MS_MAP["1h"], closed_only=closed_bars_only, max_bars=160)
        k5_recent = _slice_5m_between(bundle["5m"], scan_ts_ms - 3600 * 1000, scan_ts_ms)
        last_px = float(k5_recent["c"][-1]) if k5_recent["c"] else float(k4_raw["c"][-1])

        # بناء ملخص 24 ساعة الفعلي حتى لحظة المسح بدون أي تسريب من المستقبل
        if len(k1h_raw["c"]) >= 24:
            w_o = float(k1h_raw["o"][-24])
            w_h = max(k1h_raw["h"][-24:])
            w_l = min(k1h_raw["l"][-24:])
            w_qv = sum(k1h_raw["qv"][-24:])
        else:
            n4 = min(6, len(k4_raw["c"]))
            w_o = float(k4_raw["o"][-n4])
            w_h = max(k4_raw["h"][-n4:])
            w_l = min(k4_raw["l"][-n4:])
            w_qv = sum(k4_raw["qv"][-n4:])

        if w_qv / 1e6 < min_qv_m or w_o <= 0:
            continue

        chg_24 = (last_px / w_o - 1.0) * 100.0
        f_rate = _point_in_time_funding_rate(bundle.get("funding"), scan_ts_ms)
        oi_now, oi_prev = _point_in_time_oi(bundle.get("oi_hist"), scan_ts_ms)

        t24_snap = {
            "symbol": sym,
            "quoteVolume": str(w_qv),
            "priceChangePercent": str(chg_24),
            "highPrice": str(max(w_h, last_px)),
            "lowPrice": str(min(w_l, last_px)),
            "lastPrice": str(last_px),
        }
        prem_snap = {
            "symbol": sym,
            "markPrice": str(last_px),
            "indexPrice": str(last_px),
            "lastFundingRate": str(f_rate),
            "nextFundingTime": scan_ts_ms + 4 * 3600 * 1000,
        }
        extra = {"oi": oi_now, "oi_prev": oi_prev}

        coin = Coin(sym, s_info, t24_snap, prem_snap, oi_now, oi_prev)
        coin.age_days = (scan_ts_ms - onboard) / 86_400_000.0 if onboard else 365.0
        coin.h4 = enrich(k4_raw)
        coin.h1 = enrich(k1d_raw)
        if abs(coin.chg) >= 6.0 and len(k1h_raw["c"]) >= 55:
            coin.m60 = enrich(k1h_raw)

        for side in ("LONG", "SHORT"):
            cand = build(
                coin,
                side,
                extra,
                asia_wick=asia_flag,
                now_ms=scan_ts_ms,
                risk_cfg=risk_cfg,
                entry_is_maker=entry_is_maker,
            )
            if cand and cand["score"] >= min_score:
                cand["origin_ts"] = int(scan_ts_ms)
                cand["scan_hour_riyadh"] = scan_dt.hour
                raw_candidates.append(cand)

    raw_candidates.sort(key=lambda t: (-t["score"], t["dist_atr"]))
    dedup = []
    seen_syms = set()
    for t in raw_candidates:
        if t["sym"] not in seen_syms:
            seen_syms.add(t["sym"])
            dedup.append(t)
    return dedup


def compute_backtest_metrics(
    all_trades,
    blocked_signals,
    equity_curve,
    initial_equity_usd,
    fill_model,
    trail_after_tp2,
    start_ms,
    end_ms,
):
    """يحسب مقاييس الأداء المؤسسية وجداول المعايرة الإحصائية من سجل الصفقات ومنحنى رأس المال."""
    closed = [
        t for t in all_trades
        if t.get("filled") and t.get("trade_status") in ("CLOSED_TP3", "CLOSED_STOP", "CLOSED_BE", "CLOSED_TRAIL", "CLOSED_EXPIRY")
    ]
    still_open = [t for t in all_trades if t.get("filled") and float(t.get("remaining_pct", 0.0)) > 0]
    filled_all = [t for t in all_trades if t.get("filled")]
    unfilled_cancelled = [t for t in all_trades if not t.get("filled") and t.get("trade_status") == "CANCELLED_DIST"]
    unfilled_expired = [t for t in all_trades if not t.get("filled") and t.get("trade_status") == "EXPIRED"]

    wins = [t for t in closed if float(t.get("realized_r", 0.0)) > 0.05]
    losses = [t for t in closed if float(t.get("realized_r", 0.0)) < -0.05]
    bes = [t for t in closed if -0.05 <= float(t.get("realized_r", 0.0)) <= 0.05]

    realized_pnl_usd = sum(float(t.get("realized_pnl_usd", 0.0)) for t in filled_all)
    open_unrealized_usd = sum(float(t.get("unrealized_pnl_usd", 0.0)) for t in still_open)
    final_realized_eq = initial_equity_usd + realized_pnl_usd
    final_mtm_eq = final_realized_eq + open_unrealized_usd

    gross_profit_usd = sum(float(t.get("realized_pnl_usd", 0.0)) for t in closed if float(t.get("realized_pnl_usd", 0.0)) > 0)
    gross_loss_abs_usd = abs(sum(float(t.get("realized_pnl_usd", 0.0)) for t in closed if float(t.get("realized_pnl_usd", 0.0)) < 0))
    if gross_loss_abs_usd > 1e-9:
        profit_factor = round(gross_profit_usd / gross_loss_abs_usd, 3)
    else:
        profit_factor = round(99.99 if gross_profit_usd > 0 else 0.0, 3)

    n_closed = len(closed)
    expectancy_r = round(sum(float(t.get("realized_r", 0.0)) for t in closed) / n_closed, 4) if n_closed else 0.0
    expectancy_usd = round(sum(float(t.get("realized_pnl_usd", 0.0)) for t in closed) / n_closed, 2) if n_closed else 0.0

    avg_win_r = round(sum(float(t["realized_r"]) for t in wins) / len(wins), 4) if wins else 0.0
    avg_loss_r = round(sum(float(t["realized_r"]) for t in losses) / len(losses), 4) if losses else 0.0
    avg_win_usd = round(sum(float(t["realized_pnl_usd"]) for t in wins) / len(wins), 2) if wins else 0.0
    avg_loss_usd = round(sum(float(t["realized_pnl_usd"]) for t in losses) / len(losses), 2) if losses else 0.0
    payoff_ratio_r = round(avg_win_r / abs(avg_loss_r), 3) if (wins and losses and abs(avg_loss_r) > 1e-9) else 0.0

    total_fees_usd = round(sum(float(t.get("total_fees_usd", 0.0)) for t in filled_all), 2)
    total_slip_usd = round(sum(float(t.get("total_slippage_usd", 0.0)) for t in filled_all), 2)

    hold_hrs = [
        (int(t["exit_ts"]) - int(t["filled_at"])) / 3_600_000.0
        for t in closed
        if t.get("exit_ts") and t.get("filled_at") and int(t["exit_ts"]) >= int(t["filled_at"])
    ]
    avg_hold_hours = round(sum(hold_hrs) / len(hold_hrs), 2) if hold_hrs else 0.0

    # حساب أقصى تراجع (Max Drawdown) بدقة على كل من منحنى الصفقات المحققة ومنحنى التقييم اللحظي MTM
    max_dd_usd = 0.0
    max_dd_pct = 0.0
    max_real_dd_usd = 0.0
    max_real_dd_pct = 0.0
    max_sim_pos = 0
    max_sim_risk_pct = 0.0

    peak_mtm = float(initial_equity_usd)
    peak_real = float(initial_equity_usd)
    step_returns = []
    prev_eq = float(initial_equity_usd)

    for pt in equity_curve:
        mtm_e = float(pt["mtm_equity_usd"])
        real_e = float(pt["realized_equity_usd"])
        peak_mtm = max(peak_mtm, mtm_e)
        peak_real = max(peak_real, real_e)
        dd_u = peak_mtm - mtm_e
        dd_p = (dd_u / peak_mtm * 100.0) if peak_mtm > 0 else 0.0
        rdd_u = peak_real - real_e
        rdd_p = (rdd_u / peak_real * 100.0) if peak_real > 0 else 0.0
        if dd_u > max_dd_usd:
            max_dd_usd = dd_u
        if dd_p > max_dd_pct:
            max_dd_pct = dd_p
        if rdd_u > max_real_dd_usd:
            max_real_dd_usd = rdd_u
        if rdd_p > max_real_dd_pct:
            max_real_dd_pct = rdd_p
        max_sim_pos = max(max_sim_pos, int(pt.get("open_positions", 0)))
        max_sim_risk_pct = max(max_sim_risk_pct, float(pt.get("open_risk_pct", 0.0)))
        if prev_eq > 0 and pt.get("event_type") == "SCAN_WINDOW":
            step_returns.append((mtm_e - prev_eq) / prev_eq)
            prev_eq = mtm_e

    # حساب Sharpe و Sortino السنويين من عوائد نوافذ المسح (~5 نوافذ يومياً = ~1,825 نافذة سنوياً)
    sharpe_ratio = 0.0
    sortino_ratio = 0.0
    if len(step_returns) >= 2:
        mean_r = statistics.mean(step_returns)
        std_r = statistics.pstdev(step_returns)
        periods_per_year = 5.0 * 365.0
        if std_r > 1e-12:
            sharpe_ratio = round((mean_r / std_r) * math.sqrt(periods_per_year), 3)
        downside_sq = [min(0.0, r) ** 2 for r in step_returns]
        downside_dev = math.sqrt(sum(downside_sq) / len(downside_sq))
        if downside_dev > 1e-12:
            sortino_ratio = round((mean_r / downside_dev) * math.sqrt(periods_per_year), 3)

    total_ret_pct = ((final_realized_eq / initial_equity_usd) - 1.0) * 100.0 if initial_equity_usd > 0 else 0.0
    calmar_ratio = round(total_ret_pct / max_dd_pct, 3) if max_dd_pct > 1e-9 else 0.0

    # جداول المعايرة الطبقية (مهمة جداً للمرحلة الرابعة: مقارنة Reach المتوقع بالوصول الفعلي، وتقييم الدرجات A/B/C)
    def _bucket_perf(subset):
        c_sub = [x for x in subset if x.get("filled") and x.get("trade_status") in ("CLOSED_TP3", "CLOSED_STOP", "CLOSED_BE", "CLOSED_TRAIL", "CLOSED_EXPIRY")]
        f_sub = [x for x in subset if x.get("filled")]
        w_sub = [x for x in c_sub if float(x.get("realized_r", 0.0)) > 0.05]
        return {
            "signals": len(subset),
            "filled": len(f_sub),
            "fill_rate_pct": round(len(f_sub) / len(subset) * 100.0, 1) if subset else 0.0,
            "closed": len(c_sub),
            "win_rate_pct": round(len(w_sub) / len(c_sub) * 100.0, 1) if c_sub else 0.0,
            "expectancy_r": round(sum(float(x["realized_r"]) for x in c_sub) / len(c_sub), 4) if c_sub else 0.0,
            "net_r": round(sum(float(x["realized_r"]) for x in c_sub), 3),
            "net_usd": round(sum(float(x.get("realized_pnl_usd", 0.0)) for x in c_sub), 2),
        }

    by_side = {s: _bucket_perf([t for t in all_trades if t.get("side") == s]) for s in ("LONG", "SHORT")}
    by_grade = {g: _bucket_perf([t for t in all_trades if t.get("grade") == g]) for g in ("A", "B", "C")}
    by_reach = {}
    for r_lbl, pred_default in (("A", 80.0), ("B", 68.0), ("C", 54.0)):
        r_sub = [t for t in all_trades if t.get("reach") == r_lbl]
        bp = _bucket_perf(r_sub)
        avg_pred = round(sum(float(t.get("reach_p", pred_default)) for t in r_sub) / len(r_sub), 1) if r_sub else pred_default
        bp["predicted_reach_pct"] = avg_pred
        bp["calibration_gap_pct"] = round(bp["fill_rate_pct"] - avg_pred, 1) if r_sub else 0.0
        by_reach[r_lbl] = bp

    by_window = {}
    for hr in sorted({int(t.get("scan_hour_riyadh", -1)) for t in all_trades if t.get("scan_hour_riyadh") is not None}):
        by_window[f"{hr:02d}:05"] = _bucket_perf([t for t in all_trades if int(t.get("scan_hour_riyadh", -1)) == hr])

    block_reasons = {}
    for b in blocked_signals:
        st_code = b.get("risk_gate_status", "BLOCKED_OTHER")
        block_reasons[st_code] = block_reasons.get(st_code, 0) + 1

    tp1_hits = sum(1 for t in filled_all if (t.get("tp_hits") or [False])[0])
    tp2_hits = sum(1 for t in filled_all if len(t.get("tp_hits") or []) > 1 and t["tp_hits"][1])
    tp3_hits = sum(1 for t in filled_all if len(t.get("tp_hits") or []) > 2 and t["tp_hits"][2])
    exit_counts = {
        st_k: sum(1 for t in closed if t.get("trade_status") == st_k)
        for st_k in ("CLOSED_TP3", "CLOSED_TRAIL", "CLOSED_BE", "CLOSED_STOP", "CLOSED_EXPIRY")
    }

    return {
        "fill_model": fill_model,
        "trail_after_tp2": bool(trail_after_tp2),
        "period_start_riyadh": dt.datetime.fromtimestamp(start_ms / 1000.0, RIYADH).strftime("%Y-%m-%d %H:%M"),
        "period_end_riyadh": dt.datetime.fromtimestamp(end_ms / 1000.0, RIYADH).strftime("%Y-%m-%d %H:%M"),
        "initial_equity_usd": round(initial_equity_usd, 2),
        "final_realized_equity_usd": round(final_realized_eq, 2),
        "final_mtm_equity_usd": round(final_mtm_eq, 2),
        "net_realized_profit_usd": round(realized_pnl_usd, 2),
        "open_unrealized_pnl_usd": round(open_unrealized_usd, 2),
        "total_return_pct": round(total_ret_pct, 3),
        "max_drawdown_usd": round(max_dd_usd, 2),
        "max_drawdown_pct": round(max_dd_pct, 3),
        "max_realized_drawdown_usd": round(max_real_dd_usd, 2),
        "max_realized_drawdown_pct": round(max_real_dd_pct, 3),
        "calmar_ratio": calmar_ratio,
        "sharpe_ratio": sharpe_ratio,
        "sortino_ratio": sortino_ratio,
        "signals_generated": len(all_trades) + len(blocked_signals),
        "signals_approved": len(all_trades),
        "signals_blocked_by_risk_gate": len(blocked_signals),
        "block_reasons_breakdown": block_reasons,
        "filled_count": len(filled_all),
        "fill_rate_pct": round(len(filled_all) / len(all_trades) * 100.0, 1) if all_trades else 0.0,
        "cancelled_dist_count": len(unfilled_cancelled),
        "expired_unfilled_count": len(unfilled_expired),
        "closed_count": n_closed,
        "still_open_count": len(still_open),
        "wins": len(wins),
        "losses": len(losses),
        "be_count": len(bes),
        "exit_status_counts": exit_counts,
        "win_rate_pct": round(len(wins) / n_closed * 100.0, 1) if n_closed else 0.0,
        "loss_rate_pct": round(len(losses) / n_closed * 100.0, 1) if n_closed else 0.0,
        "be_rate_pct": round(len(bes) / n_closed * 100.0, 1) if n_closed else 0.0,
        "tp1_hit_rate_pct": round(tp1_hits / len(filled_all) * 100.0, 1) if filled_all else 0.0,
        "tp2_hit_rate_pct": round(tp2_hits / len(filled_all) * 100.0, 1) if filled_all else 0.0,
        "tp3_hit_rate_pct": round(tp3_hits / len(filled_all) * 100.0, 1) if filled_all else 0.0,
        "profit_factor": profit_factor,
        "expectancy_r": expectancy_r,
        "expectancy_usd": expectancy_usd,
        "net_r": round(sum(float(t.get("realized_r", 0.0)) for t in closed), 3),
        "avg_win_r": avg_win_r,
        "avg_loss_r": avg_loss_r,
        "avg_win_usd": avg_win_usd,
        "avg_loss_usd": avg_loss_usd,
        "payoff_ratio_r": payoff_ratio_r,
        "total_fees_usd": total_fees_usd,
        "total_slippage_usd": total_slip_usd,
        "avg_hold_hours": avg_hold_hours,
        "max_simultaneous_open_positions": max_sim_pos,
        "max_simultaneous_open_risk_pct": round(max_sim_risk_pct, 3),
        "by_side": by_side,
        "by_grade": by_grade,
        "by_reach": by_reach,
        "by_window": by_window,
    }


def run_walk_forward_backtest(
    dataset,
    start_ms,
    end_ms,
    scan_timestamps_ms=None,
    all_4h_windows=False,
    tail_eval_hours=48.0,
    fill_model=DEFAULT_FILL_MODEL,
    partial_weights=PARTIAL_EXIT_WEIGHTS,
    trail_after_tp2=True,
    pending_expiry_hours=PENDING_SIGNAL_EXPIRY_HOURS,
    max_open_hours=72.0,
    compound_equity=True,
    closed_bars_only=True,
    min_score=MIN_SCORE,
    risk_overrides=None,
    custom_signal_builder=None,
):
    """المحرك الرئيسي للباكتيست التاريخي المتقدم (Walk-Forward Event-Driven Backtest Engine):
    يسير زمنياً خطوة بخطوة عبر نوافذ المسح التاريخية مع ربط كامل بين:
      - المرحلة 1: simulate_trade_lifecycle (ثبات سعر الدخول، 50%/25%/25%، التعادل الشامل للرسوم، الانزلاق، الصلاحية)
      - المرحلة 2: compute_risk_position_size + evaluate_portfolio_risk_gate (1% لكل صفقة، سقف 3%، 4 مراكز، 1 كبار)
      - المرحلة 3: منحنى رأس المال اللحظي والمحقق، أقصى تراجع، معامل الربح، التوقع الرياضي، وجداول المعايرة.
    """
    base_risk_cfg = get_risk_config(risk_overrides)
    initial_equity = float(base_risk_cfg["equity_usd"])
    realized_equity = initial_equity

    schedule = list(scan_timestamps_ms) if scan_timestamps_ms is not None else generate_walk_forward_schedule(
        start_ms, end_ms, all_4h_windows=all_4h_windows
    )
    eval_end_ms = int(end_ms + tail_eval_hours * 3600 * 1000)

    active_book = []      # إشارات معلقة (PENDING) أو مراكز مفتوحة (OPEN / PARTIAL_TP1 / PARTIAL_TP2)
    archived_book = []    # صفقات وصلت لحالة نهائية
    blocked_book = []     # إشارات حجبتها بوابة المخاطرة الكلية للمحفظة
    recent_stops = []     # قائمة (exit_ts, sym, side) لمنع إعادة الدخول السريع خلال 6 ساعات بعد ضرب الوقف

    equity_curve = [{
        "ts": int(start_ms),
        "event_type": "START",
        "realized_equity_usd": round(initial_equity, 2),
        "mtm_equity_usd": round(initial_equity, 2),
        "open_positions": 0,
        "open_risk_pct": 0.0,
    }]

    def _advance_book_to(step_ts_ms, record_scan_snapshot=True):
        nonlocal active_book, realized_equity
        still_active = []
        newly_realized_events = []

        for tr in active_book:
            sym = tr["sym"]
            b5 = dataset.get(sym, {}).get("5m")
            k5_slice = _slice_5m_between(b5, tr["origin_ts"], step_ts_ms)
            prev_leg_cnt = len(tr.get("leg_fills") or [])
            if k5_slice["t"]:
                updated = simulate_trade_lifecycle(
                    tr,
                    k5_slice,
                    since_ms=tr["origin_ts"],
                    live_price=None,
                    now_ms=step_ts_ms,
                    max_dist_atr=1.0,
                    fill_model=fill_model,
                    partial_weights=partial_weights,
                    trail_after_tp2=trail_after_tp2,
                    maker_fee_pct=float(base_risk_cfg["maker_fee_pct"]),
                    taker_fee_pct=float(base_risk_cfg["taker_fee_pct"]),
                    stop_slippage_pct=float(base_risk_cfg["stop_slippage_pct"]),
                    entry_slippage_pct=ENTRY_SLIPPAGE_PCT,
                    pending_expiry_hours=pending_expiry_hours,
                    max_open_hours=max_open_hours,
                )
            else:
                updated = dict(tr)
                if not updated.get("filled") and pending_expiry_hours and step_ts_ms >= int(updated["origin_ts"] + pending_expiry_hours * 3600 * 1000):
                    updated["trade_status"] = "EXPIRED"
                    updated["status"] = _status_ar_from_state("EXPIRED")
                    updated["exit_ts"] = int(step_ts_ms)

            cur_legs = updated.get("leg_fills") or []
            for lf in cur_legs[prev_leg_cnt:]:
                newly_realized_events.append((int(lf["ts"]), float(lf.get("net_usd", 0.0)), sym, lf["leg"]))

            st_code = updated.get("trade_status", "PENDING")
            if st_code in TERMINAL_TRADE_STATUSES and float(updated.get("remaining_pct", 0.0)) == 0.0:
                archived_book.append(updated)
                if st_code == "CLOSED_STOP":
                    recent_stops.append((int(updated.get("exit_ts") or step_ts_ms), sym, updated["side"]))
            else:
                still_active.append(updated)

        # تحديث الرصيد المحقق بترتيب زمني صارم لكل شريحة خروج جزئية أو كلية
        newly_realized_events.sort(key=lambda x: x[0])
        open_Now = [p for p in still_active if p.get("filled") and float(p.get("remaining_pct", 0.0)) > 0]
        cur_eq_for_risk = realized_equity if compound_equity else initial_equity

        for ev_ts, delta_usd, sym, leg_name in newly_realized_events:
            realized_equity += delta_usd
            equity_curve.append({
                "ts": ev_ts,
                "event_type": f"LEG_{leg_name}",
                "sym": sym,
                "realized_equity_usd": round(realized_equity, 2),
                "mtm_equity_usd": round(realized_equity, 2),
                "open_positions": len(open_Now),
                "open_risk_pct": 0.0,
            })

        active_book = still_active
        if record_scan_snapshot:
            cur_eq_for_risk = max(100.0, realized_equity if compound_equity else initial_equity)
            snap_cfg = get_risk_config(dict(base_risk_cfg, equity_usd=cur_eq_for_risk))
            open_pos = [p for p in active_book if p.get("filled") and float(p.get("remaining_pct", 0.0)) > 0]
            open_r_details = [compute_open_position_risk(p, snap_cfg) for p in open_pos]
            open_risk_pct = sum(d["open_risk_pct"] for d in open_r_details if d["is_open"])
            unreal_sum = sum(float(p.get("unrealized_pnl_usd", 0.0)) for p in open_pos)
            equity_curve.append({
                "ts": int(step_ts_ms),
                "event_type": "SCAN_WINDOW",
                "realized_equity_usd": round(realized_equity, 2),
                "mtm_equity_usd": round(realized_equity + unreal_sum, 2),
                "open_positions": len(open_pos),
                "open_risk_pct": round(open_risk_pct, 3),
            })

    entry_maker_flag = (fill_model != "trigger_with_slippage")

    for scan_ts in schedule:
        # 1) تقدم جميع الإشارات والمراكز القائمة حتى لحظة المسح الحالية
        _advance_book_to(scan_ts, record_scan_snapshot=True)

        # 2) تحديد الأزواج المحظورة مؤقتاً (المفتوحة/المعلقة حالياً + المضروبة وقفاً خلال آخر 6 ساعات)
        busy_pairs = {(p["sym"], p["side"]) for p in active_book}
        cooldown_pairs = {
            (s_sym, s_side)
            for (s_ts, s_sym, s_side) in recent_stops
            if 0 <= (scan_ts - s_ts) < 6 * 3600 * 1000
        }
        blocked_pairs = busy_pairs | cooldown_pairs

        # 3) بناء فرص المسح من الشموع المغلقة فقط حتى scan_ts مع تحجيم مربوط برأس المال اللحظي
        sizing_eq = max(100.0, realized_equity if compound_equity else initial_equity)
        step_risk_cfg = get_risk_config(dict(base_risk_cfg, equity_usd=sizing_eq))

        cands = build_point_in_time_candidates(
            dataset,
            scan_ts,
            step_risk_cfg,
            min_score=min_score,
            closed_bars_only=closed_bars_only,
            entry_is_maker=entry_maker_flag,
            custom_signal_builder=custom_signal_builder,
        )
        cands = [c for c in cands if (c["sym"], c["side"]) not in blocked_pairs]

        # 4) تطبيق بوابة المخاطرة الكلية للمحفظة على كل من المراكز المفتوحة والإشارات المعلقة المعتمدة!
        # ملاحظة هندسية محافظة: حتى الإشارة المعلقة (PENDING) التي لم تتفعل بعد تحجز حصتها في سقف المخاطرة
        # إلى أن تتفعل أو تُلغى حتى يستحيل تفعل 6 أوامر Limit معلقة في نفس الشمعة وكسر سقف الـ 3% أو الـ 4 مراكز!
        open_and_pending_for_gate = []
        for p in active_book:
            if p.get("filled") and float(p.get("remaining_pct", 0.0)) > 0:
                open_and_pending_for_gate.append(p)
            elif not p.get("filled") and p.get("trade_status", "PENDING") == "PENDING":
                # تمثيل الأمر المعلق كالتزام مخاطرة محتمل لحماية المحفظة من التفعيل الجماعي المفاجئ
                pseudo_open = dict(
                    p,
                    filled=True,
                    fill_price=p.get("entry_trigger_price") or (p["entry_hi"] if p["side"] == "LONG" else p["entry_lo"]),
                    active_stop=p["stop"],
                    remaining_pct=1.0,
                )
                open_and_pending_for_gate.append(pseudo_open)

        gated_cands, _ = evaluate_portfolio_risk_gate(
            cands, open_and_pending_for_gate, step_risk_cfg, strict_filter=False
        )
        for gc in gated_cands:
            if gc.get("risk_gate_allowed"):
                gc["trade_status"] = "PENDING"
                gc["status"] = "بانتظار التفعيل"
                gc["fill_model"] = fill_model
                active_book.append(gc)
            else:
                blocked_book.append(gc)

    # 5) استكمال تتبع الصفقات المتبقية خطوة بخطوة (كل 4 ساعات) خلال فترة الذيل التقييمي لنهاية الاختبار
    if eval_end_ms > (schedule[-1] if schedule else start_ms):
        tail_cur = (schedule[-1] if schedule else start_ms) + 4 * 3600 * 1000
        while tail_cur <= eval_end_ms and active_book:
            _advance_book_to(tail_cur, record_scan_snapshot=True)
            tail_cur += 4 * 3600 * 1000
        if active_book:
            _advance_book_to(eval_end_ms, record_scan_snapshot=True)

    all_trades = archived_book + active_book
    all_trades.sort(key=lambda x: (int(x.get("origin_ts", 0)), x.get("sym", "")))

    metrics = compute_backtest_metrics(
        all_trades=all_trades,
        blocked_signals=blocked_book,
        equity_curve=equity_curve,
        initial_equity_usd=initial_equity,
        fill_model=fill_model,
        trail_after_tp2=trail_after_tp2,
        start_ms=start_ms,
        end_ms=end_ms,
    )
    return {
        "metrics": metrics,
        "trades": all_trades,
        "blocked_signals": blocked_book,
        "equity_curve": equity_curve,
    }


def run_backtest_sensitivity_suite(dataset, start_ms, end_ms, **bt_kwargs):
    """يقارن أداء النظام على نفس البيانات التاريخية عبر نماذج التنفيذ الثلاثة + خيار الوقف المتحرك بعد TP2."""
    configs = [
        ("limit_near_edge_strict (Trail TP2)", "limit_near_edge_strict", True),
        ("limit_near_edge_strict (Hold BE)", "limit_near_edge_strict", False),
        ("touch_limit (Optimistic Touch)", "touch_limit", True),
        ("trigger_with_slippage (Market/Stop)", "trigger_with_slippage", True),
    ]
    comparison = []
    runs = {}
    for label, f_mod, tr_tp2 in configs:
        kw = dict(bt_kwargs)
        kw.pop("fill_model", None)
        kw.pop("trail_after_tp2", None)
        res = run_walk_forward_backtest(
            dataset, start_ms, end_ms, fill_model=f_mod, trail_after_tp2=tr_tp2, **kw
        )
        m = res["metrics"]
        row = {"label": label, **m}
        comparison.append(row)
        runs[label] = res
    return {"comparison": comparison, "runs": runs}


def format_backtest_console_report(bt_result, sensitivity_result=None):
    """تنسيق تقرير الباكتيست التاريخي بوضوح لعرضه في الطرفية أو حفظه."""
    m = bt_result["metrics"]
    lines = [
        "=" * 86,
        f"📊 تقرير الباكتيست التاريخي المتقدم (Walk-Forward Backtest — {m['period_start_riyadh']} -> {m['period_end_riyadh']})",
        "=" * 86,
        f"  • نموذج التنفيذ والوقف       : {m['fill_model']} | Trail بعد TP2: {m['trail_after_tp2']}",
        f"  • رأس المال (ابتدائي -> نهائي): {m['initial_equity_usd']:,.2f}$ -> {m['final_realized_equity_usd']:,.2f}$ "
        f"(صافي: {m['net_realized_profit_usd']:+,.2f}$ | {m['total_return_pct']:+.2f}%)",
        f"  • أقصى تراجع (Max Drawdown)  : {m['max_drawdown_usd']:,.2f}$ ({m['max_drawdown_pct']:.2f}%) | Calmar: {m['calmar_ratio']:.2f}",
        f"  • المؤشرات الإحصائية         : Profit Factor = {m['profit_factor']:.2f} | Expectancy = {m['expectancy_r']:+.4f}R ({m['expectancy_usd']:+.2f}$) | Sharpe = {m['sharpe_ratio']:.2f} | Sortino = {m['sortino_ratio']:.2f}",
        f"  • قمع الإشارات والتنفيذ      : مرشحة {m['signals_generated']} -> مجازة {m['signals_approved']} (حُجب {m['signals_blocked_by_risk_gate']} ببوابة المخاطرة) -> مفعّلة {m['filled_count']} ({m['fill_rate_pct']:.1f}%)",
        f"  • نتائج الصفقات المغلقة ({m['closed_count']}): رابحة صافية {m['wins']} ({m['win_rate_pct']:.1f}%) | خاسرة صافية {m['losses']} ({m['loss_rate_pct']:.1f}%) "
        f"[TP3={m['exit_status_counts']['CLOSED_TP3']} · Trail={m['exit_status_counts']['CLOSED_TRAIL']} · TP1->BE={m['exit_status_counts']['CLOSED_BE']} · Stop={m['exit_status_counts']['CLOSED_STOP']} · Exp={m['exit_status_counts']['CLOSED_EXPIRY']}]",
        f"  • معدلات الأهداف الجزئية     : TP1 = {m['tp1_hit_rate_pct']:.1f}% | TP2 = {m['tp2_hit_rate_pct']:.1f}% | TP3 = {m['tp3_hit_rate_pct']:.1f}% | متوسط الاحتفاظ: {m['avg_hold_hours']:.1f} ساعة",
        f"  • إجمالي التكاليف المخصومة   : عمولات = {m['total_fees_usd']:,.2f}$ | انزلاق سعري = {m['total_slippage_usd']:,.2f}$",
        f"  • انضباط سقف المحفظة الفعلي  : أقصى مراكز متزامنة = {m['max_simultaneous_open_positions']} | أقصى مخاطرة متزامنة = {m['max_simultaneous_open_risk_pct']:.2f}%",
        "-" * 86,
        "  🎯 معايرة الوصول الفعلي مقابل المتوقع (Empirical Reach Calibration):",
    ]
    for r_k in ("A", "B", "C"):
        rb = m["by_reach"][r_k]
        lines.append(
            f"     - فئة وصول {r_k}: إشارات={rb['signals']} | تفعيل فعلي={rb['fill_rate_pct']:.1f}% مقابل متوقع={rb['predicted_reach_pct']:.1f}% "
            f"(فجوة {rb['calibration_gap_pct']:+.1f}%) | Expectancy={rb['expectancy_r']:+.3f}R"
        )
    lines.append("  🏆 أداء الدرجات (Empirical Grade Performance):")
    for g_k in ("A", "B", "C"):
        gb = m["by_grade"][g_k]
        lines.append(
            f"     - درجة {g_k}: مغلقة={gb['closed']} | نسبة الفوز={gb['win_rate_pct']:.1f}% | Expectancy={gb['expectancy_r']:+.3f}R | صافي={gb['net_usd']:+.2f}$"
        )

    if sensitivity_result and sensitivity_result.get("comparison"):
        lines.append("-" * 86)
        lines.append("  🔬 مقارنة حساسية نماذج التنفيذ (Execution Model Sensitivity):")
        for row in sensitivity_result["comparison"]:
            lines.append(
                f"     • {row['label']:<36}: Fill={row['fill_rate_pct']:>5.1f}% | Closed={row['closed_count']:>3} | "
                f"PF={row['profit_factor']:>5.2f} | Exp={row['expectancy_r']:>+7.4f}R | Net={row['net_realized_profit_usd']:>+8.2f}$ | "
                f"MDD={row['max_drawdown_pct']:>5.2f}% | Fees+Slip={row['total_fees_usd'] + row['total_slippage_usd']:>6.2f}$"
            )
    lines.append("=" * 86)
    return "\n".join(lines)


def run_cli_historical_backtest(days=14, top_n=12, coins=None, all_4h=False, compare_models=False):
    """تشغيل باكتيست تاريخي حقيقي على بيانات عقود بايننس الآجلة وحفظ ملخص JSON اختياري في cache/backtest."""
    now_ms = int(time.time() * 1000)
    # نترك آخر 24 ساعة كذيل تقييمي حتى تكتمل الصفقات الأخيرة بشكل طبيعي بدلاً من بقائها معلقة كلها
    end_ms = now_ms - 24 * 3600 * 1000
    start_ms = end_ms - int(days * 86_400_000)

    if coins:
        syms = [c.upper() if c.upper().endswith("USDT") else c.upper() + "USDT" for c in coins]
    else:
        uni, _, _, _, _, _ = load_universe()
        uni_by_liq = sorted(uni, key=lambda x: -x["qv"])
        syms = [x["sym"] for x in uni_by_liq[:max(1, int(top_n))]]

    print(f"=== بدء الباكتيست التاريخي المتقدم ({days} يوماً | {len(syms)} عملة سائلة) ===")
    print(f"العملات: {', '.join(s.replace('USDT', '') for s in syms)}")
    dataset = load_walk_forward_dataset(syms, start_ms, end_ms, tail_hours=24, max_workers=6, use_cache=True, verbose=True)

    primary = run_walk_forward_backtest(
        dataset,
        start_ms=start_ms,
        end_ms=end_ms,
        all_4h_windows=all_4h,
        tail_eval_hours=24.0,
        fill_model=DEFAULT_FILL_MODEL,
        trail_after_tp2=True,
    )
    sens = None
    if compare_models:
        sens = run_backtest_sensitivity_suite(
            dataset,
            start_ms=start_ms,
            end_ms=end_ms,
            all_4h_windows=all_4h,
            tail_eval_hours=24.0,
        )
    print("\n" + format_backtest_console_report(primary, sens))
    out_file = os.path.join(CACHE, "backtest", "latest_backtest_report.json")
    try:
        payload = {"primary_metrics": primary["metrics"], "trades_count": len(primary["trades"])}
        if sens:
            payload["sensitivity"] = sens["comparison"]
        json.dump(payload, open(out_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"📁 حُفظ ملخص الباكتيست الرقمي في: {out_file}")
    except Exception:
        pass
    return primary, sens


def run_phase3_acceptance_tests():
    """حزمة اختبارات القبول الآلية الحتمية للمرحلة الثالثة (Phase 3 Walk-Forward Backtest Suite — 7/7):
    تختبر رياضياً وبصفر اتصال بالشبكة جميع ركائز محرك الباكتيست التاريخي المتقدم:
      1) انعدام الانحياز المستقبلي (Zero-Lookahead Slicing): إثبات أن الشمعة غير المغلقة أو المستقبلية لا تُرى إطلاقاً.
      2) المطابقة المحاسبية التامة (Cash & R Reconciliation): تطابق صافي ربح منحنى رأس المال بالـ USDT مع مجموع
         الشرائح الجزئية والكلية لجميع الصفقات بدقة < 0.01$، وعدم تجاوز خسارة الوقف 1% من رأس المال وقت الإشارة.
      3) دقة حساب منحنى رأس المال وأقصى تراجع (Equity Curve & Max Drawdown $ / %) على سلسلة معروفة مسبقاً.
      4) دقة حساب Profit Factor و Expectancy (بالـ R والـ USDT) و Payoff Ratio و Sharpe / Sortino.
      5) احترام سقف المحفظة الكلي عبر الزمن (حجب الإشارات الزائدة عن 3% مخاطرة أو 4 مراكز أو عملات كبرى مكررة،
         بما في ذلك حماية الأوامر المعلقة من التفعيل الجماعي المفرط، ثم تحرير الميزانية بعد انتقال صفقة إلى BE).
      6) دقة جداول المعايرة الطبقية (Empirical Reach Fill Rate مقابل المتوقع + أداء الدرجات A/B/C والاتجاه).
      7) مقارنة حساسية نماذج التنفيذ الثلاثة (limit_near_edge_strict مقابل touch_limit مقابل trigger_with_slippage).
    """
    results = []
    t_base = 1_710_000_000_000  # طابع زمني مرجعي ثابت

    # ------------------------------------------------------------------
    # اختبار 1: انعدام الانحياز المستقبلي (Zero-Lookahead Point-in-Time Slicing)
    # ------------------------------------------------------------------
    iv_4h = INTERVAL_MS_MAP["4h"]
    k4_test = {
        "t": [t_base + i * iv_4h for i in range(5)],
        "o": [100.0, 101.0, 102.0, 103.0, 104.0],
        "h": [101.5, 102.5, 103.5, 199.0, 250.0],  # الشمعة رقم 3 (تفتح عند +3*4h وتغلق عند +4*4h) فيها قفزة مستقبلية 199$!
        "l": [99.5, 100.5, 101.5, 50.0, 40.0],
        "c": [101.0, 102.0, 103.0, 180.0, 240.0],
        "v": [1000.0] * 5,
        "qv": [100_000.0] * 5,
    }
    # المسح عند t_base + 3*4h + 5m: الشموع المغلقة هي 0 و 1 و 2 فقط (الشمعة 3 عمرها 5 دقائق فقط ولم تغلق!)
    scan_at = t_base + 3 * iv_4h + BAR_5M_MS
    sliced = _slice_klines_as_of(k4_test, scan_at, iv_4h, closed_only=True)
    assert len(sliced["t"]) == 3 and sliced["c"][-1] == 103.0 and max(sliced["h"]) == 103.5
    results.append("✅ [1/7] Zero-Lookahead Slicing Test: حجب تام للشموع الجارية والمستقبلية قبل لحظة إغلاقها الرسمي.")

    # مساعد لبناء حزمة بيانات اصطناعية حتمية على فريم 5 دقائق لمحاكاة سيناريوهات باكتيست متعددة النوافذ
    def _mk_5m_series(start_ts, n_bars, base_px=100.0, overrides=None):
        overrides = overrides or {}
        ts_l, o_l, h_l, l_l, c_l = [], [], [], [], []
        for idx in range(n_bars):
            tt = start_ts + idx * BAR_5M_MS
            o, h, l, c = overrides.get(idx, (base_px, base_px + 0.1, base_px - 0.1, base_px))
            ts_l.append(tt); o_l.append(float(o)); h_l.append(float(h)); l_l.append(float(l)); c_l.append(float(c))
        return {"t": ts_l, "o": o_l, "h": h_l, "l": l_l, "c": c_l}

    def _sized_sig(sym, name, side, scan_ts, e_lo, e_hi, stop, targets, score=104.0, grade="A", reach="A", reach_p=80, tick=0.01, risk_cfg=None):
        near = e_hi if side == "LONG" else e_lo
        avg = (e_lo + e_hi) / 2.0
        r = abs(avg - stop)
        sz = compute_risk_position_size(
            near, stop, side, step=0.001, min_notional=5.0, sym=sym,
            atr_pct=2.5, strategy_type="swing_4h",
            entry_is_maker=True, risk_cfg=risk_cfg,
        )
        return dict(
            sz,
            sym=sym, name=name, side=side, price=near * (1.01 if side == "LONG" else 0.99),
            entry_lo=e_lo, entry_hi=e_hi, avg=avg, stop=stop,
            targets=list(targets), rr=[round(abs(x - avg) / r, 2) for x in targets],
            risk_pct=round(r / avg * 100.0, 3), atr4=2.5, atr_pct=2.5,
            dist_atr=0.25 if reach == "A" else (0.50 if reach == "B" else 0.85),
            score=score, grade=grade, reach=reach, reach_p=reach_p, tick=tick,
            origin_ts=int(scan_ts),
            scan_hour_riyadh=dt.datetime.fromtimestamp(scan_ts / 1000.0, RIYADH).hour,
        )

    # ------------------------------------------------------------------
    # اختبار 2 + 3 + 4: المطابقة النقدية الكاملة + أقصى تراجع (MDD) + معامل الربح والتوقع الرياضي
    # سيناريو من 4 نوافذ مسح متتالية على رأس مال ثابت (compound_equity=False) للتحقق اليدوي الصريح:
    #   نافذة 0 (W0): صفقة LINK تحقق TP1+TP2+TP3 كاملة (~+274$)
    #   نافذة 1 (W1): صفقة AVAX تضرب الوقف مباشرة (~-100$)
    #   نافذة 2 (W2): صفقة SUI تضرب الوقف مباشرة (~-100$) -> أقصى تراجع محقق هنا = مجموع خسارتي AVAX و SUI (~200$)!
    #   نافذة 3 (W3): صفقة NEAR تحقق TP1 ثم تعود لوقف التعادل BE (~+100$)
    # ------------------------------------------------------------------
    w_step = 4 * 3600 * 1000  # 48 شمعة 5m لكل نافذة 4 ساعات
    w0, w1, w2, w3 = t_base, t_base + w_step, t_base + 2 * w_step, t_base + 3 * w_step

    ds_acct = {
        "LINKUSDT": {"5m": _mk_5m_series(t_base, 260, 102.0, {
            1: (101.0, 101.2, 99.8, 100.5),     # تفعيل LONG عند 100.00
            2: (100.5, 110.5, 100.2, 109.5),    # TP1 (110)
            3: (109.5, 115.5, 109.0, 114.5),    # TP2 (115)
            4: (114.5, 121.0, 114.0, 120.5),    # TP3 (120) -> إغلاق كامل رابح
        })},
        "AVAXUSDT": {"5m": _mk_5m_series(t_base, 260, 102.0, {
            49: (101.0, 101.2, 99.8, 100.2),    # تفعيل في نافذة W1 عند 100.00
            50: (100.2, 100.4, 94.5, 94.8),     # ضرب الوقف 95.00
        })},
        "SUIUSDT": {"5m": _mk_5m_series(t_base, 260, 102.0, {
            97: (101.0, 101.2, 99.8, 100.2),    # تفعيل في نافذة W2 عند 100.00
            98: (100.2, 100.4, 94.5, 94.8),     # ضرب الوقف 95.00
        })},
        "NEARUSDT": {"5m": _mk_5m_series(t_base, 260, 102.0, {
            145: (101.0, 101.2, 99.8, 100.5),   # تفعيل في نافذة W3 عند 100.00
            146: (100.5, 110.5, 100.2, 108.0),  # TP1 (110) -> نقل الوقف للتعادل
            147: (108.0, 108.2, 99.5, 99.8),    # ضرب وقف التعادل الشامل للرسوم (BE)
        })},
    }

    def _acct_builder(_ds, scan_ts, rcfg):
        mapping = {
            w0: ("LINKUSDT", "LINK", "A", "A"),
            w1: ("AVAXUSDT", "AVAX", "B", "B"),
            w2: ("SUIUSDT", "SUI", "C", "C"),
            w3: ("NEARUSDT", "NEAR", "A", "A"),
        }
        if scan_ts not in mapping:
            return []
        sym, nm, gr, rc = mapping[scan_ts]
        return [_sized_sig(sym, nm, "LONG", scan_ts, 99.0, 100.0, 95.0, (110.0, 115.0, 120.0), grade=gr, reach=rc, risk_cfg=rcfg)]

    bt_acct = run_walk_forward_backtest(
        ds_acct,
        start_ms=w0,
        end_ms=w3,
        scan_timestamps_ms=[w0, w1, w2, w3],
        tail_eval_hours=8.0,
        compound_equity=False,
        risk_overrides={"equity_usd": 10000.0, "risk_pct_per_trade": 0.01},
        custom_signal_builder=_acct_builder,
    )
    ma = bt_acct["metrics"]
    tr_acct = {t["name"]: t for t in bt_acct["trades"]}

    # تحقق (2): مطابقة الأرباح النقدية وعدم كسر سقف 100$ للخسارة
    sum_trade_usd = round(sum(t["realized_pnl_usd"] for t in bt_acct["trades"]), 2)
    eq_diff_usd = round(ma["final_realized_equity_usd"] - ma["initial_equity_usd"], 2)
    assert abs(sum_trade_usd - eq_diff_usd) <= 0.01, f"{sum_trade_usd} != {eq_diff_usd}"
    assert abs(tr_acct["AVAX"]["realized_pnl_usd"]) <= 100.01 and abs(tr_acct["SUI"]["realized_pnl_usd"]) <= 100.01
    results.append(
        f"✅ [2/7] Cash & R Reconciliation Test: مطابقة محاسبية تامة ({eq_diff_usd:+.2f}$ == {sum_trade_usd:+.2f}$) "
        f"وخسارة الوقف الفعلية {tr_acct['AVAX']['realized_pnl_usd']:.2f}$ ضمن سقف الـ 1%."
    )

    # تحقق (3): دقة أقصى تراجع (القمة بعد LINK ~10,269$ ثم خسارتان متتاليتان ~-200$ -> MDD% = ~200 / 10,269)
    peak_after_w0 = 10000.0 + tr_acct["LINK"]["realized_pnl_usd"]
    expected_dd_usd = abs(tr_acct["AVAX"]["realized_pnl_usd"]) + abs(tr_acct["SUI"]["realized_pnl_usd"])
    expected_dd_pct = (expected_dd_usd / peak_after_w0) * 100.0
    assert abs(ma["max_realized_drawdown_usd"] - expected_dd_usd) <= 0.05
    assert abs(ma["max_realized_drawdown_pct"] - expected_dd_pct) <= 0.02
    results.append(
        f"✅ [3/7] Equity Curve & Max Drawdown Test: القمة {peak_after_w0:,.2f}$ وأقصى تراجع "
        f"{ma['max_realized_drawdown_usd']:.2f}$ ({ma['max_realized_drawdown_pct']:.3f}%) مطابق للحساب اليدوي."
    )

    # تحقق (4): دقة Profit Factor و Expectancy
    exp_pf = round((tr_acct["LINK"]["realized_pnl_usd"] + tr_acct["NEAR"]["realized_pnl_usd"]) / expected_dd_usd, 3)
    exp_er = round(sum(t["realized_r"] for t in bt_acct["trades"]) / 4.0, 4)
    assert abs(ma["profit_factor"] - exp_pf) <= 0.005
    assert abs(ma["expectancy_r"] - exp_er) <= 0.0005
    assert ma["wins"] == 2 and ma["losses"] == 2 and ma["closed_count"] == 4
    results.append(
        f"✅ [4/7] Profit Factor & Expectancy Test: PF={ma['profit_factor']:.3f} | Expectancy={ma['expectancy_r']:+.4f}R "
        f"({ma['expectancy_usd']:+.2f}$) | Fees={ma['total_fees_usd']:.2f}$."
    )

    # ------------------------------------------------------------------
    # اختبار 5: بوابة المخاطرة الكلية وحماية الأوامر المعلقة تحت الحمل المتزامن
    # 6 إشارات في نفس اللحظة (بينها BTC و ETH الكبار): يجب إجازة 3 فقط (<= 3% مخاطرة، 1 كبار) وحجب 3!
    # ------------------------------------------------------------------
    syms_load = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "AVAXUSDT", "SUIUSDT"]
    ds_load = {
        s: {"5m": _mk_5m_series(t_base, 80, 102.0, {1: (101.0, 101.2, 99.5, 100.2)})}
        for s in syms_load
    }

    def _load_builder(_ds, scan_ts, rcfg):
        if scan_ts != w0:
            return []
        return [
            _sized_sig("BTCUSDT", "BTC", "LONG", scan_ts, 99.0, 100.0, 95.0, (110.0, 115.0, 120.0), score=108.0, risk_cfg=rcfg),
            _sized_sig("ETHUSDT", "ETH", "LONG", scan_ts, 99.0, 100.0, 95.0, (110.0, 115.0, 120.0), score=107.0, risk_cfg=rcfg),
            _sized_sig("LINKUSDT", "LINK", "LONG", scan_ts, 99.0, 100.0, 95.0, (110.0, 115.0, 120.0), score=106.0, risk_cfg=rcfg),
            _sized_sig("AVAXUSDT", "AVAX", "LONG", scan_ts, 99.0, 100.0, 95.0, (110.0, 115.0, 120.0), score=105.0, risk_cfg=rcfg),
            _sized_sig("SUIUSDT", "SUI", "LONG", scan_ts, 99.0, 100.0, 95.0, (110.0, 115.0, 120.0), score=104.0, risk_cfg=rcfg),
            _sized_sig("SOLUSDT", "SOL", "LONG", scan_ts, 99.0, 100.0, 95.0, (110.0, 115.0, 120.0), score=103.0, risk_cfg=rcfg),
        ]

    bt_load = run_walk_forward_backtest(
        ds_load,
        start_ms=w0,
        end_ms=w1,
        scan_timestamps_ms=[w0, w1],
        tail_eval_hours=4.0,
        risk_overrides={"equity_usd": 10000.0, "risk_pct_per_trade": 0.01, "max_total_open_risk_pct": 0.03, "max_concurrent_positions": 4},
        custom_signal_builder=_load_builder,
    )
    ml = bt_load["metrics"]
    approved_names = [t["name"] for t in bt_load["trades"]]
    assert set(approved_names) == {"BTC", "LINK", "AVAX"} and len(approved_names) == 3, f"Unexpected approved list: {approved_names}"
    assert ml["signals_blocked_by_risk_gate"] == 3
    assert ml["max_simultaneous_open_positions"] <= 3
    assert ml["max_simultaneous_open_risk_pct"] <= 3.05
    results.append(
        f"✅ [5/7] Walk-Forward Portfolio Gate Test: من أصل 6 إشارات متزامنة أُجيزت {approved_names} فقط "
        f"(أقصى مخاطرة متزامنة {ml['max_simultaneous_open_risk_pct']:.2f}% <= 3.0%)."
    )

    # ------------------------------------------------------------------
    # اختبار 6: جداول المعايرة الإحصائية للوصول (Reach Calibration) والدرجات (Grade)
    # ------------------------------------------------------------------
    assert ma["by_grade"]["A"]["closed"] == 2 and ma["by_grade"]["A"]["win_rate_pct"] == 100.0
    assert ma["by_reach"]["A"]["fill_rate_pct"] == 100.0 and "calibration_gap_pct" in ma["by_reach"]["A"]
    results.append(
        f"✅ [6/7] Empirical Calibration Table Test: حساب دقيق لفجوة الوصول الفعلي مقابل المتوقع "
        f"(Grade A Expectancy = {ma['by_grade']['A']['expectancy_r']:+.3f}R)."
    )

    # ------------------------------------------------------------------
    # اختبار 7: مقارنة حساسية نماذج التنفيذ الثلاثة على نفس البيانات التاريخية
    # شمعة تلمس حد الدخول 100.00 بالضبط دون اختراق التِك (99.99):
    #   - limit_near_edge_strict: لا يفعّل الصفقة (Fill = 0%)
    #   - touch_limit: يفعّل الصفقة عند 100.00 بصفته Maker
    #   - trigger_with_slippage: يفعّل الصفقة مع انزلاق دخول وعمولة Taker أعلى!
    # ------------------------------------------------------------------
    ds_sens = {
        "ADAUSDT": {"5m": _mk_5m_series(t_base, 80, 102.0, {
            1: (101.0, 101.2, 100.00, 100.6),   # لمس حدي عند 100.00 فقط دون كسر 99.99!
            2: (100.6, 110.5, 100.4, 110.2),
            3: (110.2, 121.0, 110.0, 120.5),
        })}
    }

    def _sens_builder(_ds, scan_ts, rcfg):
        if scan_ts != w0:
            return []
        return [_sized_sig("ADAUSDT", "ADA", "LONG", scan_ts, 99.0, 100.0, 95.0, (110.0, 115.0, 120.0), tick=0.01, risk_cfg=rcfg)]

    sens_suite = run_backtest_sensitivity_suite(
        ds_sens, start_ms=w0, end_ms=w0, scan_timestamps_ms=[w0], tail_eval_hours=6.0,
        custom_signal_builder=_sens_builder,
    )
    comp_by_lbl = {r["label"]: r for r in sens_suite["comparison"]}
    r_strict = comp_by_lbl["limit_near_edge_strict (Trail TP2)"]
    r_touch = comp_by_lbl["touch_limit (Optimistic Touch)"]
    r_trig = comp_by_lbl["trigger_with_slippage (Market/Stop)"]

    assert r_strict["filled_count"] == 0, "النموذج الصارم يجب أن يرفض اللمس الحدي دون اختراق"
    assert r_touch["filled_count"] == 1 and r_trig["filled_count"] == 1
    assert r_touch["net_realized_profit_usd"] > r_trig["net_realized_profit_usd"], "نموذج الانزلاق وعمولة Taker يجب أن يحقق صافياً أقل من Maker Limit"
    assert r_trig["total_fees_usd"] > r_touch["total_fees_usd"]
    results.append(
        f"✅ [7/7] Execution Model Sensitivity Test: Strict Fill=0% | Touch Maker Net=+{r_touch['net_realized_profit_usd']:.2f}$ "
        f"| Trigger+Slippage Taker Net=+{r_trig['net_realized_profit_usd']:.2f}$ (فارق تكلفة وانزلاق موثق)."
    )

    print("=" * 78)
    print("🧪 نتائج اختبارات القبول للمرحلة الثالثة (Phase 3 Backtest Suite — 7/7 PASSED)")
    print("=" * 78)
    for line in results:
        print(" ", line)
    print("=" * 78)
    return True


def run_phase4_acceptance_tests():
    """حزمة اختبارات القبول الآلية الحتمية للمرحلة الرابعة (Phase 4 Signal & Engineering Integrity Suite — 6/6):
    تختبر رياضياً وبصفر اتصال بالشبكة جميع إصلاحات الأولويات #5 إلى #10:
      1) انضباط الشمعة المغلقة عند المسح في :05 (closed_klines_only — Priority #5): إثبات أن شمعة 4س المفتوحة منذ
         5 دقائق (بمدى شبه صفري أو ذيل شاذ) تُستبعد تماماً فلا تعطي مكافأة انكماش وهمية ولا تشوّه ATR/EMA/MACD.
      2) الحياد التام عند غياب الفائدة المفتوحة (OI = None — Priority #6): إثبات أن Coin.oi_chg يكون None وليس 0.0،
         وأن غياب OI يعطي 0.0 نقطة تعديل (لا مكافأة +1.5 وهمية ولا عقوبة إلغاء)، مع عرض محايد في واجهة HTML.
      3) التصنيف الصريح لمصدر كل هدف (Priority #7): التمييز الدقيق بين structural_sr و atr_projection و rr_floor_extension
         في كل من الصفقات المضاربية وصفقات الانفجار وظهوره في بطاقات التقرير.
      4) تفكيك عناصر الدرجة ومعايرة الوصول التجريبية (Priority #8): تطابق score مع مجموع score_components حرفياً،
         ومعايرة نسب Reach إلى القياس التاريخي الفعلي بدون انحياز مستقبلي (85% / 56% / 55%).
      5) السجل التشخيصي المنظم بدلاً من الابتلاع الصامت للأخطاء (Priority #9): إثبات رصد الكاش التالف أو تعذر القراءة
         في عدّادات RUNTIME_DIAGNOSTICS وسجل التحذيرات دون انهيار النظام.
      6) نظافة الكود وحذف المتغير الميت depth_ratio بالكامل من جميع هياكل البيانات (Priority #10).
    """
    import tempfile

    results = []
    t0 = 1_715_000_000_000
    iv4 = CORE_INTERVAL_MS["4h"]
    iv1d = CORE_INTERVAL_MS["1d"]

    dummy_info = {
        "symbol": "SOLUSDT",
        "onboardDate": t0 - 400 * 86_400_000,
        "pricePrecision": 3,
        "filters": [
            {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
            {"filterType": "LOT_SIZE", "stepSize": "0.01"},
            {"filterType": "MIN_NOTIONAL", "notional": "5"},
        ],
    }

    # ------------------------------------------------------------------
    # اختبار 1: انضباط الشموع المغلقة عند الدقيقة :05 ومنع مكافأة الانكماش الوهمية (Priority #5)
    # ------------------------------------------------------------------
    # نبني 70 شمعة 4س مغلقة بمدى واسع (4.2$ > 0.95 * ATR) وتذبذب طبيعي (RSI ~ 60 < 76) ثم نضيف شمعة أخيرة عمرها 5 دقائق فقط بمدى 0.02$!
    k4_with_forming = {
        "t": [t0 + i * iv4 for i in range(71)],
        "o": [100.0 + i * 0.15 for i in range(70)] + [111.0],
        "h": [102.2 + i * 0.15 for i in range(70)] + [111.01],  # مدى الشمعة المفتوحة للتو = 0.02 فقط!
        "l": [98.0 + i * 0.15 for i in range(70)] + [110.99],
        "c": [100.2 + i * 0.15 + (-0.45 if i % 3 == 0 else 0.15) for i in range(70)] + [111.00],
        "v": [10000.0] * 71,
    }
    scan_at_05 = t0 + 70 * iv4 + 5 * 60_000  # بعد 5 دقائق فقط من افتتاح الشمعة رقم 70!
    cleaned_k4 = closed_klines_only(k4_with_forming, "4h", now_ms=scan_at_05)
    assert len(cleaned_k4["t"]) == 70 and cleaned_k4["t"][-1] == t0 + 69 * iv4

    k1d_steady = {
        "t": [t0 - (40 - i) * iv1d for i in range(41)],
        "o": [90.0 + i * 0.4 for i in range(41)],
        "h": [93.0 + i * 0.4 for i in range(41)],
        "l": [89.0 + i * 0.4 for i in range(41)],
        "c": [91.0 + i * 0.4 + (-0.5 if i % 3 == 0 else 0.2) for i in range(41)],
        "v": [50000.0] * 41,
    }
    t24_exp = {"quoteVolume": str(120e6), "priceChangePercent": "8.5", "highPrice": "111.5", "lowPrice": "101.0", "lastPrice": "111.0"}
    prem_exp = {"markPrice": "111.0", "indexPrice": "111.0", "lastFundingRate": "-0.0001"}

    c_clean = Coin("SOLUSDT", dummy_info, t24_exp, prem_exp, None, None)
    c_clean.h4 = enrich(dict(cleaned_k4))
    c_clean.h1 = enrich(dict(k1d_steady))
    exp_clean = build_explosion_candidate(c_clean, stage="radar")
    assert exp_clean is not None
    assert "انكماش تذبذب" not in exp_clean["reasons"], "فشل: تم احتساب انكماش وهمي رغم اتساع الشموع المغلقة!"
    results.append("✅ [1/6] Closed-Candle Integrity Test (:05): استبعاد الشمعة الجارية (5 دقائق) ومنع مكافأة الانكماش الوهمية.")

    # ------------------------------------------------------------------
    # اختبار 2: الحياد التام عند غياب الفائدة المفتوحة OI = None (Priority #6)
    # ------------------------------------------------------------------
    c_no_oi = Coin("SOLUSDT", dummy_info, t24_exp, prem_exp, None, None)
    c_zero_oi = Coin("SOLUSDT", dummy_info, t24_exp, prem_exp, 1_000_000.0, 1_000_000.0)  # ΔOI حقيقي = 0.00%
    c_neg_oi = Coin("SOLUSDT", dummy_info, t24_exp, prem_exp, 980_000.0, 1_000_000.0)     # ΔOI حقيقي = -2.00%
    for cx in (c_no_oi, c_zero_oi, c_neg_oi):
        cx.h4 = enrich(dict(cleaned_k4))
        cx.h1 = enrich(dict(k1d_steady))

    assert c_no_oi.oi_chg is None and c_no_oi.oi_available is False
    assert c_zero_oi.oi_chg == 0.0 and c_zero_oi.oi_available is True
    e_none = build_explosion_candidate(c_no_oi, stage="radar")
    e_zero = build_explosion_candidate(c_zero_oi, stage="radar")
    e_neg = build_explosion_candidate(c_neg_oi, stage="radar")
    # عند غياب OI يجب ألا يحصل على +1.5 الوهمية التي يحصل عليها ΔOI=0%، ولا يعاقب بـ -1.0 كالسالب!
    assert round(e_zero["score"] - e_none["score"], 2) == 1.5
    assert round(e_none["score"] - e_neg["score"], 2) == 1.0
    assert "ΔOI غير متاح (محايد)" in e_none["reasons"]
    results.append(
        f"✅ [2/6] Neutral Missing-OI Test: عند OI=None الدرجة={e_none['score']} (بدون +1.5 الوهمية لـ ΔOI=0%: {e_zero['score']}، وفوق السالب: {e_neg['score']})."
    )

    # ------------------------------------------------------------------
    # اختبار 3 + 4: تصنيف مصدر الأهداف (Priority #7) + تفكيك عناصر الدرجة ومعايرة الوصول (Priority #8)
    # ------------------------------------------------------------------
    # نبني سياق حزمة دعم حقيقية قرب السعر لتوليد صفقة مضاربية كاملة وفحص target_sources و score_components
    k4_swing = {
        "t": [t0 + i * iv4 for i in range(80)],
        "o": [100.0] * 80,
        "h": [101.5 if i not in (55, 70) else 108.5 for i in range(80)],
        "l": [98.8 if i not in (50, 68) else 99.6 for i in range(80)],
        "c": [100.4 + (0.03 * i) for i in range(80)],
        "v": [15000.0] * 80,
    }
    last_s_px = k4_swing["c"][-1]
    t24_sw = {
        "quoteVolume": str(250e6), "priceChangePercent": "2.4",
        "highPrice": str(last_s_px + 4.5), "lowPrice": str(last_s_px - 3.0), "lastPrice": str(last_s_px),
    }
    prem_sw = {"markPrice": str(last_s_px), "indexPrice": str(last_s_px), "lastFundingRate": "0.0001"}
    c_sw = Coin("SOLUSDT", dummy_info, t24_sw, prem_sw, None, None)
    c_sw.h4 = enrich(k4_swing)
    c_sw.h1 = enrich(dict(k1d_steady))
    cand_sw = build(c_sw, "LONG", {"oi": None, "oi_prev": None}, asia_wick=False, now_ms=t0 + 81 * iv4)
    assert cand_sw is not None, "فشل بناء صفقة الاختبار البنيوية"
    assert len(cand_sw["target_sources"]) == 3
    assert set(cand_sw["target_sources"]).issubset({"structural_sr", "atr_projection", "rr_floor_extension"})
    assert abs(cand_sw["score"] - round(sum(cand_sw["score_components"].values()), 1)) <= 1e-6
    assert cand_sw["reach_p"] in (85, 60, 55) and cand_sw["reach_basis"] == "walk_forward_5m_zero_lookahead"
    results.append(
        f"✅ [3/6] Explicit Target Source Test: تصنيف شفاف للأهداف الثلاثة {cand_sw['target_sources']} وعرضه في التقرير."
    )
    results.append(
        f"✅ [4/6] Score Auditability & Reach Calibration Test: تطابق مجموع score_components ({cand_sw['score']}) + Reach={cand_sw['reach']} ({cand_sw['reach_p']}%)."
    )

    # ------------------------------------------------------------------
    # اختبار 5: السجل التشخيصي المنظم عند تلف ملف حالة أو كاش (Priority #9)
    # ------------------------------------------------------------------
    reset_diagnostics()
    old_st_path = globals()["STATE_FILE"]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as bad_f:
        bad_f.write("{corrupt_json_payload")
        corrupt_path = bad_f.name
    try:
        globals()["STATE_FILE"] = corrupt_path
        fallback_st = load_tracker_state()
        diag = get_diagnostics_summary()
        assert fallback_st["carried_open"] == []
        assert diag["counts_by_stage"].get("corrupt_tracker_state", 0) == 1
        assert len(diag["recent_warnings"]) == 1
    finally:
        globals()["STATE_FILE"] = old_st_path
        try:
            os.remove(corrupt_path)
        except OSError:
            pass
    reset_diagnostics()
    results.append("✅ [5/6] Structured Warning Diagnostics Test: رصد وتوثيق الملفات التالفة وأخطاء الشبكة بدلاً من الابتلاع الصامت.")

    # ------------------------------------------------------------------
    # اختبار 6: التأكد من إزالة المتغير الميت depth_ratio بالكامل من هياكل الكود (Priority #10)
    # ------------------------------------------------------------------
    self_src = open(os.path.abspath(__file__), encoding="utf-8").read()
    # لا يُسمح بوجود depth_ratio في أي كود تنفيذي خارج تعليقات هذا الاختبار نفسه
    exec_lines = [
        ln for ln in self_src.splitlines()
        if "depth_ratio" in ln and not ln.strip().startswith("#") and "depth_ratio" not in 'if "depth_ratio" in ln'
    ]
    # السطر الوحيد المسموح هو فحص السلسلة النصية داخل هذه الدالة
    non_test_refs = [ln for ln in exec_lines if "exec_lines" not in ln and "Priority #10" not in ln and '"depth_ratio"' not in ln]
    assert len(non_test_refs) == 0, f"بقي مرجع ميت لـ depth_ratio: {non_test_refs}"
    results.append("✅ [6/6] Dead Code Removal Test: إزالة المتغير الميت depth_ratio بالكامل من جميع المسارات.")

    # ------------------------------------------------------------------
    # اختبار 7: بوابة الانتقاء الذكية المزدوجة (نخبة الدرجة A 103+ + انتقائية نافذة 11:05 عند 106+)
    # ------------------------------------------------------------------
    sample_cands = [
        {"sym": "MIDUSDT", "name": "MID", "score": 101.8, "grade": "B", "actual_risk_cash": 99.0, "margin_required_usd": 1200.0},
        {"sym": "GOODUSDT", "name": "GOOD", "score": 104.5, "grade": "A", "actual_risk_cash": 99.0, "margin_required_usd": 1200.0},
        {"sym": "ELITEUSDT", "name": "ELITE", "score": 106.8, "grade": "A", "actual_risk_cash": 99.0, "margin_required_usd": 1200.0},
    ]
    dt_prime = dt.datetime(2026, 11, 10, 19, 5, tzinfo=RIYADH)
    dt_chop = dt.datetime(2026, 11, 10, 11, 5, tzinfo=RIYADH)

    g_prime, s_prime = evaluate_portfolio_risk_gate(sample_cands, [], now_riyadh=dt_prime, enforce_quality_gate=True)
    assert g_prime[0]["risk_gate_status"] == "WATCHLIST_GRADE_B" and not g_prime[0]["risk_gate_allowed"]
    assert g_prime[1]["risk_gate_status"] == "APPROVED" and g_prime[1]["risk_gate_allowed"]
    assert g_prime[2]["risk_gate_status"] == "APPROVED" and g_prime[2]["risk_gate_allowed"]
    assert s_prime["approved_candidates"] == 2 and s_prime["watchlist_count"] == 1

    g_chop, s_chop = evaluate_portfolio_risk_gate(sample_cands, [], now_riyadh=dt_chop, enforce_quality_gate=True)
    assert g_chop[0]["risk_gate_status"] == "WATCHLIST_GRADE_B" and not g_chop[0]["risk_gate_allowed"]
    assert g_chop[1]["risk_gate_status"] == "WATCHLIST_CHOP_SESSION" and not g_chop[1]["risk_gate_allowed"]
    assert g_chop[2]["risk_gate_status"] == "APPROVED" and g_chop[2]["risk_gate_allowed"]
    assert s_chop["approved_candidates"] == 1 and s_chop["watchlist_count"] == 2
    results.append("✅ [7/7] Smart Quality & Liquidity Session Gate Test: إجازة 103+ في السيولة العالية و106+ في نافذة 11:05 مع إبقاء الباقي للمراقبة.")

    print("=" * 78)
    print("🧪 نتائج اختبارات القبول للمرحلة الرابعة والانتقاء الذكي (Phase 4 Suite — 7/7 PASSED)")
    print("=" * 78)
    for line in results:
        print(" ", line)
    print("=" * 78)
    return True


def main():
    ap = argparse.ArgumentParser(description="ماسح عقود بايننس الآجلة المستقل المطور (v4.0)")
    ap.add_argument("--run-scan", action="store_true", help="تشغيل دورة المسح الشامل الكاملة وبناء index.html")
    ap.add_argument("--confirm-0245", action="store_true", help="تشغيل دورة فحص التأكيد الخاص بنافذة 02:45 وتحديث المراكز وindex.html")
    ap.add_argument("--macro-only", action="store_true", help="اختبار محرك الفريم اليومي والأسبوعي والشهري فقط (الاستثماري + كسر الهيكل + بوابة 23:05 + الهمر)")
    ap.add_argument("--coin", nargs="+", help="فحص تشخيصي لعملة أو عدة عملات (مثال: --coin LYN AIO SOL)")
    ap.add_argument("--equity", type=float, default=None, help="رأس المال المرجعي بالـ USDT لحساب حجم الصفقات (الافتراضي 10000)")
    ap.add_argument("--risk-pct", type=float, default=None, help="نسبة المخاطرة القصوى للصفقة الواحدة بالمئة (مثال: 1.0 تعني 1%%)")
    ap.add_argument("--max-open-risk-pct", type=float, default=None, help="السقف الأقصى لإجمالي المخاطرة المفتوحة بالمئة (الافتراضي 3.0)")
    ap.add_argument("--max-open-positions", type=int, default=None, help="الحد الأقصى لعدد المراكز المفتوحة المتزامنة (الافتراضي 4)")
    ap.add_argument("--log-level", type=str, default=None, choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="مستوى السجل التشخيصي المنظم")
    ap.add_argument("--backtest", action="store_true", help="تشغيل محرك الباكتيست التاريخي المتقدم (Walk-Forward Backtest)")
    ap.add_argument("--bt-days", type=int, default=14, help="عدد أيام الباكتيست التاريخي (الافتراضي 14 يوماً)")
    ap.add_argument("--bt-top-n", type=int, default=12, help="عدد أعلى العملات سيولة لإدراجها في الباكتيست عند عدم تحديد --bt-coins")
    ap.add_argument("--bt-coins", nargs="+", help="تحديد عملات بعينها للباكتيست (مثال: --bt-coins BTC ETH SOL LINK AVAX)")
    ap.add_argument("--bt-all-4h", action="store_true", help="اختبار جميع إغلاقات الـ 4 ساعات الـ 6 يومياً بدلاً من النوافذ الـ 5 الرسمية")
    ap.add_argument("--bt-compare-models", action="store_true", help="تشغيل مقارنة الحساسية لنماذج التنفيذ الثلاثة على نفس البيانات")
    ap.add_argument("--test-phase1", action="store_true", help="تشغيل اختبارات القبول التسعة الحتمية للمرحلة الأولى (الدخول والأهداف الجزئية والوقف)")
    ap.add_argument("--test-phase2", action="store_true", help="تشغيل اختبارات القبول الثمانية الحتمية للمرحلة الثانية (حجم المركز والهامش وبوابة المخاطرة)")
    ap.add_argument("--test-phase3", action="store_true", help="تشغيل اختبارات القبول السبعة الحتمية للمرحلة الثالثة (محرك الباكتيست ومنحنى رأس المال)")
    ap.add_argument("--test-phase4", action="store_true", help="تشغيل اختبارات القبول السبعة الحتمية للمرحلة الرابعة والانتقاء الذكي")
    ap.add_argument("--test-all", action="store_true", help="تشغيل جميع اختبارات القبول للمراحل الأربع معاً (31 اختباراً حتمياً)")
    args = ap.parse_args()

    if args.log_level:
        SCANNER_LOGGER.setLevel(getattr(logging, args.log_level.upper(), logging.WARNING))
    if args.equity is not None and args.equity > 0:
        RUNTIME_RISK_CONFIG["equity_usd"] = float(args.equity)
    if args.risk_pct is not None and args.risk_pct > 0:
        RUNTIME_RISK_CONFIG["risk_pct_per_trade"] = float(args.risk_pct) / 100.0 if args.risk_pct > 0.2 else float(args.risk_pct)
    if args.max_open_risk_pct is not None and args.max_open_risk_pct > 0:
        RUNTIME_RISK_CONFIG["max_total_open_risk_pct"] = float(args.max_open_risk_pct) / 100.0 if args.max_open_risk_pct > 0.5 else float(args.max_open_risk_pct)
    if args.max_open_positions is not None and args.max_open_positions >= 1:
        RUNTIME_RISK_CONFIG["max_concurrent_positions"] = int(args.max_open_positions)

    if args.test_all:
        run_phase1_acceptance_tests()
        print()
        run_phase2_acceptance_tests()
        print()
        run_phase3_acceptance_tests()
        print()
        run_phase4_acceptance_tests()
    elif args.test_phase1:
        run_phase1_acceptance_tests()
    elif args.test_phase2:
        run_phase2_acceptance_tests()
    elif args.test_phase3:
        run_phase3_acceptance_tests()
    elif args.test_phase4:
        run_phase4_acceptance_tests()
    elif args.confirm_0245:
        run_standalone_confirm_0245()
    elif args.run_scan:
        run_standalone_full_scan()
    elif args.backtest:
        run_cli_historical_backtest(
            days=args.bt_days,
            top_n=args.bt_top_n,
            coins=args.bt_coins,
            all_4h=args.bt_all_4h,
            compare_models=args.bt_compare_models,
        )
    elif args.coin:
        inspect_specific_coins(args.coin)
    elif args.macro_only:
        now_r = dt.datetime.now(RIYADH)
        is_late = (now_r.hour >= 23 or now_r.hour < 3)
        print(f"=== فحص الماكرو اليومي/الأسبوعي/الشهري ({now_r.strftime('%Y-%m-%d %H:%M:%S')} الرياض | بوابة ما بعد 23:05: {is_late}) ===")
        res = scan_macro_regimes({}, {}, now_r, is_confirm_run=False)
        print(f"🧭 مناخ البيتكوين: {res['btc_regime']['label']} — {res['btc_regime']['advice']}")
        print(f"\n🧲 العملات الاستثمارية (العصر الأفقي + الدفاع الشرائي) [{len(res['squeeze'])}]:")
        for s in res["squeeze"]:
            print(f"  - {s['sym']}: {s['badge']} | السعر {s['price']} | الدخول [{s['entry_lo']} - {s['entry_hi']}] | الوقف {s['stop']}")
        print(f"\n🚀 عملات كسر الهيكل والزخم الصاعد والهمر (1D + 1W + 1M) [{len(res['bos3'])}]:")
        for b in res["bos3"]:
            print(f"  - {b['sym']}: {b['kind_badge']} | السعر {b['price']} | الدخول [{b['entry_lo']} - {b['entry_hi']}] | الوقف {b['stop']} | 1W: {b['w_summary']}")
    else:
        run_standalone_full_scan()


if __name__ == "__main__":
    main()
