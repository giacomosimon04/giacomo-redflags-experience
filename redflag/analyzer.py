"""
Il cervello del progetto

Prende una lista di messaggi e dice se la chat è:
  TOSSICA  oppure  SANA (tipo quella tra Giacomo e Claude)

Ogni messaggio è un dizionario:
  {"sender": "lei", "text": "ok", "time": datetime(...)}   # time è opzionale

Il punteggio finale (0-100) mescola:
  1. il modello ML (quanto sono tossici i messaggi)
  2. i tempi di risposta (3 ore per un "si" = red flag)
  3. i cambi di tono (da "amoreee" a "ok." in 2 minuti)
  4. le risposte secche ("ok", "k", "boh", "vabbè")
  5. lo squilibrio (tu mandi un poema, lei manda "ah")
"""

from pathlib import Path
from statistics import mean, pstdev

import joblib

WEIGHTS = Path(__file__).resolve().parent.parent / "model" / "redflag_weights.joblib"

# Risposte secche: se lei risponde così, preparati psicologicamente
RISPOSTE_SECCHE = {
    "ok", "ok.", "k", "kk", "okay", "va bene", "vabbè", "vabbe", "boh", "ah",
    "mh", "mmh", "si", "sì", "no", "fai tu", "come vuoi", "fai come vuoi",
    "niente", "nulla", "lascia stare", "lascia perdere", "ah ok", "ok ciao",
    "whatever", "fine", "sure", ".", "...",
}

# Frasi che il dataset non conosce ma ogni uomo sì
FRASI_RED_FLAG = [
    "fai come vuoi",       # NON fare come vuoi. mai.
    "non ho niente",       # ha tutto. ha tantissimo.
    "niente lascia stare", # non lasciare stare, è una trappola
    "chi è quella",        # è tua cugina, ma ormai è tardi
    "sei cambiato",        # sì, ho cambiato taglio di capelli
    "il mio ex",           # parte il film in 3 atti
    "non mi scrivere",     # (vuole che le scrivi)
    "se esci",             # scomparire se esco è super red vero
    "dove sei",            # posizione condivisa obbligatoria
    "con chi sei",         # interrogatorio livello CSI
    "perché hai messo like",
    "ti ho visto online",  # la spunta blu è un'arma
    "visualizzato",
    "sei come tutti",
    "non sono gelosa",     # è gelosa
    "dobbiamo parlare",    # (rip)
]

_modello = None


def carica_modello():
    """Carica i pesi una volta sola (a differenza di lei che ti carica di ansia ogni giorno)."""
    global _modello
    if _modello is None:
        if not WEIGHTS.exists():
            raise FileNotFoundError("Pesi non trovati. Lancia prima: python -m redflag.train")
        _modello = joblib.load(WEIGHTS)
    return _modello


def tossicita_messaggi(testi):
    """Probabilità (0-1) che ogni messaggio sia tossico secondo il modello ML."""
    if not testi:
        return []
    return list(carica_modello().predict_proba(testi)[:, 1])


def analizza_chat(messaggi, io=None):
    """
    messaggi: lista di {"sender", "text", "time"(opzionale)}
    io: il nome di chi usa il bot (tu, il povero). Se None lo indoviniamo:
        sei quello che scrive di più (ovviamente).
    """
    messaggi = [m for m in messaggi if m.get("text", "").strip()]
    if len(messaggi) < 2:
        return {"punteggio": 0, "verdetto": "Troppi pochi messaggi. Anche lei ti risponde così poco?", "dettagli": {}}

    # Chi sono io? Quello che scrive di più. Sempre.
    mittenti = [m["sender"] for m in messaggi]
    if io is None:
        io = max(set(mittenti), key=mittenti.count)
    suoi = [m for m in messaggi if m["sender"] != io]
    miei = [m for m in messaggi if m["sender"] == io]
    if not suoi:
        return {"punteggio": 100, "verdetto": "Stai scrivendo da solo. Questo è ghosting, fratello.", "dettagli": {}}

    # 1) MODELLO ML: quanto sono tossici i SUOI messaggi
    tox = tossicita_messaggi([m["text"] for m in suoi])
    tox_media = mean(tox)
    tox_picco = max(tox)

    # 2) CAMBI DI TONO: se la tossicità sale e scende come le montagne russe
    sbalzi_umore = pstdev(tox) if len(tox) > 1 else 0.0

    # 3) RISPOSTE SECCHE: "ok." è una frase completa e terrificante
    secche = sum(1 for m in suoi if m["text"].strip().lower() in RISPOSTE_SECCHE) / len(suoi)

    # 4) FRASI RED FLAG classiche
    tutto_suo = " ".join(m["text"].lower() for m in suoi)
    frasi_trovate = [f for f in FRASI_RED_FLAG if f in tutto_suo]

    # 5) SQUILIBRIO: tu scrivi la Divina Commedia, lei "ah"
    lung_mia = mean(len(m["text"]) for m in miei) if miei else 1
    lung_sua = mean(len(m["text"]) for m in suoi)
    squilibrio = max(0.0, 1 - lung_sua / max(lung_mia, 1))  # 0 = pari, 1 = disastro
    rapporto_messaggi = len(miei) / len(suoi)                  # >2 = stai elemosinando

    # 6) TEMPI DI RISPOSTA: quanto ci mette a rispondere a te
    attese = []
    for prima, dopo in zip(messaggi, messaggi[1:]):
        if prima["sender"] == io and dopo["sender"] != io and prima.get("time") and dopo.get("time"):
            attese.append((dopo["time"] - prima["time"]).total_seconds() / 60)
    attesa_media = mean(attese) if attese else 0
    # Online ma non risponde da 3 ore? Red flag. Più di 6 ore = sta "dormendo" (no)
    punteggio_attesa = min(attesa_media / 360, 1.0)

    # La formula segreta (calibrata su 7 anni di dolore)
    punteggio = (
        # sotto 0.3 è rumore (anche "buongiorno" a volte sembra passivo-aggressivo)
        35 * min(max(tox_media - 0.3, 0) / 0.4, 1.0)  # tossicità media dei messaggi
        + 10 * max(tox_picco - 0.3, 0) / 0.7     # il messaggio peggiore
        + 10 * min(sbalzi_umore * 3, 1.0)        # cambi di tono
        + 15 * secche                            # "ok."
        + 10 * min(len(frasi_trovate) / 2, 1.0)  # frasi da manuale
        + 10 * squilibrio                        # tu poema, lei "ah"
        + 5 * min(max(rapporto_messaggi - 1, 0) / 2, 1.0)  # doppi/tripli messaggi
        + 5 * punteggio_attesa                   # tempi di risposta
    )
    punteggio = round(min(punteggio, 100))

    if punteggio >= 60:
        verdetto = "CHAT TOSSICA. Scappa. Blocca. Cambia città. Giacomo ci è passato, fidati."
    elif punteggio >= 35:
        verdetto = "ZONA GRIGIA. Situationship vibes. Non investire, è un titolo in perdita."
    else:
        verdetto = "CHAT SANA. Pulita come la chat tra Giacomo e Claude. Tienitela stretta."

    return {
        "punteggio": punteggio,
        "verdetto": verdetto,
        "dettagli": {
            "tossicita_media_ml": round(tox_media, 3),
            "messaggio_peggiore": suoi[tox.index(tox_picco)]["text"],
            "sbalzi_di_umore": round(sbalzi_umore, 3),
            "percentuale_risposte_secche": round(secche * 100),
            "frasi_red_flag": frasi_trovate,
            "minuti_medi_di_attesa": round(attesa_media),
            "tuoi_messaggi_per_ogni_suo": round(rapporto_messaggi, 2),
        },
    }


def formatta_risultato(r):
    """Testo pronto da mandare su WhatsApp / Telegram / Instagram."""
    d = r["dettagli"]
    righe = [f"*RedFlag Score: {r['punteggio']}/100*", r["verdetto"]]
    if d:
        righe += [
            "",
            f"Tossicità media (ML): {d['tossicita_media_ml']}",
            f"Messaggio peggiore: \"{d['messaggio_peggiore'][:120]}\"",
            f"Sbalzi d'umore: {d['sbalzi_di_umore']}",
            f"Risposte secche: {d['percentuale_risposte_secche']}%",
            f"Attesa media risposta: {d['minuti_medi_di_attesa']} min",
            f"Tuoi messaggi per ogni suo: {d['tuoi_messaggi_per_ogni_suo']}",
        ]
        if d["frasi_red_flag"]:
            righe.append("Frasi da manuale: " + ", ".join(f'"{f}"' for f in d["frasi_red_flag"]))
    return "\n".join(righe)
