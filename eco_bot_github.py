#!/usr/bin/env python3
"""
Publie sur un canal Telegram les annonces économiques à fort impact,
environ 15 minutes avant leur publication.

Version sans fichier de mémoire, conçue pour GitHub Actions :
le script est lancé toutes les 5 minutes et ne publie que les annonces
dont l'heure tombe dans la fenêtre [maintenant + 10 min ; maintenant + 15 min].
Chaque annonce tombe donc dans une seule fenêtre : pas de doublon.

Variables d'environnement requises :
  TELEGRAM_BOT_TOKEN  -> token donné par @BotFather
  TELEGRAM_CHAT_ID    -> identifiant du canal (ex. -1001234567890)
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
PARIS = ZoneInfo("Europe/Paris")

# Impacts publiés : "High" uniquement. Ajoute "Medium" pour plus d'annonces.
IMPACTS = {"High"}

# Fenêtre : doit correspondre à la fréquence d'exécution (5 minutes)
WINDOW_START_MIN = 10
WINDOW_END_MIN = 15


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        result = json.loads(r.read().decode("utf-8"))
        if not result.get("ok"):
            raise RuntimeError(f"Erreur Telegram : {result}")


def format_message(ev, event_time):
    lines = [
        f"🚨 Dans environ 15 min : {ev['title']} ({ev['country']})",
        f"🕒 {event_time.strftime('%H:%M')} (heure de Paris)",
    ]
    if ev.get("forecast"):
        lines.append(f"📊 Prévision : {ev['forecast']}")
    if ev.get("previous"):
        lines.append(f"📉 Précédent : {ev['previous']}")
    lines.append("⚠️ Information à titre indicatif, pas un conseil en investissement.")
    return "\n".join(lines)


def main():
    if not TOKEN or not CHAT_ID:
        sys.exit("Erreur : TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID doivent être définis.")

    events = json.loads(http_get(FEED_URL))
    now = datetime.now(PARIS)
    window_start = now + timedelta(minutes=WINDOW_START_MIN)
    window_end = now + timedelta(minutes=WINDOW_END_MIN)

    sent = 0
    for ev in events:
        if ev.get("impact") not in IMPACTS:
            continue
        event_time = datetime.fromisoformat(ev["date"]).astimezone(PARIS)
        if window_start < event_time <= window_end:
            send_telegram(format_message(ev, event_time))
            sent += 1

    print(f"{now:%Y-%m-%d %H:%M} : {sent} annonce(s) publiée(s)")


if __name__ == "__main__":
    main()
