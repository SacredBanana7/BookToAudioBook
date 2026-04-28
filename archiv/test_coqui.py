# -*- coding: utf-8 -*-
"""
Coqui XTTS v2 Voice-Cloning Test
==================================
Nutzung:
    python test_coqui.py <stimme> [exaggeration]
    python test_coqui.py fred
    python test_coqui.py kugel
    python test_coqui.py ma
    python test_coqui.py doll

XTTS v2 hat native Deutsch-Unterstuetzung (language="de") und
Voice Cloning - kein Fremdakzent wie beim englisch-basierten Chatterbox.
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
os.environ["TTS_HOME"] = str(MODELS_DIR / "coqui")  # Coqui-Modell-Cache
os.environ["COQUI_TOS_AGREED"] = "1"               # Lizenz-Prompt automatisch akzeptieren

for p in [MODELS_DIR / "coqui", PROJECT_DIR / "test_output"]:
    p.mkdir(parents=True, exist_ok=True)

stimme = sys.argv[1] if len(sys.argv) > 1 else "fred"
SAMPLES_DIR = PROJECT_DIR / "Audio Samples Whatzapp"

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

# Mehrere Clips zusammenkleben (XTTS braucht WAV, kein OGG)
import numpy as np
import soundfile as sf
import librosa

TARGET_SR = 22050

def clips_zu_wav(clip_pfade):
    teile = []
    for pfad in clip_pfade:
        audio, _ = librosa.load(str(pfad), sr=TARGET_SR, mono=True)
        teile.append(audio)
        print(f"[voice]   {pfad.name}: {len(audio)/TARGET_SR:.1f}s")
    return np.concatenate(teile)

audio = clips_zu_wav(alle_clips)
print(f"[voice] Gesamt-Sample: {len(audio)/TARGET_SR:.1f}s")

# Temp-WAV erstellen (XTTS braucht WAV-Datei)
tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
tmp_wav.close()  # Windows: Handle schließen bevor soundfile und os.unlink drauf zugreifen
sf.write(tmp_wav.name, audio, TARGET_SR)
audio_prompt = tmp_wav.name

# XTTS v2 laden
print(f"\n[coqui] lade XTTS v2 ...")
import torch
print(f"[torch] {torch.__version__}, CUDA: {torch.cuda.is_available()}, "
      f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'n/a'}")

# torchcodec-DLL lässt sich auf Windows/CUDA 12.8 nicht laden → torchaudio.load/save
# mit soundfile ersetzen bevor coqui-tts sie aufruft
import torchaudio as _ta
def _ta_load(filepath, frame_offset=0, num_frames=-1, **_kw):
    data, sr = sf.read(str(filepath), always_2d=True, dtype="float32")
    t = torch.from_numpy(data.T.copy())  # (channels, samples)
    if frame_offset > 0: t = t[:, frame_offset:]
    if num_frames and num_frames > 0: t = t[:, :num_frames]
    return t, sr
def _ta_save(filepath, src, sample_rate, **_kw):
    arr = src.squeeze().cpu().numpy()
    sf.write(str(filepath), arr if arr.ndim == 1 else arr.T, sample_rate)
_ta.load = _ta_load
_ta.save = _ta_save

# transformers 5.x hat isin_mps_friendly entfernt, coqui-tts erwartet 4.x
import transformers.pytorch_utils as _pt_utils
if not hasattr(_pt_utils, "isin_mps_friendly"):
    _pt_utils.isin_mps_friendly = torch.isin

t0 = time.time()
from TTS.api import TTS

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = tts.to(device)
print(f"[coqui] Modell geladen in {time.time() - t0:.1f}s")

test_text = (
    "Es war einmal ein Lindwurm namens Hildegunst von Mythenmetz. "
    "Er lebte in einem einsamen Turm auf der Lindwurmfeste."
)

print(f"\n[gen] Text: {test_text!r}")
t0 = time.time()
wav_list = tts.tts(
    text=test_text,
    speaker_wav=audio_prompt,
    language="de",
)
gen_time = time.time() - t0

# tts.tts() liefert Liste von floats -> numpy -> soundfile (kein torchaudio noetig)
wav_np = np.array(wav_list, dtype=np.float32)
sample_rate = tts.synthesizer.output_sample_rate
audio_seconds = len(wav_np) / sample_rate

out_path = PROJECT_DIR / "test_output" / f"coqui_{stimme}.wav"
sf.write(str(out_path), wav_np, sample_rate)

print(f"[gen] {gen_time:.1f}s fuer {audio_seconds:.1f}s Audio (RTF={gen_time/audio_seconds:.2f})")
print(f"[gen] gespeichert: {out_path}")
print(f"\n[ok] Fertig.")

# Temp aufraumen
os.unlink(tmp_wav.name)
