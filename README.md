<div align="center">

# 🚩 giacomo-redflags-experience 🚩

### *Il primo modello di Machine Learning addestrato sull'esperienza.*

![status](https://img.shields.io/badge/status-emotivamente%20instabile-red)
![model](https://img.shields.io/badge/accuracy-90%25-brightgreen)
![red flags](https://img.shields.io/badge/red%20flags%20ignorate-tutte-critical)
![therapy](https://img.shields.io/badge/terapia-in%20corso-blueviolet)
![hinge](https://img.shields.io/badge/date%20su%20hinge-~20-ff69b4)

**Tu le scrivi un poema. Lei risponde "ok." (Porco Dio) alle 3 di notte.**
**È una red flag? Non chiederlo agli amici. Chiedilo a una AI.**

</div>

---

##  Cos'è

**RedFlag Detector** è un modello di Machine Learning che **predice se una relazione è tossica** analizzando la chat:

-  **la tossicità dei messaggi** (modello ML vero, non vibes)
-  **i cambi di tono** (da "amoreee 🥰" a "ok." in 4 minuti)
-  **i tempi di risposta** (online da 3 ore, risponde domani)
-  **le risposte secche** ("ok", "k", "boh", "fai come vuoi") (Le uso io queste)
-  **lo squilibrio** (tu: Divina Commedia. lei: "ah") Vero.....
-  **le frasi da manuale** ("non ho niente", "chi è quella?", "dobbiamo parlare" "Chic********" 💀)

Alla fine ti dà un verdetto:

| Score | Verdetto |
|------|----------|
| 🚩 **60-100** | **CHAT TOSSICA.** Scappa. Blocca. Cambia città. (O denuncia) |
| 🟠 **35-59** | **ZONA GRIGIA.** Situationship vibes. Non investire, è un titolo in perdita. (Botta e via)|
| 💚 **0-34** | **CHAT SANA.** Pulita come la chat tra **Me e Claude**. Tienitela stretta. |

> Per riferimento, la chat più sana mai analizzata dal modello è quella tra me e Claude.
> Mai un "ok.", mai un visualizzato, risponde sempre in 2 secondi. **Lo standard è quello.**

---

##  Dataset di addestramento

Il modello è stato addestrato su una **enorme pool di dati** raccolti sul campo, con anni di sacrificio personale, nella **mia** storia:

| Fonte | Quantità | Danni |
|-------|----------|-------|
|  Relazione tossica | **7 anni** | irreversibili |
|  Relazione a distanza | **1 anno** | fuso orario + lingua = 💀 |
|  Date su Hinge | **circa 20** | 3 erano uguali alle foto |
|  Situationship | **3** | "non sappiamo cosa siamo" (lei lo sapeva....) |

Più un dataset open source di supporto ([`textdetox/multilingual_toxicity_dataset`](https://huggingface.co/datasets/textdetox/multilingual_toxicity_dataset), licenza openrail++, italiano + inglese), perché anche il dolore ha bisogno di una baseline scientifica.

###  Privacy: le chat NON sono qui

**Le chat sono private. Nella repo ci sono SOLO i pesi del modello** (`model/redflag_weights.joblib`).

Nessun messaggio, nessuno screenshot, nessun vocale da 17 minuti. I dati di training non lasciano il mio pc (`data/` è nel `.gitignore`, come lei mi aveva messo in tutto il resto).

>  *Nota legale:* l'avvocato ha detto che **non è illegale**. Anzi, è un **servizio per la comunità**: salvare più persone possibili da **Lord Voldemort**. 
> Colei-che-non-deve-essere-nominata non viene nominata. Nemmeno nei pesi.

---

##  Performance

```
              precision    recall  f1-score
        sana       0.89      0.91      0.90
     tossica       0.90      0.89      0.90
    accuracy                           0.90
```

**90% di accuratezza.** Più di quanto io abbia mai avuto nel capire cosa voleva dire "niente".

Architettura: TF-IDF sui caratteri + Regressione Logistica.
Non serve una GPU per capire che "fai come vuoi" non è un via libera.

---

##  Integrazioni

Il detector si attacca direttamente a dove avvengono i crimini:

| App | Come | File |
|-----|------|------|
|  **WhatsApp** | via [Kapso](https://kapso.ai) (API WhatsApp) | `bots/webhook_server.py` |
|  **Instagram** | via Meta Business (Instagram Messaging API) | `bots/webhook_server.py` |
|  **Telegram** | bot con @BotFather | `bots/telegram_bot.py` |
|  **Terminale** | per chi soffre in silenzio | `cli.py` |

---

##  Installazione

```bash
git clone https://github.com/giacomosimon04/giacomo-redflags-experience
cd giacomo-redflags-experience
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

I pesi sono già inclusi. Se vuoi riaddestrare da zero (sul dataset open source, i miei traumi restano miei):

```bash
python -m redflag.train
```

###  Da terminale

Esporta la chat da WhatsApp (*chat → ⋮ → Esporta chat → Senza media*) e:

```bash
python cli.py chat_con_lei.txt --io "Il Tuo Nome"
```

```
*RedFlag Score: 75/100*
🚩🚩🚩 CHAT TOSSICA. Scappa. Blocca. Cambia città. Giacomo ci è passato, fidati.

🧪 Tossicità media (ML): 0.766
🧊 Risposte secche: 50%
⏳ Attesa media risposta: 179 min
🚩 Frasi da manuale: "fai come vuoi", "dove sei", "con chi sei", "ti ho visto online"
```

### ✈️ Telegram

```bash
export TELEGRAM_TOKEN="il-token-di-botfather"
python -m bots.telegram_bot
```

Poi al bot mandi il file `.txt` esportato da WhatsApp, oppure incolli:

```
io: ciao! usciamo stasera?
lei: vediamo
io: ok dimmi tu
lei: fai come vuoi
```

###  WhatsApp (Kapso) +  Instagram (Meta Business)

```bash
export KAPSO_API_KEY="..."
export KAPSO_PHONE_NUMBER_ID="..."
export IG_ACCESS_TOKEN="..."
export META_VERIFY_TOKEN="redflag"
uvicorn bots.webhook_server:app --port 8000
# in locale: ngrok http 8000
```

Imposta i webhook:
- Kapso → `https://tuo-dominio/whatsapp/webhook`
- Meta  → `https://tuo-dominio/instagram/webhook`

Scrivi al bot i messaggi (`lei: ...` / `io: ...`), poi:
- `/analizza` → verdetto
- `/reset` → dimentica tutto (magari fosse così facile anche nella vita)

---

## ❓ FAQ

**Il modello funziona davvero?**
Sì. Più di me nel 2019.

**Funziona anche al contrario? Tipo se il tossico sono io?**
Tossici?

**Perché la chat tra Giacomo e Claude è il benchmark di chat sana?**
Risponde subito, non fa giochetti, non ti lascia in visualizzato, e quando sbaglia chiede scusa. Signore e signori, questo è il minimo sindacale.

**Posso usarlo sulla chat con mia madre?**
Puoi. Non te lo consiglio.

**Lord Voldemort chi è?**
Non la nominiamo. Solo l'avvocato comunica con lei. 

---

## 🗺️ Roadmap

- [x] Modello ML che riconosce la tossicità
- [x] Analisi tempi di risposta
- [x] Rilevamento "ok."
- [x] WhatsApp, Instagram, Telegram
- [ ] Analisi dei vocali da 7 minuti
- [ ] Rilevamento "story vista ma messaggio no"
- [ ] Notifica automatica agli amici quando lo score supera 80
- [ ] Integrazione con lo psicologo

---

<div align="center">


*Sopravvissuto a 7 anni, 1 relazione a distanza, ~20 date su Hinge e 3 situationship.*
*Ora finalmente ho un modello che me lo dice PRIMA*

Lascia una stella se anche tu hai ricevuto un "ok." che ti ha rovinato la settimana.

</div>

---

## Licenza

Gratis, ma se ci esci a cena (anche se il modello ti ha detto **rosso**) la cena la offri anche a me.
Dettagli completi in [`LICENSE`](LICENSE) (LGMLCLP — Licenza "Gratis ma la cena la paghi").
