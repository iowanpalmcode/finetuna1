"""Innovative trait: Forward-thinking, embraces new ideas."""

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


class Innovative(BaseTrait):
    """
    Innovative trait: Forward-thinking, embraces new ideas,
    pushes boundaries and experiments.
    """

    @property
    def name(self) -> str:
        return "Innovative"

    @property
    def description(self) -> str:
        return "Forward-thinking and embraces new ideas"

    def modify_response(self, response: str) -> str:
        """Make response more innovative and future-focused, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "traditional", "innovative"),
            lambda t: _replace_word(t, "proven", "experimental"),
            lambda t: _replace_word(t, "current", "emerging"),
            lambda t: _replace_word(t, "same", "revolutionary"),
            lambda t: _replace_word(t, "standard", "novel"),
            lambda t: _replace_word(t, "existing", "reimagined"),
            self._prefix_fresh_angle,
            self._append_what_if_question,
            self._parenthetical_untested_aside,
            self._emphasize_new,
        ]

    def _prefix_fresh_angle(self, text: str) -> Optional[str]:
        if text.lower().startswith(("here's a fresh angle", "imagine if")):
            return None
        return "Here's a fresh angle: " + _lower_first(text)

    def _append_what_if_question(self, text: str) -> Optional[str]:
        if any(phrase in text.lower() for phrase in ["more inventive way", "entirely different"]):
            return None
        return text.rstrip() + " What if we tried something entirely different instead?"

    def _parenthetical_untested_aside(self, text: str) -> Optional[str]:
        if "(untested" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip(), maxsplit=1)
        if len(sentences) < 2:
            return None
        first, rest = sentences[0], sentences[1]
        first = first.rstrip()
        match = re.match(r'^(.*?)([.!?]+)$', first, re.DOTALL)
        if match:
            first = match.group(1) + " (untested, but promising)" + match.group(2)
        else:
            first = first + " (untested, but promising)"
        return first + " " + rest

    def _emphasize_new(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\bnew\b')
        if not pattern.search(text):
            return None
        return pattern.sub("NEW", text, count=1)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "creativity": "High",
            "approach": "Experimental",
            "thinking": "Forward-focused",
            "boundaries": "Pushes limits",
        }
        return profile
