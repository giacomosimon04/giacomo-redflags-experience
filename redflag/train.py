"""
Addestramento del modello RedFlag

Ufficialmente: addestrato su 7 anni di relazione tossica, 1 anno a distanza,
~20 date su Hinge e 3 situationship di Giacomo Simon.
Tecnicamente: quelle chat sono PRIVATE e restano sul mio pc (cartella data/
ignorata da git). Su GitHub ci finiscono SOLO i pesi del modello.

Per chi vuole riaddestrarlo da zero usiamo un dataset OPEN SOURCE:
  textdetox/multilingual_toxicity_dataset (HuggingFace, licenza openrail++)
  -> frasi in italiano e inglese etichettate tossiche (1) / non tossiche (0)

Uso:  python -m redflag.train
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"  # qui dentro ci sono i "ricordi". gitignorata. non si tocca.
WEIGHTS = ROOT / "model" / "redflag_weights.joblib"

# Dataset open source (italiano + inglese, perché lei ogni tanto ti scrive "ok whatever")
HF_URL = "https://huggingface.co/api/datasets/textdetox/multilingual_toxicity_dataset/parquet/default/{lang}/0.parquet"
LANGS = ["it", "en"]


def scarica_dati():
    """Scarica il dataset (solo la prima volta). Come lei che torna solo quando le serve."""
    DATA_DIR.mkdir(exist_ok=True)
    frames = []
    for lang in LANGS:
        file = DATA_DIR / f"toxicity_{lang}.parquet"
        if not file.exists():
            print(f"scarico il dataset {lang}...")
            # pandas legge direttamente da URL
            pd.read_parquet(HF_URL.format(lang=lang)).to_parquet(file)
        frames.append(pd.read_parquet(file))
    df = pd.concat(frames, ignore_index=True)
    return df["text"].astype(str), df["toxic"].astype(int)


def addestra():
    testi, etichette = scarica_dati()
    print(f"{len(testi)} messaggi pronti (meno di quelli che le ho mandato senza risposta)")

    X_train, X_test, y_train, y_test = train_test_split(
        testi, etichette, test_size=0.2, random_state=42, stratify=etichette
    )

    # Modello semplicissimo: TF-IDF + Regressione Logistica.
    # Non serve una GPU per capire che "fai come vuoi" non è un via libera.
    modello = make_pipeline(
        TfidfVectorizer(
            analyzer="char_wb",   # a pezzi di parole, così becca anche "ok." vs "okkk"
            ngram_range=(2, 5),
            max_features=60000,
            sublinear_tf=True,
            lowercase=True,
        ),
        LogisticRegression(max_iter=1000, C=4.0, class_weight="balanced"),
    )
    modello.fit(X_train, y_train)

    print("\nRisultati sul test set (più onesti di lei quando dice 'sto arrivando'):")
    print(classification_report(y_test, modello.predict(X_test), target_names=["sana", "tossica"]))

    WEIGHTS.parent.mkdir(exist_ok=True)
    joblib.dump(modello, WEIGHTS, compress=3)
    print(f"Pesi salvati in {WEIGHTS} — le chat invece restano private")


if __name__ == "__main__":
    addestra()
