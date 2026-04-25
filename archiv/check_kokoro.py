# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from faster_whisper import WhisperModel

INPUT_DIR = Path(__file__).parent.parent / "preset_stimmen_kokoro"

KEYWORDS_S1 = ["lindwurm", "hildegunst", "mythenmetz"]
KEYWORDS_S2 = ["lindwurmfeste", "turm"]
KEYWORDS_S3 = ["bücher", "buecher", "abenteuern", "träumte", "traeumte"]

print("[whisper] lade Modell ...")
model = WhisperModel("medium", device="cuda", compute_type="float16")

wavs = sorted(INPUT_DIR.glob("kokoro_*.wav"))
print(f"[check] {len(wavs)} Dateien\n")

ok = teil = fail = 0
results = []

for wav in wavs:
    voice = wav.stem.replace("kokoro_", "")
    segs, info = model.transcribe(str(wav), language="de", beam_size=3)
    text = " ".join(s.text for s in segs).lower()

    s1 = any(k in text for k in KEYWORDS_S1)
    s2 = any(k in text for k in KEYWORDS_S2)
    s3 = any(k in text for k in KEYWORDS_S3)
    hits = sum([s1, s2, s3])

    if hits == 3:
        status = "OK  "
        ok += 1
    elif hits >= 1:
        status = "TEIL"
        teil += 1
    else:
        status = "FAIL"
        fail += 1

    results.append((status, voice, hits, text[:80]))
    print(f"  [{status}] {voice:20} ({hits}/3)  {text[:60]!r}")

print(f"\n{'='*60}")
print(f"OK: {ok}  TEIL: {teil}  FAIL: {fail}")
print(f"\n--- Beste Stimmen (OK) ---")
for status, voice, hits, text in results:
    if status == "OK  ":
        print(f"  {voice}")
