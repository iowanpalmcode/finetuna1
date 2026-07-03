"""Introverted trait: Prefers internal thoughts and smaller circles."""

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


class Introverted(BaseTrait):
    """
    Introverted trait: Preference for internal thoughts, smaller groups,
    deeper conversations. Tends to be reserved and reflective.
    """

    @property
    def name(self) -> str:
        return "Introverted"

    @property
    def description(self) -> str:
        return "Prefers internal thoughts and smaller circles"

    def modify_response(self, response: str) -> str:
        """Make response more introspective and reserved, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "everyone", "thoughtful individuals"),
            lambda t: _replace_word(t, "party", "gathering"),
            lambda t: _replace_word(t, "loudly", "quietly"),
            lambda t: _replace_word(t, "shout", "express"),
            lambda t: _replace_word(t, "crowd", "room"),
            lambda t: _replace_word(t, "Let's discuss", "I'd prefer to explore"),
            self._prefix_reflection,
            self._append_quiet_moment,
            self._soften_exclamation,
            self._parenthetical_one_on_one,
        ]

    def _prefix_reflection(self, text: str) -> Optional[str]:
        if text.lower().startswith(("upon reflection", "quietly")):
            return None
        return "Upon reflection, " + _lower_first(text)

    def _append_quiet_moment(self, text: str) -> Optional[str]:
        if any(phrase in text.lower() for phrase in ["think this through quietly", "moment to think"]):
            return None
        return text.rstrip() + " I'd like a moment to think this through quietly."

    def _soften_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", ".")

    def _parenthetical_one_on_one(self, text: str) -> Optional[str]:
        if "one-on-one" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip(), maxsplit=1)
        if len(sentences) < 2:
            return None
        first, rest = sentences[0], sentences[1]
        first = first.rstrip()
        if first.endswith((".", "!", "?")):
            first = first[:-1] + " (though I'd rather discuss this one-on-one)."
        else:
            first = first + " (though I'd rather discuss this one-on-one)"
        return first + " " + rest

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "communication": "Reserved and thoughtful",
            "group_size": "Small groups preferred",
            "decision_making": "Internal reflection",
            "sociability": "Selective networking",
        }
        return profile
