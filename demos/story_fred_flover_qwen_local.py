# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
"""
"Der Code-Krieg" lokal mit Qwen3-TTS-1.7B-Base + echtem Voice Cloning.
Nutzt die hochwertigen Referenz-Audiofiles aus 'Voice Cloning Text Audio Samples better Quality'.

Ausfuehren mit: .qwen_venv/Scripts/python.exe demos/story_fred_flover_qwen_local.py
"""
import os, time, torch
import numpy as np
import soundfile as sf
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.resolve()
SAMPLES_DIR = PROJECT_DIR / "Voice Cloning Text Audio Samples better Quality"
OUTPUT_DIR  = PROJECT_DIR / "demo_output" / "code_krieg_qwen_lokal"

env_file = PROJECT_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("HF_TOKEN="):
            os.environ["HF_TOKEN"] = line.split("=", 1)[1].strip()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REF_FRED   = SAMPLES_DIR / "Fred Voice Cloning text2 .wav"
REF_FLOVER = SAMPLES_DIR / "flover2.wav"

SZENEN = [
    ("Fred",   "Es war einmal ein Codebase so gross wie ein Kontinent - und irgendwo in seinen dunkelsten Tiefen lauerte das Chaos. Die Bugs hatten sich versammelt. Tausende. Jede Zeile ein potenzielles Minenfeld."),
    ("Flover", "Fred! Fred, ich seh es! Dort hinten, hinter dem API-Gateway - ein Stack Overflow, und der Kerl ist riesig!"),
    ("Fred",   "Ich sehe es. Ruhig bleiben. Claude - aktiviere das Analyse-Protokoll."),
    ("Flover", "Was analysieren?! Der frisst unsere Request-Handler! Wir muessen jetzt ran!"),
    ("Fred",   "Und so stürzten sie sich in den Kampf. Fred mit der Praezision eines Debuggers, Schritt fuer Schritt durch den Stack Trace. Flover dagegen - wild, unberechenbar - sprang von Branch zu Branch wie ein Affe auf Koffein."),
    ("Flover", "Ha! Null Pointer - du hast dich verraten! Claude, zeig ihm den Weg! Wirf die Exception!"),
    ("Fred",   "Der Schlag sass. Der erste Bug kollabierte in einem Meer aus rotem Terminal-Text. Aber da - der Boss. Ein zirkulaerer Import, gross wie ein Serverraum, mit tausend Abhaengigkeiten als Tentakeln."),
    ("Flover", "Das... das ist gross. Fred, ich glaube, ich hab Angst."),
    ("Fred",   "Kein Grund. Wir haben Claude. Und Claude hat immer einen Plan."),
    ("Flover", "Wir zerlegten ihn Modul fuer Modul. Fred trennte die Abhaengigkeiten, ich hielt die Tests am Laufen - und Claude? Claude hielt uns wach. Am Ende blieb nur gruenes Terminal. Alle Tests bestanden. Stille."),
    ("Fred",   "Gut gemacht, Flover."),
    ("Flover", "Du weisst was das Beste ist? Morgen gibt es neue Bugs."),
    ("Fred",   "Und sie lachten. Denn das war ihre Welt - fehlerhaft, chaotisch, wunderbar. Der Codebase schlief. Bis zum naechsten Mal."),
]

SR_OUT = 24000
SILENCE_GLEICH  = np.zeros(int(SR_OUT * 0.25), dtype=np.float32)
SILENCE_WECHSEL = np.zeros(int(SR_OUT * 0.55), dtype=np.float32)


def trim_stille(wav, schwelle=0.005, rand_ms=40, sr=SR_OUT):
    rand = int(sr * rand_ms / 1000)
    maske = np.abs(wav) > schwelle
    idx = np.where(maske)[0]
    if len(idx) == 0:
        return wav
    return wav[max(0, idx[0]-rand):min(len(wav), idx[-1]+rand)]


print("[qwen3] lade Base-Modell (Voice Cloning) ...")
t0 = time.time()

from qwen_tts import Qwen3TTSModel

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    device_map="cuda",
    dtype=torch.bfloat16,
)
print(f"[qwen3] geladen in {time.time()-t0:.1f}s")

# Referenz-Audio laden — nur erste 10s nutzen (ICL braucht nicht mehr)
def lade_ref(path, max_sec=10):
    wav, sr = sf.read(str(path), dtype="float32")
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    if max_sec:
        wav = wav[:int(sr * max_sec)]
    return wav, sr

print("[qwen3] erstelle Voice-Clone-Prompts ...")
ref_fred_wav, ref_fred_sr     = lade_ref(REF_FRED)
ref_flover_wav, ref_flover_sr = lade_ref(REF_FLOVER)

prompt_fred   = model.create_voice_clone_prompt((ref_fred_wav,   ref_fred_sr),   x_vector_only_mode=True)
prompt_flover = model.create_voice_clone_prompt((ref_flover_wav, ref_flover_sr), x_vector_only_mode=True)
print("[qwen3] Prompts erstellt.")

prompts = {"Fred": prompt_fred, "Flover": prompt_flover}

print(f"\n[gen] {len(SZENEN)} Szenen ...\n")
t_start = time.time()
audio_parts, prev_sprecher = [], None

for i, (sprecher, text) in enumerate(SZENEN, 1):
    out_path = OUTPUT_DIR / f"{i:02d}_{sprecher}.wav"
    print(f"  [{i:02d}] {sprecher}: {text[:55]}...")

    t0 = time.time()
    wavs, sr = model.generate_voice_clone(
        text=text,
        voice_clone_prompt=prompts[sprecher],
        language="German",
    )
    wav = wavs[0].astype(np.float32)
    sf.write(str(out_path), wav, SR_OUT)
    dauer = len(wav) / SR_OUT
    print(f"         -> {time.time()-t0:.1f}s gen, {dauer:.1f}s Audio")

    pause = SILENCE_GLEICH if sprecher == prev_sprecher else SILENCE_WECHSEL
    if prev_sprecher is not None:
        audio_parts.append(pause)
    audio_parts.append(trim_stille(wav))
    prev_sprecher = sprecher

full_audio = np.concatenate(audio_parts)
total_min  = len(full_audio) / SR_OUT / 60
gen_total  = time.time() - t_start

final_path = OUTPUT_DIR / "code_krieg_komplett.wav"
sf.write(str(final_path), full_audio, SR_OUT)

print(f"\n[fertig] {total_min:.1f} Minuten Audio in {gen_total:.0f}s generiert")
print(f"[fertig] Gespeichert: {final_path}")
