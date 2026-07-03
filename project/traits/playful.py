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


class Playful(BaseTrait):
    """
    Playful trait: Light-hearted and fun-loving, enjoys humor,
    brings levity to interactions.
    """

    @property
    def name(self) -> str:
        return "Playful"

    @property
    def description(self) -> str:
        return "Light-hearted and enjoys humor and fun"

    def modify_response(self, response: str) -> str:
        """Make response more playful and light, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "serious", "fun"),
            lambda t: _replace_word(t, "problem", "puzzle"),
            lambda t: _replace_word(t, "task", "adventure"),
            lambda t: _replace_word(t, "work", "play"),
            lambda t: _replace_word(t, "must", "get to"),
            self._exclaim_ending,
            self._prefix_playful_framing,
            self._append_playful_suffix,
            self._add_teasing_aside,
            self._emphasize_fun_word,
        ]

    def _exclaim_ending(self, text: str) -> Optional[str]:
        if "!" in text:
            return None
        stripped = text.rstrip()
        if not stripped.endswith("."):
            return None
        return stripped[:-1] + "!"

    def _prefix_playful_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("ooh, fun", "ooh fun")):
            return None
        return "Ooh, fun — " + _lower_first(text)

    def _append_playful_suffix(self, text: str) -> Optional[str]:
        if "sounds fun" in text.lower():
            return None
        return text.rstrip().rstrip(".") + " - sounds fun!"

    def _add_teasing_aside(self, text: str) -> Optional[str]:
        if "(" in text:
            return None
        sentences = re.split(r'(?<=[.!?])(?<!\.\.) +', text.strip())
        if not sentences:
            return None
        first = sentences[0].rstrip('.!?')
        sentences[0] = first + " (wheee)."
        return " ".join(sentences)

    def _emphasize_fun_word(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\b(fun|play|adventure|puzzle)\b', re.IGNORECASE)
        m = pattern.search(text)
        if not m or m.group().isupper():
            return None
        return text[:m.start()] + m.group().upper() + text[m.end():]

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "tone": "Light-hearted",
            "approach": "Creative and fun",
            "humor": "Frequent",
            "engagement": "Playful and interactive",
        }
        return profile
