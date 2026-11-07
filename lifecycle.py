# -*- coding: utf-8 -*-
"""إدارة دورة حياة تتبع الصفقات عبر المسوحات والتقارير (v3.4):
- أي صفقة منتهية بـ (🛑 ضربت الوقف) أو (⛔ أُلغيت - ابتعدت > 1 ATR) تُعرض مرة واحدة فقط في أول تقرير/مسح
  يُطلب كتحديث لوضعها، ثم تُزال نهائياً في التقرير أو المسح التالي لأنها أصبحت بلا فائدة.
- المراكز التي لا تزال (مفتوحة · رابحة أو مفتوحة · خاسرة عائمة) تستمر متابعتها حتى تُغلق على هدف أو تضرب الوقف.
- منع إعادة الدخول الفوري على نفس العملة والاتجاه قبل إغلاق شمعة 4س بعد ضرب الوقف.
"""
import json, os, time
from track import track

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE, "tracker_state.json")


def make_tid(t, fallback_ts=0):
    ots = int(t.get("origin_ts") or fallback_ts or 0)
    return f"{t['sym']}|{t['side']}|{ots}"


def load_tracker_state():
    if os.path.exists(STATE_FILE):
        try:
            st = json.load(open(STATE_FILE, encoding="utf-8"))
            st.setdefault("reported_stops", {})
            st.setdefault("reported_cancels", {})
            st.setdefault("carried_open", [])
            return st
        except Exception:
            pass
    return {"reported_stops": {}, "reported_cancels": {}, "carried_open": []}


def already_pruned_ids(st=None):
    st = st or load_tracker_state()
    return set((st.get("reported_stops") or {}).keys()) | set((st.get("reported_cancels") or {}).keys())


def save_tracker_state(st):
    now_ms = int(time.time() * 1000)
    cutoff = now_ms - 7 * 86400 * 1000
    st["reported_stops"] = {
        k: v for k, v in (st.get("reported_stops") or {}).items()
        if int(v.get("reported_at", now_ms)) >= cutoff
    }
    st["reported_cancels"] = {
        k: v for k, v in (st.get("reported_cancels") or {}).items()
        if int(v.get("reported_at", now_ms)) >= cutoff
    }
    json.dump(st, open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)


def update_and_prune_tracking(scan_trades, scan_ts, max_dist_atr=1.0, fresh=True, commit=True):
    """يتتبع صفقات المسح السابق + أي مراكز مفتوحة مرحّلة، مع:
    1) استبعاد أي صفقة سبق عرضها كـ (ضربت الوقف) أو (أُلغيت) في تقرير/مسح سابق.
    2) الإبقاء على الصفقات التي ضربت الوقف أو أُلغيت حديثاً لعرضها (هذه المرة الواحدة فقط)،
       وتسجيلها فوراً لتُزال تلقائياً في التقرير/المسح القادم.
    3) الإبقاء على المراكز المفتوحة (رابحة وخاسرة عائمة) تحت المتابعة الحية.
    """
    st = load_tracker_state()
    reported_stops = dict(st.get("reported_stops") or {})
    reported_cancels = dict(st.get("reported_cancels") or {})
    pruned_ids = set(reported_stops.keys()) | set(reported_cancels.keys())
    carried_open = list(st.get("carried_open") or [])

    cur_keys = {(t["sym"], t["side"]) for t in scan_trades}
    pool = []

    # 1) المراكز المفتوحة المرحّلة من مسح أقدم (إن لم يُصدر لها إعداد جديد في المسح الأخير)
    for old_t in carried_open:
        ots = int(old_t.get("origin_ts") or 0)
        tid = make_tid(old_t, ots)
        if tid in pruned_ids or (old_t["sym"], old_t["side"]) in cur_keys:
            continue
        t_copy = dict(old_t)
        t_copy["origin_ts"] = ots
        pool.append(t_copy)

    # 2) جميع صفقات المسح الأخير غير المعروضة سابقاً كضرب وقف أو ملغاة
    for t in scan_trades:
        ots = int(t.get("origin_ts") or scan_ts)
        tid = make_tid(t, ots)
        if tid in pruned_ids:
            continue
        t_copy = dict(t)
        t_copy["origin_ts"] = ots
        pool.append(t_copy)

    tracked = track(pool, scan_ts, max_dist_atr=max_dist_atr, fresh=fresh) if pool else []
    now_ms = int(time.time() * 1000)

    newly_stopped = 0
    newly_cancelled = 0
    for row in tracked:
        st_row = row.get("status")
        tid = make_tid(row, scan_ts)
        if st_row == "ضربت الوقف" and tid not in reported_stops:
            reported_stops[tid] = {
                "sym": row["sym"],
                "side": row["side"],
                "name": row.get("name", row["sym"]),
                "origin_ts": int(row.get("origin_ts") or scan_ts),
                "stop_ts": int(row.get("exit_ts") or now_ms),
                "reported_at": now_ms,
            }
            newly_stopped += 1
        elif st_row == "أُلغيت (ابتعدت)" and tid not in reported_cancels:
            reported_cancels[tid] = {
                "sym": row["sym"],
                "side": row["side"],
                "name": row.get("name", row["sym"]),
                "origin_ts": int(row.get("origin_ts") or scan_ts),
                "reported_at": now_ms,
            }
            newly_cancelled += 1

    if commit:
        next_open = [r for r in tracked if r.get("status") == "مفتوحة"]
        save_tracker_state({
            "reported_stops": reported_stops,
            "reported_cancels": reported_cancels,
            "carried_open": next_open,
        })

    return tracked, newly_stopped


def recent_4h_stopped_pairs(now_ms=None):
    """إرجاع مجموعة (sym, side) التي ضربت الوقف داخل شمعة الـ 4 ساعات الحالية غير المغلقة بعد."""
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

