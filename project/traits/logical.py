"""Logical trait: Reason-based thinking focused on evidence."""

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


class Logical(BaseTrait):
    """
    Logical trait: Reason-based thinking, follows causal chains,
    empirical and evidence-focused.
    """

    @property
    def name(self) -> str:
        return "Logical"

    @property
    def description(self) -> str:
        return "Reason-based thinking focused on evidence"

    def modify_response(self, response: str) -> str:
        """Make response more logical and evidence-based, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "feel", "logically conclude"),
            lambda t: _replace_word(t, "guess", "determine"),
            lambda t: _replace_word(t, "maybe", "based on the evidence"),
            lambda t: _replace_word(t, "I think", "it follows that"),
            lambda t: _replace_word(t, "somehow", "through logical deduction"),
            lambda t: _replace_word(t, "assume", "deduce"),
            self._prefix_following_logic,
            self._append_conclusion_suffix,
            self._flatten_exclamation,
            self._insert_therefore_before_last,
        ]

    def _prefix_following_logic(self, text: str) -> Optional[str]:
        if text.lower().startswith(("following the logic", "it follows that")):
            return None
        return "Following the logic: " + _lower_first(text)

    def _append_conclusion_suffix(self, text: str) -> Optional[str]:
        if "follows from the evidence" in text.lower():
            return None
        return text.rstrip() + " That conclusion follows from the evidence at hand."

    def _flatten_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", ".")

    def _insert_therefore_before_last(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'\b(therefore|thus|hence|consequently)\b', text, re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "Therefore, " + _lower_first(last)
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "reasoning": "Analytical and evidence-based",
            "approach": "Systematic",
            "decision_making": "Logical",
            "evidence_priority": "High",
        }
        return profile
