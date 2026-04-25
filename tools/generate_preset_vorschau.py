# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
"""
XTTS v2 Preset-Stimmen Vorschau Generator
==========================================
Generiert fuer alle 58 eingebauten XTTS v2 Sprecher eine Sprachprobe
und speichert sie in preset_stimmen/.

Nutzung:
    python generate_preset_vorschau.py
    python generate_preset_vorschau.py --force
"""

import os
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.resolve()
MODELS_DIR  = PROJECT_DIR / "models"
OUTPUT_DIR  = PROJECT_DIR / "preset_stimmen"

os.environ["HF_HOME"]            = str(MODELS_DIR / "huggingface")
os.environ["HF_HUB_CACHE"]       = str(MODELS_DIR / "huggingface" / "hub")
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

import numpy as np
import soundfile as sf
import torch

print(f"[torch] {torch.__version__}, CUDA: {torch.cuda.is_available()}, "
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

speakers = sorted(tts.speakers)
print(f"[info] {len(speakers)} Preset-Stimmen")
print(f"[gen]  Text: {TEST_TEXT!r}\n")

ok, fail = 0, 0

for i, speaker in enumerate(speakers, 1):
    safe_name = speaker.replace(" ", "_").replace("/", "-")
    out_path = OUTPUT_DIR / f"{safe_name}.wav"

    if out_path.exists() and not FORCE:
        print(f"[{i:2}/{len(speakers)}] {speaker} — existiert bereits")
        ok += 1
        continue

    print(f"[{i:2}/{len(speakers)}] {speaker} ...", end=" ", flush=True)
    try:
        t0 = time.time()
        wav_list = tts.tts(text=TEST_TEXT, speaker=speaker, language="de")
        gen_time = time.time() - t0
        wav_np = np.array(wav_list, dtype=np.float32)
        sr = tts.synthesizer.output_sample_rate
        audio_sec = len(wav_np) / sr
        sf.write(str(out_path), wav_np, sr)
        print(f"{gen_time:.1f}s -> {audio_sec:.1f}s (RTF={gen_time/audio_sec:.2f}) -> {out_path.name}")
        ok += 1
    except Exception as e:
        print(f"FEHLER: {e}")
        fail += 1

print(f"\n[ok] Fertig: {ok} erfolgreich, {fail} Fehler")
print(f"[ok] Dateien in: {OUTPUT_DIR}")
