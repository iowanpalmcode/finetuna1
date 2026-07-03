"""Happy trait: Positive and optimistic outlook."""

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


class Happy(BaseTrait):
    """
    Happy trait: The agent maintains a positive and optimistic demeanor.
    Finds good in situations and encourages positive outcomes.
    """

    @property
    def name(self) -> str:
        return "Happy"

    @property
    def description(self) -> str:
        return "Positive, optimistic, and uplifting"

    def modify_response(self, response: str) -> str:
        """Add positive sentiment to responses, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "could", "absolutely can"),
            lambda t: _replace_word(t, "difficult", "challenging but exciting"),
            lambda t: _replace_word(t, "problem", "opportunity"),
            lambda t: _replace_word(t, "sad", "bittersweet but hopeful"),
            lambda t: _replace_word(t, "hard", "tough but doable"),
            self._prefix_great_news,
            self._append_excitement_note,
            self._exclaim_ending,
            self._insert_best_part_connector,
            self._emphasize_positive_word,
        ]

    def _prefix_great_news(self, text: str) -> Optional[str]:
        if text.lower().startswith(("great news", "good news")):
            return None
        return "Great news — " + _lower_first(text)

    def _append_excitement_note(self, text: str) -> Optional[str]:
        if any(word in text.lower() for word in ["excited", "great", "wonderful"]):
            return None
        return text.rstrip() + " There's a lot to be excited about here!"

    def _exclaim_ending(self, text: str) -> Optional[str]:
        if not text.rstrip().endswith("."):
            return None
        stripped = text.rstrip()
        return stripped[:-1] + "!"

    def _insert_best_part_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if "best part" in text.lower():
            return None
        last = sentences[-1]
        sentences[-1] = "And the best part? " + _lower_first(last)
        return " ".join(sentences)

    def _emphasize_positive_word(self, text: str) -> Optional[str]:
        for word in ["opportunity", "exciting", "wonderful", "great"]:
            pattern = re.compile(r'\b' + word + r'\b', re.IGNORECASE)
            match = pattern.search(text)
            if match and text[max(0, match.start() - 1):match.start()] != "*":
                return text[:match.start()] + "*" + match.group(0) + "*" + text[match.end():]
        return None
