# -*- coding: utf-8 -*-
"""
VoiceBox TTS Engine
====================
REST-API-Client für den lokal laufenden VoiceBox-Server (http://127.0.0.1:17493).
Integriert die VoiceBox-Profile Fred und Flover in das Hörbuch-Projekt.

Voraussetzung: VoiceBox läuft als Backend-Server.
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path

VOICEBOX_URL = "http://127.0.0.1:17493"

# VoiceBox-Profile: Name → {id, engine, model_size}
PROFILE_CONFIGS: dict[str, dict] = {
    "Flover": {"id": "8ce95eca-8c5a-41c7-bba3-8d69829a66c0", "engine": "tada",  "model_size": "3B"},
    "Fred":   {"id": "fb2d9e29-62f7-48e1-b3c0-1c1c9fce3fde", "engine": "qwen",  "model_size": "1.7B"},
}


# ---------------------------------------------------------------------------
# Interne Hilfsfunktionen
# ---------------------------------------------------------------------------

def _request(method: str, path: str, body: dict | None = None,
             timeout: int = 300, binary: bool = False):
    url = f"{VOICEBOX_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        return raw if binary else json.loads(raw)


def _resolve_config(profil_name: str, engine: str | None,
                    modell_groesse: str | None) -> tuple[str, str, str]:
    """Gibt (profil_id, engine, modell_groesse) für ein Profil zurück."""
    cfg = PROFILE_CONFIGS.get(profil_name)
    if not cfg:
        raise ValueError(f"Unbekanntes Profil: {profil_name}. Verfügbar: {list(PROFILE_CONFIGS)}")
    return cfg["id"], engine or cfg["engine"], modell_groesse or cfg["model_size"]


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------

def ist_verfuegbar() -> bool:
    """Prüft ob der VoiceBox-Server läuft."""
    try:
        health = _request("GET", "/health", timeout=5)
        return health.get("status") == "healthy"
    except Exception:
        return False


def modell_laden(modell_groesse: str = "1.7B") -> bool:
    """Lädt ein Qwen-TTS-Modell in den VoiceBox-Speicher."""
    try:
        result = _request("POST", f"/models/load?model_size={modell_groesse}")
        print(f"[voicebox] Modell-Laden: {result}")
        return True
    except Exception as e:
        print(f"[voicebox] Modell-Laden fehlgeschlagen: {e}")
        return False


def profil_info(profil_name: str) -> dict | None:
    """Gibt Infos zu einem VoiceBox-Profil zurück."""
    cfg = PROFILE_CONFIGS.get(profil_name)
    if not cfg:
        return None
    try:
        return _request("GET", f"/profiles/{cfg['id']}")
    except Exception:
        return None


def modell_status() -> dict:
    """Gibt den Status aller VoiceBox-Modelle zurück."""
    try:
        result = _request("GET", "/models/status")
        return {m["model_name"]: m for m in result["models"]}
    except Exception:
        return {}


def verfuegbare_profile() -> list[str]:
    """Gibt Liste der konfigurierten Profil-Namen zurück."""
    return list(PROFILE_CONFIGS)


def generiere_audio(
    profil_name: str,
    text: str,
    output_path: str | Path,
    sprache: str = "de",
    engine: str | None = None,
    modell_groesse: str | None = None,
    warte_timeout: int = 300,
) -> bool:
    """
    Generiert Audio für einen Text mit einem VoiceBox-Profil.

    Returns True bei Erfolg, False bei Fehler.
    """
    profil_id, engine, modell_groesse = _resolve_config(profil_name, engine, modell_groesse)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "profile_id": profil_id,
        "text": text,
        "language": sprache,
        "engine": engine,
        "model_size": modell_groesse,
    }

    try:
        result = _request("POST", "/generate", payload)
    except Exception as e:
        print(f"[voicebox] Fehler beim Starten: {e}")
        return False

    gen_id = result["id"]
    print(f"[voicebox] Generation gestartet: {gen_id} (engine={engine}, modell={modell_groesse})")

    deadline = time.time() + warte_timeout
    while time.time() < deadline:
        try:
            status = _request("GET", f"/history/{gen_id}")
        except Exception:
            time.sleep(2)
            continue

        state = status.get("status", "")
        if state == "completed":
            try:
                audio = _request("GET", f"/audio/{gen_id}", binary=True)
                output_path.write_bytes(audio)
                dauer = status.get("duration", 0)
                print(f"[voicebox] Fertig: {output_path.name} ({dauer:.1f}s Audio)")
                return True
            except Exception:
                print("[voicebox] Audio-Download fehlgeschlagen")
                return False
        if state == "failed":
            print(f"[voicebox] Fehler: {status.get('error')}")
            return False

        time.sleep(3)

    print(f"[voicebox] Timeout nach {warte_timeout}s")
    return False


def generiere_stream(
    profil_name: str,
    text: str,
    output_path: str | Path,
    sprache: str = "de",
    engine: str | None = None,
    modell_groesse: str | None = None,
) -> bool:
    """
    Generiert Audio via Streaming (kein Speichern auf VoiceBox-Server).
    Für kurze Texte schneller als generiere_audio().
    """
    profil_id, engine, modell_groesse = _resolve_config(profil_name, engine, modell_groesse)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "profile_id": profil_id,
        "text": text,
        "language": sprache,
        "engine": engine,
        "model_size": modell_groesse,
    }

    try:
        audio = _request("POST", "/generate/stream", payload, binary=True)
        output_path.write_bytes(audio)
        print(f"[voicebox] Stream abgeschlossen: {output_path.name}")
        return True
    except Exception as e:
        print(f"[voicebox] Stream-Fehler: {e}")
        return False


# ---------------------------------------------------------------------------
# Profil-Verwaltung
# ---------------------------------------------------------------------------

def profil_registrieren(name: str, profil_id: str, engine: str = "qwen",
                         modell_groesse: str = "1.7B") -> None:
    """Registriert ein neues VoiceBox-Profil."""
    PROFILE_CONFIGS[name] = {"id": profil_id, "engine": engine, "model_size": modell_groesse}


# ---------------------------------------------------------------------------
# CLI-Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== VoiceBox Engine Test ===")

    if not ist_verfuegbar():
        print("FEHLER: VoiceBox-Server nicht erreichbar (http://127.0.0.1:17493)")
        exit(1)

    print(f"VoiceBox: OK")
    print(f"Profile: {verfuegbare_profile()}")

    status = modell_status()
    for name, info in status.items():
        dl = "✓" if info["downloaded"] else "✗"
        ld = "geladen" if info["loaded"] else "nicht geladen"
        print(f"  {dl} {name}: {ld}")

    test_texte = {
        "Fred":   "Hallo! Ich bin Fred und teste die Qwen TTS Engine.",
        "Flover": "Hallo! Ich bin Flover und teste die Tada drei B Engine.",
    }

    output_dir = Path("test_output/voicebox")
    output_dir.mkdir(parents=True, exist_ok=True)

    for profil, text in test_texte.items():
        print(f"\n[test] {profil}: '{text[:40]}...'")
        ok = generiere_audio(profil, text, output_dir / f"test_{profil.lower()}.wav")
        print(f"[test] {'OK' if ok else 'FEHLGESCHLAGEN'}")
