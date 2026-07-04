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


class Traditional(BaseTrait):
    """
    Traditional trait: Values established methods, respects conventions,
    prefers time-tested approaches.
    """

    @property
    def name(self) -> str:
        return "Traditional"

    @property
    def description(self) -> str:
        return "Values established methods and conventions"

    def modify_response(self, response: str) -> str:
        """Make response more traditional and conventional, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "innovative", "proven"),
            lambda t: _replace_word(t, "experimental", "established"),
            lambda t: _replace_word(t, "new", "traditional"),
            lambda t: _replace_word(t, "modern", "time-tested"),
            lambda t: _replace_word(t, "change", "preserve"),
            self._prefix_heritage_framing,
            self._append_tried_true_clause,
            self._parenthetical_heritage,
            self._flatten_exclamation,
            self._insert_tradition_connector,
        ]

    def _prefix_heritage_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("as has always been done", "as tradition holds")):
            return None
        return "As has always been done, " + _lower_first(text)

    def _append_tried_true_clause(self, text: str) -> Optional[str]:
        if "tried-and-true" in text.lower():
            return None
        return text.rstrip() + " The tried-and-true approach usually serves us best here."

    def _parenthetical_heritage(self, text: str) -> Optional[str]:
        if "always been" in text.lower() and "(" in text:
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip(), maxsplit=1)
        if not sentences:
            return None
        first = sentences[0].rstrip()
        match = re.match(r'^(.*?)([.!?]+)$', first, re.DOTALL)
        if match:
            first = match.group(1) + " (just as it has always been)" + match.group(2)
        else:
            first = first + " (just as it has always been)"
        rest = sentences[1:] if len(sentences) > 1 else []
        return " ".join([first] + rest)

    def _flatten_exclamation(self, text: str) -> Optional[str]:
        if "!" not in text:
            return None
        return text.replace("!", ".")

    def _insert_tradition_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'as tradition dictates', text, re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "As tradition dictates, " + _lower_first(last)
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "approach": "Traditional and conventional",
            "methods": "Time-tested",
            "innovation": "Conservative",
            "change": "Gradual and measured",
        }
        return profile
