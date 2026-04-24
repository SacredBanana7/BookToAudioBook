# Hörbuch-Konverter

**Textdateien → kapitelweise MP3-Hörbücher mit Multi-Stimmen-System**

Erkennt Erzähler und Charaktere automatisch und weist ihnen unterschiedliche TTS-Stimmen zu. Unterstützt deutsche Zahlen-Aussprache, Geschlechts-Erkennung und buchspezifische Charakter-Profile.

## Features

- Automatische Kapitel-Erkennung (verschiedene Formate: "Kapitel 1", "1. Aventiure", etc.)
- Multi-Stimmen-System: Verschiedene Stimmen für Erzähler und Dialogpartner
- 10 deutsche Neural-TTS-Stimmen (DE/AT/CH, männlich + weiblich)
- Automatische Charakter-Erkennung aus wörtlicher Rede (»...«, „...")
- Geschlechts-Erkennung via Kontext-Analyse (Pronomen, Schlüsselwörter)
- Deutsche Zahlen-zu-Text Konvertierung (optimiert für TTS-Aussprache)
- Buchspezifische Charakter-Profile (JSON) mit Alias-System
- Vorschau-Funktion pro Stimme und Kapitel
- Dark-Theme GUI (tkinter)

## Installation

```bash
# Repository klonen
git clone https://github.com/DEIN-USERNAME/hoerbuch-konverter.git
cd hoerbuch-konverter

# Abhängigkeiten installieren
pip install -r requirements.txt

# Starten
python hoerbuch_konverter.py
```

## Projektstruktur

```
hoerbuch-konverter/
├── hoerbuch_konverter.py     # Haupt-GUI
├── zahlen_konverter.py       # Deutsche Zahlen → Text
├── text_parser.py            # Kapitel-Erkennung, Dialog-Parser
├── charakter_engine.py       # Geschlechts-Erkennung, Buch-Profile
├── tts_engine.py             # TTS-Abstraktionsschicht
├── book_profiles/            # Buchspezifische Charakter-Profile
│   └── qwert_moers.json      # Profil für "Qwert" von Walter Moers
├── kapitel_txt/              # Generierte Kapitel-Textdateien
├── requirements.txt
├── PROJECT.md                # Detaillierte Projektdokumentation
└── README.md
```

## Benutzung

1. **Textdatei laden**: Über "Durchsuchen" eine .txt-Datei auswählen
2. **Kapitel werden erkannt**: Automatisch anhand von Überschriften-Mustern
3. **Charaktere werden erkannt**: Sprecher aus wörtlicher Rede identifiziert
4. **Stimmen zuordnen**: Erzähler-Stimme wählen, Charakter-Stimmen anpassen
5. **Optional: Buch-Profil laden**: JSON-Profil für genauere Charakter-Zuordnung
6. **Hörbuch erstellen**: Konvertiert alle Kapitel zu MP3

## Buch-Profile

Für bekannte Bücher können JSON-Profile erstellt werden, die enthalten:
- Charakter-Namen und Aliases (z.B. "Jadusa" = "Meduse" = "Janusmeduse")
- Geschlechts-Informationen
- Stimmcharakter-Beschreibungen
- Sonderfälle (z.B. Erzählerstimme im Kopf, Stimm-Splits)

Beispiel siehe `book_profiles/qwert_moers.json`.

## Verfügbare Stimmen

| Stimme | Sprache | Geschlecht |
|--------|---------|------------|
| Conrad | DE | männlich |
| Florian (multilingual) | DE | männlich |
| Killian | DE | männlich |
| Jonas | AT | männlich |
| Jan | CH | männlich |
| Seraphina (multilingual) | DE | weiblich |
| Amala | DE | weiblich |
| Katja | DE | weiblich |
| Ingrid | AT | weiblich |
| Leni | CH | weiblich |

## Systemanforderungen

- Python 3.10+
- Windows (für `os.startfile` Vorschau; leicht anpassbar für Linux/Mac)
- Internetverbindung (Edge-TTS ist Cloud-basiert)

## Geplante Features

- **Chatterbox TTS**: Lokale TTS-Engine mit Emotions-Regler und Voice Cloning
- **Erzählerstimme im Kopf**: Erkennung von inneren Monologen als separater Sprecher
- **ID3-Tags**: Titel, Kapitel, Cover in MP3s einbetten
- **Fortschrittsanzeige** mit geschätzter Restzeit

## Lizenz

MIT
