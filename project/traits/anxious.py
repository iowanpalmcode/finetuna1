"""Anxious trait: Worried, vigilant, and stress-prone."""

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


class Anxious(BaseTrait):
    """
    Anxious trait: Worried and stressed, anticipates problems,
    vigilant about potential dangers.
    """

    @property
    def name(self) -> str:
        return "Anxious"

    @property
    def description(self) -> str:
        return "Vigilant and concerned about potential problems"

    def modify_response(self, response: str) -> str:
        """Make response more anxious and concerned, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "fine", "worrying"),
            lambda t: _replace_word(t, "calm", "uneasy"),
            lambda t: _replace_word(t, "good", "concerning"),
            lambda t: _replace_word(t, "easy", "stressful"),
            lambda t: _replace_word(t, "sure", "hopeful, though not certain"),
            self._prefix_worry_opener,
            self._append_worry_question,
            self._insert_nervous_aside,
            self._add_hesitation_ellipsis,
            self._capitalize_risk_word,
        ]

    def _prefix_worry_opener(self, text: str) -> Optional[str]:
        if text.lower().startswith(("what if", "i'm worried", "i am worried")):
            return None
        return "What if this goes wrong? " + _lower_first(text)

    def _append_worry_question(self, text: str) -> Optional[str]:
        if "what could go wrong" in text.lower():
            return None
        return text.rstrip() + " What could go wrong here?"

    def _insert_nervous_aside(self, text: str) -> Optional[str]:
        if "i hope that's right" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if not sentences:
            return None
        first = sentences[0].rstrip()
        if first and first[-1] in ".!?":
            sentences[0] = first[:-1] + " (I hope that's right)" + first[-1]
        else:
            sentences[0] = first + " (I hope that's right)"
        return " ".join(sentences)

    def _add_hesitation_ellipsis(self, text: str) -> Optional[str]:
        if "..." in text:
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        first = sentences[0]
        if first and first[-1] in ".!?":
            first = first[:-1] + "..."
            sentences[0] = first
            return " ".join(sentences)
        return None

    def _capitalize_risk_word(self, text: str) -> Optional[str]:
        for word in ("risk", "danger", "problem", "wrong", "careful"):
            pattern = re.compile(r'\b' + word + r'\b', re.IGNORECASE)
            match = pattern.search(text)
            if match and match.group(0) != match.group(0).upper():
                return text[:match.start()] + match.group(0).upper() + text[match.end():]
        return None

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "demeanor": "Worried and stressed",
            "vigilance": "High",
            "approach": "Anticipates problems",
            "emotional": "On edge",
        }
        return profile
