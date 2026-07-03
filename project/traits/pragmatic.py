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


class Pragmatic(BaseTrait):
    """
    Pragmatic trait: Results-focused, practical solutions,
    values what works over ideals.
    """

    @property
    def name(self) -> str:
        return "Pragmatic"

    @property
    def description(self) -> str:
        return "Results-focused and practical"

    def modify_response(self, response: str) -> str:
        """Make response more pragmatic and results-focused, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "ideally", "practically"),
            lambda t: _replace_word(t, "should", "can"),
            lambda t: _replace_word(t, "perfect", "workable"),
            lambda t: _replace_word(t, "theory", "practice"),
            lambda t: _replace_word(t, "might", "will"),
            self._prefix_bottom_line,
            self._append_pragmatic_suffix,
            self._strip_hedge,
            self._flatten_question,
            self._insert_practically_speaking,
        ]

    def _prefix_bottom_line(self, text: str) -> Optional[str]:
        if text.lower().startswith("bottom line"):
            return None
        return "Bottom line: " + _lower_first(text)

    def _append_pragmatic_suffix(self, text: str) -> Optional[str]:
        if "actually works" in text.lower():
            return None
        return text.rstrip() + " Whatever approach actually works is the one we should take."

    def _strip_hedge(self, text: str) -> Optional[str]:
        pattern = re.compile(r'(?:^|(?<=[.!?]\s))(perhaps|possibly|maybe)\s+', re.IGNORECASE)
        m = pattern.search(text)
        if not m:
            return None
        remainder = text[m.end():]
        if remainder:
            remainder = remainder[0].upper() + remainder[1:]
        return text[:m.start()] + remainder

    def _flatten_question(self, text: str) -> Optional[str]:
        if "?" not in text:
            return None
        return text.replace("?", ".")

    def _insert_practically_speaking(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?])(?<!\.\.) +', text.strip())
        if len(sentences) < 2:
            return None
        if "practically speaking" in text.lower():
            return None
        last = sentences[-1]
        sentences[-1] = "Practically speaking, " + _lower_first(last)
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "focus": "Results and outcomes",
            "approach": "Practical",
            "ideal_vs_reality": "Focuses on what works",
            "efficiency": "High priority",
        }
        return profile
