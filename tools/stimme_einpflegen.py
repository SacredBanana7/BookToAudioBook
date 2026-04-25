# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
"""
Stimme einpflegen - XTTS v2 Speaker-Profil erstellen
======================================================
Berechnet GPT-Conditioning-Latents + Speaker-Embedding aus Referenz-Audio
und speichert das Profil als .pt-Datei. Einmalig ausfuehren, danach
kann die Stimme ohne erneutes Audio-Processing direkt genutzt werden.

Nutzung:
    python stimme_einpflegen.py <name>                 # sucht auto in Samples-Ordner
    python stimme_einpflegen.py <name> <audiodatei>    # explizite Datei

    python stimme_einpflegen.py bea
    python stimme_einpflegen.py kugel
    python stimme_einpflegen.py jadusa stimmen_vorschau/bea.wav
"""

import os
import time
import tempfile
from pathlib import Path

PROJECT_DIR  = Path(__file__).parent.parent.resolve()
MODELS_DIR   = PROJECT_DIR / "models"
SAMPLES_DIR  = PROJECT_DIR / "Audio Samples whatzapp"
PROFILES_DIR = PROJECT_DIR / "stimmen_profile"

os.environ["HF_HOME"]            = str(MODELS_DIR / "huggingface")
os.environ["HF_HUB_CACHE"]       = str(MODELS_DIR / "huggingface" / "hub")
os.environ["TORCH_HOME"]          = str(MODELS_DIR / "torch")
os.environ["TRANSFORMERS_CACHE"]  = str(MODELS_DIR / "huggingface" / "transformers")
os.environ["TTS_HOME"]            = str(MODELS_DIR / "coqui")
os.environ["COQUI_TOS_AGREED"]    = "1"

PROFILES_DIR.mkdir(parents=True, exist_ok=True)

if len(sys.argv) < 2:
    print("Nutzung: python stimme_einpflegen.py <name> [audiodatei]")
    sys.exit(1)

name = sys.argv[1].lower()

if len(sys.argv) >= 3:
    audio_files = [Path(sys.argv[2])]
    if not audio_files[0].exists():
        print(f"[fehler] Datei nicht gefunden: {audio_files[0]}")
        sys.exit(1)
else:
    audio_files = sorted([
        f for f in SAMPLES_DIR.iterdir()
        if f.suffix.lower() in (".ogg", ".wav", ".mp3", ".opus")
        and name in f.stem.lower()
    ])
    if not audio_files:
        print(f"[fehler] Keine Datei fuer '{name}' in {SAMPLES_DIR}")
        sys.exit(1)

print(f"[info] Stimme : {name}")
print(f"[info] Audio  : {[f.name for f in audio_files]}")

import numpy as np
import soundfile as sf
import librosa
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

TARGET_SR   = 22050
MAX_REF_SEC = 30

teile = []
for f in audio_files:
    audio, _ = librosa.load(str(f), sr=TARGET_SR, mono=True)
    teile.append(audio)
combined = np.concatenate(teile)
ref_len = len(combined) / TARGET_SR
if ref_len > MAX_REF_SEC:
    combined = combined[:int(MAX_REF_SEC * TARGET_SR)]
    ref_len = MAX_REF_SEC
print(f"[info] Referenz: {ref_len:.1f}s")

tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
tmp.close()
sf.write(tmp.name, combined, TARGET_SR)

print(f"\n[xtts] lade Modell ...")
t0 = time.time()
from TTS.api import TTS
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
model = tts.synthesizer.tts_model
print(f"[xtts] geladen in {time.time()-t0:.1f}s")

print(f"[xtts] berechne Latents ...")
t0 = time.time()
gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
    audio_path=[tmp.name],
    max_ref_length=MAX_REF_SEC,
    gpt_cond_len=int(min(ref_len, 30)),
    gpt_cond_chunk_len=6,
)
print(f"[xtts] Latents in {time.time()-t0:.1f}s")
print(f"       gpt_cond_latent : {tuple(gpt_cond_latent.shape)}")
print(f"       speaker_embedding: {tuple(speaker_embedding.shape)}")

out_path = PROFILES_DIR / f"{name}.pt"
torch.save({
    "name":              name,
    "gpt_cond_latent":   gpt_cond_latent.cpu(),
    "speaker_embedding": speaker_embedding.cpu(),
    "sample_rate":       24000,
}, str(out_path))

os.unlink(tmp.name)
print(f"\n[ok] Profil: {out_path}")
