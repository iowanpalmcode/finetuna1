"""Analytical trait: Logical, systematic, and data-driven."""

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


class Analytical(BaseTrait):
    """
    Analytical trait: The agent approaches problems with logic and systematic analysis.
    Values data, evidence, and rigorous reasoning.
    """

    @property
    def name(self) -> str:
        return "Analytical"

    @property
    def description(self) -> str:
        return "Logical, systematic, and data-driven"

    def modify_response(self, response: str) -> str:
        """Add analytical rigor to responses, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "think", "calculate"),
            lambda t: _replace_word(t, "believe", "conclude, based on the evidence, that"),
            lambda t: _replace_word(t, "good", "statistically favorable"),
            lambda t: _replace_word(t, "guess", "estimate"),
            lambda t: _replace_word(t, "maybe", "there is a measurable chance that"),
            lambda t: _replace_word(t, "important", "statistically significant"),
            self._prefix_systematic_framing,
            self._append_data_disclaimer,
            self._flatten_exclamation,
            self._insert_therefore,
        ]

    def _prefix_systematic_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("breaking this down", "systematically")):
            return None
        return "Breaking this down systematically: " + _lower_first(text)

    def _append_data_disclaimer(self, text: str) -> Optional[str]:
        if any(word in text.lower() for word in ["data", "evidence", "analyz"]):
            return None
        return text.rstrip() + " This conclusion is based on careful analysis of the available data."

    def _flatten_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", ".")

    def _insert_therefore(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'\b(therefore|thus|hence|consequently)\b', text, re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "Therefore, " + _lower_first(last)
        return " ".join(sentences)
