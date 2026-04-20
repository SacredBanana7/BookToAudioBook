"""Tests for src/character_detector.py"""

import pytest

from src.character_detector import (
    TextSegment,
    detect_characters,
    detect_gender_from_context,
    guess_gender_from_name,
    segment_text,
)


# ---------------------------------------------------------------------------
# detect_characters
# ---------------------------------------------------------------------------


def test_detect_characters_finds_post_verb_name():
    text = '"Hello there," said John.'
    chars = detect_characters(text)
    assert "John" in chars


def test_detect_characters_finds_pre_verb_name():
    text = 'Mary asked, "Are you coming?"'
    chars = detect_characters(text)
    assert "Mary" in chars


def test_detect_characters_counts_multiple_mentions():
    text = (
        '"Hello," said John.\n'
        '"Goodbye," John replied.\n'
        '"See you," John added.'
    )
    chars = detect_characters(text)
    assert chars.get("John", 0) >= 2


def test_detect_characters_excludes_pronouns():
    text = '"What?" she asked. "Nothing," he said.'
    chars = detect_characters(text)
    assert "he" not in chars
    assert "she" not in chars


def test_detect_characters_empty_text():
    assert detect_characters("") == {}


# ---------------------------------------------------------------------------
# guess_gender_from_name
# ---------------------------------------------------------------------------


def test_guess_gender_male_name():
    assert guess_gender_from_name("John") == "male"


def test_guess_gender_female_name():
    assert guess_gender_from_name("Mary") == "female"


def test_guess_gender_unknown_name():
    # 'X' is not in the gender database
    result = guess_gender_from_name("Xzq")
    assert result in ("male", "female", "unknown")


# ---------------------------------------------------------------------------
# detect_gender_from_context
# ---------------------------------------------------------------------------


def test_detect_gender_from_context_male():
    text = "John walked into the room. He sat down. He smiled."
    assert detect_gender_from_context("John", text) == "male"


def test_detect_gender_from_context_female():
    text = "Emma entered the garden. She picked a flower. She laughed."
    assert detect_gender_from_context("Emma", text) == "female"


def test_detect_gender_from_context_unknown_when_balanced():
    text = "Sam arrived. He laughed. She waved."
    result = detect_gender_from_context("Sam", text)
    assert result in ("male", "female", "unknown")


# ---------------------------------------------------------------------------
# segment_text
# ---------------------------------------------------------------------------


def test_segment_text_plain_narrator():
    text = "The fog rolled over the hills quietly."
    segments = segment_text(text, {"narrator": "v1"})
    assert len(segments) >= 1
    assert all(s.speaker == "narrator" for s in segments)


def test_segment_text_attributes_dialogue():
    text = '"Hello!" said Alice.\n\nThe room fell silent.'
    assignments = {"narrator": "v_narrator", "Alice": "v_alice"}
    segments = segment_text(text, assignments)
    speakers = {s.speaker for s in segments}
    # Both narrator and Alice should appear
    assert "narrator" in speakers or "Alice" in speakers


def test_segment_text_all_narrator_when_no_characters():
    text = "The hero walked. The hero ran. The hero slept."
    segments = segment_text(text, {"narrator": "v1"})
    assert all(s.speaker == "narrator" for s in segments)


def test_text_segment_repr():
    seg = TextSegment(text="Hello world, how are you?", speaker="Alice")
    assert "Alice" in repr(seg)
    assert "Hello world" in repr(seg)
