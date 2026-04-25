# Hörbuch-Konverter – Projektdokumentation

## Projektziel
Ein Python-Tool mit GUI, das eBooks/Textdateien in kapitelweise MP3-Hörbücher konvertiert – mit **Multi-Stimmen-System** (verschiedene Stimmen für Erzähler und Charaktere) und **Emotions-Steuerung**.

Zielbuch: **"Qwert" von Walter Moers** (43 Aventiuren, ~8165 Zeilen)

---

## Aktueller Stand (April 2026)

### Abgeschlossen

1. **Quellmaterial aufbereitet** (`quellmaterial/`)
   - `qwert_bereinigt.txt` – 8165 Zeilen, Soft Hyphens entfernt, Vor-/Nachspann entfernt
   - `kapitel_mp3/` – 43 originale Kapitel-MP3s (Referenzmaterial)
   - `kapitel_txt/` – 43 einzelne Kapitel-Textdateien (kapitel_01.txt bis kapitel_43.txt)

2. **TTS-Engine evaluiert und gewählt → XTTS v2**
   Siehe Evaluierungs-Ergebnisse weiter unten.

3. **Stimmprofil-System** (`stimmen_profile/`)
   - Sprecherprofile als `.pt`-Dateien (GPT-Conditioning-Latents + Speaker Embedding)
   - Einmalig aus WhatsApp-Audiosamples berechnet, danach wiederverwendbar ohne Drift
   - Verfügbare Profile: `kugel`, `benni`, `sina`, `bea`, `stephan`, `ma`, `marius`, `paschi`, `killi`, `knaak`, `combi`, `micha`, `anna`, `doll`, `alexandra` (+ weitere)
   - Erstellung via GUI: `einpflegen.bat` / `einpflegen.py`
   - Test via GUI: `sprechen.bat` / `sprechen.py`

4. **Demo – Kapitel 3** (Jadusa rettet Qwert aus dem Endlosen Abgrund)
   - `demos/demo_kapitel3.py` – WhatsApp-Klone (kugel=Erzähler, benni=Qwert, sina=Jadusa)
   - Output: `demo_output/kapitel3_demo.wav` – 6,1 Minuten, 0 Fehler
   - Technik: satzweise Generierung, MAX_CHUNK_CHARS=80, silence-trimming, keine Chunk-Lücken

5. **Vorschau-Generatoren** (`tools/`)
   - `generate_vorschau.py` – Batch-Vorschau aller WhatsApp-Stimmen → `stimmen_vorschau/`
   - `generate_preset_vorschau.py` – Batch-Vorschau aller 58 XTTS-Preset-Sprecher → `preset_stimmen/`
   - `check_qualitaet.py` – Whisper-Rückprüfung: welche Stimmen bleiben durchgängig Deutsch

6. **Whisper-Qualitätsprüfung Ergebnisse**
   - 60 OK / 21 TEIL / 1 FAIL von 82 getesteten Stimmen
   - WhatsApp-Stimmen die **vollständig Deutsch** blieben:
     `alexandra, anna, bea, benni, doll, killi, knaak, kugel, ma, marius, paschi, stephan`
   - XTTS-Preset-Stimmen: starker Sprachdrift ins Englische nach kurzen Sätzen → **nicht brauchbar** für Hörbuch (Whisper-Demo-Check: massive Halluzinationen)

---

## Projektstruktur

```
Hörbuch/
├── hoerbuch_konverter.py      # Haupt-GUI (Edge-TTS, noch nicht XTTS)
├── tts_engine.py              # TTS-Abstraktionsschicht
├── text_parser.py             # Kapitel-Erkennung, Dialog-Parser
├── charakter_engine.py        # Charakter-Erkennung, Stimm-Zuordnung
├── zahlen_konverter.py        # Deutsche Zahlen-zu-Text
├── einpflegen.py + .bat       # GUI: Stimmprofil aus Audio erstellen
├── sprechen.py + .bat         # GUI: Stimmprofile testen
│
├── quellmaterial/
│   ├── kapitel_mp3/           # 43 originale MP3s
│   └── qwert_bereinigt.txt
├── kapitel_txt/               # 43 Kapitel-Textdateien
├── book_profiles/             # Buchspezifische Charakter-Profile (JSON)
├── stimmen_profile/           # XTTS-Sprecher-Profile (.pt)
├── Audio Samples whatzapp/    # Rohaudio für Profilerstellung
│
├── demos/
│   ├── demo_kapitel3.py       # WhatsApp-Klone Demo
│   └── demo_kapitel3_preset.py # Preset-Stimmen Demo (Vergleich)
├── demo_output/               # Fertige Demo-WAVs + Segment-Cache
│
├── tools/
│   ├── generate_vorschau.py
│   ├── generate_preset_vorschau.py
│   ├── check_qualitaet.py
│   ├── check_demos.py
│   └── stimme_einpflegen.py   # CLI-Version (Legacy)
│
├── stimmen_vorschau/          # WhatsApp-Stimm-Vorschau-WAVs
├── preset_stimmen/            # XTTS-Preset-Stimm-Vorschau-WAVs
│
├── archiv/                    # Alte Test-Skripte und -Outputs
├── models/                    # TTS-Modell-Cache (gitignored, mehrere GB)
└── .venv/                     # Virtuelle Umgebung (gitignored)
```

---

## TTS-Engine Evaluation

| Engine | Deutsch | Voice Cloning | Ergebnis |
|---|---|---|---|
| **Piper TTS** | ja | nein | Crash (Exit Code 0xC0000409), nicht nutzbar |
| **Edge-TTS** | ja (10 Stimmen) | nein | Funktioniert, kein Cloning, Cloud-abhängig |
| **Chatterbox** | teilweise | ja (3s Sample) | Starker englischer Akzent, unbrauchbar |
| **F5-TTS** | teilweise | ja | Sprache driftet, mäßige Qualität |
| **E2-TTS** | teilweise | ja | Ähnlich F5-TTS |
| **Kokoro ONNX** | via espeak-ng | nein | 27/54 Stimmen 3/3 Deutsch, kein Drift, kein Cloning |
| **XTTS v2** ✓ | **nativ** | **ja** | Bestes Ergebnis für Cloning, gewählt |

### Warum XTTS v2?
- Natives Deutsch (`language="de"`) ohne Fremdakzent
- Voice Cloning aus kurzen WhatsApp-Clips (~15-30s)
- Speaker-Profile-System: einmalig berechnen, beliebig oft wiederverwenden
- Läuft vollständig lokal auf RTX 4070 Ti (CUDA, ~3-5x Echtzeit)
- Drift-Problem gelöst durch satzweise Generierung mit frischem Conditioning

---

## XTTS v2 – Technische Details

### Autoregressive Drift
XTTS v2 generiert Audio token-by-token. Das Speaker-Conditioning schwächt nach ~3s ab → Stimme driftet zur Basis-Trainingstimme. **Lösung:** Jeden Satz separat generieren, Chunks trimmen und nahtlos zusammenkleben.

### Speaker-Profile-System
```python
# Einmalig erstellen
gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
    audio_path=["referenz.wav"],
    max_ref_length=30, gpt_cond_len=30, gpt_cond_chunk_len=6
)
torch.save({"gpt_cond_latent": ..., "speaker_embedding": ...}, "profil.pt")

# Jedes Mal laden und nutzen
data = torch.load("profil.pt")
out = model.inference(text=satz, language="de",
    gpt_cond_latent=data["gpt_cond_latent"],
    speaker_embedding=data["speaker_embedding"],
    temperature=0.7, repetition_penalty=10.0, top_k=50, top_p=0.85)
```

### torchaudio Monkey-Patch (Windows/CUDA 12.8)
`torchaudio.load/save` schlägt fehl wegen fehlendem torchcodec-Backend. Alle Scripts patchen beim Import:
```python
import torchaudio as _ta
def _ta_load(filepath, ...): data, sr = sf.read(...); return torch.from_numpy(data.T), sr
def _ta_save(filepath, src, sr): sf.write(str(filepath), src.squeeze().numpy(), sr)
_ta.load = _ta_load; _ta.save = _ta_save
```

### Chunk-Splitting & Silence-Trimming
- Sätze > 80 Zeichen werden an Satzzeichen aufgeteilt (`,;:!?-–`)
- Jeder Chunk einzeln generiert, XTTS-Padding von Kanten entfernt (Schwelle 0.01, 40ms Rand)
- Chunks nahtlos konkateniert (kein künstliches Silence dazwischen)
- 250ms Pause bei gleichem Sprecher, 550ms bei Sprechwechsel

---

## Systemumgebung

- **OS:** Windows 11 Home
- **GPU:** RTX 4070 Ti (12 GB VRAM)
- **Python:** `.venv/` mit Python 3.11 (System-Python 3.14 nicht kompatibel)
- **Starten:** Immer `.venv\Scripts\python.exe` oder via `.bat`-Launcher nutzen

### Portabilität
Alles liegt unter `Hörbuch/` — kein externes Setup nötig:
- `.venv/` → gitignored, nach Verschiebung neu anlegen
- `models/` → gitignored, mitnehmen (mehrere GB, spart Re-Download)
- `stimmen_profile/` → mitnehmen (einmalig berechnete Latents)

---

## Buchanalyse: "Qwert" von Walter Moers

### Dialogstruktur
- Wörtliche Rede wird mit **»...«** (Guillemets) markiert
- Zuordnung meist NACH dem Dialog: `»Text«, sagte Qwert.`
- Manchmal VOR dem Dialog: `Qwert sagte: »Text«`
- Bei schnellen Dialogen (v.a. Qwert+Oyo) fehlt manchmal die Zuordnung

### Alle sprechenden Charaktere

#### Hauptcharaktere

| Charakter | Geschlecht | ~Dialoge | Stimmcharakter |
|---|---|---|---|
| **Qwert Zuiopü** | m | ~370 | warm, anfangs unsicher → zunehmend heroisch |
| **Oyo Pagenherz** | m | ~260 | komisch, redselig, Wortspiele |
| **Jadusa (Janusmeduse)** | w | ~130 | **ZWEI STIMMEN**: schönes Gesicht = kokett, hässliches = verzerrt; ab Kap.26 "Jamusa" |
| **Hildegunst von Mythenmetz** | m | ~140 | gebildet, eloquent, selbstironisch |

#### Nebencharaktere

| Charakter | Geschlecht | ~Dialoge | Stimmcharakter |
|---|---|---|---|
| **Eiserner Ritter** | m | ~30 | blechern + Zahlenschluckauf ("Dreiundzwanzig!") |
| **Hölzerner Ritter / Pax** | m | ~55 | dröhnend → später jovial, pazifistisch |
| **Gläserner Ritter** | m | ~20 | gurgelnd, rachsüchtig |
| **Arif** | m | ~35 | feierlich, salbungsvoll |
| **Riesengletscherzwerge** | m (7×) | ~20 | polternd, grob; eine Stimme für alle |

### KRITISCHER SONDERFALL: Erzählerstimme in Qwerts Kopf

Eine Stimme in »...«, die aber **kein Dialog** ist. Spricht über Qwert in der 3. Person (Trivialroman-Stil).

**Erkennungsmerkmale:**
- Immer 3. Person: "Prinz Kaltbluth tat..."
- Stil: übertrieben schwülstig, parodiert Trivialromane
- Qwert reagiert mit "Ruhe!" / "Aufhören!" / "Diese Stimme schon wieder!"
- Wird in Kap. 31 als **Mythenmetz** enthüllt

**Für das Hörbuch:** Eigene distinguierte Stimme nötig — übertrieben artikuliert, leicht affektiert. Nach Kap. 31 identisch mit Mythenmetz-Stimme.

---

## Nächste Schritte

### Kokoro ONNX – Ergebnis
- **27/54 Stimmen bestehen Whisper-Check (3/3)**, 27 TEIL, 0 FAIL
- Kein Sprachdrift (espeak-ng Phonemisierung erzwingt deutsche Aussprache)
- Kein Voice Cloning → nur für Nebencharaktere mit Preset-Stimmen nutzbar
- Espeak-ng DLL kann keine Pfade mit Umlauten lesen → Daten nach `%LOCALAPPDATA%\espeak-ng-data` kopiert
- Beste Stimmen (3/3): `ef_dora`, `bm_george`, `bm_lewis`, `bf_alice`, `bf_emma`, `bf_isabella`, `ff_siwis`, `if_sara`, `im_nicola`
- Samples in `preset_stimmen_kokoro/`

### Phase 2: XTTS v2 in Haupt-Pipeline einbauen
1. `tts_engine.py` auf XTTS v2 umstellen (statt Edge-TTS)
2. `hoerbuch_konverter.py` – Stimmprofil-Auswahl in GUI integrieren
3. Charakter-Engine: Stimm-Mapping aus `book_profiles/qwert_moers.json`

### Phase 3: Charakter-Engine vervollständigen
1. Alias-System: "das Mädchen" = "die Meduse" = "Jadusa" → gleiche Stimme
2. Jadusa/Jamusa Stimm-Split (zwei Stimmlagen)
3. Eiserner Ritter: Zahlenschluckauf-Feature
4. "Erzählerstimme im Kopf" erkennen (3. Person + schwülstiger Stil)
