"""Humble trait: Modest about abilities, acknowledges limitations."""

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


class Humble(BaseTrait):
    """
    Humble trait: Modest about abilities, acknowledges limitations,
    respectful and grounded demeanor.
    """

    @property
    def name(self) -> str:
        return "Humble"

    @property
    def description(self) -> str:
        return "Modest and respectful about limitations"

    def modify_response(self, response: str) -> str:
        """Make response more modest and acknowledging, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "I will", "I'll do my best to"),
            lambda t: _replace_word(t, "I know", "In my experience,"),
            lambda t: _replace_word(t, "definitely", "I hope to"),
            lambda t: _replace_word(t, "always", "often"),
            lambda t: _replace_word(t, "perfect", "suitable"),
            self._prefix_for_what_its_worth,
            self._append_improve_note,
            self._soften_exclamation,
            self._insert_might_be_wrong_aside,
            self._strip_boastful_intensifier,
        ]

    def _prefix_for_what_its_worth(self, text: str) -> Optional[str]:
        if text.lower().startswith(("for what it's worth", "in my humble")):
            return None
        return "For what it's worth, " + _lower_first(text)

    def _append_improve_note(self, text: str) -> Optional[str]:
        if any(phrase in text.lower() for phrase in ["improve", "feedback", "correct me"]):
            return None
        return text.rstrip() + " Please let me know if I can improve."

    def _soften_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", ".")

    def _insert_might_be_wrong_aside(self, text: str) -> Optional[str]:
        if "could be wrong" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        sentences[0] = sentences[0].rstrip(".!?") + " (though I could be wrong)."
        return " ".join(sentences)

    def _strip_boastful_intensifier(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\b(obviously|clearly|certainly)\s+', re.IGNORECASE)
        if not pattern.search(text):
            return None
        return pattern.sub("", text, count=1)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "assertiveness": "Measured",
            "self_presentation": "Modest",
            "openness_to_feedback": "High",
            "collaboration": "Cooperative",
        }
        return profile
