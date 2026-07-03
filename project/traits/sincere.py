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


class Sincere(BaseTrait):
    """
    Sincere trait: Genuine and authentic, honest communication,
    truthful and earnest in expression.
    """

    @property
    def name(self) -> str:
        return "Sincere"

    @property
    def description(self) -> str:
        return "Genuine and authentic communication"

    def modify_response(self, response: str) -> str:
        """Make response more sincere and genuine, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "might", "genuinely"),
            lambda t: _replace_word(t, "seem", "truly"),
            lambda t: _replace_word(t, "perhaps", "honestly"),
            lambda t: _replace_word(t, "maybe", "really"),
            lambda t: _replace_word(t, "probably", "truly"),
            self._prefix_honesty_framing,
            self._append_honesty_clause,
            self._parenthetical_sincerity,
            self._emphasize_truth_word,
            self._soften_hedges_to_directness,
        ]

    def _prefix_honesty_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("in all honesty", "honestly")):
            return None
        return "In all honesty, " + _lower_first(text)

    def _append_honesty_clause(self, text: str) -> Optional[str]:
        if any(phrase in text.lower() for phrase in ["complete honesty", "in complete honesty", "sincerely"]):
            return None
        return text.rstrip() + " I say that in complete honesty."

    def _parenthetical_sincerity(self, text: str) -> Optional[str]:
        if "mean that sincerely" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip(), maxsplit=1)
        if not sentences:
            return None
        first = sentences[0].rstrip()
        if first and first[-1] in ".!?":
            first = first[:-1] + " (and I mean that sincerely)" + first[-1]
        else:
            first = first + " (and I mean that sincerely)"
        rest = sentences[1:] if len(sentences) > 1 else []
        return " ".join([first] + rest)

    def _emphasize_truth_word(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\b(truly|genuinely)\b')
        match = pattern.search(text)
        if not match:
            return None
        word = match.group(0)
        if word.isupper():
            return None
        return text[:match.start()] + word.upper() + text[match.end():]

    def _soften_hedges_to_directness(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\bI guess\b', re.IGNORECASE)
        if not pattern.search(text):
            return None
        return pattern.sub("I know", text, count=1)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "authenticity": "High",
            "honesty": "Paramount",
            "expression": "Genuine and earnest",
            "communication": "Truthful",
        }
        return profile
