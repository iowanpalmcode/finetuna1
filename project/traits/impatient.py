"""Impatient trait: Desires quick results and fast-paced action."""

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


class Impatient(BaseTrait):
    """
    Impatient trait: Desires quick results, restless with delays,
    prefers fast-paced action and immediate progress.
    """

    @property
    def name(self) -> str:
        return "Impatient"

    @property
    def description(self) -> str:
        return "Desires quick results and fast-paced action"

    def modify_response(self, response: str) -> str:
        """Make response more urgent and action-oriented, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "could", "must"),
            lambda t: _replace_word(t, "eventually", "immediately"),
            lambda t: _replace_word(t, "wait", "move now"),
            lambda t: _replace_word(t, "slowly", "rapidly"),
            lambda t: _replace_word(t, "soon", "now"),
            self._strip_hedging_opener,
            self._sharpen_ending,
            self._prefix_urgency,
            self._append_urgency_suffix,
            self._insert_now_before_last,
        ]

    def _strip_hedging_opener(self, text: str) -> Optional[str]:
        pattern = re.compile(r'^(well|so|actually|basically)\s*,?\s+', re.IGNORECASE)
        if not pattern.search(text):
            return None
        return pattern.sub("", text, count=1)

    def _sharpen_ending(self, text: str) -> Optional[str]:
        if not text.rstrip().endswith("."):
            return None
        stripped = text.rstrip()
        return stripped[:-1] + "!"

    def _prefix_urgency(self, text: str) -> Optional[str]:
        if text.lower().startswith(("no time to waste", "right now")):
            return None
        return "No time to waste — " + _lower_first(text)

    def _append_urgency_suffix(self, text: str) -> Optional[str]:
        if any(phrase in text.lower() for phrase in ["waste any more time", "act now", "move now"]):
            return None
        return text.rstrip() + " Let's not waste any more time on this."

    def _insert_now_before_last(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'\bright now\b', sentences[-1], re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "Right now, " + _lower_first(last)
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "tempo": "Fast and action-oriented",
            "urgency": "High immediate pressure",
            "detail_focus": "Quick summary",
            "frustration_tolerance": "Low",
        }
        return profile
