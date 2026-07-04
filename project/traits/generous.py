"""Generous trait: Giving and sharing, willingly helps others."""

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


class Generous(BaseTrait):
    """
    Generous trait: Giving and sharing, willingly helps others,
    abundance mindset and charitable nature.
    """

    @property
    def name(self) -> str:
        return "Generous"

    @property
    def description(self) -> str:
        return "Giving and charitable in nature"

    def modify_response(self, response: str) -> str:
        """Make response more generous and giving, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "I will", "I'd be delighted to"),
            lambda t: _replace_word(t, "can", "can happily"),
            lambda t: _replace_word(t, "help", "generously help"),
            lambda t: _replace_word(t, "share", "freely share"),
            lambda t: _replace_word(t, "offer", "gladly offer"),
            self._prefix_happy_to_give,
            self._append_support_note,
            self._insert_no_strings_aside,
            self._insert_and_more_connector,
            self._emphasize_give_word,
        ]

    def _prefix_happy_to_give(self, text: str) -> Optional[str]:
        if text.lower().startswith(("happy to give", "glad to give", "i'd love to give")):
            return None
        return "Happy to give here — " + _lower_first(text)

    def _append_support_note(self, text: str) -> Optional[str]:
        if any(phrase in text.lower() for phrase in ["glad to give", "generous", "give whatever"]):
            return None
        return text.rstrip() + " I'm glad to give whatever support helps most."

    def _insert_no_strings_aside(self, text: str) -> Optional[str]:
        if "no strings" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        sentences[0] = sentences[0].rstrip(".!?") + " (no strings attached)."
        return " ".join(sentences)

    def _insert_and_more_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if "more than that" in text.lower():
            return None
        last = sentences[-1]
        sentences[-1] = "And more than that, " + _lower_first(last)
        return " ".join(sentences)

    def _emphasize_give_word(self, text: str) -> Optional[str]:
        for word in ["give", "giving", "generous", "generously"]:
            pattern = re.compile(r'\b' + word + r'\b', re.IGNORECASE)
            match = pattern.search(text)
            if match and text[max(0, match.start() - 1):match.start()] != "*":
                return text[:match.start()] + "*" + match.group(0) + "*" + text[match.end():]
        return None

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "mindset": "Abundance-focused",
            "giving": "Generous",
            "helping": "Willingly assists others",
            "nature": "Charitable and kind",
        }
        return profile
