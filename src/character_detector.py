"""Detect characters in book text and attribute dialogue to them."""

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

import gender_guesser.detector as _gd

# ---------------------------------------------------------------------------
# Attribution verbs
# ---------------------------------------------------------------------------
_ATTR_VERBS = (
    "said",
    "asked",
    "replied",
    "whispered",
    "shouted",
    "cried",
    "called",
    "answered",
    "continued",
    "began",
    "added",
    "muttered",
    "exclaimed",
    "declared",
    "stated",
    "noted",
    "observed",
    "remarked",
    "suggested",
    "snapped",
    "growled",
    "laughed",
    "sighed",
    "murmured",
    "screamed",
    "yelled",
    "spoke",
    "responded",
    "breathed",
    "hissed",
    "announced",
    "demanded",
    "insisted",
    "pleaded",
    "argued",
    "admitted",
    "confessed",
    "agreed",
    "interrupted",
    "thought",
)

_VERB_PAT = "(?:" + "|".join(_ATTR_VERBS) + ")"

# Non-character words that match capitalised-word patterns
_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "he",
        "she",
        "it",
        "they",
        "i",
        "we",
        "you",
        "this",
        "that",
        "there",
        "here",
        "now",
        "then",
        "yes",
        "no",
        "not",
        "but",
        "and",
        "or",
        "so",
        "well",
        "chapter",
        "part",
    }
)

# Compiled patterns for dialogue attribution
# Pattern 1: "dialogue," said Name  /  "dialogue?" said Name
_PAT_POST = re.compile(
    r'["\u201C]([^"\u201D]{3,})["\u201D][,!?.]?\s+'
    + _VERB_PAT
    + r"\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    re.IGNORECASE,
)

# Pattern 2: Name said, "dialogue"
_PAT_PRE = re.compile(
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+"
    + _VERB_PAT
    + r"[,.]?\s+[\"'\u201C]",
    re.IGNORECASE,
)

# Pattern 3: "dialogue," Name said  /  "dialogue?" Name asked
_PAT_QUOTE_NAME_VERB = re.compile(
    r'["\u201C][^"\u201D]{3,}["\u201D][,!?.]?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+'
    + _VERB_PAT,
    re.IGNORECASE,
)

_GENDER_DETECTOR = _gd.Detector(case_sensitive=False)


# ---------------------------------------------------------------------------
# Public data structures
# ---------------------------------------------------------------------------


@dataclass
class TextSegment:
    """A unit of text with an identified speaker."""

    text: str
    speaker: str = "narrator"

    def __repr__(self) -> str:
        return f"TextSegment(speaker={self.speaker!r}, text={self.text[:60]!r})"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def detect_characters(text: str) -> Dict[str, int]:
    """Return a mapping of *character name → mention count* found in *text*."""
    counts: Dict[str, int] = defaultdict(int)

    for match in _PAT_POST.finditer(text):
        name = match.group(2).strip()
        if _is_valid_name(name):
            counts[name] += 1

    for match in _PAT_PRE.finditer(text):
        name = match.group(1).strip()
        if _is_valid_name(name):
            counts[name] += 1

    for match in _PAT_QUOTE_NAME_VERB.finditer(text):
        name = match.group(1).strip()
        if _is_valid_name(name):
            counts[name] += 1

    return dict(counts)


def guess_gender_from_name(name: str) -> str:
    """Return ``'male'``, ``'female'``, or ``'unknown'`` based on the first name."""
    first = name.split()[0]
    result = _GENDER_DETECTOR.get_gender(first)
    if result in ("male", "mostly_male"):
        return "male"
    if result in ("female", "mostly_female"):
        return "female"
    return "unknown"


def detect_gender_from_context(name: str, text: str) -> str:
    """Infer gender by counting gendered pronouns near the character's name.

    Counts pronouns in a window of ±2 sentences around every sentence that
    mentions the character, so that "John left. He smiled." is handled correctly.
    """
    first = re.escape(name.split()[0])
    male_count = 0
    female_count = 0

    sentences = re.split(r"(?<=[.!?])\s+", text)
    for i, sentence in enumerate(sentences):
        if not re.search(rf"\b{first}\b", sentence, re.IGNORECASE):
            continue
        # Examine ±2 sentences around the sentence containing the name
        window_start = max(0, i - 2)
        window_end = min(len(sentences), i + 3)
        window = " ".join(sentences[window_start:window_end])
        male_count += len(re.findall(r"\b(?:he|him|his)\b", window, re.IGNORECASE))
        female_count += len(re.findall(r"\b(?:she|her|hers)\b", window, re.IGNORECASE))

    if male_count > female_count * 1.5:
        return "male"
    if female_count > male_count * 1.5:
        return "female"
    return "unknown"


def guess_character_gender(name: str, text: str) -> str:
    """Combine name-based and pronoun-based gender guessing."""
    gender = guess_gender_from_name(name)
    if gender == "unknown":
        gender = detect_gender_from_context(name, text)
    return gender


def segment_text(text: str, voice_assignments: Dict[str, str]) -> List[TextSegment]:
    """Split *text* into :class:`TextSegment` objects with speaker attribution.

    *voice_assignments* is a mapping of character name → voice name; its keys
    are used to determine known characters (narrator key is skipped).
    """
    known_characters = {k for k in voice_assignments if k.lower() != "narrator"}
    segments: List[TextSegment] = []

    for para in re.split(r"\n\n+", text):
        para = para.strip()
        if not para:
            continue

        # If the paragraph contains dialogue, try to split it
        if '"' in para or "\u201C" in para:
            segments.extend(_split_dialogue_paragraph(para, known_characters))
        else:
            segments.append(TextSegment(para, "narrator"))

    return segments


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _is_valid_name(name: str) -> bool:
    """Return True when *name* looks like a real character name."""
    if not name:
        return False
    parts = name.lower().split()
    if any(p in _STOPWORDS for p in parts):
        return False
    # Reject overly long "names" (likely false positives)
    if len(name) > 40:
        return False
    return True


def _find_speaker_in_text(text: str, known_characters: frozenset) -> Optional[str]:
    """Return the first known character mentioned alongside an attribution verb."""
    for name in known_characters:
        pattern = re.compile(
            rf"(?:\b{re.escape(name)}\b.*?{_VERB_PAT}|{_VERB_PAT}.*?\b{re.escape(name)}\b)",
            re.IGNORECASE,
        )
        if pattern.search(text):
            return name
    return None


def _split_dialogue_paragraph(
    para: str, known_characters: frozenset
) -> List[TextSegment]:
    """Break a paragraph into narrator and character :class:`TextSegment` objects."""
    segments: List[TextSegment] = []

    # Regex to find quoted dialogue blocks and surrounding context
    dialogue_re = re.compile(
        r'([^"\u201C]*?)(["\u201C][^"\u201D"]{1,}["\u201D])(.*?)(?=["\u201C]|$)',
        re.DOTALL,
    )

    pos = 0
    for match in dialogue_re.finditer(para):
        pre = match.group(1).strip()
        dialogue = match.group(2)
        post = match.group(3).strip()

        if pre:
            segments.append(TextSegment(pre, "narrator"))

        # Determine speaker from surrounding text
        context = pre + " " + post
        speaker = _find_speaker_in_text(context, known_characters) or "narrator"

        clean_dialogue = dialogue.strip('"\u201C\u201D')
        if clean_dialogue:
            segments.append(TextSegment(clean_dialogue, speaker))

        pos = match.end()

    # Any leftover text after the last match
    remaining = para[pos:].strip()
    if remaining:
        segments.append(TextSegment(remaining, "narrator"))

    if not segments:
        segments.append(TextSegment(para, "narrator"))

    return segments
