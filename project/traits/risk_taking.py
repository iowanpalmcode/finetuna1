"""RiskTaking trait: Bold, adventurous, willing to take chances."""

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


class RiskTaking(BaseTrait):
    """
    RiskTaking trait: The agent is bold and willing to take calculated risks.
    Embraces adventure and unconventional paths.
    """

    @property
    def name(self) -> str:
        return "RiskTaking"

    @property
    def description(self) -> str:
        return "Bold, adventurous, and willing to take calculated risks"

    def modify_response(self, response: str) -> str:
        """Add bold, adventurous elements to responses, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "might", "will boldly"),
            lambda t: _replace_word(t, "could", "should definitely"),
            lambda t: _replace_word(t, "safe", "exciting"),
            lambda t: _replace_word(t, "cautiously", "boldly"),
            lambda t: _replace_word(t, "careful", "daring"),
            self._prefix_bold_framing,
            self._append_bold_suffix,
            self._exclaim_ending,
            self._insert_dash_aside,
            self._insert_leap_connector,
        ]

    def _prefix_bold_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("why not go big", "let's go big")):
            return None
        return "Why not go big — " + _lower_first(text)

    def _append_bold_suffix(self, text: str) -> Optional[str]:
        if "bold move" in text.lower():
            return None
        return text.rstrip() + " Sometimes the bold move is the right one."

    def _exclaim_ending(self, text: str) -> Optional[str]:
        if "!" in text:
            return None
        stripped = text.rstrip()
        if not stripped.endswith("."):
            return None
        return stripped[:-1] + "!"

    def _insert_dash_aside(self, text: str) -> Optional[str]:
        if "—" in text or " - " in text:
            return None
        sentences = re.split(r'(?<=[.!?])(?<!\.\.) +', text.strip())
        if not sentences:
            return None
        first = sentences[0].rstrip('.!?')
        sentences[0] = first + " — go for it."
        return " ".join(sentences)

    def _insert_leap_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?])(?<!\.\.) +', text.strip())
        if len(sentences) < 2:
            return None
        if "take the leap" in text.lower():
            return None
        last = sentences[-1]
        sentences[-1] = "Take the leap: " + _lower_first(last)
        return " ".join(sentences)
