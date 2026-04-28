# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
"""
Demo: Kapitel 3 - Jadusa rettet Qwert aus dem Endlosen Abgrund
===============================================================
Generiert den Dialog satzweise (ein Satz = ein Aufruf) fuer
konsistente Stimmbeibehaltung ohne Drift.

Benoetigt vorher:
    python stimme_einpflegen.py kugel
    python stimme_einpflegen.py stephan
    python stimme_einpflegen.py bea

Nutzung:
    python demo_kapitel3.py
    python demo_kapitel3.py --force   (bereits generierte Saetze neu machen)
"""

import os
import sys
import time
from pathlib import Path

PROJECT_DIR  = Path(__file__).parent.parent.resolve()
MODELS_DIR   = PROJECT_DIR / "models"
PROFILES_DIR = PROJECT_DIR / "stimmen_profile"
OUTPUT_DIR   = PROJECT_DIR / "demo_output"
SEGMENTS_DIR = OUTPUT_DIR / "segmente"

os.environ["TORCH_HOME"]          = str(MODELS_DIR / "torch")
os.environ["TRANSFORMERS_CACHE"]  = str(MODELS_DIR / "huggingface" / "transformers")
os.environ["TTS_HOME"]            = str(MODELS_DIR / "coqui")
os.environ["COQUI_TOS_AGREED"]    = "1"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)

FORCE = "--force" in sys.argv

SAMPLE_RATE = 24000  # XTTS v2 Output-SR

# Stimmenzuweisung: Profilname -> Rolle
STIMMEN = {
    "erzaehler": "kugel",
    "qwert":     "benni",
    "jadusa":    "sina",
}

# Passage: Kapitel 3, Zeilen 37-82
# Qwert sturzt, Jadusa rettet ihn, Spongesprehs-Erklarung
PASSAGE = [
    ("erzaehler", "Dann vernahm er ein gleichmäßiges Rauschen über sich und drehte mühsam seinen Kopf, sodass er nach oben blicken konnte."),
    ("erzaehler", "Zuerst sah er nur zwei gewaltige Flügel, die über ihm auf und ab schwangen."),
    ("erzaehler", "Aufgrund ihrer einzigartigen Form und der schillernden Farben wusste er sofort, wem sie gehörten."),
    ("erzaehler", "Das waren die Schwingen der Janusmeduse, kein Zweifel!"),
    ("erzaehler", "Sie flatterte über ihm, hatte ihm ihr hübsches Gesicht zugewandt und hielt ihn mit etwas im Genick gepackt, das sich anfühlte wie große kräftige Vogelkrallen."),
    ("jadusa",    "Ich habe dich doch wiederholt davor gewarnt, dass hier manche Dinge nicht das sind, was sie zu sein vorgeben."),
    ("jadusa",    "Und dir gesagt, dass du dich vorsehen sollst."),
    ("jadusa",    "Aber blindlings in einen schwarzen Schlund zu springen, das ist besonders dämlich."),
    ("jadusa",    "Oder ist das in deiner Dimension so üblich?"),
    ("qwert",     "Nein. Ich war gerade dabei, es zu bereuen."),
    ("jadusa",    "Und? Was sagt man denn?"),
    ("qwert",     "Wie bitte?"),
    ("jadusa",    "Nein, man sagt auf jeden Fall nicht Wie bitte, wenn einem das Leben gerettet wird."),
    ("jadusa",    "Man sagt Danke schön! Oder herrschen in deiner Dimension auch andere Gesetze in Sachen Höflichkeit?"),
    ("qwert",     "Nein. Vielen Dank! Danke schön! Danke!"),
    ("jadusa",    "Na also. Geht doch!"),
    ("jadusa",    "Jetzt sind wir quitt, würde ich mal sagen."),
    ("jadusa",    "Du hast mich vor dem Medusenwächter gerettet, und ich rette dich aus dem Endlosen Abgrund."),
    ("jadusa",    "Eine Hand wäscht die andere."),
    ("erzaehler", "Sie ließ Qwerts Hals los und packte stattdessen seine Rüstung bei den Schultern."),
    ("erzaehler", "Er baumelte nun stabil unter ihr und konnte wieder frei atmen."),
    ("qwert",     "Ja. Jetzt sind wir quitt."),
    ("jadusa",    "Hervorragend! Dann kann ich dich ja wieder loslassen."),
    ("qwert",     "Nein! Bitte nicht loslassen!"),
    ("erzaehler", "Die Meduse lachte entzückend."),
    ("jadusa",    "Haha! War nur ein Scherz, Kleiner! Keine Panik!"),
    ("jadusa",    "Ich bin den weiten Weg nicht gekommen, um dich zuerst zu retten und dann wieder fallen zu lassen."),
    ("jadusa",    "Ich bin böse, aber nicht grundlos gemein."),
    ("qwert",     "Den weiten Weg? Wie kommst du überhaupt hierher?"),
    ("qwert",     "Ich habe dich in entgegengesetzter Richtung über den Wald davonfliegen sehen."),
    ("qwert",     "Und jetzt bist du plötzlich hier. Wie ist das möglich?"),
    ("jadusa",    "Also, wirklich erklären kann ich dir das auch nicht."),
    ("jadusa",    "Nur so viel: Manchmal bewegen wir uns hier in Spongesprüs fort."),
    ("qwert",     "In ... Spongesprüs?"),
    ("jadusa",    "Ja. So nennen wir das: spontane Gedankensprünge. Ein Kofferwort."),
    ("jadusa",    "Die kommen nicht oft vor, aber manchmal eben doch."),
    ("jadusa",    "Vielleicht so: eine Mischung aus Wunschdenken, Eskapismus und Teleportation."),
    ("jadusa",    "Es ist so ähnlich, wie wenn man beim Lesen eines Buches ein paar Seiten überspringt."),
    ("jadusa",    "Eben war man noch hier, und dann ist man plötzlich woanders. Einfach so!"),
    ("jadusa",    "Keine große Sache. Es passiert eben manchmal."),
    ("qwert",     "Tatsächlich? Wo warst du denn, bevor du dich plötzlich hier wiederfandest?"),
    ("jadusa",    "Da hatte ich den Wald schon hinter mich gebracht und flog gerade über die Große Ebene, als ..."),
    ("qwert",     "Die Große Ebene?"),
    ("jadusa",    "Ja. Das ist so eine total flache Landschaft, ohne Berge oder nennenswerte Vegetation."),
    ("qwert",     "Ich weiß, was eine Ebene ist."),
    ("qwert",     "Haben die Gegenden hier keine Namen? Heißen die immer nur Wald oder Ebene?"),
    ("jadusa",    "Ja, eigentlich kommen wir damit ganz gut aus."),
    ("jadusa",    "Manchmal fügen wir noch ein Adjektiv hinzu, das reicht dann völlig."),
    ("jadusa",    "Wofür braucht ein Wald schon einen Namen, wenn er morgen wieder verschwunden oder blau statt grün ist?"),
    ("jadusa",    "Soll ich dir jetzt erzählen, wie ich hierhergekommen bin, oder nicht?"),
    ("qwert",     "Entschuldigung."),
    ("jadusa",    "Entschuldigung akzeptiert, Süßer!"),
]

import re
import numpy as np
import soundfile as sf
import torch

MAX_CHUNK_CHARS = 80  # ~4-5 Sekunden Sprechzeit

def teile_satz(text, max_chars=MAX_CHUNK_CHARS):
    """Teilt langen Satz an natuerlichen Pausen in Chunks <= max_chars."""
    if len(text) <= max_chars:
        return [text.strip()]
    # An Satzzeichen aufteilen, Satzzeichen am Ende des jeweiligen Chunks behalten
    raw = re.split(r'(?<=[,;:!?\-–])\s+', text)
    chunks = []
    current = ""
    for part in raw:
        if not current:
            current = part
        elif len(current) + 1 + len(part) <= max_chars:
            current += " " + part
        else:
            chunks.append(current.strip())
            current = part
    if current.strip():
        chunks.append(current.strip())
    # Einzelne Chunks die noch zu lang sind an Wortgrenzen aufteilen
    result = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            result.append(chunk)
        else:
            words = chunk.split()
            curr = ""
            for w in words:
                if not curr:
                    curr = w
                elif len(curr) + 1 + len(w) <= max_chars:
                    curr += " " + w
                else:
                    result.append(curr)
                    curr = w
            if curr:
                result.append(curr)
    return [r for r in result if r.strip()]

print(f"[torch] {torch.__version__}, CUDA: {torch.cuda.is_available()}")

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

# Profile pruefen
fehlend = [r for r in set(s for s, _ in PASSAGE) if not (PROFILES_DIR / f"{STIMMEN[r]}.pt").exists()]
if fehlend:
    print(f"\n[fehler] Fehlende Profile: {fehlend}")
    for r in fehlend:
        print(f"  -> python stimme_einpflegen.py {STIMMEN[r]}")
    sys.exit(1)

print(f"\n[xtts] lade Modell ...")
t0 = time.time()
from TTS.api import TTS
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
model = tts.synthesizer.tts_model
print(f"[xtts] geladen in {time.time()-t0:.1f}s")

# Profile laden
profile_cache = {}
for rolle, profil_name in STIMMEN.items():
    pt_path = PROFILES_DIR / f"{profil_name}.pt"
    data = torch.load(str(pt_path), map_location=device)
    profile_cache[rolle] = {
        "gpt_cond_latent":   data["gpt_cond_latent"].to(device),
        "speaker_embedding": data["speaker_embedding"].to(device),
    }
    print(f"[profile] {rolle:12} <- {profil_name}.pt")

SILENCE_GLEICH  = np.zeros(int(SAMPLE_RATE * 0.25), dtype=np.float32)  # 250ms gleicher Sprecher
SILENCE_WECHSEL = np.zeros(int(SAMPLE_RATE * 0.55), dtype=np.float32)  # 550ms Sprecherwechsel

def trim_stille(wav, sr=SAMPLE_RATE, schwelle=0.01, rand_ms=40):
    """Trimmt führende und nachfolgende Stille, lässt rand_ms stehen."""
    rand = int(sr * rand_ms / 1000)
    maske = np.abs(wav) > schwelle
    idx = np.where(maske)[0]
    if len(idx) == 0:
        return wav
    start = max(0, idx[0] - rand)
    ende  = min(len(wav), idx[-1] + rand)
    return wav[start:ende]

def generiere_chunk(rolle, text, seg_path):
    if seg_path.exists() and not FORCE:
        wav_np, _ = sf.read(str(seg_path), dtype="float32")
        return wav_np, True  # aus Cache
    prof = profile_cache[rolle]
    out = model.inference(
        text=text,
        language="de",
        gpt_cond_latent=prof["gpt_cond_latent"],
        speaker_embedding=prof["speaker_embedding"],
        temperature=0.7,
        repetition_penalty=10.0,
        top_k=50,
        top_p=0.85,
        enable_text_splitting=False,
    )
    wav_np = np.array(out["wav"], dtype=np.float32)
    if wav_np.ndim > 1:
        wav_np = wav_np.squeeze()
    sf.write(str(seg_path), wav_np, SAMPLE_RATE)
    return wav_np, False

print(f"\n[gen] {len(PASSAGE)} Segmente (max {MAX_CHUNK_CHARS} Zeichen/Chunk) ...\n")
t_start = time.time()

audio_parts = []
prev_rolle = None
ok = fail = 0
chunk_idx = 0

for i, (rolle, text) in enumerate(PASSAGE, 1):
    chunks = teile_satz(text)
    n = len(chunks)
    label = f"[{i:2}/{len(PASSAGE)}] {rolle:12}"

    if n == 1:
        print(f"{label} {text[:55]!r}")
    else:
        print(f"{label} -> {n} Chunks: {text[:45]!r}...")

    seg_wavs = []
    for j, chunk in enumerate(chunks):
        chunk_idx += 1
        seg_path = SEGMENTS_DIR / f"{chunk_idx:04d}_{rolle}.wav"
        try:
            t0 = time.time()
            wav_np, from_cache = generiere_chunk(rolle, chunk, seg_path)
            if not from_cache:
                gt = time.time() - t0
                print(f"    [{j+1}/{n}] {gt:.1f}s -> {len(wav_np)/SAMPLE_RATE:.1f}s  {chunk[:45]!r}")
            seg_wavs.append(wav_np)
            ok += 1
        except Exception as e:
            print(f"    [{j+1}/{n}] FEHLER: {e}")
            seg_wavs.append(SILENCE_GLEICH)
            fail += 1

    # Chunks eines Satzes trimmen und nahtlos zusammenkleben
    trimmed = [trim_stille(w) for w in seg_wavs]
    satz_wav = np.concatenate(trimmed)

    # Pause zwischen Saetzen/Sprechern
    if prev_rolle is not None:
        pause = SILENCE_GLEICH if rolle == prev_rolle else SILENCE_WECHSEL
        audio_parts.append(pause)

    audio_parts.append(satz_wav)
    prev_rolle = rolle

# Zusammenkleben und speichern
full_audio = np.concatenate(audio_parts)
total_sec = len(full_audio) / SAMPLE_RATE
gen_total = time.time() - t_start

out_path = OUTPUT_DIR / "kapitel3_demo.wav"
sf.write(str(out_path), full_audio, SAMPLE_RATE)

print(f"\n[ok] {ok} Segmente OK, {fail} Fehler")
print(f"[ok] Gesamt: {total_sec/60:.1f} Minuten Audio in {gen_total:.0f}s generiert")
print(f"[ok] Gespeichert: {out_path}")
