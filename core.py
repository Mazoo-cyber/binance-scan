"""
محرك مسح عقود بايننس الآجلة — v3
- بيانات: Binance Futures API عبر النطاق www.binance.com/fapi (النطاق fapi محجوب)
- تركيز: مناطق دخول واقعية (قريبة من السعر ومُصنَّفة باحتمال الوصول)
"""
import json, math, os, time, concurrent.futures as cf, urllib.request, urllib.error

BASE = "https://www.binance.com/fapi"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE, exist_ok=True)
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Accept": "application/json"}


def _get(path, retries=4):
    url = BASE + path
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
            return json.load(open(f))
        except Exception:
            pass
    d = _get_data(path) if path.startswith("/futures/data") else _get(path)
    try:
        json.dump(d, open(f, "w"))
    except Exception:
        pass
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
        self.oi_chg = (oi / oi_prev - 1) * 100 if (oi and oi_prev) else 0.0
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
