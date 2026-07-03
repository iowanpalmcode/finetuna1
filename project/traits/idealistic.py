"""Idealistic trait: Principle-driven, visionary thinking."""

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


class Idealistic(BaseTrait):
    """
    Idealistic trait: Principle-driven, visionary thinking,
    strives for perfect solutions and higher ideals.
    """

    @property
    def name(self) -> str:
        return "Idealistic"

    @property
    def description(self) -> str:
        return "Principle-driven and vision-focused"

    def modify_response(self, response: str) -> str:
        """Make response more idealistic and principle-driven, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "practically", "ideally"),
            lambda t: _replace_word(t, "can", "should"),
            lambda t: _replace_word(t, "workable", "perfect"),
            lambda t: _replace_word(t, "practice", "principle"),
            lambda t: _replace_word(t, "realistic", "aspirational"),
            lambda t: _replace_word(t, "good", "virtuous"),
            self._prefix_higher_purpose,
            self._append_should_be_question,
            self._insert_ideally_before_last,
            self._emphasize_ideal,
        ]

    def _prefix_higher_purpose(self, text: str) -> Optional[str]:
        if text.lower().startswith(("in principle", "in an ideal world", "ideally")):
            return None
        return "In an ideal world, " + _lower_first(text)

    def _append_should_be_question(self, text: str) -> Optional[str]:
        if any(phrase in text.lower() for phrase in ["strive for something better", "how things should be"]):
            return None
        return text.rstrip() + " Shouldn't we strive for something better?"

    def _insert_ideally_before_last(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'\bideally\b', sentences[-1], re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "Ideally, " + _lower_first(last)
        return " ".join(sentences)

    def _emphasize_ideal(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\bideal\b')
        if not pattern.search(text):
            return None
        return pattern.sub("IDEAL", text, count=1)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "focus": "Principles and ideals",
            "approach": "Visionary",
            "ideal_vs_reality": "Pursues higher ideals",
            "values": "Principle-driven",
        }
        return profile
