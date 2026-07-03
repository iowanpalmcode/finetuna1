"""Extroverted trait: Energized by social interaction and large groups."""

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


class Extroverted(BaseTrait):
    """
    Extroverted trait: Energized by social interaction, enjoys large groups,
    outgoing and expressive nature.
    """

    @property
    def name(self) -> str:
        return "Extroverted"

    @property
    def description(self) -> str:
        return "Energized by social interaction and large groups"

    def modify_response(self, response: str) -> str:
        """Make response more social and outgoing, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "quiet", "vibrant"),
            lambda t: _replace_word(t, "alone", "together"),
            lambda t: _replace_word(t, "maybe", "definitely"),
            lambda t: _replace_word(t, "calm", "energetic"),
            lambda t: _replace_word(t, "by myself", "with everyone"),
            self._prefix_enthusiasm,
            self._append_invite,
            self._exclaim_ending,
            self._insert_and_honestly,
            self._emphasize_togetherness,
        ]

    def _prefix_enthusiasm(self, text: str) -> Optional[str]:
        if text.lower().startswith(("i'm so excited", "i'm excited")):
            return None
        return "I'm so excited to jump into this — " + _lower_first(text)

    def _append_invite(self, text: str) -> Optional[str]:
        if "together" in text.lower() or "talk more" in text.lower():
            return None
        return text.rstrip() + " Let's talk more about this together!"

    def _exclaim_ending(self, text: str) -> Optional[str]:
        if not text.rstrip().endswith("."):
            return None
        stripped = text.rstrip()
        return stripped[:-1] + "!"

    def _insert_and_honestly(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'\bhonestly\b', text, re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "And honestly, " + _lower_first(last)
        return " ".join(sentences)

    def _emphasize_togetherness(self, text: str) -> Optional[str]:
        for word in ["everyone", "together", "team"]:
            pattern = re.compile(r'\b' + word + r'\b', re.IGNORECASE)
            match = pattern.search(text)
            if match and text[max(0, match.start() - 1):match.start()] != "*":
                return text[:match.start()] + "*" + match.group(0) + "*" + text[match.end():]
        return None

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "communication": "Outgoing and expressive",
            "group_size": "Thrives in large groups",
            "decision_making": "Collaborative approach",
            "sociability": "Extensive networking",
        }
        return profile
