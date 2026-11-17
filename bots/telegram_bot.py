"""
Bot Telegram 🤖🚩

Come si usa:
  1. Crea un bot con @BotFather e copia il token
  2. export TELEGRAM_TOKEN="123:abc"
  3. python -m bots.telegram_bot
  4. Al bot mandi l'export .txt di una chat WhatsApp
     oppure incolli i messaggi, uno per riga, tipo:
        io: ciao come stai?
        lei: ok.
     e lui ti dice se devi scappare.

Long polling semplice con requests: niente librerie strane.
(Unica cosa che fa polling più di te è lei che controlla quando eri online.)
"""

import os
import time

import requests

from redflag import analizza_chat, formatta_risultato
from redflag.whatsapp_parser import leggi_chat

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
API = f"https://api.telegram.org/bot{TOKEN}"

BENVENUTO = (
    "Ciao 👋 sono il RedFlag Detector di Giacomo Simon.\n\n"
    "Mandami l'export .txt di una chat WhatsApp oppure incolla i messaggi così:\n"
    "io: ciao, usciamo stasera?\n"
    "lei: vediamo\n\n"
    "Ti dirò se è tossica 🚩 o sana 💚 (come la chat tra Giacomo e Claude)."
)


def manda(chat_id, testo):
    requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": testo}, timeout=30)


def messaggi_da_testo(testo):
    """Prima proviamo il formato WhatsApp, se no 'nome: messaggio' riga per riga."""
    messaggi = leggi_chat(testo)
    if messaggi:
        return messaggi
    for riga in testo.splitlines():
        if ":" in riga:
            chi, cosa = riga.split(":", 1)
            messaggi.append({"sender": chi.strip().lower(), "text": cosa.strip()})
    return messaggi


def scarica_file(file_id):
    info = requests.get(f"{API}/getFile", params={"file_id": file_id}, timeout=30).json()
    path = info["result"]["file_path"]
    return requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{path}", timeout=60).content.decode("utf-8", "ignore")


def gestisci(update):
    msg = update.get("message") or {}
    chat_id = msg.get("chat", {}).get("id")
    if not chat_id:
        return

    if msg.get("document"):
        testo = scarica_file(msg["document"]["file_id"])
    else:
        testo = msg.get("text", "")

    if testo.startswith("/start") or not testo.strip():
        manda(chat_id, BENVENUTO)
        return

    messaggi = messaggi_da_testo(testo)
    # se usa il formato "io: ..." sappiamo già chi è l'utente
    io = "io" if any(m["sender"] == "io" for m in messaggi) else None
    manda(chat_id, formatta_risultato(analizza_chat(messaggi, io=io)).replace("*", ""))


def main():
    if not TOKEN:
        raise SystemExit("Manca TELEGRAM_TOKEN. Anche lei ti diceva che mancava qualcosa.")
    print("🤖 Bot avviato. In attesa di chat tossiche...")
    offset = 0
    while True:
        try:
            r = requests.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 50}, timeout=60).json()
            for update in r.get("result", []):
                offset = update["update_id"] + 1
                gestisci(update)
        except Exception as e:  # il bot non molla mai. a differenza tua al terzo "ok."
            print("errore:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()
