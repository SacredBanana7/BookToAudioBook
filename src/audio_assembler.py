"""Assemble text segments into a single chapter MP3 using pydub."""

import asyncio
import os
import tempfile
from typing import Callable, List, Optional

from pydub import AudioSegment

from src.character_detector import TextSegment
from src.tts_engine import text_to_audio
from src.voice_manager import VoiceManager

# Short silence injected between character dialogue turns (ms)
_DIALOGUE_PAUSE_MS = 350
# Short silence between narrator paragraphs (ms)
_NARRATOR_PAUSE_MS = 150


async def generate_chapter_audio(
    segments: List[TextSegment],
    voice_manager: VoiceManager,
    output_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> str:
    """Convert a list of :class:`TextSegment` objects into a single MP3 file.

    Parameters
    ----------
    segments:
        Ordered list of text segments (narrator + characters).
    voice_manager:
        Provides voice assignments for each speaker.
    output_path:
        Destination path for the resulting MP3.
    progress_callback:
        Optional callable invoked as ``callback(current, total)`` after each
        segment is processed.

    Returns
    -------
    str
        The *output_path* that was written.
    """
    non_empty = [s for s in segments if s.text.strip()]
    total = len(non_empty)
    combined = AudioSegment.empty()
    tmp_files: List[str] = []

    try:
        for idx, segment in enumerate(non_empty):
            voice = voice_manager.get_voice(segment.speaker)

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            tmp_files.append(tmp_path)

            await text_to_audio(segment.text, voice, tmp_path)
            audio = AudioSegment.from_mp3(tmp_path)
            combined += audio

            # Add a pause to separate segments naturally
            pause_ms = (
                _DIALOGUE_PAUSE_MS
                if segment.speaker != "narrator"
                else _NARRATOR_PAUSE_MS
            )
            combined += AudioSegment.silent(duration=pause_ms)

            if progress_callback:
                progress_callback(idx + 1, total)

        combined.export(output_path, format="mp3")
        return output_path

    finally:
        for fpath in tmp_files:
            if os.path.exists(fpath):
                os.unlink(fpath)
