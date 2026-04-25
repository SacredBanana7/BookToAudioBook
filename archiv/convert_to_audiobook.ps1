# ============================================================
# Qwert Hoerbuch-Konverter
# Konvertiert bereinigte Kapitel-Textdateien direkt zu MP3
# Nutzt edge-tts (Microsoft Neural TTS)
# ============================================================

$ErrorActionPreference = "Stop"
$baseDir = $PSScriptRoot
$txtDir  = "$baseDir\kapitel_txt"
$mp3Dir  = "$baseDir"

# Deutsche Stimme - ConradNeural ist maennlich, natuerlich
$voice = "de-DE-ConradNeural"

# Pruefe ob edge-tts installiert ist
$edgeTts = Get-Command edge-tts -ErrorAction SilentlyContinue
if (-not $edgeTts) {
    Write-Host "edge-tts nicht gefunden. Installiere mit: pip install edge-tts" -ForegroundColor Red
    exit 1
}

# Zaehle Kapitel
$chapters = Get-ChildItem -Path $txtDir -Filter "kapitel_*.txt" | Sort-Object Name
$total = $chapters.Count
Write-Host "=== Qwert Hoerbuch-Konverter ===" -ForegroundColor Cyan
Write-Host "Stimme: $voice"
Write-Host "$total Kapitel gefunden."
Write-Host ""

$i = 0
$errors = @()
foreach ($chapter in $chapters) {
    $i++
    $num = $chapter.BaseName -replace 'kapitel_', ''
    $mp3File = "$mp3Dir\kapitel_$num.mp3"

    Write-Host "  [$i/$total] $($chapter.Name) -> kapitel_$num.mp3 ..." -NoNewline

    # edge-tts liest direkt aus Datei und erzeugt MP3
    $textFile = $chapter.FullName
    $text = Get-Content -Path $textFile -Raw -Encoding UTF8

    # Schreibe Text in temp-Datei (UTF-8 ohne BOM fuer edge-tts)
    $tempFile = "$baseDir\temp_chapter.txt"
    [System.IO.File]::WriteAllText($tempFile, $text, [System.Text.UTF8Encoding]::new($false))

    & edge-tts --voice $voice --file $tempFile --write-media $mp3File 2>$null

    if ((Test-Path $mp3File) -and (Get-Item $mp3File).Length -gt 1000) {
        $sizeMB = [math]::Round((Get-Item $mp3File).Length / 1MB, 1)
        Write-Host " OK (${sizeMB} MB)" -ForegroundColor Green
    } else {
        Write-Host " FEHLER!" -ForegroundColor Red
        $errors += $chapter.Name
    }
}

# Temp-Datei aufraeumen
Remove-Item -Path "$baseDir\temp_chapter.txt" -ErrorAction SilentlyContinue

# --- Zusammenfassung ---
Write-Host ""
Write-Host "=== Fertig! ===" -ForegroundColor Cyan
$mp3Files = Get-ChildItem -Path $mp3Dir -Filter "kapitel_*.mp3"
if ($mp3Files.Count -gt 0) {
    $totalSizeMB = [math]::Round(($mp3Files | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
    Write-Host "$($mp3Files.Count) MP3-Dateien erstellt (gesamt: ${totalSizeMB} MB)"
    Write-Host "Speicherort: $mp3Dir"
}
if ($errors.Count -gt 0) {
    Write-Host ""
    Write-Host "Fehler bei: $($errors -join ', ')" -ForegroundColor Red
}
