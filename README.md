# 🎧 BookToAudioBook

Convert any `.epub` or `.txt` book into a fully-voiced MP3 audiobook — one file per chapter — with automatic character detection and configurable voices.

## Features

| Feature | Details |
|---------|---------|
| **Input formats** | `.epub`, `.txt` |
| **Output** | One `.mp3` file per chapter |
| **Character detection** | Dialogue attribution using pattern matching |
| **Gender-aware voices** | Male voices for male characters, female voices for female characters (auto-detected) |
| **Voice preview** | Listen to any voice before assigning it |
| **Manual override** | Re-assign voices and genders per character in the UI |
| **Clean output** | URLs, e-mail addresses, and non-printable characters are stripped before TTS |

## Prerequisites

| Requirement | Install |
|-------------|---------|
| Python ≥ 3.9 | [python.org](https://www.python.org/) |
| ffmpeg | `sudo apt install ffmpeg` / `brew install ffmpeg` / [ffmpeg.org](https://ffmpeg.org/) |
| Internet access | Required by Microsoft Edge TTS at runtime |

## Installation

```bash
# Clone the repo
git clone https://github.com/SacredBanana7/BookToAudioBook.git
cd BookToAudioBook

# Install Python dependencies
pip install -r requirements.txt
```

## Running the app

```bash
streamlit run app.py
```

Your browser opens at `http://localhost:8501`.

## How to use

1. **Upload** your `.epub` or `.txt` file in the sidebar.
2. **Book Overview** tab — review extracted chapters and auto-detected characters.
3. **Voice Assignment** tab — each character has an auto-assigned voice.  
   - Click **▶ Preview** to hear a sample before confirming.  
   - Use the dropdown to pick any of the 12 built-in Neural voices.  
   - Override the detected gender if needed.
4. **Generate Audiobook** tab — select chapters, click **Generate**.  
   Download links appear for each chapter once conversion is complete.

## Architecture

```
BookToAudioBook/
├── app.py                   # Streamlit UI
├── requirements.txt
└── src/
    ├── book_parser.py        # epub / txt parsing + text cleaning
    ├── character_detector.py # dialogue attribution & gender detection
    ├── voice_manager.py      # voice catalogue & assignment logic
    ├── tts_engine.py         # edge-tts wrapper with chunking
    └── audio_assembler.py    # pydub-based chapter audio assembly
```

## Running tests

```bash
pytest tests/ -v
```

## Available voices

The tool ships with 12 default Microsoft Edge Neural voices:

| Gender | Voices |
|--------|--------|
| Male | `en-US-GuyNeural`, `en-US-DavisNeural`, `en-US-TonyNeural`, `en-US-ChristopherNeural`, `en-GB-RyanNeural`, `en-AU-WilliamNeural` |
| Female | `en-US-JennyNeural`, `en-US-AriaNeural`, `en-US-SaraNeural`, `en-US-NancyNeural`, `en-GB-SoniaNeural`, `en-AU-NatashaNeural` |

## Notes

- TTS is provided free of charge by Microsoft's Edge read-aloud service via the `edge-tts` Python package.  There are no official rate-limit guarantees; very large books may require retries.
- For books with no chapter headings (common in plain `.txt` exports), the entire file is treated as a single chapter.
- Character detection works best on books with traditional dialogue attribution ("she said", "he replied", etc.).  First-person or stream-of-consciousness prose will have fewer detected characters.
