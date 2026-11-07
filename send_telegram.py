#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""إشعار تيليجرام اختياري مجاني بعد كل مسح (يعمل تلقائياً إذا أضاف المستخدم TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID)."""
import json, os, urllib.request, urllib.parse, datetime as dt

RIYADH = dt.timezone(dt.timedelta(hours=3))
BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat_id:
        return

    try:
        trades = json.load(open(os.path.join(BASE, "scan_result.json"), encoding="utf-8"))
        held = json.load(open(os.path.join(BASE, "held.json"), encoding="utf-8"))
        exp = json.load(open(os.path.join(BASE, "explosion_candidates.json"), encoding="utf-8"))
    except Exception:
        return

    now_str = dt.datetime.now(RIYADH).strftime("%Y-%m-%d %H:%M")
    longs = sum(1 for t in trades if t["side"] == "LONG")
    shorts = sum(1 for t in trades if t["side"] == "SHORT")
    open_win = sum(1 for x in held if x.get("status") == "مفتوحة" and x.get("open_state") == "رابحة")
    tps = sum(1 for x in held if str(x.get("status", "")).startswith("وصل"))
    top_a = [f"• {t['name']} ({'شراء' if t['side']=='LONG' else 'بيع'} {t['grade']}/{t['reach']} · {t['score']:.1f})" for t in trades[:5]]
    exp_names = [f"🔥 {e['name']} ({e['grade']})" for e in (exp.get("active") or [])[:4]]

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    app_url = ""
    if "/" in repo:
        owner, rname = repo.split("/", 1)
        app_url = f"https://{owner}.github.io/{rname}/"

    lines = [
        f"📊 *تحديث ماسح بايننس — {now_str} (الرياض)*",
        f"الصفقات المؤهلة: *{len(trades)}* (شراء {longs} · بيع {shorts})",
        f"متابعة السابق: 🟢 رابحة {open_win} · 🎯 أهداف {tps}",
        "",
        "*أقوى 5 فرص الآن:*",
        *top_a,
    ]
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


if __name__ == "__main__":
    main()
