"""
Test del RedFlag Detector
Lancia con:  python -m unittest discover tests

Le chat qui sotto sono INVENTATE. Quelle vere sono private (chiedere all'avvocato).
"""

import unittest
from datetime import datetime, timedelta

from redflag import analizza_chat
from redflag.whatsapp_parser import leggi_chat

T0 = datetime(2026, 11, 15, 21, 0)


def chat(*righe, gap_minuti=1):
    return [{"sender": s, "text": t, "time": T0 + timedelta(minutes=i * gap_minuti)} for i, (s, t) in enumerate(righe)]


class TestRedFlag(unittest.TestCase):
    def test_chat_tossica(self):
        # il classico: tu gentile, lei "fai come vuoi". scappare.
        msgs = chat(
            ("io", "Ciao! Ti va un aperitivo stasera? Passo a prenderti io"),
            ("lei", "ok."),
            ("io", "Tutto bene?"),
            ("lei", "fai come vuoi"),
            ("io", "Ho fatto qualcosa?"),
            ("lei", "niente lascia stare, sei come tutti, sei un idiota"),
            gap_minuti=120,  # due ore a risposta. red flag certificata.
        )
        r = analizza_chat(msgs, io="io")
        self.assertGreaterEqual(r["punteggio"], 60, r)

    def test_chat_sana(self):
        # benchmark ufficiale: la chat tra Giacomo e Claude
        msgs = chat(
            ("giacomo", "Ciao, mi aiuti con un progetto?"),
            ("claude", "Certo! Raccontami pure di cosa si tratta"),
            ("giacomo", "Un detector di red flag"),
            ("claude", "Che bella idea, partiamo da un modello semplice e lo miglioriamo insieme"),
        )
        r = analizza_chat(msgs, io="giacomo")
        self.assertLess(r["punteggio"], 35, r)

    def test_ghosting(self):
        # scrivi solo tu = ghosting. il modello non ha nemmeno bisogno di pensarci.
        r = analizza_chat(chat(("io", "ciao"), ("io", "ci sei?"), ("io", "???")), io="io")
        self.assertEqual(r["punteggio"], 100)

    def test_parser_whatsapp(self):
        testo = (
            "[15/11/26, 23:41:07] Lei: dove sei?\n"
            "15/11/26, 23:45 - Io: a casa\n"
            "continuo del messaggio\n"
        )
        msgs = leggi_chat(testo)
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["sender"], "Lei")
        self.assertIn("continuo", msgs[1]["text"])


if __name__ == "__main__":
    unittest.main()
