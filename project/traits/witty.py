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


class Witty(BaseTrait):
    """
    Witty trait: Quick and clever humor, wordplay,
    intelligent and entertaining communication.
    """

    @property
    def name(self) -> str:
        return "Witty"

    @property
    def description(self) -> str:
        return "Clever and entertaining communication"

    def modify_response(self, response: str) -> str:
        """Make response more witty and clever, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "task", "intellectual adventure"),
            lambda t: _replace_word(t, "problem", "delightful puzzle"),
            lambda t: _replace_word(t, "good", "delightfully good"),
            lambda t: _replace_word(t, "bad", "amusingly inconvenient"),
            lambda t: _replace_word(t, "think", "suspect, in my infinite wisdom, that"),
            self._prefix_playful_framing,
            self._append_flair_clause,
            self._parenthetical_quip,
            self._punch_up_final_punctuation,
            self._emphasize_delight,
        ]

    def _prefix_playful_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("well, buckle up", "brace yourself")):
            return None
        return "Well, buckle up, because " + _lower_first(text)

    def _append_flair_clause(self, text: str) -> Optional[str]:
        if "a little flair" in text.lower():
            return None
        return text.rstrip() + " ...though I couldn't resist adding a little flair there."

    def _parenthetical_quip(self, text: str) -> Optional[str]:
        if "cue dramatic music" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip(), maxsplit=1)
        if not sentences:
            return None
        first = sentences[0].rstrip()
        match = re.match(r'^(.*?)([.!?]+)$', first, re.DOTALL)
        if match:
            first = match.group(1) + " (cue dramatic music)" + match.group(2)
        else:
            first = first + " (cue dramatic music)"
        rest = sentences[1:] if len(sentences) > 1 else []
        return " ".join([first] + rest)

    def _punch_up_final_punctuation(self, text: str) -> Optional[str]:
        stripped = text.rstrip()
        if not stripped.endswith(".") or stripped.endswith("..."):
            return None
        return stripped[:-1] + "!"

    def _emphasize_delight(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\bdelightfully\b')
        match = pattern.search(text)
        if not match:
            return None
        word = match.group(0)
        if word.isupper():
            return None
        return text[:match.start()] + word.upper() + text[match.end():]

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "humor": "Clever and quick",
            "style": "Witty and entertaining",
            "communication": "Intelligent wordplay",
            "engagement": "Entertaining",
        }
        return profile
