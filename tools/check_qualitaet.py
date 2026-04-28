# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
"""
Whisper-Qualitaetspruefung fuer generierte Stimmen-Samples
===========================================================
Prueft alle WAV-Dateien in stimmen_vorschau/ und preset_stimmen/
ob sie vollstaendig auf Deutsch bleiben.

Kriterien fuer "gut":
- Erkannte Sprache: Deutsch (>70%)
- Mindestens Schluesselbegriffe aus Satz 1+2+3 erkannt
  (= der ganze Text wurde auf Deutsch gesprochen)
"""

import os
from pathlib import Path
import torch

PROJECT_DIR = Path(__file__).parent.parent.resolve()
MODELS_DIR  = PROJECT_DIR / "models"

os.environ["TORCH_HOME"]          = str(MODELS_DIR / "torch")
os.environ["TRANSFORMERS_CACHE"]  = str(MODELS_DIR / "huggingface" / "transformers")

# Erwartet aus Satz 1, 2 und 3 – mindestens eines pro Satz
KEYWORDS_S1 = ["lindwurm", "hildegunst", "mythenmetz"]
KEYWORDS_S2 = ["lindwurmfeste", "turm"]
KEYWORDS_S3 = ["bücher", "buecher", "abenteuern", "träumte", "traeumte"]

def satz_ok(text_lower, keywords):
    return any(k in text_lower for k in keywords)

print(f"[torch] CUDA: {torch.cuda.is_available()}")
print(f"\n[whisper] lade Modell ...")
from faster_whisper import WhisperModel
device = "cuda" if torch.cuda.is_available() else "cpu"
whisper = WhisperModel("base", device=device,
                       download_root=str(MODELS_DIR / "whisper"))
print(f"[whisper] bereit\n")

ORDNER = {
    "whatsapp": PROJECT_DIR / "stimmen_vorschau",
    "preset":   PROJECT_DIR / "preset_stimmen",
}

gut    = []
maessig = []
schlecht = []

for kategorie, ordner in ORDNER.items():
    wavs = sorted(ordner.glob("*.wav"))
    print(f"{'='*60}")
    print(f"  {kategorie.upper()} — {len(wavs)} Dateien")
    print(f"{'='*60}")

    for wav in wavs:
        segments, info = whisper.transcribe(str(wav), language=None)
        text = " ".join(seg.text.strip() for seg in segments)
        tl = text.lower()

        lang_ok  = info.language == "de" and info.language_probability >= 0.70
        s1_ok    = satz_ok(tl, KEYWORDS_S1)
        s2_ok    = satz_ok(tl, KEYWORDS_S2)
        s3_ok    = satz_ok(tl, KEYWORDS_S3)
        alle_ok  = lang_ok and s1_ok and s2_ok and s3_ok
        teilweise = lang_ok and (s1_ok or s2_ok) and not alle_ok

        if alle_ok:
            status = "OK  "
            gut.append(f"{kategorie}/{wav.stem}")
        elif teilweise:
            status = "TEIL"
            maessig.append(f"{kategorie}/{wav.stem}")
        else:
            status = "FAIL"
            schlecht.append(f"{kategorie}/{wav.stem}")

        s_flags = f"S1={'✓' if s1_ok else '✗'} S2={'✓' if s2_ok else '✗'} S3={'✓' if s3_ok else '✗'}"
        print(f"[{status}] {wav.stem:<28} lang={info.language}({info.language_probability:.0%})  {s_flags}")
        print(f"       {text[:90]!r}")

print(f"\n{'='*60}")
print(f"  ERGEBNIS")
print(f"{'='*60}")
print(f"\nOK ({len(gut)}):")
for s in gut:
    print(f"  + {s}")

print(f"\nTEIL ({len(maessig)}) — Satz 1+2 ok aber Satz 3 abbricht:")
for s in maessig:
    print(f"  ~ {s}")

print(f"\nFAIL ({len(schlecht)}) — Sprachswitch oder unverstaendlich:")
for s in schlecht:
    print(f"  - {s}")

print(f"\n[ok] Fertig.")
