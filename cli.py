"""
Analizza una chat WhatsApp esportata direttamente dal terminale.

Uso:
  python cli.py examples/chat_tossica.txt
  python cli.py la_mia_chat.txt --io "Giacomo"
"""

import argparse
from pathlib import Path

from redflag import analizza_chat, formatta_risultato
from redflag.whatsapp_parser import leggi_chat


def main():
    p = argparse.ArgumentParser(description="È una red flag o no? Scoprilo prima di lei.")
    p.add_argument("chat", help="file .txt esportato da WhatsApp")
    p.add_argument("--io", help="il tuo nome nella chat (default: chi scrive di più, cioè tu)")
    args = p.parse_args()

    messaggi = leggi_chat(Path(args.chat).read_text(encoding="utf-8"))
    print(formatta_risultato(analizza_chat(messaggi, io=args.io)))


if __name__ == "__main__":
    main()
