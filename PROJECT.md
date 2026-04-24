# Hörbuch-Konverter – Projektdokumentation

## Projektziel
Ein Python-Tool mit GUI, das eBooks/Textdateien in kapitelweise MP3-Hörbücher konvertiert – mit **Multi-Stimmen-System** (verschiedene Stimmen für Erzähler und Charaktere) und **Emotions-Steuerung**.

## Aktueller Stand

### Was bereits existiert und funktioniert:
1. **`qwert_bereinigt.txt`** – Bereinigte Textdatei (8165 Zeilen, 43 Aventiuren)
   - Soft Hyphens (402 Stück) entfernt
   - Vorspann (Klappentext, Copyright, ISBN) entfernt
   - Nachspann (Fußnoten, Newsletter) entfernt

2. **`kapitel_txt/`** – 43 einzelne Kapitel-Textdateien (kapitel_01.txt bis kapitel_43.txt)

3. **`hoerbuch_konverter.py`** – GUI-Anwendung (tkinter) mit:
   - Dateiauswahl + automatische Kapitel-Erkennung
   - 10 Edge-TTS Stimmen (DE/AT/CH, männlich+weiblich)
   - Zahlen-zu-Text Konvertierung (deutsch, mit TTS-optimierter Aussprache)
   - Automatische Charakter-Erkennung aus wörtlicher Rede
   - Geschlechts-Erkennung (Kontext-Analyse + Schlüsselwort-Matching)
   - Automatische Stimm-Zuordnung (m→männliche Stimme, w→weibliche)
   - Multi-Stimmen-Konvertierung (segment-weise TTS + MP3-Konkatenation)
   - Vorschau-Funktion pro Stimme und Charakter

### Was noch gemacht werden muss:
1. **TTS-Engine wechseln**: Edge-TTS → **Chatterbox** (via Voicebox oder direkt)
   - Emotions-Regler (monoton ↔ dramatisch)
   - Voice Cloning (3 Sek. Audio-Sample pro Stimme)
   - Paralinguistische Tags: `[laugh]`, `[sigh]`, etc.
   - Läuft lokal, kein Cloud-Service
2. **Buchspezifisches Charakter-Profil** einbauen (siehe Analyse unten)
3. **GitHub-Repo** aufsetzen mit sauberer Projektstruktur
4. **Erzählerstimme im Kopf** als separaten Sprecher erkennen

---

## Buchanalyse: "Qwert" von Walter Moers

### Dialogstruktur
- Wörtliche Rede wird mit **»...«** (Guillemets) markiert
- Zuordnung meist NACH dem Dialog: `»Text«, sagte Qwert.`
- Manchmal VOR dem Dialog: `Qwert sagte: »Text«`
- Bei schnellen Dialogen (v.a. Qwert+Oyo) fehlt manchmal die Zuordnung

### Sprechverben im Text
```
sagte, sprach, rief, fragte, flüsterte, schrie, murmelte, antwortete,
erwiderte, meinte, brummte, seufzte, stöhnte, knurrte, zischte,
jammerte, jubelte, wimmerte, brüllte, krächzte, hauchte,
entgegnete, bemerkte, erklärte, fügte hinzu, wiederholte,
dachte, überlegte, dröhnte, grunzte, piepste, kreischte,
verkündete, protestierte, schluchzte, lachte, kicherte,
flötete, bellte, donnerte, säuselte, stammelte, stotterte,
lallte, schnarrte
```

### Alle sprechenden Charaktere

#### Hauptcharaktere (hohes Dialogvolumen)

| Charakter | Geschlecht | ~Dialoge | Textvarianten | Stimmcharakter |
|---|---|---|---|---|
| **Qwert Zuiopü** | m | ~370 | "Qwert", "Prinz Kaltbluth", "der Ritter", "mein edler Herr" | warm, anfangs unsicher/lallig → zunehmend heroisch |
| **Oyo Pagenherz** | m | ~260 | "Oyo", "der Knappe", "der Gnom", "Queekwigg", "Ritter von Queekwigg-Pagenherz" | komisch, redselig, Wortspiele, drollig |
| **Jadusa (Janusmeduse)** | w | ~130 | "Jadusa", "die Meduse", "die Janusmeduse", "das Mädchen", "die Schönheit", "die befreite Schönheit", "die Kreatur", "Jamusa" (ab Kap.26) | **ZWEI STIMMEN**: schönes Gesicht = kokett/charmant, hässliches Gesicht = "grässlich verzerrt". Ab Kap.26 wird sie zu "Jamusa" (Muse) |
| **Hildegunst von Mythenmetz** | m | ~140 | "Mythenmetz", "der Lindwurm", "der Einsame Denker", "Hildegunst" | gebildet, eloquent, selbstironisch, langatmig |

#### Nebencharaktere (mittleres Dialogvolumen)

| Charakter | Geschlecht | ~Dialoge | Textvarianten | Stimmcharakter |
|---|---|---|---|---|
| **Eiserner Ritter** | m | ~30 | "der Eiserne Ritter" | blechern/schnarrend + **Zahlenschluckauf** (schiebt zufällige Zahlen in Rede ein: "Dreiundzwanzig!", "Sechsundvierzig!") |
| **Hölzerner Ritter / Pax** | m | ~55 | "der Hölzerne Ritter", "der Pflanzenriese", "der Goldene Ritter", "Pax", "Ukuthula Pax Uxolo" | dröhnend, größenwahnsinnig → später (als Pax) jovial, pazifistisch, verliebt |
| **Gläserner Ritter** | m | ~20 | "der Gläserne Ritter" | gurgelnd, rachsüchtig, pathetisch |
| **Arif** | m | ~35 | "Arif", der volle Name ist extrem lang | feierlich, salbungsvoll |
| **Riesengletscherzwerge** | m (7×) | ~20 | "der Riesengletscherzwerg namens Eins/Zwei/.../Sieben", "einer von ihnen" | polternd, grob, langsam; können alle eine Stimme teilen |

#### Kleinere Rollen

| Charakter | Geschlecht | ~Dialoge | Stimmcharakter |
|---|---|---|---|
| **Flederfrosch (Fleischberg-Dolmetscher)** | m | ~15 | quakend, beschwichtigend |
| **Janusmännlein** | m | ~10 | Oyo-Imitat → grotesk verzerrt |
| **Tentakel-Stimmen** | m (div.) | ~5 | anonyme Einwürfe |
| **Danzelot (Flederfrosch bei Mythenmetz)** | m | ~15 | echohafte Wiederholungen: "Hallohallo! Gib Küsschen!" |
| **Jungmusen** (Jasamu, Musaja etc.) | w | wenige | Chor, zwitschernde Einwürfe |

### KRITISCHER SONDERFALL: Die Erzählerstimme in Qwerts Kopf

Dies ist das größte Problem für die Zuordnung. Es gibt eine **Stimme**, die auch in »...« spricht, aber **KEIN Dialog** ist. Sie ist ein literarischer Erzähler, der in Trivialroman-Manier über "Prinz Kaltbluth" in der 3. Person berichtet.

**Erkennungsmerkmale:**
- Spricht von Qwert/Prinz Kaltbluth immer in der **3. Person** ("Prinz Kaltbluth tat...", "Tarnmeister wollte tanzen!")
- Stil: übertrieben schwülstig, blumig, klischeehaft → parodiert Trivialromane
- Kein Gesprächspartner antwortet direkt darauf
- Qwert reagiert darauf mit "Ruhe!" oder "Aufhören!" oder "Diese Stimme schon wieder!"
- Wird in Kap. 31 als **Mythenmetz** enthüllt (der schrieb die Prinz-Kaltbluth-Romane)

**Stellen im Text:**
- Erster Anblick im Spiegel (Kap.1)
- Anblick des Mädchens (Kap.1)
- Kampf mit Medusenwächter (Kap.1)
- Sturz in den Abgrund (Kap.3)
- Buhurt-Szene (Kap.11)
- Ruinenraupe (Kap.16)
- Diverse weitere Stellen

**Für das Hörbuch:** Braucht eine eigene, distinguierte Stimme – übertrieben artikuliert, leicht affektiert, deutlich abgegrenzt von allen anderen. Nach der Enthüllung in Kap. 31 könnte sie mit der Mythenmetz-Stimme identisch sein.

---

## Technische Details

### Systemumgebung
- **OS:** Windows
- **GPU:** RTX 4070 Ti (12 GB VRAM) → reicht für alle lokalen TTS-Modelle
- **Python:** 3.14 (installiert)
- **Piper TTS:** Installiert aber crasht (Exit Code 0xC0000409), nicht nutzbar
- **Edge-TTS:** Funktioniert, aktuell als Fallback im Einsatz
- **ffmpeg:** Nicht im PATH installiert

### Dateipfade
- **Projekt:** `C:\Users\PC\Documents\Claude\Projects\Hörbuch\`
- **Bereinigte Textdatei:** `C:\Users\PC\Documents\Claude\Projects\Hörbuch\qwert_bereinigt.txt`
- **Kapitel-Dateien:** `C:\Users\PC\Documents\Claude\Projects\Hörbuch\kapitel_txt\`
- **GUI-App:** `C:\Users\PC\Documents\Claude\Projects\Hörbuch\hoerbuch_konverter.py`
- **Originaldatei:** `C:\Users\PC\Calibre-Bibliothek\Moers, Walter\Qwert (2)\Qwert - Moers, Walter.txt`

### Bekannte Probleme
1. **PowerShell Encoding:** `.ps1`-Dateien mit Umlauten (ö, ü, ä) müssen entweder `$PSScriptRoot` statt hardcodierte Pfade nutzen, oder als UTF-8 mit BOM gespeichert werden
2. **Zahlen-Aussprache:** Große zusammengesetzte Zahlwörter müssen mit Leerzeichen zwischen Blöcken getrennt werden, damit TTS sie nicht verschluckt (z.B. "zweitausend dreihundertvierundsechzigsten")
3. **Ordinalzahlen:** Immer deklinierte Form verwenden ("ersten", "zweiten", "dritten" statt "erste", "zweite", "dritte"), da im Fließtext fast immer Dativ/Genitiv/Akkusativ

### Verfügbare Edge-TTS Stimmen (aktueller Fallback)
```
de-DE-ConradNeural        Male
de-DE-FlorianMultilingualNeural  Male
de-DE-KillianNeural       Male
de-AT-JonasNeural         Male
de-CH-JanNeural           Male
de-DE-SeraphinaMultilingualNeural Female
de-DE-AmalaNeural         Female
de-DE-KatjaNeural         Female
de-AT-IngridNeural        Female
de-CH-LeniNeural          Female
```

---

## Geplante TTS-Engine: Chatterbox (via Voicebox)

### Warum Chatterbox?
- **Emotions-Regler:** Skaliert von monoton bis dramatisch expressiv (perfekt für Hörbuch-Szenen)
- **Voice Cloning:** 3 Sekunden Audio reichen für eine neue Stimme
- **Paralinguistische Tags:** `[laugh]`, `[sigh]` → perfekt für expressiven Dialog
- **23 Sprachen** inkl. Deutsch
- **Lokal & kostenlos** (MIT-Lizenz)
- **12 GB VRAM** der RTX 4070 Ti ist mehr als genug

### Installation
```bash
pip install chatterbox-tts
# oder Voicebox Desktop-App: https://voicebox.sh/
```

### Alternative: Qwen3-TTS 1.7B
- Emotion über natürliche Anweisungen ("sprich traurig, langsam")
- 8 GB VRAM Minimum, 12 GB ideal
- Ebenfalls Deutsch + Voice Cloning

---

## Nächste Schritte (Reihenfolge)

### Phase 1: Chatterbox/TTS-Setup
1. Chatterbox installieren und testen (oder Voicebox Desktop-App)
2. Deutsche Sprachqualität evaluieren
3. Voice Cloning testen: verschiedene Stimm-Samples für Charaktere erstellen
4. Emotions-Regler testen: monoton vs. expressiv

### Phase 2: Charakter-Engine umbauen
1. Buchspezifisches Charakter-Profil aus der Analyse oben einbauen
2. "Erzählerstimme im Kopf" als eigenen Sprecher-Typ erkennen (3. Person + schwülstiger Stil)
3. Alias-System: "das Mädchen" = "die Meduse" = "Jadusa" = gleiche Stimme
4. Jadusa/Jamusa Stimm-Split: zwei Stimmlagen für schönes/hässliches Gesicht
5. Eiserner Ritter: Zahlenschluckauf als Charakter-Feature

### Phase 3: GitHub-Repo
1. Projektstruktur:
   ```
   hoerbuch-konverter/
   ├── README.md
   ├── requirements.txt
   ├── hoerbuch_konverter.py      # Haupt-GUI
   ├── tts_engine.py              # TTS-Abstraktionsschicht (Edge/Chatterbox/Qwen)
   ├── text_parser.py             # Kapitel-Erkennung, Dialog-Parser
   ├── charakter_engine.py        # Charakter-Erkennung, Geschlecht, Stimm-Zuordnung
   ├── zahlen_konverter.py        # Deutsche Zahlen-zu-Text
   ├── book_profiles/             # Buchspezifische Charakter-Profile
   │   └── qwert_moers.json
   └── samples/                   # Stimm-Samples für Voice Cloning
   ```
2. README mit Installationsanleitung
3. Requirements: `edge-tts`, `chatterbox-tts`, `tkinter`

### Phase 4: Feinschliff
1. Fortschrittsanzeige mit geschätzter Restzeit
2. Kapitel-Preview mit Multi-Stimmen
3. Export als einzelne MP3s oder als zusammenhängendes Hörbuch
4. ID3-Tags (Titel, Kapitel, Cover) in MP3s einbetten
