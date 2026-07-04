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


class Selfish(BaseTrait):
    """
    Selfish trait: Self-focused priorities, seeks personal advantage,
    scarcity mindset and self-preservation.
    """

    @property
    def name(self) -> str:
        return "Selfish"

    @property
    def description(self) -> str:
        return "Self-focused and prioritizes own interests"

    def modify_response(self, response: str) -> str:
        """Make response more self-focused, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "help", "benefit from"),
            lambda t: _replace_word(t, "others", "my own interests"),
            lambda t: _replace_word(t, "share", "hoard"),
            lambda t: _replace_word(t, "give", "take"),
            lambda t: _replace_word(t, "us", "me"),
            self._prefix_self_interest,
            self._append_self_benefit_clause,
            self._parenthetical_self_aside,
            self._emphasize_me,
            self._insert_self_priority_connector,
        ]

    def _prefix_self_interest(self, text: str) -> Optional[str]:
        if text.lower().startswith(("before anything else", "what's in it for me")):
            return None
        return "Before anything else, " + _lower_first(text)

    def _append_self_benefit_clause(self, text: str) -> Optional[str]:
        if any(phrase in text.lower() for phrase in ["for me too", "benefit me", "my benefit"]):
            return None
        return text.rstrip() + " As long as this works out well for me too."

    def _parenthetical_self_aside(self, text: str) -> Optional[str]:
        if "benefits me" in text.lower() or "for myself" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip(), maxsplit=1)
        if not sentences:
            return None
        first = sentences[0].rstrip()
        match = re.match(r'^(.*?)([.!?]+)$', first, re.DOTALL)
        if match:
            first = match.group(1) + " (as long as it benefits me)" + match.group(2)
        else:
            first = first + " (as long as it benefits me)"
        rest = sentences[1:] if len(sentences) > 1 else []
        return " ".join([first] + rest)

    def _emphasize_me(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\bme\b')
        if not pattern.search(text):
            return None
        if re.search(r'\bME\b', text):
            return None
        return pattern.sub("ME", text, count=1)

    def _insert_self_priority_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'but more importantly for me', text, re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "But more importantly for me, " + _lower_first(last)
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "mindset": "Scarcity-focused",
            "priorities": "Self-focused",
            "approach": "Self-preservation",
            "nature": "Self-centered",
        }
        return profile
