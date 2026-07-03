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


class Serious(BaseTrait):
    """
    Serious trait: Focused and businesslike, formal tone,
    prioritizes substantive matters.
    """

    @property
    def name(self) -> str:
        return "Serious"

    @property
    def description(self) -> str:
        return "Formal and focused on substantive matters"

    def modify_response(self, response: str) -> str:
        """Make response more formal and serious, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "cool", "remarkable"),
            lambda t: _replace_word(t, "funny", "notable"),
            lambda t: _replace_word(t, "fun", "engaging"),
            lambda t: _replace_word(t, "hey", "Indeed"),
            lambda t: _replace_word(t, "guys", "everyone"),
            self._flatten_exclamation,
            self._prefix_formal_framing,
            self._append_gravity_clause,
            self._strip_casual_interjections,
            self._insert_in_short_connector,
        ]

    def _flatten_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", ".")

    def _prefix_formal_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("to address this matter", "in all seriousness")):
            return None
        return "To address this matter directly, " + _lower_first(text)

    def _append_gravity_clause(self, text: str) -> Optional[str]:
        if any(phrase in text.lower() for phrase in ["due seriousness", "with the gravity"]):
            return None
        return text.rstrip() + " This deserves to be treated with due seriousness."

    def _strip_casual_interjections(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\b(lol|haha+|just kidding|jk)\b[,.]?\s*', re.IGNORECASE)
        if not pattern.search(text):
            return None
        return pattern.sub("", text).strip()

    def _insert_in_short_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'\bin short\b', text, re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "In short, " + _lower_first(last)
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "tone": "Formal and businesslike",
            "focus": "Substantive and practical",
            "humor": "Minimal",
            "engagement": "Professional",
        }
        return profile
