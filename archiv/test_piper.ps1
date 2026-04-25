$baseDir = $PSScriptRoot
$piperExe = "C:\Users\PC\Downloads\piper_windows_amd64\piper\piper.exe"
$piperModel = "$baseDir\piper_model\de_DE-thorsten-high.onnx"

Write-Host "=== Piper Debug Test ===" -ForegroundColor Cyan
Write-Host "Piper: $piperExe"
Write-Host "Model: $piperModel"
Write-Host "Model exists: $(Test-Path $piperModel)"
Write-Host ""

# Test with a simple sentence first
Write-Host "--- Test 1: Einfacher Satz ---" -ForegroundColor Yellow
$testWav = "$baseDir\test_output.wav"
"Dies ist ein Test." | & $piperExe --model $piperModel --output_file $testWav
Write-Host "Exit code: $LASTEXITCODE"
Write-Host "WAV exists: $(Test-Path $testWav)"
if (Test-Path $testWav) {
    Write-Host "WAV size: $((Get-Item $testWav).Length) bytes"
}

Write-Host ""
Write-Host "--- Test 2: Erstes Kapitel (erste 3 Zeilen) ---" -ForegroundColor Yellow
$testWav2 = "$baseDir\test_kapitel.wav"
$text = Get-Content "$baseDir\kapitel_txt\kapitel_01.txt" -TotalCount 3 -Encoding UTF8
Write-Host "Text: $text"
$text | & $piperExe --model $piperModel --output_file $testWav2
Write-Host "Exit code: $LASTEXITCODE"
Write-Host "WAV exists: $(Test-Path $testWav2)"
