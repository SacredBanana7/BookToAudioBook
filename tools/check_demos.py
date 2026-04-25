# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from faster_whisper import WhisperModel

PROJECT_DIR = Path(__file__).parent.parent.resolve()

DEMOS = {
    "WhatsApp-Klone (benni/sina/kugel)": PROJECT_DIR / "demo_output/kapitel3_demo.wav",
    "Preset-Stimmen (Damien/Andrew/Gitta)": PROJECT_DIR / "demo_output/kapitel3_preset.wav",
}

print("[whisper] lade Modell medium ...")
model = WhisperModel("medium", device="cuda", compute_type="float16")

for label, wav in DEMOS.items():
    if not wav.exists():
        print(f"\n[skip] {wav} nicht gefunden")
        continue
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  Datei: {wav}")
    print(f"{'='*60}")
    segments, info = model.transcribe(str(wav), language="de", beam_size=5)
    full_text = ""
    for seg in segments:
        line = f"[{seg.start:5.1f}s] {seg.text.strip()}"
        print(line)
        full_text += seg.text.strip() + " "
    print(f"\n--- Volltext ---")
    print(full_text.strip())
