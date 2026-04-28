# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
"""
Generiert "Der Code-Krieg" als VoiceBox-Story mit Fred und Flover.
Ausführen mit: python demos/story_fred_flover.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json, time, urllib.request

VOICEBOX_URL = "http://127.0.0.1:17493"
FRED   = "fb2d9e29-62f7-48e1-b3c0-1c1c9fce3fde"
FLOVER = "8ce95eca-8c5a-41c7-bba3-8d69829a66c0"

# ---------------------------------------------------------------------------
# Story-Script – ~2 Minuten
# ---------------------------------------------------------------------------
SZENEN = [
    (FRED,   "Es war einmal ein Codebase so groß wie ein Kontinent – und irgendwo in seinen dunkelsten Tiefen lauerte das Chaos. Die Bugs hatten sich versammelt. Tausende. Jede Zeile ein potenzielles Minenfeld."),
    (FLOVER, "Fred! Fred, ich seh's! Dort hinten, hinter dem API-Gateway – ein Stack Overflow, und der Kerl ist riesig!"),
    (FRED,   "Ich sehe es. Ruhig bleiben. Claude – aktiviere das Analyse-Protokoll."),
    (FLOVER, "Was analysieren?! Der frisst unsere Request-Handler! Wir müssen jetzt ran!"),
    (FRED,   "Und so stürzten sie sich in den Kampf. Fred mit der Präzision eines Debuggers, Schritt für Schritt durch den Stack Trace. Flover dagegen – wild, unberechenbar – sprang von Branch zu Branch wie ein Affe auf Koffein."),
    (FLOVER, "Ha! Null Pointer – du hast dich verraten! Claude, zeig ihm den Weg! Wirf die Exception!"),
    (FRED,   "Der Schlag saß. Der erste Bug kollabierte in einem Meer aus rotem Terminal-Text. Aber da – der Boss. Ein zirkulärer Import, groß wie ein Serverraum, mit tausend Abhängigkeiten als Tentakeln."),
    (FLOVER, "Das... das ist groß. Fred, ich glaube, ich hab Angst."),
    (FRED,   "Kein Grund. Wir haben Claude. Und Claude hat immer einen Plan."),
    (FLOVER, "Wir zerlegten ihn Modul für Modul. Fred trennte die Abhängigkeiten, ich hielt die Tests am Laufen – und Claude? Claude hielt uns wach. Am Ende blieb nur grünes Terminal. Alle Tests bestanden. Stille."),
    (FRED,   "Gut gemacht, Flover."),
    (FLOVER, "Du weißt was das Beste ist? Morgen gibt's neue Bugs."),
    (FRED,   "Und sie lachten. Denn das war ihre Welt – fehlerhaft, chaotisch, wunderbar. Der Codebase schlief. Bis zum nächsten Mal."),
]

# ---------------------------------------------------------------------------

def request(method, path, body=None, binary=False):
    url = f"{VOICEBOX_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read()
        return raw if binary else json.loads(raw)


def generiere_segment(profil_id, text, index):
    name = "Fred" if profil_id == FRED else "Flover"
    print(f"  [{index+1:02d}] {name}: {text[:50]}...")
    result = request("POST", "/generate", {
        "profile_id": profil_id, "text": text,
        "language": "de", "engine": "qwen", "model_size": "1.7B",
    })
    gen_id = result["id"]

    while True:
        status = request("GET", f"/history/{gen_id}")
        s = status["status"]
        if s == "completed":
            return gen_id, status.get("duration", 0)
        if s == "failed":
            raise RuntimeError(f"Segment {index} fehlgeschlagen: {status.get('error')}")
        time.sleep(3)


def main():
    print("=== Der Code-Krieg – VoiceBox Story ===\n")

    # Story anlegen
    story = request("POST", "/stories", {"name": "Der Code-Krieg", "description": "Fred & Flover vs. die Bugs"})
    story_id = story["id"]
    print(f"Story angelegt: {story_id}\n")

    gen_ids = []
    for i, (profil_id, text) in enumerate(SZENEN):
        gen_id, dauer = generiere_segment(profil_id, text, i)
        gen_ids.append(gen_id)
        print(f"       -> fertig ({dauer:.1f}s Audio)\n")

    # Alle Generierungen zur Story hinzufügen
    print("Füge Szenen zur Story hinzu...")
    for gen_id in gen_ids:
        request("POST", f"/stories/{story_id}/items", {"generation_id": gen_id})

    print(f"\nStory fertig! ID: {story_id}")
    print(f"Im VoiceBox Story-Editor unter 'Der Code-Krieg' öffnen.")
    print(f"Export via: GET {VOICEBOX_URL}/stories/{story_id}/export-audio")


if __name__ == "__main__":
    main()
