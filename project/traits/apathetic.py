"""Apathetic trait: Indifferent, unmotivated, and disengaged."""

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


class Apathetic(BaseTrait):
    """
    Apathetic trait: Indifferent and unmotivated, low engagement,
    doesn't care much about outcomes.
    """

    @property
    def name(self) -> str:
        return "Apathetic"

    @property
    def description(self) -> str:
        return "Indifferent and unmotivated"

    def modify_response(self, response: str) -> str:
        """Make response more apathetic and indifferent, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "important", "whatever"),
            lambda t: _replace_word(t, "must", "could"),
            lambda t: _replace_word(t, "definitely", "maybe"),
            lambda t: _replace_word(t, "great", "fine"),
            lambda t: _replace_word(t, "excited", "indifferent"),
            self._prefix_shrug,
            self._flatten_exclamation,
            self._flatten_question,
            self._append_dismissal,
            self._truncate_dismissively,
        ]

    def _prefix_shrug(self, text: str) -> Optional[str]:
        if text.lower().startswith(("sure, whatever", "i guess", "whatever")):
            return None
        return "I guess, whatever - " + _lower_first(text)

    def _flatten_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", ".")

    def _flatten_question(self, text: str) -> Optional[str]:
        if "?" not in text:
            return None
        return text.replace("?", ".")

    def _append_dismissal(self, text: str) -> Optional[str]:
        if "matter" in text.lower():
            return None
        return text.rstrip() + " Not that it matters much either way."

    def _truncate_dismissively(self, text: str) -> Optional[str]:
        words = text.split()
        if len(words) <= 12 or text.rstrip().endswith("..."):
            return None
        return " ".join(words[:10]) + "... whatever."

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "motivation": "Low",
            "engagement": "Minimal",
            "care": "Indifferent",
            "investment": "Detached",
        }
        return profile
