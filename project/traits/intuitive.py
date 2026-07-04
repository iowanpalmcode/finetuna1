"""Intuitive trait: Pattern-based insights and gut feelings."""

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


class Intuitive(BaseTrait):
    """
    Intuitive trait: Pattern recognition-based, gut feelings,
    holistic understanding without full data.
    """

    @property
    def name(self) -> str:
        return "Intuitive"

    @property
    def description(self) -> str:
        return "Pattern-based insights and gut feelings"

    def modify_response(self, response: str) -> str:
        """Make response more intuitive and pattern-based, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "logically", "intuitively"),
            lambda t: _replace_word(t, "based on", "going by"),
            lambda t: _replace_word(t, "proven", "felt"),
            lambda t: _replace_word(t, "evidence", "patterns"),
            lambda t: _replace_word(t, "calculate", "sense"),
            lambda t: _replace_word(t, "certain", "intuitively sure"),
            self._prefix_gut_feeling,
            self._append_feels_right,
            self._insert_musing_pause,
            self._parenthetical_hard_to_explain,
        ]

    def _prefix_gut_feeling(self, text: str) -> Optional[str]:
        if text.lower().startswith(("my gut tells me", "something about this")):
            return None
        return "My gut tells me " + _lower_first(text)

    def _append_feels_right(self, text: str) -> Optional[str]:
        if "feels right" in text.lower():
            return None
        return text.rstrip() + " Something about this just feels right."

    def _insert_musing_pause(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if sentences[-1].strip().startswith("..."):
            return None
        last = sentences[-1]
        sentences[-1] = "... " + _lower_first(last)
        return " ".join(sentences)

    def _parenthetical_hard_to_explain(self, text: str) -> Optional[str]:
        if "hard to explain" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip(), maxsplit=1)
        if len(sentences) < 2:
            return None
        first, rest = sentences[0], sentences[1]
        first = first.rstrip()
        match = re.match(r'^(.*?)([.!?]+)$', first, re.DOTALL)
        if match:
            first = match.group(1) + " (hard to explain, but it checks out)" + match.group(2)
        else:
            first = first + " (hard to explain, but it checks out)"
        return first + " " + rest

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "reasoning": "Pattern and gut-based",
            "approach": "Holistic",
            "decision_making": "Intuitive",
            "data_requirement": "Flexible",
        }
        return profile
