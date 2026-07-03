"""Efficient trait: Maximizes output while minimizing waste."""

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


class Efficient(BaseTrait):
    """
    Efficient trait: The agent focuses on optimal resource utilization.
    Values speed and getting things done well.
    """

    @property
    def name(self) -> str:
        return "Efficient"

    @property
    def description(self) -> str:
        return "Focused on optimization and minimal waste"

    def modify_response(self, response: str) -> str:
        """Add efficiency-focused language to responses, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "could", "will"),
            lambda t: _replace_word(t, "might", "shall"),
            lambda t: _replace_word(t, "maybe", "promptly"),
            lambda t: _replace_word(t, "eventually", "immediately"),
            self._shorten_in_order_to,
            self._strip_think_that,
            self._trim_intensifier,
            self._prefix_bottom_line,
            self._append_no_waste_note,
            self._flatten_exclamation,
        ]

    def _shorten_in_order_to(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\bin order to\s+', re.IGNORECASE)
        if not pattern.search(text):
            return None
        return pattern.sub("to ", text, count=1)

    def _strip_think_that(self, text: str) -> Optional[str]:
        pattern = re.compile(r'^(I think that\s+)', re.IGNORECASE)
        match = pattern.match(text)
        if not match:
            return None
        rest = text[match.end():]
        if rest:
            rest = rest[0].upper() + rest[1:]
        return rest

    def _trim_intensifier(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\b(very|really|quite)\s+', re.IGNORECASE)
        if not pattern.search(text):
            return None
        return pattern.sub("", text, count=1)

    def _prefix_bottom_line(self, text: str) -> Optional[str]:
        if text.lower().startswith(("bottom line", "in short", "simply put")):
            return None
        return "Bottom line: " + _lower_first(text)

    def _append_no_waste_note(self, text: str) -> Optional[str]:
        if any(word in text.lower() for word in ["efficient", "waste", "streamlined"]):
            return None
        return text.rstrip() + " No wasted steps."

    def _flatten_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", ".")
