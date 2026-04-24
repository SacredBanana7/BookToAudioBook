# -*- coding: utf-8 -*-
"""
Deutsche Zahlen-zu-Text Konvertierung
======================================
Konvertiert Kardinal- und Ordinalzahlen in ausgeschriebenen
deutschen Text, optimiert für TTS-Aussprache.

- Große Zahlen werden mit Leerzeichen zwischen Blöcken getrennt
- Ordinalzahlen immer in deklinierter Form ("ersten", "zweiten")
"""

import re

# =============================================================================
# Grundzahlen
# =============================================================================

EINER = ["", "ein", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun"]
ZEHNER = ["", "zehn", "zwanzig", "dreißig", "vierzig", "fünfzig", "sechzig", "siebzig", "achtzig", "neunzig"]
SONDER = {
    10: "zehn", 11: "elf", 12: "zwölf", 13: "dreizehn", 14: "vierzehn",
    15: "fünfzehn", 16: "sechzehn", 17: "siebzehn", 18: "achtzehn", 19: "neunzehn"
}


def _unter_hundert(n):
    """Hilfsfunktion: Zahl 1-99 als ein Wort."""
    if n == 0:
        return ""
    if n in SONDER:
        return SONDER[n]
    if n < 10:
        return EINER[n]
    einer = n % 10
    zehner = n // 10
    if einer > 0:
        return EINER[einer] + "und" + ZEHNER[zehner]
    return ZEHNER[zehner]


def zahl_zu_text(n):
    """Konvertiert eine Ganzzahl (0-999999) in deutschen Text.
    Ab 100 werden Blöcke mit Leerzeichen getrennt für bessere TTS-Aussprache."""
    if n == 0:
        return "null"
    if n < 0:
        return "minus " + zahl_zu_text(-n)
    if n < 100:
        return _unter_hundert(n)

    parts = []

    if n >= 1000000:
        millionen = n // 1000000
        if millionen == 1:
            parts.append("eine Million")
        else:
            parts.append(zahl_zu_text(millionen) + " Millionen")
        n %= 1000000

    if n >= 1000:
        tausender = n // 1000
        if tausender == 1:
            parts.append("eintausend")
        else:
            parts.append(_unter_hundert(tausender) + "tausend")
        n %= 1000

    if n >= 100:
        rest = n % 100
        hundert_teil = EINER[n // 100] + "hundert"
        if rest > 0:
            hundert_teil += _unter_hundert(rest)
        parts.append(hundert_teil)
        n = 0
    elif n > 0:
        parts.append(_unter_hundert(n))

    return " ".join(parts).strip()


def ordinal_zu_text(n):
    """Konvertiert eine Zahl in deutsche Ordinalform (dekliniert)."""
    ordinals_klein = {
        1: "ersten", 2: "zweiten", 3: "dritten", 4: "vierten",
        5: "fünften", 6: "sechsten", 7: "siebten", 8: "achten",
        9: "neunten", 10: "zehnten", 11: "elften", 12: "zwölften",
        13: "dreizehnten", 14: "vierzehnten", 15: "fünfzehnten",
        16: "sechzehnten", 17: "siebzehnten", 18: "achtzehnten",
        19: "neunzehnten"
    }
    if n in ordinals_klein:
        return ordinals_klein[n]
    if n < 100:
        return _unter_hundert(n) + "sten"

    # Ab 100: Blöcke mit Leerzeichen, Endung ans letzte Wort
    parts = []

    if n >= 1000000:
        millionen = n // 1000000
        if millionen == 1:
            parts.append("eine Million")
        else:
            parts.append(zahl_zu_text(millionen) + " Millionen")
        n %= 1000000

    if n >= 1000:
        tausender = n // 1000
        if tausender == 1:
            parts.append("eintausend")
        else:
            parts.append(_unter_hundert(tausender) + "tausend")
        n %= 1000

    if n >= 100:
        rest_unter = n % 100
        hundert_teil = EINER[n // 100] + "hundert"
        if rest_unter > 0:
            if rest_unter in ordinals_klein:
                hundert_teil += ordinals_klein[rest_unter]
            else:
                hundert_teil += _unter_hundert(rest_unter) + "sten"
        else:
            hundert_teil += "sten"
        parts.append(hundert_teil)
    elif n > 0:
        if n in ordinals_klein:
            parts.append(ordinals_klein[n])
        else:
            parts.append(_unter_hundert(n) + "sten")
    else:
        if parts:
            parts[-1] = parts[-1] + "sten"

    return " ".join(parts)


def zahlen_ersetzen(text):
    """Ersetzt Zahlen im Text durch ausgeschriebene deutsche Wörter.
    - '42.' → 'zweiundvierzigsten' (Ordinalzahl)
    - '42' → 'zweiundvierzig' (Kardinalzahl)
    - Kapitelüberschriften (z.B. '1. Aventiure') werden nicht ersetzt.
    """
    def ordinal_match(m):
        n = int(m.group(1))
        if n > 999999:
            return m.group(0)
        return ordinal_zu_text(n) + " "

    text = re.sub(r'(?<!\n)(\d+)\.\s(?!Aventiure)', ordinal_match, text)

    def kardinal_match(m):
        n = int(m.group(0))
        if n > 999999:
            return m.group(0)
        return zahl_zu_text(n)

    text = re.sub(r'(?<=\s)\d+(?=\s|[,;:!?\)])', kardinal_match, text)
    return text
