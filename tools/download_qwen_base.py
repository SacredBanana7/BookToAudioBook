# -*- coding: utf-8 -*-
"""
Lädt Qwen3-TTS-12Hz-1.7B-Base in den System-HF-Cache (für VoiceBox).
Ausführen mit:  .qwen_venv/Scripts/python.exe tools/download_qwen_base.py
"""
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# Token aus .env
from pathlib import Path
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("HF_TOKEN="):
            os.environ["HF_TOKEN"] = line.split("=", 1)[1].strip()
            print("[info] HF_TOKEN geladen")

MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"

print(f"[download] Lade {MODEL_ID}")
_hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
print(f"[download] Ziel: {os.path.join(_hf_home, 'hub')}")
print("[download] Modell ist ~3-5 GB, bitte warten...")

from huggingface_hub import snapshot_download
import time

t0 = time.time()
local_path = snapshot_download(
    MODEL_ID,
    ignore_patterns=["*.msgpack", "*.h5", "flax_*"],
)
print(f"[download] Fertig in {time.time()-t0:.0f}s")
print(f"[download] Pfad: {local_path}")
print()
print("[info] VoiceBox kann das Modell jetzt laden.")
print("[info] Starte VoiceBox neu und prüfe Modell-Status unter /models.")
