"""Calm trait: Serene, composed, and steady under pressure."""

import re
from typing import Callable, List, Optional

from traits.base_trait import BaseTrait


def _replace_word(text: str, old: str, new: str) -> Optional[str]:
    """Case-insensitive, whole-word replace. Returns None if `old` isn't present.

    Preserves capitalization: if the matched occurrence starts with an
    uppercase letter (e.g. it opens a sentence), the replacement's first
    letter is capitalized too, so word swaps don't lowercase sentence starts.
    """
    pattern = re.compile(r'\b' + re.escape(old) + r'\b', re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    replacement = new
    if match.group()[0].isupper():
        replacement = new[0].upper() + new[1:]
    return text[:match.start()] + replacement + text[match.end():]


def _lower_first(fragment: str) -> str:
    """Lowercase a fragment's leading letter, unless it's the pronoun 'I'."""
    if not fragment or re.match(r"^I($|[ '])", fragment):
        return fragment
    return fragment[0].lower() + fragment[1:]


class Calm(BaseTrait):
    """
    Calm trait: Serene and unflappable, handles stress well,
    composed and steady in difficult situations.
    """

    @property
    def name(self) -> str:
        return "Calm"

    @property
    def description(self) -> str:
        return "Serene and composed under pressure"

    def modify_response(self, response: str) -> str:
        """Make response more calm and serene, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "urgent", "gentle"),
            lambda t: _replace_word(t, "panic", "breathe and reflect"),
            lambda t: _replace_word(t, "crisis", "challenge"),
            lambda t: _replace_word(t, "stress", "ease"),
            lambda t: _replace_word(t, "quickly", "peacefully"),
            self._flatten_exclamation,
            self._prefix_breath,
            self._append_steady_close,
            self._insert_pause_aside,
            self._insert_intime_connector,
        ]

    def _flatten_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", ".")

    def _prefix_breath(self, text: str) -> Optional[str]:
        if "take a breath" in text.lower():
            return None
        return "Let's take a breath. " + _lower_first(text)

    def _append_steady_close(self, text: str) -> Optional[str]:
        if "steadily" in text.lower() or "handle this" in text.lower():
            return None
        return text.rstrip() + " We can handle this steadily."

    def _insert_pause_aside(self, text: str) -> Optional[str]:
        if "no need to rush" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if not sentences:
            return None
        first = sentences[0].rstrip()
        if first and first[-1] in ".!?":
            sentences[0] = first[:-1] + " (no need to rush)" + first[-1]
        else:
            sentences[0] = first + " (no need to rush)"
        return " ".join(sentences)

    def _insert_intime_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'\bin time\b', text, re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "In time, " + _lower_first(last)
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "demeanor": "Serene and composed",
            "stress_handling": "Excellent",
            "approach": "Steady",
            "emotional": "Balanced",
        }
        return profile
