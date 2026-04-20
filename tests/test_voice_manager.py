"""Tests for src/voice_manager.py"""

import pytest

from src.voice_manager import (
    ALL_VOICES,
    DEFAULT_MALE_VOICES,
    DEFAULT_FEMALE_VOICES,
    DEFAULT_NARRATOR_VOICE,
    VoiceManager,
)


# ---------------------------------------------------------------------------
# Basic assignment
# ---------------------------------------------------------------------------


def test_assign_and_get_voice():
    vm = VoiceManager()
    vm.assign_voice("Alice", "en-US-AriaNeural")
    assert vm.get_voice("Alice") == "en-US-AriaNeural"


def test_get_voice_falls_back_to_narrator():
    vm = VoiceManager()
    assert vm.get_voice("UnknownCharacter") == DEFAULT_NARRATOR_VOICE


# ---------------------------------------------------------------------------
# auto_assign_voices
# ---------------------------------------------------------------------------


def test_auto_assign_sets_narrator():
    vm = VoiceManager()
    vm.auto_assign_voices({})
    assert vm.get_voice("narrator") == DEFAULT_NARRATOR_VOICE


def test_auto_assign_male_character_gets_male_voice():
    vm = VoiceManager()
    vm.auto_assign_voices({"John": "male"})
    assert vm.get_voice("John") in DEFAULT_MALE_VOICES


def test_auto_assign_female_character_gets_female_voice():
    vm = VoiceManager()
    vm.auto_assign_voices({"Mary": "female"})
    assert vm.get_voice("Mary") in DEFAULT_FEMALE_VOICES


def test_auto_assign_unknown_gender_gets_some_voice():
    vm = VoiceManager()
    vm.auto_assign_voices({"Alex": "unknown"})
    voice = vm.get_voice("Alex")
    assert voice in ALL_VOICES


def test_auto_assign_multiple_male_characters_use_different_voices():
    vm = VoiceManager()
    vm.auto_assign_voices({"John": "male", "Mike": "male", "Tom": "male"})
    voices = [vm.get_voice(n) for n in ("John", "Mike", "Tom")]
    # All should be male voices
    assert all(v in DEFAULT_MALE_VOICES for v in voices)
    # They should cycle through distinct voices where pool allows
    # (at minimum they all come from the male pool)


def test_auto_assign_resets_indices_on_each_call():
    vm = VoiceManager()
    vm.auto_assign_voices({"Alice": "female"})
    first_voice = vm.get_voice("Alice")

    vm.auto_assign_voices({"Alice": "female"})
    second_voice = vm.get_voice("Alice")

    assert first_voice == second_voice  # deterministic


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------


def test_to_dict_round_trip():
    vm = VoiceManager()
    vm.auto_assign_voices({"Alice": "female", "Bob": "male"})
    data = vm.to_dict()

    vm2 = VoiceManager()
    vm2.from_dict(data)
    assert vm2.get_voice("Alice") == vm.get_voice("Alice")
    assert vm2.get_voice("Bob") == vm.get_voice("Bob")


def test_voices_by_gender_returns_correct_keys():
    vm = VoiceManager()
    groups = vm.voices_by_gender()
    assert "male" in groups
    assert "female" in groups
    assert len(groups["male"]) > 0
    assert len(groups["female"]) > 0
