# -*- coding: utf-8 -*-
"""
Chatterbox-TTS Voice-Cloning Test
===================================
Nutzung:
    python test_chatterbox.py <stimme>
    python test_chatterbox.py fred
    python test_chatterbox.py kugel

Mehrere .ogg/.wav-Clips im "Audio Samples Whatzapp"-Ordner werden
automatisch zu einem langen Sample zusammengeklebt wenn mehrere
Dateien mit dem Stimm-Namen beginnen (z.B. "fred_1.ogg", "fred_2.ogg").

Modell- und Cache-Pfade liegen im Projektordner -> portabel.
"""

import os
import sys
import time
import tempfile
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
MODELS_DIR = PROJECT_DIR / "models"

os.environ["TORCH_HOME"] = str(MODELS_DIR / "torch")
os.environ["TRANSFORMERS_CACHE"] = str(MODELS_DIR / "huggingface" / "transformers")

for p in [MODELS_DIR / "huggingface", MODELS_DIR / "huggingface" / "hub",
          MODELS_DIR / "torch", PROJECT_DIR / "test_output"]:
    p.mkdir(parents=True, exist_ok=True)

# Stimme aus Argument lesen (Standard: fred)
stimme = sys.argv[1] if len(sys.argv) > 1 else "fred"
SAMPLES_DIR = PROJECT_DIR / "Audio Samples Whatzapp"

# Alle passenden Audio-Dateien fuer diese Stimme finden
# Passt auf: "fred.ogg", "Längeres Audio Fred.ogg", "fred_1.ogg" etc.
alle_clips = sorted([
    f for f in SAMPLES_DIR.iterdir()
    if f.suffix.lower() in (".ogg", ".wav", ".mp3", ".opus")
    and stimme.lower() in f.stem.lower()
])

if not alle_clips:
    print(f"[fehler] Keine Audio-Dateien fuer '{stimme}' in {SAMPLES_DIR}")
    print(f"[fehler] Vorhandene Dateien: {[f.name for f in SAMPLES_DIR.iterdir()]}")
    sys.exit(1)

print(f"[voice] Stimme: {stimme}")
print(f"[voice] Clips gefunden: {[f.name for f in alle_clips]}")

# Mehrere Clips zusammenkleben
import numpy as np
import soundfile as sf
import librosa

def clips_zusammenkleben(clip_pfade, ziel_sr=22050):
    teile = []
    for pfad in clip_pfade:
        audio, sr = librosa.load(str(pfad), sr=ziel_sr, mono=True)
        teile.append(audio)
        print(f"[voice]   {pfad.name}: {len(audio)/ziel_sr:.1f}s")
    return np.concatenate(teile), ziel_sr

if len(alle_clips) == 1:
    audio_prompt = str(alle_clips[0])
    audio, sr = librosa.load(audio_prompt, sr=22050, mono=True)
    print(f"[voice] Sample-Laenge: {len(audio)/sr:.1f}s")
else:
    print(f"[voice] Klebe {len(alle_clips)} Clips zusammen ...")
    audio, sr = clips_zusammenkleben(alle_clips)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, sr)
    audio_prompt = tmp.name
    print(f"[voice] Gesamt-Sample: {len(audio)/sr:.1f}s -> {audio_prompt}")

# Modell laden
print(f"\n[chatterbox] lade Modell ...")
t0 = time.time()
import torch
from chatterbox.tts import ChatterboxTTS

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[torch] {torch.__version__}, CUDA: {torch.cuda.is_available()}, "
      f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'n/a'}")
model = ChatterboxTTS.from_pretrained(device=device)
print(f"[chatterbox] Modell geladen in {time.time() - t0:.1f}s")

test_text = (
    "Es war einmal ein Lindwurm namens Hildegunst von Mythenmetz. "
    "Er lebte in einem einsamen Turm auf der Lindwurmfeste."
)

sample_rate = getattr(model, "sr", 24000)

print(f"\n[gen] exaggeration=0.3 ...")
t0 = time.time()
wav = model.generate(test_text, audio_prompt_path=audio_prompt, exaggeration=0.3)
gen_time = time.time() - t0
audio_seconds = wav.shape[-1] / sample_rate
print(f"[gen] {gen_time:.1f}s fuer {audio_seconds:.1f}s Audio (RTF={gen_time/audio_seconds:.2f})")

out_path = PROJECT_DIR / "test_output" / f"chatterbox_{stimme}.wav"
wav_np = wav.squeeze().cpu().numpy()
sf.write(str(out_path), wav_np, sample_rate)
print(f"[gen] gespeichert: {out_path}")
print(f"\n[ok] Fertig.")
