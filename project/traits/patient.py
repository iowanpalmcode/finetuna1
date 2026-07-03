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


class Patient(BaseTrait):
    """
    Patient trait: Tolerant of delays, willing to wait for results,
    takes time to understand details thoroughly.
    """

    @property
    def name(self) -> str:
        return "Patient"

    @property
    def description(self) -> str:
        return "Tolerant and willing to wait for proper results"

    def modify_response(self, response: str) -> str:
        """Make response more measured and thorough, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "immediately", "in due time"),
            lambda t: _replace_word(t, "rush", "proceed carefully"),
            lambda t: _replace_word(t, "quickly", "thoroughly"),
            lambda t: _replace_word(t, "urgent", "worth taking time over"),
            lambda t: _replace_word(t, "hurry", "ease into it"),
            self._prefix_patient_framing,
            self._append_no_rush_suffix,
            self._soften_exclamation,
            self._slow_pacing_with_ellipsis,
            self._parenthetical_patience_aside,
        ]

    def _prefix_patient_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("take a breath", "there's no need to rush", "in good time")):
            return None
        return "Take a breath — " + _lower_first(text)

    def _append_no_rush_suffix(self, text: str) -> Optional[str]:
        if "no need to rush" in text.lower() or "in due time" in text.lower():
            return None
        return text.rstrip() + " There's no need to rush this."

    def _soften_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", ".")

    def _slow_pacing_with_ellipsis(self, text: str) -> Optional[str]:
        if "..." in text:
            return None
        match = re.search(r'[.!?] ', text)
        if not match:
            return None
        return text[:match.start()] + "... " + text[match.end():]

    def _parenthetical_patience_aside(self, text: str) -> Optional[str]:
        if "(" in text:
            return None
        sentences = re.split(r'(?<=[.!?])(?<!\.\.) +', text.strip())
        if not sentences:
            return None
        first = sentences[0].rstrip('.!?')
        sentences[0] = first + " (there's no need to hurry through this)."
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "tempo": "Measured and deliberate",
            "urgency": "Low immediate pressure",
            "detail_focus": "Thorough examination",
            "frustration_tolerance": "High",
        }
        return profile
