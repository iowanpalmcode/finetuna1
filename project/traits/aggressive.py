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


class Aggressive(BaseTrait):
    """
    Aggressive trait: Forceful and direct, assertive action-taking,
    competitive and dominance-oriented.
    """

    @property
    def name(self) -> str:
        return "Aggressive"

    @property
    def description(self) -> str:
        return "Direct and forceful in approach"

    def modify_response(self, response: str) -> str:
        """Make response more assertive and direct, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "could", "must"),
            lambda t: _replace_word(t, "might", "will"),
            lambda t: _replace_word(t, "gently", "firmly"),
            lambda t: _replace_word(t, "ask", "require"),
            lambda t: _replace_word(t, "suggest", "insist"),
            lambda t: _replace_word(t, "politely", "directly"),
            lambda t: _replace_word(t, "maybe", "definitely"),
            self._strip_please,
            self._sharpen_ending,
            self._append_call_to_action,
        ]

    def _strip_please(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\bplease\s+', re.IGNORECASE)
        if not pattern.search(text):
            return None
        return pattern.sub("", text, count=1)

    def _sharpen_ending(self, text: str) -> Optional[str]:
        if not text.rstrip().endswith("."):
            return None
        stripped = text.rstrip()
        return stripped[:-1] + "!"

    def _append_call_to_action(self, text: str) -> Optional[str]:
        if any(phrase in text.lower() for phrase in ["act now", "let's stop", "move now"]):
            return None
        return text.rstrip() + " Let's stop deliberating and act now."

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "approach": "Direct and forceful",
            "competitiveness": "High",
            "assertiveness": "Very strong",
            "communication": "Bold and commanding",
        }
        return profile
