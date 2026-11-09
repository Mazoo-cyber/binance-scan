# -*- coding: utf-8 -*-
"""تحديث الصفقات السابقة: هل تفعّلت؟ هل هي مفتوحة رابحة أم خاسرة؟ هل ضربت الوقف أم وصلت هدفاً؟"""
import concurrent.futures as cf
from core import _get, cached_get


def _fetch_5m(sym, fresh=True):
    key = f"k_{sym}_5m_1000"
    raw = _get(f"/v1/klines?symbol={sym}&interval=5m&limit=1000") if fresh else cached_get(
        f"/v1/klines?symbol={sym}&interval=5m&limit=1000", key, ttl=120
    )
    return {
        "t": [int(x[0]) for x in raw],
        "h": [float(x[2]) for x in raw],
        "l": [float(x[3]) for x in raw],
        "c": [float(x[4]) for x in raw],
    }


def track(trades, since_ms, max_dist_atr=1.0, fresh=True):
    try:
        live_prices = {x["symbol"]: float(x["price"]) for x in _get("/v1/ticker/price")}
    except Exception:
        live_prices = {}

    syms = [t["sym"] for t in trades]
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
            out.append(t2)
            continue

        t_since = int(t.get("origin_ts") or since_ms)
        bars = [(tt, h, l, c) for tt, h, l, c in zip(k["t"], k["h"], k["l"], k["c"]) if tt >= t_since]
        side = t["side"]
        e_lo, e_hi = t["entry_lo"], t["entry_hi"]
        stop, tp1, tp2, tp3 = t["stop"], t["targets"][0], t["targets"][1], t["targets"][2]
        prev_filled = bool(t.get("filled")) and (t.get("filled_at") is not None)
        filled_at = int(t["filled_at"]) if prev_filled else None
        prev_fill_px = float(t["fill_price"]) if (prev_filled and t.get("fill_price") is not None) else None
        exit_ts = None
        res = None
        hi = max((b[1] for b in bars), default=t.get("hi_since"))
        lo = min((b[2] for b in bars), default=t.get("lo_since"))
        hi_after = t.get("hi_after") if prev_filled else None
        lo_after = t.get("lo_after") if prev_filled else None

        for tt, h, l, _c in bars:
            if prev_filled and tt < filled_at:
                continue
            just_filled = False
            if filled_at is None:
                if (side == "LONG" and l <= e_hi) or (side == "SHORT" and h >= e_lo):
                    filled_at = tt
                    just_filled = True
                    hi_after = h
                    lo_after = l
            elif prev_filled and tt == filled_at:
                just_filled = True
            if filled_at is not None:
                hi_after = max(hi_after, h) if hi_after is not None else h
                lo_after = min(lo_after, l) if lo_after is not None else l
                if side == "LONG":
                    if l <= stop:
                        res = ("ضربت الوقف", -1.0, stop); exit_ts = tt
                        break
                    if not just_filled:
                        if h >= tp3:
                            res = ("وصل الهدف 3", t["rr"][2], tp3); exit_ts = tt; break
                        if h >= tp2:
                            res = ("وصل الهدف 2", t["rr"][1], tp2); exit_ts = tt; break
                        if h >= tp1:
                            res = ("وصل الهدف 1", t["rr"][0], tp1); exit_ts = tt; break
                else:
                    if h >= stop:
                        res = ("ضربت الوقف", -1.0, stop); exit_ts = tt
                        break
                    if not just_filled:
                        if l <= tp3:
                            res = ("وصل الهدف 3", t["rr"][2], tp3); exit_ts = tt; break
                        if l <= tp2:
                            res = ("وصل الهدف 2", t["rr"][1], tp2); exit_ts = tt; break
                        if l <= tp1:
                            res = ("وصل الهدف 1", t["rr"][0], tp1); exit_ts = tt; break

        last = live_prices.get(sym, k["c"][-1] if k["c"] else t["price"])
        now_bar_ts = k["t"][-1] if k["t"] else t_since
        # تضمين السعر اللحظي في فحص الوقف/الأهداف بعد التفعيل
        if filled_at is not None and res is None:
            hi_after = max(hi_after, last) if hi_after is not None else last
            lo_after = min(lo_after, last) if lo_after is not None else last
            if side == "LONG":
                if last <= stop:
                    res = ("ضربت الوقف", -1.0, stop); exit_ts = now_bar_ts
                elif last >= tp3:
                    res = ("وصل الهدف 3", t["rr"][2], tp3); exit_ts = now_bar_ts
                elif last >= tp2:
                    res = ("وصل الهدف 2", t["rr"][1], tp2); exit_ts = now_bar_ts
                elif last >= tp1:
                    res = ("وصل الهدف 1", t["rr"][0], tp1); exit_ts = now_bar_ts
            else:
                if last >= stop:
                    res = ("ضربت الوقف", -1.0, stop); exit_ts = now_bar_ts
                elif last <= tp3:
                    res = ("وصل الهدف 3", t["rr"][2], tp3); exit_ts = now_bar_ts
                elif last <= tp2:
                    res = ("وصل الهدف 2", t["rr"][1], tp2); exit_ts = now_bar_ts
                elif last <= tp1:
                    res = ("وصل الهدف 1", t["rr"][0], tp1); exit_ts = now_bar_ts

        t2 = dict(t)
        t2["origin_ts"] = t_since
        t2["filled"] = filled_at is not None
        t2["filled_at"] = filled_at
        t2["exit_ts"] = exit_ts
        t2["hi_since"] = hi
        t2["lo_since"] = lo
        t2["hi_after"] = hi_after
        t2["lo_after"] = lo_after
        t2["last"] = last

        if filled_at is not None:
            if side == "LONG":
                calc_fp = (e_hi + max(e_lo, lo_after if lo_after is not None else e_hi)) / 2.0
                fill_price = min(prev_fill_px, calc_fp) if prev_fill_px is not None else calc_fp
            else:
                calc_fp = (e_lo + min(e_hi, hi_after if hi_after is not None else e_lo)) / 2.0
                fill_price = max(prev_fill_px, calc_fp) if prev_fill_px is not None else calc_fp
            t2["fill_price"] = fill_price

            if res is not None:
                exit_p = res[2]
                pnl_pct = ((exit_p - fill_price) / fill_price * 100.0) if side == "LONG" else ((fill_price - exit_p) / fill_price * 100.0)
                t2["status"] = res[0]
                t2["r_now"] = round(res[1], 2)
                t2["pnl_pct"] = round(pnl_pct, 2)
                t2["open_state"] = None
            else:
                r_unit = abs(fill_price - stop) or abs(t["avg"] - stop) or 1e-9
                diff = (last - fill_price) if side == "LONG" else (fill_price - last)
                rn = diff / r_unit
                pnl_pct = (diff / fill_price) * 100.0
                r_disp = 0.0 if abs(round(rn, 2)) == 0 else round(rn, 2)
                p_disp = 0.0 if abs(round(pnl_pct, 2)) == 0 else round(pnl_pct, 2)
                t2["status"] = "مفتوحة"
                t2["r_raw"] = rn
                t2["r_now"] = r_disp
                t2["pnl_pct"] = p_disp
                if r_disp > 0 or (r_disp == 0 and p_disp > 0):
                    t2["open_state"] = "رابحة"
                elif r_disp < 0 or (r_disp == 0 and p_disp < 0):
                    t2["open_state"] = "خاسرة"
                else:
                    t2["open_state"] = "عند الدخول"
        else:
            near_edge = e_hi if side == "LONG" else e_lo
            d = abs(last - near_edge) / t["atr4"]
            t2["dist_now_atr"] = round(d, 2)
            t2["open_state"] = None
            if d > max_dist_atr:
                t2["status"] = "أُلغيت (ابتعدت)"
            else:
                t2["status"] = "بانتظار التفعيل"
        out.append(t2)
    return out
