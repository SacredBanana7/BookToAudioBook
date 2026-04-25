# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
"""
Demo Kapitel 3 – Kokoro ONNX Preset-Stimmen
============================================
Gleiche Passage wie demo_kapitel3.py, aber mit Kokoro ONNX statt XTTS v2.
Kein Voice Cloning – reine Preset-Stimmen mit espeak-ng Deutsch-Phonemisierung.

Stimmen:
  Erzaehler -> bm_george  (British Male, seriös)
  Qwert     -> am_puck    (American Male, jung/dynamisch)
  Jadusa    -> ef_dora    (European Female, charmant)
"""

import os, re, time
from pathlib import Path

PROJECT_DIR  = Path(__file__).parent.parent.resolve()
OUTPUT_DIR   = PROJECT_DIR / "demo_output"
SEGMENTS_DIR = OUTPUT_DIR / "segmente_kokoro"

# espeak-ng DLL verträgt keine Umlaut-Pfade → ASCII-Kopie in AppData
ESPEAK_DATA = os.path.join(os.environ["LOCALAPPDATA"], "espeak-ng-data")
os.environ["ESPEAK_DATA_PATH"] = ESPEAK_DATA

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)

FORCE = "--force" in sys.argv

KOKORO_STIMMEN = {
    "erzaehler": "bm_george",
    "qwert":     "am_puck",
    "jadusa":    "ef_dora",
}

MAX_CHUNK_CHARS = 80

def teile_satz(text, max_chars=MAX_CHUNK_CHARS):
    if len(text) <= max_chars:
        return [text.strip()]
    raw = re.split(r'(?<=[,;:!?\-–])\s+', text)
    chunks, current = [], ""
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

import numpy as np
import soundfile as sf
import espeakng_loader

espeakng_loader.make_library_available()

from kokoro_onnx import Kokoro, EspeakConfig

MODEL_PATH  = PROJECT_DIR / "models" / "kokoro" / "kokoro-v1.0.onnx"
VOICES_PATH = PROJECT_DIR / "models" / "kokoro" / "voices-v1.0.bin"

espeak_cfg = EspeakConfig(
    lib_path=espeakng_loader.get_library_path(),
    data_path=ESPEAK_DATA,
)

print(f"\n[kokoro] lade Modell ...")
t0 = time.time()
kokoro = Kokoro(str(MODEL_PATH), str(VOICES_PATH), espeak_config=espeak_cfg)
SR_OUT = 24000
print(f"[kokoro] geladen in {time.time()-t0:.1f}s")

for rolle, voice in KOKORO_STIMMEN.items():
    print(f"[stimme] {rolle:12} -> {voice}")

def trim_stille(wav, schwelle=0.005, rand_ms=40, sr=SR_OUT):
    rand = int(sr * rand_ms / 1000)
    maske = np.abs(wav) > schwelle
    idx = np.where(maske)[0]
    if len(idx) == 0:
        return wav
    return wav[max(0, idx[0]-rand):min(len(wav), idx[-1]+rand)]

SILENCE_GLEICH  = np.zeros(int(SR_OUT * 0.25), dtype=np.float32)
SILENCE_WECHSEL = np.zeros(int(SR_OUT * 0.55), dtype=np.float32)

print(f"\n[gen] {len(PASSAGE)} Segmente ...\n")
t_start = time.time()
audio_parts, prev_rolle = [], None
ok = fail = chunk_idx = 0

for i, (rolle, text) in enumerate(PASSAGE, 1):
    chunks = teile_satz(text)
    n = len(chunks)
    label = f"[{i:2}/{len(PASSAGE)}] {rolle:12}"
    if n == 1:
        print(f"{label} {text[:60]!r}")
    else:
        print(f"{label} -> {n} Chunks: {text[:50]!r}...")

    seg_wavs = []
    for j, chunk in enumerate(chunks):
        chunk_idx += 1
        seg_path = SEGMENTS_DIR / f"{chunk_idx:04d}_{rolle}.wav"
        if seg_path.exists() and not FORCE:
            wav_np, _ = sf.read(str(seg_path), dtype="float32")
        else:
            try:
                t0 = time.time()
                voice = KOKORO_STIMMEN[rolle]
                samples, sr = kokoro.create(chunk, voice=voice, speed=1.0, lang="de")
                wav_np = samples.astype(np.float32)
                sf.write(str(seg_path), wav_np, SR_OUT)
                gt = time.time() - t0
                if n > 1:
                    print(f"    [{j+1}/{n}] {gt:.1f}s -> {len(wav_np)/SR_OUT:.1f}s  {chunk[:45]!r}")
                else:
                    print(f"             {gt:.1f}s -> {len(wav_np)/SR_OUT:.1f}s")
                ok += 1
            except Exception as e:
                print(f"    FEHLER: {e}")
                wav_np = SILENCE_GLEICH.copy()
                fail += 1
        seg_wavs.append(wav_np)

    satz_wav = np.concatenate([trim_stille(w) for w in seg_wavs])

    if prev_rolle is not None:
        pause = SILENCE_GLEICH if rolle == prev_rolle else SILENCE_WECHSEL
        audio_parts.append(pause)
    audio_parts.append(satz_wav)
    prev_rolle = rolle

full_audio = np.concatenate(audio_parts)
total_sec  = len(full_audio) / SR_OUT
gen_total  = time.time() - t_start

out_path = OUTPUT_DIR / "kapitel3_kokoro.wav"
sf.write(str(out_path), full_audio, SR_OUT)

print(f"\n[ok] {ok} Segmente OK, {fail} Fehler")
print(f"[ok] Gesamt: {total_sec/60:.1f} Minuten Audio in {gen_total:.0f}s generiert")
print(f"[ok] Gespeichert: {out_path}")
