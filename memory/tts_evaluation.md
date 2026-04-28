---
name: TTS-Engine Evaluation
description: Welche TTS-Engines für das deutsche Hörbuch-Projekt getestet wurden und warum XTTS v2 gewählt wurde
type: project
originSessionId: c6bcdee1-d794-43b3-9b99-f2af5ddd2538
---
Folgende Engines wurden für das deutsche Hörbuch-Projekt evaluiert:

| Engine | Ergebnis |
|---|---|
| Piper TTS | Crash (Exit Code 0xC0000409) — nicht nutzbar |
| Edge-TTS | Funktioniert, aber kein Voice-Cloning, Cloud-abhängig |
| Chatterbox | Starker englischer Akzent auf Deutsch — unbrauchbar |
| F5-TTS | Sprachdrift, mäßige Qualität |
| E2-TTS | Ähnlich F5-TTS |
| **XTTS v2** | ✓ Gewählt — nativ Deutsch, bestes Voice-Cloning |

**Why:** XTTS v2 ist das einzige Modell das Deutsch nativ unterstützt (language="de") ohne Fremdakzent und gleichzeitig Voice-Cloning aus kurzen WhatsApp-Clips ermöglicht.

**How to apply:** Nicht nochmal die anderen Engines vorschlagen ohne guten Grund. Neues zu evaluieren nur wenn explizit gewünscht.

## Kokoro ONNX — getestet April 2026
- Installiert als `kokoro-onnx` (ONNX-basiert, kein Build-Problem)
- Keine dedizierten de_*-Stimmen — alle 54 mit `lang="de"` + espeak-ng Phonemisierung getestet
- **27/54 bestehen Whisper-Check (3/3)**, 27 TEIL, 0 FAIL — kein kompletter Ausfall
- Kein Sprachdrift (espeak-ng erzwingt korrekte Phoneme)
- **Kein Voice Cloning** → nur für Nebencharaktere mit Preset-Stimmen sinnvoll
- Windows-Problem: espeak-ng DLL kann keine Pfade mit Umlauten (ö in "Hörbuch") lesen → Daten nach `%LOCALAPPDATA%\espeak-ng-data` kopiert
- Beste Stimmen: ef_dora, bm_george, bm_lewis, bf_alice, bf_emma, bf_isabella, ff_siwis, if_sara, im_nicola

## XTTS v2 Preset-Stimmen — auch gescheitert
Die 58 eingebauten Preset-Stimmen (z.B. "Damien Black", "Andrew Chipper", "Gitta Nikolina") driften ebenfalls stark ins Englische. Whisper-Check auf kapitel3_preset.wav zeigte massive Halluzinationen. → Für Hörbuch unbrauchbar, eigene WhatsApp-Klone sind deutlich besser.

## Qwen3-TTS 1.7B CustomVoice — getestet April 2026
- Modell: `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` (~3.5GB, benötigt HF-Token + Apache 2.0 Lizenz)
- Separates Venv `.qwen_venv/` nötig (transformers==4.57.3 inkompatibel mit XTTS v2 / HF Hub 1.x)
- **9 feste Speaker:** aiden, dylan, eric, ono_anna, ryan, serena, sohee, uncle_fu, vivian
- Deutsch nativ unterstützt (`language="German"`) — kein Akzent-Problem erwartet
- **Kein Voice Cloning** im CustomVoice-Modell (dafür wäre das separate Base-Modell nötig)
- Geschwindigkeit: ~7-28s pro Satz (RTX 4070 Ti, ohne flash-attn) — langsamer als XTTS v2
- Whisper-Qualitätsprüfung auf Deutsch noch ausstehend
- API: `Qwen3TTSModel.from_pretrained(..., device_map="cuda", dtype=torch.bfloat16)` dann `generate_custom_voice(text, speaker, language="German")`

## Gute WhatsApp-Stimmen (Whisper-verifiziert)
alexandra, anna, bea, benni, doll, killi, knaak, kugel, ma, marius, paschi, stephan
