"""TTS generation using edge-tts (Microsoft Edge Neural voices)."""

import asyncio
import re
import tempfile
import os
from typing import List

import edge_tts

_MAX_CHUNK_CHARS = 3000  # edge-tts handles up to ~5 000 chars; keep a safe margin


def chunk_text(text: str, max_chars: int = _MAX_CHUNK_CHARS) -> List[str]:
    """Split *text* into sentence-boundary-aligned chunks of at most *max_chars*."""
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for sentence in sentences:
        if current and current_len + len(sentence) + 1 > max_chars:
            chunks.append(" ".join(current))
            current = [sentence]
            current_len = len(sentence)
        else:
            current.append(sentence)
            current_len += len(sentence) + 1

    if current:
        chunks.append(" ".join(current))

    return chunks


async def text_to_audio(text: str, voice: str, output_path: str) -> str:
    """Convert *text* to an MP3 file at *output_path* using *voice*.

    If *text* is longer than the safe chunk size it is split and each chunk
    is appended to form the final file.
    """
    chunks = chunk_text(text.strip())

    if len(chunks) == 1:
        communicate = edge_tts.Communicate(chunks[0], voice)
        await communicate.save(output_path)
        return output_path

    # Multiple chunks — generate individually and concatenate with pydub
    from pydub import AudioSegment  # local import to avoid circular deps

    combined = AudioSegment.empty()
    for chunk in chunks:
        if not chunk.strip():
            continue
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            communicate = edge_tts.Communicate(chunk, voice)
            await communicate.save(tmp_path)
            combined += AudioSegment.from_mp3(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    combined.export(output_path, format="mp3")
    return output_path


async def generate_preview(
    voice: str,
    sample_text: str = "Hello, this is a preview of my voice for the audiobook.",
) -> bytes:
    """Return raw MP3 bytes for a short voice preview clip."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        await text_to_audio(sample_text, voice, tmp_path)
        with open(tmp_path, "rb") as fh:
            return fh.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
