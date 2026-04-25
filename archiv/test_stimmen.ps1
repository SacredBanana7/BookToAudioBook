$baseDir = $PSScriptRoot
$textFile = "$baseDir\test_text.txt"

edge-tts --voice de-DE-ConradNeural --file $textFile --write-media "$baseDir\test_conrad.mp3"
edge-tts --voice de-DE-FlorianMultilingualNeural --file $textFile --write-media "$baseDir\test_florian.mp3"
edge-tts --voice de-DE-KillianNeural --file $textFile --write-media "$baseDir\test_killian.mp3"
edge-tts --voice de-DE-SeraphinaMultilingualNeural --file $textFile --write-media "$baseDir\test_seraphina.mp3"

Write-Host "Fertig! 4 Testdateien erstellt." -ForegroundColor Green
