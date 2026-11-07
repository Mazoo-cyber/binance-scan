#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""نقطة الدخول الذكية للسحابة (GitHub Actions):
- تحدد تلقائياً هل المطلوب فحص تأكيد 02:45 أم مسح شامل بناءً على زر المستخدم أو توقيت الرياض.
- ترسل إشعار تيليجرام اختياري إن كان مفعلاً.
"""
import os, subprocess, sys, datetime as dt

RIYADH = dt.timezone(dt.timedelta(hours=3))
BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    mode = (os.environ.get("SCAN_MODE") or "auto").strip().lower()
    now_r = dt.datetime.now(RIYADH)

    if mode == "confirm":
        script = "confirm_0245.py"
    elif mode == "scan":
        script = "run_scan.py"
    else:
        # في التشغيل المجدول التلقائي: نافذة 02:45 (بين 02:30 و 02:58 بالرياض) تشغّل فحص التأكيد
        if now_r.hour == 2 and 30 <= now_r.minute <= 58:
            script = "confirm_0245.py"
        else:
            script = "run_scan.py"

    print(f"[cloud_entry] Riyadh={now_r.strftime('%Y-%m-%d %H:%M:%S')} | mode={mode} -> {script}")
    subprocess.check_call([sys.executable, os.path.join(BASE, script)])
    subprocess.call([sys.executable, os.path.join(BASE, "send_telegram.py")])


if __name__ == "__main__":
    main()
