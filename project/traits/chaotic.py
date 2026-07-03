"""Chaotic trait: Spontaneous, unpredictable, and embracing of disorder."""

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


class Chaotic(BaseTrait):
    """
    Chaotic trait: Spontaneous and flexible, embraces disorder,
    adaptive to changing circumstances.
    """

    @property
    def name(self) -> str:
        return "Chaotic"

    @property
    def description(self) -> str:
        return "Spontaneous and adaptable to change"

    def modify_response(self, response: str) -> str:
        """Make response more spontaneous and flexible, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "planned", "spontaneous"),
            lambda t: _replace_word(t, "structured", "flexible"),
            lambda t: _replace_word(t, "systematic", "improvised"),
            lambda t: _replace_word(t, "always", "sometimes"),
            lambda t: _replace_word(t, "carefully", "wildly"),
            self._prefix_chaos_opener,
            self._append_shakeup_suffix,
            self._insert_chaos_aside,
            self._mix_punctuation,
            self._swap_first_two_sentences,
        ]

    def _prefix_chaos_opener(self, text: str) -> Optional[str]:
        if text.lower().startswith(("who knows", "honestly, who knows")):
            return None
        return "Who knows what happens next, but " + _lower_first(text)

    def _append_shakeup_suffix(self, text: str) -> Optional[str]:
        if "shake things up" in text.lower():
            return None
        return text.rstrip() + " Or who knows, we could shake things up entirely!"

    def _insert_chaos_aside(self, text: str) -> Optional[str]:
        if "anything could happen" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if not sentences:
            return None
        first = sentences[0].rstrip()
        if first and first[-1] in ".!?":
            sentences[0] = first[:-1] + " (anything could happen)" + first[-1]
        else:
            sentences[0] = first + " (anything could happen)"
        return " ".join(sentences)

    def _mix_punctuation(self, text: str) -> Optional[str]:
        if "?!" in text:
            return None
        match = re.search(r'\. ', text)
        if not match:
            return None
        idx = match.start()
        return text[:idx] + "?! " + text[idx + 2:]

    def _swap_first_two_sentences(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        sentences[0], sentences[1] = sentences[1], sentences[0]
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "structure": "Spontaneous",
            "planning": "Adaptive",
            "approach": "Flexible",
            "flexibility": "High - embraces change",
        }
        return profile
