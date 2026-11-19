"""
Server webhook per WhatsApp (via Kapso) e Instagram (via Meta Business)

Come funziona:
  - Inoltri/scrivi i messaggi al numero WhatsApp o all'account Instagram del bot
  - Il bot li accumula (ultimi 200 per persona)
  - Quando scrivi "/analizza" ti risponde col verdetto
  - "/reset" svuota tutto (magari fosse così facile anche nella vita)

Formato dei messaggi da mandare al bot:
    lei: dove sei?
    io: a casa
    lei: con chi?

Avvio:
  export KAPSO_API_KEY=...            # dashboard Kapso
  export KAPSO_PHONE_NUMBER_ID=...    # id del numero WhatsApp collegato a Kapso
  export IG_ACCESS_TOKEN=...          # token Instagram (Meta Business / developers.facebook.com)
  export META_VERIFY_TOKEN=redflag    # stringa a scelta per verificare il webhook
  uvicorn bots.webhook_server:app --port 8000

Poi su Kapso e su Meta imposti il webhook su:
  https://tuo-dominio/whatsapp/webhook
  https://tuo-dominio/instagram/webhook
(in locale: ngrok http 8000)
"""

import os
from collections import defaultdict, deque

import requests
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from redflag import analizza_chat, formatta_risultato

KAPSO_API_KEY = os.environ.get("KAPSO_API_KEY", "")
KAPSO_PHONE_NUMBER_ID = os.environ.get("KAPSO_PHONE_NUMBER_ID", "")
KAPSO_URL = os.environ.get("KAPSO_URL", "https://api.kapso.ai/meta/whatsapp/v24.0")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
IG_URL = os.environ.get("IG_URL", "https://graph.instagram.com/v21.0/me/messages")
VERIFY_TOKEN = os.environ.get("META_VERIFY_TOKEN", "redflag")

app = FastAPI(title="RedFlag Detector")

# Memoria delle chat in RAM: niente database, niente salvataggi.
# Le chat restano private (lo ha detto anche l'avvocato).
chat_in_corso = defaultdict(lambda: deque(maxlen=200))


def gestisci_testo(utente, testo):
    """Logica comune a WhatsApp e Instagram. Ritorna la risposta da mandare."""
    testo = testo.strip()
    if testo.lower() == "/reset":
        chat_in_corso[utente].clear()
        return "Chat dimenticata. Ora dimentica anche lei."
    if testo.lower() == "/analizza":
        r = analizza_chat(list(chat_in_corso[utente]), io="io")
        return formatta_risultato(r)

    for riga in testo.splitlines():
        if ":" in riga:
            chi, cosa = riga.split(":", 1)
            chi = chi.strip().lower()
            chi = "io" if chi in ("io", "me", "tu") else chi
            chat_in_corso[utente].append({"sender": chi, "text": cosa.strip()})
    return None  # niente risposta finché non chiede /analizza (non come lei che risponde quando vuole)


# ---------------------------------------------------------------- WhatsApp (Kapso)

def manda_whatsapp(numero, testo):
    # Kapso espone la stessa API di WhatsApp Cloud (Meta), con la sua API key
    requests.post(
        f"{KAPSO_URL}/{KAPSO_PHONE_NUMBER_ID}/messages",
        headers={"X-API-Key": KAPSO_API_KEY},
        json={"messaging_product": "whatsapp", "to": numero, "type": "text", "text": {"body": testo}},
        timeout=30,
    )


def estrai_whatsapp(payload):
    """Accetta sia il formato Meta classico che quello degli eventi Kapso."""
    trovati = []
    # formato Meta: entry -> changes -> value -> messages
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for m in change.get("value", {}).get("messages", []):
                if m.get("type") == "text":
                    trovati.append((m["from"], m["text"]["body"]))
    # formato evento Kapso: {"message": {...}} oppure {"data": {"message": {...}}}
    m = payload.get("message") or payload.get("data", {}).get("message")
    if m and m.get("text"):
        corpo = m["text"]["body"] if isinstance(m["text"], dict) else m["text"]
        trovati.append((m.get("from"), corpo))
    return trovati


@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    for numero, testo in estrai_whatsapp(await request.json()):
        risposta = gestisci_testo(f"wa:{numero}", testo)
        if risposta:
            manda_whatsapp(numero, risposta)
    return {"ok": True}


# ---------------------------------------------------------------- Instagram (Meta Business)

def manda_instagram(utente_id, testo):
    requests.post(
        IG_URL,
        params={"access_token": IG_ACCESS_TOKEN},
        json={"recipient": {"id": utente_id}, "message": {"text": testo[:1000]}},
        timeout=30,
    )


@app.get("/instagram/webhook")
def instagram_verifica(request: Request):
    """Meta verifica il webhook. Unica verifica che passi al primo colpo."""
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(q.get("hub.challenge", ""))
    return PlainTextResponse("no", status_code=403)


@app.post("/instagram/webhook")
async def instagram_webhook(request: Request):
    payload = await request.json()
    for entry in payload.get("entry", []):
        for evento in entry.get("messaging", []):
            testo = evento.get("message", {}).get("text")
            if not testo or evento.get("message", {}).get("is_echo"):
                continue  # gli echo sono i nostri messaggi: non ci analizziamo da soli (troppo dolore)
            utente = evento["sender"]["id"]
            risposta = gestisci_testo(f"ig:{utente}", testo)
            if risposta:
                manda_instagram(utente, risposta)
    return {"ok": True}


@app.get("/")
def home():
    return {"status": "RedFlag Detector online. Lei invece no, ma ha visualizzato."}
