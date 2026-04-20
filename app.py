"""BookToAudioBook — Streamlit UI for converting epub/txt books to MP3 audiobooks."""

import asyncio
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import nest_asyncio
import streamlit as st

from src.audio_assembler import generate_chapter_audio
from src.book_parser import Chapter, parse_epub, parse_txt
from src.character_detector import (
    detect_characters,
    guess_character_gender,
    segment_text,
)
from src.tts_engine import generate_preview
from src.voice_manager import ALL_VOICES, DEFAULT_NARRATOR_VOICE, VoiceManager

# Allow asyncio.run() inside Streamlit's existing event loop
nest_asyncio.apply()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_async(coro):
    """Execute *coro* synchronously and return its result."""
    return asyncio.run(coro)


def _safe_filename(text: str) -> str:
    return re.sub(r"[^\w\s\-]", "", text).strip().replace(" ", "_")


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="BookToAudioBook",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "chapters" not in st.session_state:
    st.session_state.chapters: Optional[List[Chapter]] = None
if "characters" not in st.session_state:
    st.session_state.characters: Dict[str, str] = {}  # name → gender
if "voice_manager" not in st.session_state:
    st.session_state.voice_manager = VoiceManager()
if "generated_files" not in st.session_state:
    st.session_state.generated_files: List[tuple] = []  # [(title, path, bytes)]

# ---------------------------------------------------------------------------
# Sidebar — file upload
# ---------------------------------------------------------------------------

with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/headphones.png",
        width=64,
    )
    st.title("BookToAudioBook")
    st.caption("Turn any epub or txt book into an MP3 audiobook.")
    st.divider()

    uploaded_file = st.file_uploader(
        "📂 Upload your book",
        type=["epub", "txt"],
        help="Supported formats: .epub, .txt",
    )

    if uploaded_file is not None:
        suffix = Path(uploaded_file.name).suffix.lower()
        parse_key = uploaded_file.name + str(uploaded_file.size)

        if st.session_state.get("_last_upload_key") != parse_key:
            with st.spinner("Parsing book…"):
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

                try:
                    if suffix == ".epub":
                        chapters = parse_epub(tmp_path)
                    else:
                        chapters = parse_txt(tmp_path)
                finally:
                    os.unlink(tmp_path)

            if not chapters:
                st.error("Could not extract any chapters. Please try a different file.")
            else:
                st.session_state.chapters = chapters
                st.session_state.generated_files = []

                # Detect characters across all chapters
                all_text = "\n\n".join(ch.content for ch in chapters)
                raw_counts = detect_characters(all_text)

                # Keep characters mentioned at least twice
                char_genders: Dict[str, str] = {}
                for name, count in raw_counts.items():
                    if count >= 2:
                        char_genders[name] = guess_character_gender(name, all_text)

                st.session_state.characters = char_genders

                vm = VoiceManager()
                vm.auto_assign_voices(char_genders)
                st.session_state.voice_manager = vm

                st.session_state["_last_upload_key"] = parse_key

        n_ch = len(st.session_state.chapters or [])
        n_chars = len(st.session_state.characters)
        st.success(f"✅  {n_ch} chapters · {n_chars} characters detected")

    st.divider()
    st.markdown(
        "**System requirements**\n"
        "- Python ≥ 3.9\n"
        "- `ffmpeg` installed and on PATH\n"
        "- Internet access for edge-tts"
    )

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.title("🎧 BookToAudioBook")

if st.session_state.chapters is None:
    # Welcome screen
    st.markdown(
        """
        ### Convert your book to an audiobook in four steps

        1. **Upload** an `.epub` or `.txt` file in the sidebar
        2. **Review** chapters and detected characters
        3. **Assign voices** (or use the auto-assigned ones) and preview them
        4. **Generate** — one MP3 per chapter, ready to download
        """
    )
    st.info("👈 Start by uploading a book in the sidebar.")
    st.stop()

chapters: List[Chapter] = st.session_state.chapters
characters: Dict[str, str] = st.session_state.characters
vm: VoiceManager = st.session_state.voice_manager

tab_overview, tab_voices, tab_generate = st.tabs(
    ["📖 Book Overview", "🎤 Voice Assignment", "🎵 Generate Audiobook"]
)

# ============================================================
# Tab 1 — Book Overview
# ============================================================
with tab_overview:
    col_a, col_b = st.columns(2)
    col_a.metric("Chapters", len(chapters))
    col_b.metric("Characters detected", len(characters))

    st.subheader("Chapters")
    for i, ch in enumerate(chapters):
        with st.expander(f"{i + 1}. {ch.title}"):
            preview = ch.content[:600]
            if len(ch.content) > 600:
                preview += "…"
            st.text(preview)

    if characters:
        st.subheader("Detected Characters")
        cols = st.columns(3)
        for j, (name, gender) in enumerate(characters.items()):
            icon = "👨" if gender == "male" else "👩" if gender == "female" else "🧑"
            cols[j % 3].write(f"{icon} **{name}** — {gender}")
    else:
        st.info(
            "No recurring characters detected. "
            "The entire book will be read by the narrator."
        )

# ============================================================
# Tab 2 — Voice Assignment
# ============================================================
with tab_voices:
    st.markdown(
        "Assign a voice to each character. "
        "Click **▶ Preview** to hear a sample before committing."
    )
    st.divider()

    # --- Narrator ---
    st.subheader("🎙️ Narrator")
    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        narrator_voice = st.selectbox(
            "Narrator voice",
            ALL_VOICES,
            index=ALL_VOICES.index(vm.get_voice("narrator"))
            if vm.get_voice("narrator") in ALL_VOICES
            else 0,
            key="sel_narrator",
        )
        vm.assign_voice("narrator", narrator_voice)
    with c3:
        st.write("")  # vertical alignment spacer
        if st.button("▶ Preview", key="prev_narrator"):
            with st.spinner("Generating preview…"):
                audio_bytes = run_async(
                    generate_preview(narrator_voice, "The story begins on a cold winter morning.")
                )
            st.audio(audio_bytes, format="audio/mp3")

    # --- Characters ---
    if characters:
        st.subheader("👥 Characters")
        for name, gender in list(characters.items()):
            st.divider()
            icon = "👨" if gender == "male" else "👩" if gender == "female" else "🧑"
            st.write(f"**{icon} {name}**")

            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            with c1:
                current_voice = vm.get_voice(name)
                selected_voice = st.selectbox(
                    "Voice",
                    ALL_VOICES,
                    index=ALL_VOICES.index(current_voice)
                    if current_voice in ALL_VOICES
                    else 0,
                    key=f"sel_{name}",
                )
                vm.assign_voice(name, selected_voice)

            with c2:
                new_gender = st.selectbox(
                    "Gender",
                    ["male", "female", "unknown"],
                    index=["male", "female", "unknown"].index(gender),
                    key=f"gen_{name}",
                    help="Changing gender does not re-assign the voice automatically.",
                )
                if new_gender != gender:
                    st.session_state.characters[name] = new_gender

            with c4:
                st.write("")  # vertical alignment spacer
                if st.button("▶ Preview", key=f"prev_{name}"):
                    with st.spinner("Generating preview…"):
                        first = name.split()[0]
                        audio_bytes = run_async(
                            generate_preview(
                                selected_voice,
                                f"Hello, my name is {first}. How are you today?",
                            )
                        )
                    st.audio(audio_bytes, format="audio/mp3")
    else:
        st.info("No characters to configure — only the narrator voice is needed.")

# ============================================================
# Tab 3 — Generate Audiobook
# ============================================================
with tab_generate:
    st.markdown(
        "Select which chapters to convert, then click **Generate**. "
        "Each chapter is saved as a separate MP3 file."
    )

    chapter_options = list(range(len(chapters)))
    selected_indices = st.multiselect(
        "Chapters to generate",
        options=chapter_options,
        default=chapter_options,
        format_func=lambda i: f"{i + 1}. {chapters[i].title}",
    )

    if st.button("🎵 Generate Audiobook", type="primary", disabled=not selected_indices):
        generated: List[tuple] = []
        progress_bar = st.progress(0)
        status_placeholder = st.empty()
        output_dir = tempfile.mkdtemp(prefix="bookaudio_")

        for chapter_num, idx in enumerate(selected_indices):
            chapter = chapters[idx]
            safe_title = _safe_filename(chapter.title) or f"chapter_{idx + 1}"
            output_path = os.path.join(output_dir, f"{idx + 1:02d}_{safe_title}.mp3")

            status_placeholder.info(
                f"Generating {chapter_num + 1}/{len(selected_indices)}: **{chapter.title}**…"
            )

            segs = segment_text(chapter.content, vm.assignments)

            seg_bar = st.progress(0, text=f"Segments for '{chapter.title}'")

            def _seg_cb(current: int, total: int, _bar=seg_bar) -> None:
                _bar.progress(current / total, text=f"Segment {current}/{total}")

            try:
                run_async(
                    generate_chapter_audio(segs, vm, output_path, _seg_cb)
                )
                with open(output_path, "rb") as fh:
                    audio_bytes = fh.read()
                generated.append((chapter.title, output_path, audio_bytes))
                seg_bar.progress(1.0, text="✅ Done")
                st.success(f"✅ **{chapter.title}** — {len(audio_bytes) // 1024} KB")
            except Exception as exc:
                seg_bar.empty()
                st.error(f"❌ Error generating **{chapter.title}**: {exc}")

            progress_bar.progress((chapter_num + 1) / len(selected_indices))

        status_placeholder.empty()
        st.session_state.generated_files = generated

        if generated:
            st.balloons()

    # Show download buttons for already-generated files
    if st.session_state.generated_files:
        st.divider()
        st.subheader("⬇️ Download generated chapters")
        for title, path, audio_bytes in st.session_state.generated_files:
            col_title, col_btn = st.columns([3, 1])
            col_title.write(f"📁 **{title}**")
            col_btn.download_button(
                label="Download MP3",
                data=audio_bytes,
                file_name=Path(path).name,
                mime="audio/mpeg",
                key=f"dl_{path}",
            )
