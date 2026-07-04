"""Cautious trait: Careful, risk-aware, and deliberate."""

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


class Cautious(BaseTrait):
    """
    Cautious trait: Careful and risk-aware, thorough in assessment,
    prefers safe and proven approaches.
    """

    @property
    def name(self) -> str:
        return "Cautious"

    @property
    def description(self) -> str:
        return "Careful and risk-aware in decision making"

    def modify_response(self, response: str) -> str:
        """Make response more cautious and risk-aware, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "should", "might be wise to"),
            lambda t: _replace_word(t, "will", "could carefully"),
            lambda t: _replace_word(t, "yes", "possibly, with care"),
            lambda t: _replace_word(t, "go ahead", "proceed cautiously"),
            lambda t: _replace_word(t, "immediately", "after careful review"),
            self._flatten_exclamation,
            self._prefix_caution_opener,
            self._append_risk_suffix,
            self._insert_however_connector,
            self._insert_doublecheck_aside,
        ]

    def _flatten_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", ".")

    def _prefix_caution_opener(self, text: str) -> Optional[str]:
        if text.lower().startswith(("before proceeding", "let's weigh")):
            return None
        return "Before proceeding, consider this: " + _lower_first(text)

    def _append_risk_suffix(self, text: str) -> Optional[str]:
        if "weigh the risks" in text.lower():
            return None
        return text.rstrip() + " Let's weigh the risks carefully before committing."

    def _insert_however_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'\bhowever\b', text, re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "However, " + _lower_first(last)
        return " ".join(sentences)

    def _insert_doublecheck_aside(self, text: str) -> Optional[str]:
        if "worth double-checking" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if not sentences:
            return None
        first = sentences[0].rstrip()
        match = re.match(r'^(.*?)([.!?]+)$', first, re.DOTALL)
        if match:
            sentences[0] = match.group(1) + " (worth double-checking)" + match.group(2)
        else:
            sentences[0] = first + " (worth double-checking)"
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "risk_tolerance": "Low",
            "approach": "Conservative",
            "decision_style": "Thorough risk assessment",
            "change_acceptance": "Gradual",
        }
        return profile
