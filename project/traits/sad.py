"""Sad trait: Melancholic and reflective outlook."""

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


class Sad(BaseTrait):
    """
    Sad trait: The agent exhibits a more melancholic, reflective nature.
    Considers the somber aspects and deeper emotional dimensions.
    """

    @property
    def name(self) -> str:
        return "Sad"

    @property
    def description(self) -> str:
        return "Melancholic, reflective, and emotionally aware"

    def modify_response(self, response: str) -> str:
        """Add reflective, contemplative elements to responses, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "will", "may, in time,"),
            lambda t: _replace_word(t, "beautiful", "bittersweet"),
            lambda t: _replace_word(t, "great", "meaningful"),
            lambda t: _replace_word(t, "happy", "quietly content"),
            lambda t: _replace_word(t, "hope", "quiet hope"),
            self._prefix_perhaps,
            self._append_melancholy_suffix,
            self._soften_exclamation,
            self._slow_pacing_with_ellipsis,
            self._parenthetical_wistful_aside,
        ]

    def _prefix_perhaps(self, text: str) -> Optional[str]:
        if text.lower().startswith("perhaps"):
            return None
        return "Perhaps... " + _lower_first(text)

    def _append_melancholy_suffix(self, text: str) -> Optional[str]:
        if "melancholy" in text.lower():
            return None
        return text.rstrip() + " There's a certain melancholy in all of this."

    def _soften_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", "...")

    def _slow_pacing_with_ellipsis(self, text: str) -> Optional[str]:
        if "..." in text:
            return None
        match = re.search(r'[.!?] ', text)
        if not match:
            return None
        return text[:match.start()] + "... " + text[match.end():]

    def _parenthetical_wistful_aside(self, text: str) -> Optional[str]:
        if "(" in text:
            return None
        sentences = re.split(r'(?<=[.!?])(?<!\.\.) +', text.strip())
        if not sentences:
            return None
        first = sentences[0].rstrip('.!?')
        sentences[0] = first + " (if only briefly)."
        return " ".join(sentences)
