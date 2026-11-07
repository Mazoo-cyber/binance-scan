#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فحص 02:45 التأكيدي الخاص: تأكيد قائمة (قابلة للانفجار) قبل الإغلاق اليومي + تحديث المراكز المفتوحة."""
import json, os, subprocess, sys, time, datetime as dt
from engine import scan_explosions, RIYADH
from lifecycle import update_and_prune_tracking, already_pruned_ids, make_tid

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    now_r = dt.datetime.now(RIYADH)
    print(f"=== فحص التأكيد 02:45 ({now_r.strftime('%Y-%m-%d %H:%M:%S')} الرياض) ===")

    # مسح الكاش السعري اللحظي للحصول على قراءة حية قبل الإغلاق اليومي
    cache_dir = os.path.join(BASE, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    for f in os.listdir(cache_dir):
        if f != "exchangeInfo.json" and not f.endswith("_1d_300.json"):
            try:
                os.remove(os.path.join(cache_dir, f))
            except Exception:
                pass

    radar_path = os.path.join(BASE, "explosion_radar.json")
    prev_radar = json.load(open(radar_path)) if os.path.exists(radar_path) else []
    exp_data = scan_explosions(stage="confirm", prev_radar=prev_radar, max_workers=10)
    json.dump(exp_data, open(os.path.join(BASE, "explosion_candidates.json"), "w"), ensure_ascii=False, default=str)
    print(f"تأكيد الانفجار: {len(exp_data['active'])} مؤكدة | {len(exp_data['cancelled'])} أُلغيت")

    state_path = os.path.join(BASE, "cycle_state.json")
    state = json.load(open(state_path)) if os.path.exists(state_path) else {}
    meta_path = os.path.join(BASE, "scan_meta.json")
    sr_path = os.path.join(BASE, "scan_result.json")
    if os.path.exists(meta_path) and os.path.exists(sr_path):
        cur_meta = json.load(open(meta_path))
        cur_trades = json.load(open(sr_path))
        prev_ts = cur_meta.get("ts", state.get("prev_ts"))
        already_pruned = already_pruned_ids()
        pruned_prev_stops = sum(1 for t in cur_trades if make_tid(t, prev_ts) in already_pruned)

        tracked, newly_stopped = update_and_prune_tracking(cur_trades, prev_ts, max_dist_atr=1.0, fresh=True, commit=True)
        json.dump(tracked, open(os.path.join(BASE, "held.json"), "w"), ensure_ascii=False, default=str)
        json.dump(tracked, open(os.path.join(BASE, "prev_tracked.json"), "w"), ensure_ascii=False, default=str)
        # في التقارير التحديثية، إزالة الصفقات التي سبق الإبلاغ عن ضربها للوقف أو إلغائها في تقرير سابق
        if pruned_prev_stops > 0:
            filtered_cur = [t for t in cur_trades if make_tid(t, prev_ts) not in already_pruned]
            json.dump(filtered_cur, open(sr_path, "w"), ensure_ascii=False, default=str)
        state["prev_ts"] = prev_ts
        state["pruned_stops"] = pruned_prev_stops
        print(f"التتبع: {len(tracked)} صفقة معروضة | {newly_stopped} ضربت الوقف (تُعرض لمرة واحدة) | {pruned_prev_stops} أُزيلت سابقاً")

    now_ms = int(time.time() * 1000)
    state["track_ts"] = now_ms
    state["confirm_ts"] = now_ms
    json.dump(state, open(state_path, "w"), ensure_ascii=False)

    subprocess.check_call([sys.executable, os.path.join(BASE, "gen_report.py")])


if __name__ == "__main__":
    main()
