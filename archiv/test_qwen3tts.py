# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
"""
Qwen3-TTS-12Hz-1.7B-CustomVoice Test
======================================
CustomVoice-Modell: feste Speaker-IDs, keine externen Referenz-Audiodateien nötig.
Stattdessen wählt man einen Speaker per Name + optional eine Stil-Instruktion.

Nutzung: .qwen_venv\Scripts\python.exe archiv\test_qwen3tts.py
"""

import os, time, torch
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.resolve()
MODELS_DIR  = PROJECT_DIR / "models" / "huggingface"
OUTPUT_DIR  = PROJECT_DIR / "test_output" / "qwen3_stimmen"

# Token aus .env laden
env_file = PROJECT_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("HF_TOKEN="):
            os.environ["HF_TOKEN"] = line.split("=", 1)[1].strip()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

import soundfile as sf
import numpy as np

print("[qwen3tts] lade Modell (einmalig ~3.5GB Download) ...")
t0 = time.time()

from qwen_tts import Qwen3TTSModel

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    device_map="cuda",
    torch_dtype=torch.bfloat16,
)
print(f"[qwen3tts] geladen in {time.time()-t0:.1f}s")

# Verfügbare Speaker und Sprachen anzeigen
speakers  = model.get_supported_speakers()
languages = model.get_supported_languages()
print(f"\n[info] {len(speakers) if speakers else '?'} Speaker verfügbar")
if speakers:
    for s in (speakers or []):
        print(f"  - {s}")
print(f"[info] Sprachen: {languages}")

# Alle Speaker testen
test_speakers = speakers or ["aiden"]

TEXTE = [
    ("test_de_kurz",   "Hallo, ich bin ein Sprachmodell von Qwen."),
    ("test_de_mittel", "Es war einmal ein Lindwurm namens Hildegunst von Mythenmetz."),
    ("test_de_lang",   (
        "Er lebte in einem einsamen Turm hoch oben auf der Lindwurmfeste. "
        "Dort schrieb er Bücher und träumte von großen Abenteuern."
    )),
    ("test_dialog_jadusa", "Aber blindlings in einen schwarzen Schlund zu springen, das ist besonders dämlich."),
    ("test_dialog_qwert",  "Nein! Bitte nicht loslassen!"),
]

print(f"\n[gen] {len(TEXTE)} Texte × {len(test_speakers)} Speaker ...\n")
for speaker in test_speakers:
    print(f"\n=== Speaker: {speaker} ===")
    for name, text in TEXTE:
        out = OUTPUT_DIR / f"qwen_{speaker}_{name}.wav"
        try:
            t0 = time.time()
            wavs, sr = model.generate_custom_voice(
                text=text,
                speaker=speaker,
                language="German",
            )
            wav = wavs[0].astype(np.float32)
            sf.write(str(out), wav, sr)
            print(f"  [ok] {name}: {time.time()-t0:.1f}s -> {len(wav)/sr:.1f}s  {text[:50]!r}")
        except Exception as e:
            print(f"  [fail] {name}: {e}")

print(f"\n[fertig] Ausgabe in {OUTPUT_DIR}")
