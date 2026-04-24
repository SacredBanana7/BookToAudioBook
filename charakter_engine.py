# -*- coding: utf-8 -*-
"""
Charakter-Engine für Hörbuch-Konvertierung
===========================================
- Geschlechts-Erkennung (Kontext-Analyse + Schlüsselwort-Matching)
- Buchspezifische Charakter-Profile (aus JSON)
- Alias-System (verschiedene Bezeichnungen → gleicher Charakter)
- Automatische Stimm-Zuordnung (m→männlich, w→weiblich)
"""

import json
import os
import re

# =============================================================================
# Geschlechts-Erkennung
# =============================================================================

# Begriffe die IMMER weiblich sind (auch wenn grammatisch sächlich wie "Mädchen")
IMMER_WEIBLICH = {
    'mädchen', 'fräulein', 'weib', 'maid', 'dirne',
    'prinzessin', 'königin', 'kaiserin', 'gräfin', 'herzogin',
    'dame', 'frau', 'jungfrau', 'hexe', 'fee',
    'schwester', 'mutter', 'tochter', 'nichte', 'tante',
    'meduse', 'janusmeduse', 'göttin', 'nonne', 'magd',
    'zofe', 'dienerin', 'kriegerin', 'ritterin', 'botin',
    'schönheit', 'geliebte', 'braut', 'witwe',
}

# Begriffe die IMMER männlich sind
IMMER_MAENNLICH = {
    'prinz', 'könig', 'kaiser', 'graf', 'herzog',
    'herr', 'ritter', 'knappe', 'junge', 'mann',
    'bruder', 'vater', 'sohn', 'neffe', 'onkel',
    'gott', 'mönch', 'knecht', 'recke', 'held',
    'bube', 'bursche', 'kerl', 'krieger', 'bote',
    'diener', 'zwerg', 'riese', 'drache', 'gallertprinz',
}


def geschlecht_erkennen(name, text):
    """Erkennt das Geschlecht eines Charakters anhand des Kontexts.

    Strategie:
    1. Sofort-Erkennung: Name enthält eindeutigen Marker (z.B. "Mädchen" → w)
    2. Kontext-Analyse: Pronomen und Schlüsselwörter in der Umgebung des Namens
    3. Scoring: Mehr weibliche als männliche Marker → weiblich und umgekehrt

    Args:
        name: Der Charakter-Name
        text: Der Gesamttext für Kontext-Analyse

    Returns:
        'm', 'w' oder None (unbekannt)
    """
    name_lower = name.lower()

    # 1. Sofort-Erkennung: Name selbst enthält eindeutigen Marker
    for marker in IMMER_WEIBLICH:
        if marker in name_lower:
            return 'w'
    for marker in IMMER_MAENNLICH:
        if marker in name_lower:
            return 'm'

    male_score = 0
    female_score = 0

    # 2. Kontext um jede Erwähnung des Namens analysieren
    for match in re.finditer(r'\b' + re.escape(name) + r'\b', text):
        kontext_nach = text[match.end():match.end() + 80]
        kontext_vor = text[max(0, match.start() - 80):match.start()]

        # Pronomen DIREKT nach dem Namen (mit Wortgrenzen!)
        if re.search(r'^[,\s]*\b(er|sein|seiner|seinem|seinen|ihm|ihn)\b', kontext_nach):
            male_score += 5
        if re.search(r'^[,\s]*\b(sie|ihr|ihre|ihrer|ihrem|ihren)\b', kontext_nach):
            female_score += 5

        # Pronomen direkt VOR dem Namen
        if re.search(r'\b(er|sein|seiner)\s*[,]?\s*$', kontext_vor):
            male_score += 3
        if re.search(r'\b(sie|ihre|ihrer)\s*[,]?\s*$', kontext_vor):
            female_score += 3

        # Begriffe in der Nähe (mit Wortgrenzen)
        kontext_weit = text[max(0, match.start() - 150):match.end() + 150].lower()
        for marker in IMMER_MAENNLICH:
            if re.search(r'\b' + re.escape(marker) + r'\b', kontext_weit):
                male_score += 2
        for marker in IMMER_WEIBLICH:
            if re.search(r'\b' + re.escape(marker) + r'\b', kontext_weit):
                female_score += 2

    # 3. Auswertung
    if female_score > male_score:
        return 'w'
    elif male_score > female_score:
        return 'm'
    return None


# =============================================================================
# Buchspezifische Profile
# =============================================================================

class BuchProfil:
    """Lädt und verwaltet buchspezifische Charakter-Profile aus JSON.

    Ein Profil enthält:
    - Charakter-Definitionen mit Aliases (verschiedene Bezeichnungen)
    - Geschlechts-Informationen
    - Stimmcharakter-Beschreibungen
    - Sonderfälle (z.B. Erzählerstimme im Kopf, Stimm-Splits)
    """

    def __init__(self, profil_pfad=None):
        self.charaktere = {}  # {canonical_name: {...}}
        self.alias_map = {}   # {alias: canonical_name}
        self.sonderfaelle = {}

        if profil_pfad and os.path.exists(profil_pfad):
            self.laden(profil_pfad)

    def laden(self, pfad):
        """Lädt ein Charakter-Profil aus einer JSON-Datei."""
        with open(pfad, 'r', encoding='utf-8') as f:
            daten = json.load(f)

        self.charaktere = daten.get('charaktere', {})
        self.sonderfaelle = daten.get('sonderfaelle', {})

        # Alias-Map aufbauen
        self.alias_map = {}
        for name, info in self.charaktere.items():
            self.alias_map[name.lower()] = name
            for alias in info.get('aliases', []):
                self.alias_map[alias.lower()] = name

    def name_aufloesen(self, erkannter_name):
        """Löst einen erkannten Namen zu seinem kanonischen Namen auf.

        Args:
            erkannter_name: Der vom Parser erkannte Name

        Returns:
            Kanonischer Name oder der Original-Name falls kein Alias gefunden
        """
        if not erkannter_name:
            return erkannter_name
        return self.alias_map.get(erkannter_name.lower(), erkannter_name)

    def geschlecht(self, name):
        """Gibt das Geschlecht eines Charakters aus dem Profil zurück."""
        kanonisch = self.name_aufloesen(name)
        if kanonisch in self.charaktere:
            return self.charaktere[kanonisch].get('geschlecht')
        return None

    def stimmcharakter(self, name):
        """Gibt den Stimmcharakter eines Charakters zurück."""
        kanonisch = self.name_aufloesen(name)
        if kanonisch in self.charaktere:
            return self.charaktere[kanonisch].get('stimmcharakter', '')
        return ''

    def alle_charaktere(self):
        """Gibt alle definierten Charaktere zurück."""
        return list(self.charaktere.keys())
