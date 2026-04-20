"""Manage TTS voice assignments for characters."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Default voice catalogue (Microsoft Edge Neural voices)
# ---------------------------------------------------------------------------

DEFAULT_MALE_VOICES: List[str] = [
    "en-US-GuyNeural",
    "en-US-DavisNeural",
    "en-US-TonyNeural",
    "en-US-ChristopherNeural",
    "en-GB-RyanNeural",
    "en-AU-WilliamNeural",
]

DEFAULT_FEMALE_VOICES: List[str] = [
    "en-US-JennyNeural",
    "en-US-AriaNeural",
    "en-US-SaraNeural",
    "en-US-NancyNeural",
    "en-GB-SoniaNeural",
    "en-AU-NatashaNeural",
]

DEFAULT_NARRATOR_VOICE: str = "en-US-GuyNeural"

# Unified list for UI dropdowns
ALL_VOICES: List[str] = DEFAULT_MALE_VOICES + DEFAULT_FEMALE_VOICES


@dataclass
class VoiceManager:
    """Maps character names to edge-tts voice strings."""

    assignments: Dict[str, str] = field(default_factory=dict)
    _male_index: int = field(default=0, repr=False, compare=False)
    _female_index: int = field(default=0, repr=False, compare=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assign_voice(self, character: str, voice: str) -> None:
        """Assign *voice* to *character*."""
        self.assignments[character] = voice

    def get_voice(self, character: str) -> str:
        """Return the voice assigned to *character*, falling back to the narrator voice."""
        return self.assignments.get(character, DEFAULT_NARRATOR_VOICE)

    def auto_assign_voices(self, characters: Dict[str, str]) -> None:
        """Automatically assign voices based on detected gender.

        *characters* maps character name → ``'male'`` | ``'female'`` | ``'unknown'``.
        Always sets the narrator as well.
        """
        self.assignments["narrator"] = DEFAULT_NARRATOR_VOICE
        self._male_index = 0
        self._female_index = 0

        for name, gender in characters.items():
            voice = self._next_voice(gender)
            self.assignments[name] = voice

    def voices_by_gender(self) -> Dict[str, List[str]]:
        """Return the default voice lists grouped by gender."""
        return {"male": list(DEFAULT_MALE_VOICES), "female": list(DEFAULT_FEMALE_VOICES)}

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, str]:
        return dict(self.assignments)

    def from_dict(self, data: Dict[str, str]) -> None:
        self.assignments = dict(data)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _next_voice(self, gender: str) -> str:
        if gender == "male":
            voice = DEFAULT_MALE_VOICES[self._male_index % len(DEFAULT_MALE_VOICES)]
            self._male_index += 1
        elif gender == "female":
            voice = DEFAULT_FEMALE_VOICES[self._female_index % len(DEFAULT_FEMALE_VOICES)]
            self._female_index += 1
        else:
            # Unknown gender — alternate between male and female pools
            if (self._male_index + self._female_index) % 2 == 0:
                voice = DEFAULT_MALE_VOICES[self._male_index % len(DEFAULT_MALE_VOICES)]
                self._male_index += 1
            else:
                voice = DEFAULT_FEMALE_VOICES[self._female_index % len(DEFAULT_FEMALE_VOICES)]
                self._female_index += 1
        return voice
