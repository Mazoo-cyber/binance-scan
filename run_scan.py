#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مشغّل دورة المسح الكاملة الموحّد (03:05 · 11:05 · 15:05 · 19:05 · 23:05 أو عند طلب المستخدم):
1) يحدث الصفقات السابقة عبر lifecycle.update_and_prune_tracking (يعرض ضرب الوقف مرة واحدة فقط ثم يزيله في المسح التالي).
2) يمنع إعادة الدخول الفوري على نفس العملة والاتجاه داخل نفس شمعة الـ 4س التي ضربت فيها الوقف.
3) يمسح الكاش السعري وينفذ المسح الشامل ويحافظ على مصائد 02:45 المؤكدة خلال نافذة 03:05.
4) يولّد التقرير الموحّد في تحليلات/ مع حذف التقرير الأقدم تلقائياً.
"""
import json, os, subprocess, sys, time, datetime as dt
from engine import scan, is_asia_wick_window, RIYADH
from track import track
from lifecycle import update_and_prune_tracking, already_pruned_ids, make_tid, recent_4h_stopped_pairs

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    now_r = dt.datetime.now(RIYADH)
    asia_mode = is_asia_wick_window(now_r)
    print(f"=== دورة مسح كاملة ({now_r.strftime('%Y-%m-%d %H:%M:%S')} الرياض) | وضع ذيل آسيا: {asia_mode} ===")

    # 0) الاحتفاظ بمصائد 02:45 المؤكدة إذا كنا في مسح 03:05 الفجري
    exp_path = os.path.join(BASE, "explosion_candidates.json")
    prev_confirmed = []
    prev_confirm_ts = int(time.time() * 1000) - 25 * 60 * 1000
    if asia_mode and os.path.exists(exp_path):
        pe = json.load(open(exp_path))
        if pe.get("stage") in ("confirm", "active"):
            prev_confirmed = pe.get("active") or []
            prev_confirm_ts = pe.get("ts") or prev_confirm_ts

    # 1) تتبع صفقات المسح السابق مع إزالة ما سبق عرضه كـ (ضربت الوقف) في تقرير سابق
    prev_trades = json.load(open(os.path.join(BASE, "scan_result.json")))
    prev_meta = json.load(open(os.path.join(BASE, "scan_meta.json")))
    prev_ts = prev_meta["ts"]
    already_pruned = already_pruned_ids()
    pruned_prev_stops = sum(1 for t in prev_trades if make_tid(t, prev_ts) in already_pruned)

    tracked, newly_stopped = update_and_prune_tracking(prev_trades, prev_ts, max_dist_atr=1.0, fresh=True, commit=True)
    track_ts = int(time.time() * 1000)
    print(f"التتبع: {len(tracked)} صفقة في #track | {newly_stopped} ضربت الوقف (تُعرض لمرة واحدة الآن وتُزال في التقرير القادم) | {pruned_prev_stops} أُزيلت لأنها عُرضت سابقاً")

    json.dump(tracked, open(os.path.join(BASE, "held.json"), "w"), ensure_ascii=False, default=str)
    json.dump(tracked, open(os.path.join(BASE, "prev_tracked.json"), "w"), ensure_ascii=False, default=str)
    json.dump(
        {"prev_ts": prev_ts, "track_ts": track_ts, "confirm_ts": 0, "pruned_stops": pruned_prev_stops},
        open(os.path.join(BASE, "cycle_state.json"), "w"),
        ensure_ascii=False,
    )

    # 2) مسح الكاش السعري بالكامل (مع الإبقاء على exchangeInfo الثابت)
    cache_dir = os.path.join(BASE, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    for f in os.listdir(cache_dir):
        if f != "exchangeInfo.json":
            try:
                os.remove(os.path.join(cache_dir, f))
            except Exception:
                pass

    # 3) تنفيذ المسح الشامل + منع إعادة الدخول الفوري داخل نفس شمعة 4س بعد ضرب الوقف
    qualified, full_meta = scan(max_workers=10, verbose=True)
    blocked_4h = recent_4h_stopped_pairs(full_meta["ts"])
    if blocked_4h:
        before_n = len(qualified)
        qualified = [t for t in qualified if (t["sym"], t["side"]) not in blocked_4h]
        if len(qualified) < before_n:
            print(f"منع إعادة الدخول قبل إغلاق 4س بعد ضرب الوقف: استُبعدت {before_n - len(qualified)} صفقة")

    for t in qualified:
        t["origin_ts"] = full_meta["ts"]

    slim_meta = {
        "universe": full_meta["universe"],
        "top_up": full_meta["top_up"],
        "top_dn": full_meta["top_dn"],
        "ts": full_meta["ts"],
    }
    json.dump(qualified, open(os.path.join(BASE, "scan_result.json"), "w"), ensure_ascii=False, default=str)
    json.dump(slim_meta, open(os.path.join(BASE, "scan_meta.json"), "w"), ensure_ascii=False, default=str)

    # 4) في مسح الفجر، دمج مصائد 02:45 المؤكدة وتحديث حالتها
    if asia_mode and prev_confirmed:
        cur_exp = json.load(open(exp_path)) if os.path.exists(exp_path) else {"active": [], "cancelled": []}
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
        json.dump(final_exp, open(exp_path, "w"), ensure_ascii=False, default=str)

    subprocess.check_call([sys.executable, os.path.join(BASE, "gen_report.py")])


if __name__ == "__main__":
    main()
