# -*- coding: utf-8 -*-
"""
TTS-Engine Abstraktionsschicht
===============================
Kapselt verschiedene TTS-Backends (Edge-TTS, Chatterbox, etc.)
hinter einer einheitlichen Schnittstelle.

Aktuell unterstützt:
- Edge-TTS (Microsoft Neural TTS, Cloud-basiert)

Geplant:
- Chatterbox (lokal, Emotionen, Voice Cloning)
- Qwen3-TTS (lokal, natürliche Emotionssteuerung)
"""

import asyncio
import os
import subprocess
import sys

try:
    import edge_tts
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])
    import edge_tts


# =============================================================================
# Edge-TTS Stimmen (alle deutschen Stimmen inkl. AT/CH)
# =============================================================================

STIMMEN = {
    "Conrad (DE, m, klar)": "de-DE-ConradNeural",
    "Florian (DE, m, multilingual)": "de-DE-FlorianMultilingualNeural",
    "Killian (DE, m, tief)": "de-DE-KillianNeural",
    "Jonas (AT, m, österreichisch)": "de-AT-JonasNeural",
    "Jan (CH, m, schweizerisch)": "de-CH-JanNeural",
    "Seraphina (DE, w, multilingual)": "de-DE-SeraphinaMultilingualNeural",
    "Amala (DE, w, warm)": "de-DE-AmalaNeural",
    "Katja (DE, w, neutral)": "de-DE-KatjaNeural",
    "Ingrid (AT, w, österreichisch)": "de-AT-IngridNeural",
    "Leni (CH, w, schweizerisch)": "de-CH-LeniNeural",
}

# Geschlecht pro Stimme
STIMMEN_GESCHLECHT = {
    "de-DE-ConradNeural": "m",
    "de-DE-FlorianMultilingualNeural": "m",
    "de-DE-KillianNeural": "m",
    "de-AT-JonasNeural": "m",
    "de-CH-JanNeural": "m",
    "de-DE-SeraphinaMultilingualNeural": "w",
    "de-DE-AmalaNeural": "w",
    "de-DE-KatjaNeural": "w",
    "de-AT-IngridNeural": "w",
    "de-CH-LeniNeural": "w",
}

STIMMEN_MAENNLICH = [v for v, g in STIMMEN_GESCHLECHT.items() if g == "m"]
STIMMEN_WEIBLICH = [v for v, g in STIMMEN_GESCHLECHT.items() if g == "w"]
STIMMEN_IDS = list(STIMMEN.values())
STIMMEN_NAMEN = list(STIMMEN.keys())

DEFAULT_VOICE = "de-DE-ConradNeural"


# =============================================================================
# TTS-Funktionen
# =============================================================================

async def text_zu_mp3(text, voice, output_path):
    """Konvertiert Text zu MP3 mit edge-tts.

    Args:
        text: Der zu sprechende Text
        voice: Voice-ID (z.B. "de-DE-ConradNeural")
        output_path: Pfad für die MP3-Datei
    """
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def text_zu_mp3_sync(text, voice, output_path):
    """Synchroner Wrapper für text_zu_mp3 (für Thread-Nutzung)."""
    asyncio.run(text_zu_mp3(text, voice, output_path))


def mp3_zusammenfuegen(segment_dateien, output_path):
    """Fügt mehrere MP3-Dateien zu einer zusammen (binäre Konkatenation).

    Hinweis: Binäre Konkatenation funktioniert bei MP3, da das Format
    rahmenbasiert ist. Für lückenlose Übergänge wäre ffmpeg besser.

    Args:
        segment_dateien: Liste von Pfaden zu MP3-Dateien
        output_path: Pfad für die zusammengefügte MP3
    """
    with open(output_path, 'wb') as out:
        for datei in segment_dateien:
            if os.path.exists(datei):
                with open(datei, 'rb') as f:
                    out.write(f.read())


# =============================================================================
# Zukünftig: Chatterbox-Integration
# =============================================================================

# TODO: Chatterbox TTS Backend
# - Emotions-Regler (exaggeration parameter)
# - Voice Cloning (3 Sek. Audio-Sample)
# - Paralinguistische Tags: [laugh], [sigh], etc.
# - Lokal auf GPU (RTX 4070 Ti, 12 GB VRAM)
#
# from chatterbox.tts import ChatterboxTTS
# model = ChatterboxTTS.from_pretrained(device="cuda")
# wav = model.generate(text, audio_prompt=ref_audio, exaggeration=0.5)
