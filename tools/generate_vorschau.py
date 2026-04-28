# -*- coding: utf-8 -*-
"""
XTTS v2 Stimmen-Vorschau Generator
====================================
Generiert fuer alle WhatsApp-Audiodateien im Samples-Ordner
eine XTTS v2 Sprachprobe und speichert sie in stimmen_vorschau/.

Nutzung:
    python generate_vorschau.py
    python generate_vorschau.py --force   (bereits existierende ueberschreiben)
"""

import os
import re
import sys
import time
import tempfile
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.resolve()
MODELS_DIR  = PROJECT_DIR / "models"
SAMPLES_DIR = PROJECT_DIR / "Audio Samples whatzapp"
OUTPUT_DIR  = PROJECT_DIR / "stimmen_vorschau"

os.environ["TORCH_HOME"]          = str(MODELS_DIR / "torch")
os.environ["TRANSFORMERS_CACHE"]  = str(MODELS_DIR / "huggingface" / "transformers")
os.environ["TTS_HOME"]            = str(MODELS_DIR / "coqui")
os.environ["COQUI_TOS_AGREED"]    = "1"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FORCE = "--force" in sys.argv

TEST_TEXT = (
    "Es war einmal ein Lindwurm namens Hildegunst von Mythenmetz. "
    "Er lebte in einem einsamen Turm hoch oben auf der Lindwurmfeste. "
    "Dort schrieb er Bücher und träumte von großen Abenteuern."
)

SKIP_STEMS = {"whatzapp audio", "testaudio tts"}

def extract_voice_name(stem: str) -> str:
    s = stem.strip()
    s = re.sub(r"(?i)^whatz?app\s+", "", s)
    s = re.sub(r"(?i)^laengeres\s+audio\s+", "", s)
    s = re.sub(r"(?i)^längeres\s+audio\s+", "", s)
    s = re.sub(r"(?i)^audio\s+von\s+", "", s)
    s = re.sub(r"(?i)\s+audio(\s+sample)?$", "", s)
    return s.strip().lower()

clips = sorted([
    f for f in SAMPLES_DIR.iterdir()
    if f.suffix.lower() in (".ogg", ".wav", ".mp3", ".opus")
])

voices = []
for clip in clips:
    name = extract_voice_name(clip.stem)
    if not name or name in SKIP_STEMS:
        print(f"[skip] {clip.name}")
        continue
    voices.append((name, clip))

print(f"\n[info] {len(voices)} Stimmen gefunden:")
for name, clip in voices:
    print(f"  {name:14} <- {clip.name}")

import numpy as np
import soundfile as sf
import librosa
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

import transformers.pytorch_utils as _pt_utils
if not hasattr(_pt_utils, "isin_mps_friendly"):
    _pt_utils.isin_mps_friendly = torch.isin

print(f"\n[xtts] lade Modell ...")
t0 = time.time()
from TTS.api import TTS
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
print(f"[xtts] Modell geladen in {time.time()-t0:.1f}s")
print(f"\n[gen] Text: {TEST_TEXT!r}\n")

TARGET_SR  = 22050
MAX_REF_SEC = 15
ok, fail = 0, 0

for i, (name, clip) in enumerate(voices, 1):
    out_path = OUTPUT_DIR / f"{name}.wav"
    if out_path.exists() and not FORCE:
        print(f"[{i:2}/{len(voices)}] {name} — existiert bereits (--force zum Ueberschreiben)")
        ok += 1
        continue

    print(f"[{i:2}/{len(voices)}] {name} ...", end=" ", flush=True)

    audio, _ = librosa.load(str(clip), sr=TARGET_SR, mono=True)
    ref_len = len(audio) / TARGET_SR
    if ref_len > MAX_REF_SEC:
        audio = audio[:int(MAX_REF_SEC * TARGET_SR)]

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    sf.write(tmp.name, audio, TARGET_SR)

    try:
        t0 = time.time()
        wav_list = tts.tts(text=TEST_TEXT, speaker_wav=tmp.name, language="de")
        gen_time = time.time() - t0
        wav_np = np.array(wav_list, dtype=np.float32)
        sr = tts.synthesizer.output_sample_rate
        audio_sec = len(wav_np) / sr
        sf.write(str(out_path), wav_np, sr)
        print(f"{gen_time:.1f}s -> {audio_sec:.1f}s Audio (RTF={gen_time/audio_sec:.2f}) -> {out_path.name}")
        ok += 1
    except Exception as e:
        print(f"FEHLER: {e}")
        fail += 1
    finally:
        os.unlink(tmp.name)

print(f"\n[ok] Fertig: {ok} erfolgreich, {fail} Fehler")
print(f"[ok] Dateien in: {OUTPUT_DIR}")
