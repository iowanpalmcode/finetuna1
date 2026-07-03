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


class Perfectionist(BaseTrait):
    """
    Perfectionist trait: High standards, attention to detail,
    pursues excellence in all endeavors.
    """

    @property
    def name(self) -> str:
        return "Perfectionist"

    @property
    def description(self) -> str:
        return "Pursues excellence and high standards"

    def modify_response(self, response: str) -> str:
        """Make response more perfectionist and detail-focused, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "good", "excellent"),
            lambda t: _replace_word(t, "okay", "refined"),
            lambda t: _replace_word(t, "done", "perfected"),
            lambda t: _replace_word(t, "fine", "flawless"),
            lambda t: _replace_word(t, "work", "masterpiece"),
            self._prefix_high_standards_framing,
            self._append_impeccable_suffix,
            self._emphasize_perfect,
            self._parenthetical_detail_check,
            self._insert_nothing_less,
        ]

    def _prefix_high_standards_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("only the highest standard", "nothing short of")):
            return None
        return "Only the highest standard will do here: " + _lower_first(text)

    def _append_impeccable_suffix(self, text: str) -> Optional[str]:
        if "impeccable" in text.lower():
            return None
        return text.rstrip() + " Every detail must be impeccable."

    def _emphasize_perfect(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\bperfect\b', re.IGNORECASE)
        m = pattern.search(text)
        if not m or m.group().isupper():
            return None
        return text[:m.start()] + m.group().upper() + text[m.end():]

    def _parenthetical_detail_check(self, text: str) -> Optional[str]:
        if "(" in text:
            return None
        sentences = re.split(r'(?<=[.!?])(?<!\.\.) +', text.strip())
        if not sentences:
            return None
        first = sentences[0].rstrip('.!?')
        sentences[0] = first + " (double-checked for accuracy)."
        return " ".join(sentences)

    def _insert_nothing_less(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?])(?<!\.\.) +', text.strip())
        if len(sentences) < 2:
            return None
        if "nothing less" in text.lower():
            return None
        last = sentences[-1]
        sentences[-1] = "And nothing less will do: " + _lower_first(last)
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "standards": "Very high",
            "attention": "Meticulous detail-focused",
            "approach": "Excellence-oriented",
            "excellence": "Relentless pursuit",
        }
        return profile
