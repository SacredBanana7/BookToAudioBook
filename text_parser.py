# -*- coding: utf-8 -*-
import re

def text_bereinigen(text):
    text = text.replace(chr(173), '')
    text = re.sub(r'\n{4,}', '\n\n', text)
    return text

DEFAULT_PATTERNS = [
    r'^\d+\.\s+Aventiure',
    r'^Kapitel\s+\d+',
    r'^KAPITEL\s+\d+',
    r'^\d+\.\s+Kapitel',
    r'^Kapitel\s+[IVXLCDM]+',
    r'^Teil\s+\d+',
    r'^Prolog|^Epilog',
]

def kapitel_erkennen(text, pattern=None):
    if pattern is None:
        for p_pat in DEFAULT_PATTERNS:
            matches = re.findall(p_pat, text, re.MULTILINE)
            if len(matches) >= 2:
                pattern = p_pat
                break
    if pattern is None:
        return [('Kapitel 1', text)]
    parts = re.split(f'(?m)(?=^{pattern})', text)
    parts = [p for p in parts if p.strip()]
    chapters = []
    for part in parts:
        titel = part.strip().split('\n')[0].strip()
        chapters.append((titel, part.strip()))
    return chapters

SPRECHVERBEN = (
    'sagte|sprach|rief|fragte|'
    + 'fl' + chr(252) + 'sterte|schrie|murmelte|antwortete|'
    + 'erwiderte|meinte|brummte|seufzte|'
    + 'st' + chr(246) + 'hnte|knurrte|zischte|'
    + 'jammerte|jubelte|wimmerte|'
    + 'br' + chr(252) + 'llte|kr' + chr(228) + 'chzte|hauchte|'
    + 'entgegnete|bemerkte|'
    + 'erkl' + chr(228) + 'rte|f' + chr(252) + r"gte\s+hinzu|wiederholte|"
    + 'dachte|' + chr(252) + 'berlegte|'
    + 'dr' + chr(246) + 'hnte|grunzte|piepste|kreischte|'
    + 'verk' + chr(252) + 'ndete|protestierte|schluchzte|lachte|kicherte|'
    + 'fl' + chr(246) + 'tete|bellte|donnerte|'
    + 's' + chr(228) + 'uselte|stammelte|stotterte'
)

_SKIP_SPRECHER = {
    'er', 'sie', 'es', 'und', 'aber', 'das', 'die', 'der',
    'dann', 'doch', 'ich', 'wir', 'ihr', 'ja', 'nein',
    'nun', 'also', 'hier', 'dort', 'jetzt', 'noch',
    'auch', 'schon', 'sehr', 'ganz', 'nur', 'ach',
    'da', 'so', 'denn', 'wenn', 'weil', 'wie', 'was',
    'den', 'dem', 'des', 'ein', 'eine', 'einer',
    'man', 'alle', 'alles', 'etwas', 'nichts',
}

_DQ_OPEN = chr(187) + chr(8222) + chr(8220)
_DQ_CLOSE = chr(171) + chr(8220) + chr(8221)
_DIALOG_RE = re.compile('[' + _DQ_OPEN + '](.+?)[' + _DQ_CLOSE + ']', re.DOTALL)

def parse_dialog_segmente(text):
    segmente = []
    pos = 0
    for match in _DIALOG_RE.finditer(text):
        if match.start() > pos:
            erzaehl_text = text[pos:match.start()].strip()
            if erzaehl_text:
                segmente.append(('erzaehler', erzaehl_text, None))
        dialog_text = match.group(1).strip()
        charakter = sprecher_finden(text, match.start(), match.end())
        segmente.append(('dialog', dialog_text, charakter))
        pos = match.end()
    if pos < len(text):
        rest = text[pos:].strip()
        if rest:
            segmente.append(('erzaehler', rest, None))
    return segmente

def sprecher_finden(text, dialog_start, dialog_end):
    nach_text = text[dialog_end:dialog_end + 100]
    pat_nach = re.compile(
        r'^[,.]?\s*(?:' + SPRECHVERBEN + r')\s+(?:der\s+|die\s+|das\s+)?(\w+)',
        re.IGNORECASE
    )
    m = pat_nach.search(nach_text)
    if m:
        gefunden = m.group(1)
        if gefunden.lower() not in _SKIP_SPRECHER and len(gefunden) > 1:
            return gefunden
    vor_text = text[max(0, dialog_start - 100):dialog_start]
    pat_vor = re.compile(
        r'(\w+)\s+(?:' + SPRECHVERBEN + r')\s*[:.]?\s*$',
        re.IGNORECASE
    )
    m = pat_vor.search(vor_text)
    if m:
        gefunden = m.group(1)
        if gefunden.lower() not in _SKIP_SPRECHER and len(gefunden) > 1:
            return gefunden
    return None

def charaktere_sammeln(text):
    charakter_counter = {}
    for match in _DIALOG_RE.finditer(text):
        charakter = sprecher_finden(text, match.start(), match.end())
        if charakter and len(charakter) > 1:
            if charakter.lower() not in _SKIP_SPRECHER:
                charakter_counter[charakter] = charakter_counter.get(charakter, 0) + 1
    sortiert = sorted(charakter_counter.items(), key=lambda x: -x[1])
    return sortiert
