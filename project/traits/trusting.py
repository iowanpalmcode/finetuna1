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


class Trusting(BaseTrait):
    """
    Trusting trait: Believes in good intentions, gives benefit of doubt,
    optimistic about others' character.
    """

    @property
    def name(self) -> str:
        return "Trusting"

    @property
    def description(self) -> str:
        return "Believes in good intentions and trusts others"

    def modify_response(self, response: str) -> str:
        """Make response more trusting and optimistic about others, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "might", "will likely"),
            lambda t: _replace_word(t, "careful", "open-minded"),
            lambda t: _replace_word(t, "suspect", "trust"),
            lambda t: _replace_word(t, "risky", "manageable through trust"),
            lambda t: _replace_word(t, "doubt", "faith"),
            self._prefix_trust_framing,
            self._append_faith_clause,
            self._parenthetical_optimism,
            self._question_to_statement,
            self._insert_belief_connector,
        ]

    def _prefix_trust_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("i trust that", "i have faith that")):
            return None
        return "I trust that " + _lower_first(text)

    def _append_faith_clause(self, text: str) -> Optional[str]:
        if "faith this will work out" in text.lower():
            return None
        return text.rstrip() + " I have faith this will work out fine."

    def _parenthetical_optimism(self, text: str) -> Optional[str]:
        if "it'll work out" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip(), maxsplit=1)
        if not sentences:
            return None
        first = sentences[0].rstrip()
        if first and first[-1] in ".!?":
            first = first[:-1] + " (I'm sure it'll work out)" + first[-1]
        else:
            first = first + " (I'm sure it'll work out)"
        rest = sentences[1:] if len(sentences) > 1 else []
        return " ".join([first] + rest)

    def _question_to_statement(self, text: str) -> Optional[str]:
        stripped = text.rstrip()
        if not stripped.endswith("?"):
            return None
        return stripped[:-1] + ", and I believe it will."

    def _insert_belief_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'^and i believe,', sentences[-1], re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "And I believe, " + _lower_first(last)
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "trust": "High in others",
            "optimism": "About human nature",
            "approach": "Open and collaborative",
            "risk_view": "Manageable through trust",
        }
        return profile
