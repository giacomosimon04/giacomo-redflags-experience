"""
Legge l'export di una chat WhatsApp (Impostazioni chat > Esporta chat > Senza media).

Formati supportati (iPhone e Android):
  [15/11/26, 23:41:07] Lei: ok.
  15/11/26, 23:41 - Lei: ok.

Le righe senza data sono il seguito del messaggio prima
(sì, quando ti manda il poema dopo 3 giorni di silenzio).
"""

import re
from datetime import datetime

IPHONE = re.compile(r"^‎?\[(\d{1,2}/\d{1,2}/\d{2,4}),? (\d{1,2}:\d{2}(?::\d{2})?)\] ([^:]+): (.*)$")
ANDROID = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}),? (\d{1,2}:\d{2}) - ([^:]+): (.*)$")

# Messaggi da ignorare: non sono red flag, sono solo WhatsApp che fa WhatsApp
IGNORA = ("<Media omessi>", "<Media omitted>", "immagine omessa", "audio omesso",
          "Questo messaggio è stato eliminato", "This message was deleted")


def _data(giorno, ora):
    for fmt in ("%d/%m/%y %H:%M:%S", "%d/%m/%y %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(f"{giorno} {ora}", fmt)
        except ValueError:
            pass
    return None


def leggi_chat(testo):
    messaggi = []
    for riga in testo.splitlines():
        riga = riga.strip()
        m = IPHONE.match(riga) or ANDROID.match(riga)
        if m:
            giorno, ora, chi, cosa = m.groups()
            if any(x in cosa for x in IGNORA):
                continue  # messaggio eliminato = red flag morale, ma il modello non lo vede
            messaggi.append({"sender": chi.strip(), "text": cosa, "time": _data(giorno, ora)})
        elif riga and messaggi:
            messaggi[-1]["text"] += "\n" + riga  # continuazione del messaggio sopra
    return messaggi
