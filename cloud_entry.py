#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""نقطة الدخول السحابية الموحدة (GitHub Actions — v4.0 الخيار الأول):
- تستدعي مباشرةً الملف الموحد المطور (binance_scanner_standalone.py) دون الاعتماد على الملفات المقسمة القديمة.
- تحدد تلقائياً هل المطلوب فحص تأكيد 02:45 (--confirm-0245) أم المسح الشامل (--run-scan) بناءً على زر المستخدم أو توقيت الرياض.
- ترسل إشعار تيليجرام مدمج يعرض الصفقات المجازة ضمن بوابة المخاطرة الذكية إن كان مفعلاً.
"""
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

RIYADH = dt.timezone(dt.timedelta(hours=3))
BASE = os.path.dirname(os.path.abspath(__file__))


def send_telegram_summary():
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat_id:
        return

    try:
        trades = json.load(open(os.path.join(BASE, "scan_result.json"), encoding="utf-8"))
        held = json.load(open(os.path.join(BASE, "held.json"), encoding="utf-8"))
        exp = json.load(open(os.path.join(BASE, "explosion_candidates.json"), encoding="utf-8"))
        meta = json.load(open(os.path.join(BASE, "scan_meta.json"), encoding="utf-8"))
    except Exception:
        return

    now_str = dt.datetime.now(RIYADH).strftime("%Y-%m-%d %H:%M")
    longs = sum(1 for t in trades if t.get("side") == "LONG")
    shorts = sum(1 for t in trades if t.get("side") == "SHORT")
    approved = [t for t in trades if t.get("risk_gate_allowed")]
    open_win = sum(1 for x in held if x.get("status") == "مفتوحة" and x.get("open_state") == "رابحة")
    tps = sum(1 for x in held if str(x.get("status", "")).startswith("وصل"))
    pr = meta.get("portfolio_risk") or {}

    top_lines = []
    for t in (approved or trades)[:4]:
        side_ar = "شراء" if t.get("side") == "LONG" else "بيع"
        notional = float(t.get("position_notional_usd") or 0)
        rcash = float(t.get("actual_risk_cash") or 0)
        flag = "✅" if t.get("risk_gate_allowed") else "👁️"
        top_lines.append(
            f"{flag} {t['name']} ({side_ar} {t['grade']}/{t['reach']} · {t['score']:.1f}) — حجم {notional:,.0f}$ · مخاطرة {rcash:.0f}$"
        )

    exp_names = [f"🔥 {e['name']} ({e['grade']})" for e in (exp.get("active") or [])[:4]]

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    app_url = ""
    if "/" in repo:
        owner, rname = repo.split("/", 1)
        app_url = f"https://{owner}.github.io/{rname}/"

    lines = [
        f"📊 *ماسح بايننس المطور v4.0 — {now_str} (الرياض)*",
        f"المؤهلة: *{len(trades)}* (شراء {longs} · بيع {shorts}) | المجاز للتنفيذ: *{len(approved)}*",
        f"المخاطرة المفتوحة: *{pr.get('open_risk_cash', 0):.0f}$ ({pr.get('open_risk_pct', 0):.2f}%)* | 🟢 رابحة {open_win} · 🎯 أهداف {tps}",
    ]
    if pr.get("session_label_ar"):
        lines.append(f"الجلسة: {pr['session_label_ar']}")
    if top_lines:
        lines += ["", "*أقوى الفرص الآن:*", *top_lines]
    if exp_names:
        lines += ["", "*قابلة للانفجار:* " + " · ".join(exp_names)]
    if app_url:
        lines += ["", f"🔗 [افتح التقرير الكامل على الجوال]({app_url})"]

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": "\n".join(lines),
        "parse_mode": "Markdown",
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST")
    try:
        urllib.request.urlopen(req, timeout=15).read()
        print("Telegram notification sent.")
    except Exception as e:
        print("Telegram warn:", e)


def main():
    mode = (os.environ.get("SCAN_MODE") or "auto").strip().lower()
    now_r = dt.datetime.now(RIYADH)

    if mode == "confirm":
        cli_flag = "--confirm-0245"
    elif mode == "scan":
        cli_flag = "--run-scan"
    else:
        # في التشغيل المجدول التلقائي: نافذة 02:45 (بين 02:30 و 02:58 بالرياض) تشغّل فحص التأكيد
        if now_r.hour == 2 and 30 <= now_r.minute <= 58:
            cli_flag = "--confirm-0245"
        else:
            cli_flag = "--run-scan"

    standalone_path = os.path.join(BASE, "binance_scanner_standalone.py")
    print(f"[cloud_entry v4.0] Riyadh={now_r.strftime('%Y-%m-%d %H:%M:%S')} | mode={mode} -> binance_scanner_standalone.py {cli_flag}")
    subprocess.check_call([sys.executable, standalone_path, cli_flag])
    send_telegram_summary()


if __name__ == "__main__":
    main()
