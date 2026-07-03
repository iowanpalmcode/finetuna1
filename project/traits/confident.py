"""Confident trait: Self-assured, decisive, and assertive."""

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


class Confident(BaseTrait):
    """
    Confident trait: Strong self-assurance, belief in capabilities,
    decisive and assertive communication.
    """

    @property
    def name(self) -> str:
        return "Confident"

    @property
    def description(self) -> str:
        return "Self-assured and decisive in communications"

    def modify_response(self, response: str) -> str:
        """Make response more assertive and confident, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "might", "will"),
            lambda t: _replace_word(t, "could be", "is"),
            lambda t: _replace_word(t, "I think", "I know"),
            lambda t: _replace_word(t, "maybe", "absolutely"),
            lambda t: _replace_word(t, "somewhat", "definitely"),
            self._strip_hedge,
            self._prefix_confidence_opener,
            self._append_confidence_suffix,
            self._flatten_question_to_statement,
            self._sharpen_ending,
        ]

    def _strip_hedge(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\b(perhaps|possibly|i could be wrong, but)\s+', re.IGNORECASE)
        if not pattern.search(text):
            return None
        return pattern.sub("", text, count=1)

    def _prefix_confidence_opener(self, text: str) -> Optional[str]:
        if text.lower().startswith(("without a doubt", "i'm confident")):
            return None
        return "Without a doubt, " + _lower_first(text)

    def _append_confidence_suffix(self, text: str) -> Optional[str]:
        if "confident this is the right path" in text.lower():
            return None
        return text.rstrip() + " I'm confident this is the right path forward."

    def _flatten_question_to_statement(self, text: str) -> Optional[str]:
        if not text.rstrip().endswith("?"):
            return None
        stripped = text.rstrip()
        return stripped[:-1] + "."

    def _sharpen_ending(self, text: str) -> Optional[str]:
        if not text.rstrip().endswith("."):
            return None
        stripped = text.rstrip()
        return stripped[:-1] + "!"

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "assertiveness": "High",
            "decision_style": "Decisive",
            "self_belief": "Strong",
            "risk_acceptance": "Comfortable with uncertainty",
        }
        return profile
