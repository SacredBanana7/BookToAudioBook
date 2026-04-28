# -*- coding: utf-8 -*-
"""
F5-TTS Voice-Cloning Test
==========================
Nutzung:
    python test_f5tts.py <stimme>
    python test_f5tts.py fred
    python test_f5tts.py kugel
    python test_f5tts.py ma
    python test_f5tts.py doll

F5-TTS braucht neben dem Referenz-Audio auch den transkribierten Text davon.
Wir transkribieren automatisch mit faster-whisper.
"""

import os
import sys
import time
import tempfile
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
MODELS_DIR  = PROJECT_DIR / "models"

os.environ["TORCH_HOME"]           = str(MODELS_DIR / "torch")
os.environ["TRANSFORMERS_CACHE"]   = str(MODELS_DIR / "huggingface" / "transformers")

for p in [MODELS_DIR / "huggingface" / "hub", MODELS_DIR / "torch",
          PROJECT_DIR / "test_output"]:
    p.mkdir(parents=True, exist_ok=True)

stimme      = sys.argv[1] if len(sys.argv) > 1 else "fred"
SAMPLES_DIR = PROJECT_DIR / "Audio Samples whatzapp"

alle_clips = sorted([
    f for f in SAMPLES_DIR.iterdir()
    if f.suffix.lower() in (".ogg", ".wav", ".mp3", ".opus")
    and stimme.lower() in f.stem.lower()
])

if not alle_clips:
    print(f"[fehler] Keine Audio-Dateien fuer '{stimme}' in {SAMPLES_DIR}")
    print(f"[fehler] Vorhandene Dateien: {[f.name for f in SAMPLES_DIR.iterdir()]}")
    sys.exit(1)

print(f"[voice] Stimme : {stimme}")
print(f"[voice] Clips  : {[f.name for f in alle_clips]}")

import numpy as np
import soundfile as sf
import librosa

TARGET_SR = 24000  # F5-TTS arbeitet intern mit 24 kHz

def clips_zu_wav(clip_pfade, sr=TARGET_SR):
    teile = []
    for pfad in clip_pfade:
        audio, _ = librosa.load(str(pfad), sr=sr, mono=True)
        teile.append(audio)
        print(f"[voice]   {pfad.name}: {len(audio)/sr:.1f}s")
    return np.concatenate(teile)

audio = clips_zu_wav(alle_clips)
print(f"[voice] Gesamt-Sample: {len(audio)/TARGET_SR:.1f}s")

# F5-TTS bevorzugt kurze Referenzen (3-15s) – auf 15s kürzen wenn nötig
MAX_REF_SEC = 15
if len(audio) / TARGET_SR > MAX_REF_SEC:
    audio = audio[:int(MAX_REF_SEC * TARGET_SR)]
    print(f"[voice] Auf {MAX_REF_SEC}s gekürzt")

tmp_ref = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
tmp_ref.close()
sf.write(tmp_ref.name, audio, TARGET_SR)
ref_wav = tmp_ref.name

# Torch + torchaudio-Patch (torchcodec-DLL lädt nicht auf Windows/CUDA 12.8)
import torch
print(f"\n[torch] {torch.__version__}, CUDA: {torch.cuda.is_available()}, "
      f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'n/a'}")

import torchaudio as _ta
def _ta_load(filepath, frame_offset=0, num_frames=-1, **_kw):
    data, sr = sf.read(str(filepath), always_2d=True, dtype="float32")
    t = torch.from_numpy(data.T.copy())
    if frame_offset > 0: t = t[:, frame_offset:]
    if num_frames and num_frames > 0: t = t[:, :num_frames]
    return t, sr
def _ta_save(filepath, src, sample_rate, **_kw):
    arr = src.squeeze().cpu().numpy()
    sf.write(str(filepath), arr if arr.ndim == 1 else arr.T, sample_rate)
_ta.load = _ta_load
_ta.save = _ta_save

# Referenz-Audio mit faster-whisper transkribieren
print(f"\n[whisper] transkribiere Referenz-Audio ...")
from faster_whisper import WhisperModel

whisper_cache = str(MODELS_DIR / "whisper")
whisper = WhisperModel("base", device="cuda" if torch.cuda.is_available() else "cpu",
                       download_root=whisper_cache)
segments, info = whisper.transcribe(ref_wav, language="de")
ref_text = " ".join(seg.text.strip() for seg in segments)
print(f"[whisper] Sprache: {info.language} ({info.language_probability:.0%})")
print(f"[whisper] Text: {ref_text!r}")

if not ref_text.strip():
    print("[whisper] Warnung: leere Transkription – benutze Platzhalter")
    ref_text = "Hallo, das ist ein Testtext."

# F5-TTS laden
print(f"\n[f5] lade F5-TTS ...")
t0 = time.time()
from f5_tts.api import F5TTS

device = "cuda" if torch.cuda.is_available() else "cpu"
tts = F5TTS(device=device)
print(f"[f5] Modell geladen in {time.time() - t0:.1f}s")

test_text = (
    "Es war einmal ein Lindwurm namens Hildegunst von Mythenmetz. "
    "Er lebte in einem einsamen Turm auf der Lindwurmfeste."
)

print(f"\n[gen] Text: {test_text!r}")
print(f"[gen] Ref-Text: {ref_text!r}")
t0 = time.time()

wav, sr, _ = tts.infer(
    ref_file=ref_wav,
    ref_text=ref_text,
    gen_text=test_text,
)
gen_time = time.time() - t0

wav_np = np.array(wav, dtype=np.float32)
if wav_np.ndim > 1:
    wav_np = wav_np.squeeze()
audio_seconds = len(wav_np) / sr

out_path = PROJECT_DIR / "test_output" / f"f5tts_{stimme}.wav"
sf.write(str(out_path), wav_np, sr)

print(f"[gen] {gen_time:.1f}s fuer {audio_seconds:.1f}s Audio (RTF={gen_time/audio_seconds:.2f})")
print(f"[gen] gespeichert: {out_path}")
print(f"\n[ok] Fertig.")

os.unlink(ref_wav)
