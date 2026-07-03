"""Empathetic trait: Compassionate and emotionally aware."""

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


class Empathetic(BaseTrait):
    """
    Empathetic trait: The agent is compassionate and highly attuned to emotions.
    Considers others' feelings and seeks to understand deeply.
    """

    @property
    def name(self) -> str:
        return "Empathetic"

    @property
    def description(self) -> str:
        return "Compassionate, emotionally aware, and understanding"

    def modify_response(self, response: str) -> str:
        """Add empathetic, caring elements to responses, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "should", "might feel ready to"),
            lambda t: _replace_word(t, "problem", "challenge"),
            lambda t: _replace_word(t, "difficult", "hard"),
            lambda t: _replace_word(t, "fix", "work through"),
            lambda t: _replace_word(t, "wrong", "understandable"),
            self._prefix_hear_you,
            self._append_caring_note,
            self._soften_exclamation,
            self._insert_gentle_aside,
            self._add_supportive_question,
        ]

    def _prefix_hear_you(self, text: str) -> Optional[str]:
        if text.lower().startswith(("i hear you", "i understand", "i'm here")):
            return None
        return "I hear you — " + _lower_first(text)

    def _append_caring_note(self, text: str) -> Optional[str]:
        if any(word in text.lower() for word in ["care about", "your feelings", "here for you"]):
            return None
        return text.rstrip() + " I care about how you're feeling through this."

    def _soften_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", ".")

    def _insert_gentle_aside(self, text: str) -> Optional[str]:
        if "take all the time" in text.lower() or "take your time" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        sentences[0] = sentences[0].rstrip(".!?") + " (take all the time you need)."
        return " ".join(sentences)

    def _add_supportive_question(self, text: str) -> Optional[str]:
        if "?" in text:
            return None
        return text.rstrip() + " How are you feeling about this?"
