# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
"""
Kokoro ONNX – Deutsche Stimmen Test
=====================================
Listet alle deutschen Kokoro-Stimmen und generiert Vorschau-Samples.
Modell wird einmalig nach models/kokoro/ heruntergeladen.

Nutzung:
    python archiv/test_kokoro.py
    python archiv/test_kokoro.py --force
"""

import os, sys, time
from pathlib import Path

PROJECT_DIR  = Path(__file__).parent.parent.resolve()
MODELS_DIR   = PROJECT_DIR / "models" / "kokoro"
OUTPUT_DIR   = PROJECT_DIR / "preset_stimmen_kokoro"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FORCE = "--force" in sys.argv

MODEL_PATH  = MODELS_DIR / "kokoro-v1.0.onnx"
VOICES_PATH = MODELS_DIR / "voices-v1.0.bin"

# Modell herunterladen wenn nicht vorhanden
BASE_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
DOWNLOADS = {
    MODEL_PATH:  f"{BASE_URL}/kokoro-v1.0.onnx",
    VOICES_PATH: f"{BASE_URL}/voices-v1.0.bin",
}

missing = [(p, u) for p, u in DOWNLOADS.items() if not p.exists()]
if missing:
    import urllib.request
    for dest, url in missing:
        print(f"[download] {dest.name} ...")
        urllib.request.urlretrieve(url, str(dest))
    print("[download] Fertig.")
else:
    print(f"[model] Bereits vorhanden: {MODELS_DIR}")

import espeakng_loader

# espeak-ng DLL kann keine Pfade mit Umlauten lesen (ö in "Hörbuch")
# Daten liegen kopiert in AppData unter ASCII-Pfad
ESPEAK_DATA = os.path.join(os.environ["LOCALAPPDATA"], "espeak-ng-data")
os.environ["ESPEAK_DATA_PATH"] = ESPEAK_DATA
espeakng_loader.make_library_available()

import soundfile as sf
from kokoro_onnx import Kokoro, EspeakConfig

espeak_cfg = EspeakConfig(
    lib_path=espeakng_loader.get_library_path(),
    data_path=ESPEAK_DATA,
)

print("\n[kokoro] lade Modell ...")
t0 = time.time()
kokoro = Kokoro(str(MODEL_PATH), str(VOICES_PATH), espeak_config=espeak_cfg)
print(f"[kokoro] geladen in {time.time()-t0:.1f}s")

# Alle Stimmen auflisten
alle_stimmen = kokoro.get_voices()
de_stimmen = [v for v in alle_stimmen if v.startswith("de_")]

print(f"\n[stimmen] Gesamt: {len(alle_stimmen)} | Deutsch: {len(de_stimmen)}")
print(f"  Deutsch: {de_stimmen}")

TEST_TEXT = (
    "Es war einmal ein Lindwurm namens Hildegunst von Mythenmetz. "
    "Er lebte in einem einsamen Turm hoch oben auf der Lindwurmfeste. "
    "Dort schrieb er Bücher und träumte von großen Abenteuern."
)

if not de_stimmen:
    print("\n[info] Keine de_*-Stimmen — teste alle 54 mit lang=de (Kokoro nutzt espeak-ng Phoneme):")
    test_stimmen = alle_stimmen
else:
    test_stimmen = de_stimmen

print(f"\n[gen] {len(test_stimmen)} Stimmen mit deutschem Text ...\n")

ok = fail = 0
for voice in test_stimmen:
    out_path = OUTPUT_DIR / f"kokoro_{voice}.wav"
    if out_path.exists() and not FORCE:
        print(f"  [skip] {voice}")
        ok += 1
        continue
    try:
        t0 = time.time()
        samples, sr = kokoro.create(TEST_TEXT, voice=voice, speed=1.0, lang="de")
        sf.write(str(out_path), samples, sr)
        dur = len(samples) / sr
        print(f"  [ok]   {voice:20} {time.time()-t0:.1f}s -> {dur:.1f}s audio")
        ok += 1
    except Exception as e:
        print(f"  [fail] {voice:20} {e}")
        fail += 1

print(f"\n[fertig] {ok} OK, {fail} Fehler")
print(f"[output] {OUTPUT_DIR}")
