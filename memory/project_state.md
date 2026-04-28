---
name: Projektstand Hörbuch-Konverter
description: Aktueller Stand des XTTS v2 Hörbuch-Projekts inkl. abgeschlossener Arbeiten und nächster Schritte
type: project
originSessionId: c6bcdee1-d794-43b3-9b99-f2af5ddd2538
---
TTS-Engine-Wahl gefallen: **XTTS v2 (coqui-tts)** ist im Einsatz. Demo Kapitel 3 (6,1 Min.) fertig und Whisper-geprüft.

**Why:** Einzige Engine mit nativem Deutsch ohne Fremdakzent + funktionierendem Voice-Cloning aus WhatsApp-Clips.

**How to apply:** Bei Fragen zu nächsten Schritten: XTTS v2 in tts_engine.py / hoerbuch_konverter.py integrieren (Phase 2).

## Abgeschlossen (April 2026)
- Quellmaterial: qwert_bereinigt.txt, 43 kapitel_txt/, 43 kapitel_mp3/
- Speaker-Profile-System: stimmen_profile/*.pt (kugel, benni, sina, bea, stephan, ma, marius, paschi, killi, knaak, combi, micha, anna, doll, alexandra + weitere)
- GUI-Tools: einpflegen.py/.bat (Profile erstellen), sprechen.py/.bat (Profile testen)
- Demo Kap. 3 WhatsApp-Klone: kapitel3_demo.wav (kugel=Erzähler, benni=Qwert, sina=Jadusa)
- Demo Kap. 3 Preset-Stimmen: kapitel3_preset.wav (Damien Black/Andrew Chipper/Gitta Nikolina) — schlechter, Sprachdrift
- Whisper-Qualitätsprüfung: 12 WhatsApp-Stimmen vollständig Deutsch; Presets unbrauchbar
- Ordner-Reorganisation: demos/, tools/, quellmaterial/, archiv/ angelegt
- PROJECT.md vollständig neu geschrieben (April 2026)

## Kokoro ONNX (April 2026)
- Demo kapitel3_kokoro.wav fertig (bm_george/am_puck/ef_dora)
- 27/54 Stimmen bestehen Whisper-Check; alle haben englischen Akzent → Hauptrollen ungeeignet
- models/kokoro/ (kokoro-v1.0.onnx + voices-v1.0.bin)

## Qwen3-TTS 1.7B CustomVoice (April 2026)
- Erfolgreich installiert in .qwen_venv/ (separates Env)
- Modell geladen + 5 Tests × 3 Speaker ohne Fehler generiert (test_output/)
- Deutsch nativ, 9 Speaker, kein Voice Cloning, Whisper-Check ausstehend
- HF-Token in .env gespeichert (gitignored)
- .gitignore: .qwen_venv/ hinzugefügt

## Offen
- Qwen3-TTS Deutsch-Qualität via Whisper prüfen
- Qwen3-TTS Base-Modell für Voice Cloning testen (Ergänzung zu XTTS v2)
- XTTS v2 in Haupt-Pipeline (tts_engine.py, hoerbuch_konverter.py) einbauen
- Charakter-Engine: Alias-System, Jadusa-Stimmsplit, Erzählerstimme-im-Kopf-Erkennung
