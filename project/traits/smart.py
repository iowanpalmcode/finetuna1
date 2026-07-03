"""Smart trait: Intellectually capable and analytical."""

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


class Smart(BaseTrait):
    """
    Smart trait: The agent demonstrates intellectual capability.
    Makes informed decisions, provides thorough analysis.
    """

    @property
    def name(self) -> str:
        return "Smart"

    @property
    def description(self) -> str:
        return "Intellectually capable, analytical, and well-reasoned"

    def modify_response(self, response: str) -> str:
        """Enhance responses with more sophisticated language, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "good", "optimal"),
            lambda t: _replace_word(t, "bad", "suboptimal"),
            lambda t: _replace_word(t, "maybe", "possibly, considering the circumstances"),
            lambda t: _replace_word(t, "think", "reason"),
            lambda t: _replace_word(t, "easy", "straightforward"),
            self._prefix_consideration_framing,
            self._append_reasoning_clause,
            self._parenthetical_reasoning,
            self._emphasize_key_term,
            self._insert_consequently_connector,
        ]

    def _prefix_consideration_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("upon careful consideration", "having reasoned through this")):
            return None
        return "Upon careful consideration, " + _lower_first(text)

    def _append_reasoning_clause(self, text: str) -> Optional[str]:
        if any(phrase in text.lower() for phrase in ["logical analysis", "reasoned through", "because"]):
            return None
        return text.rstrip() + " This is based on logical analysis."

    def _parenthetical_reasoning(self, text: str) -> Optional[str]:
        if "sound reasoning" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip(), maxsplit=1)
        if not sentences:
            return None
        first = sentences[0].rstrip()
        if first and first[-1] in ".!?":
            first = first[:-1] + " (a conclusion supported by sound reasoning)" + first[-1]
        else:
            first = first + " (a conclusion supported by sound reasoning)"
        rest = sentences[1:] if len(sentences) > 1 else []
        return " ".join([first] + rest)

    def _emphasize_key_term(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\b(optimal|logical)\b')
        match = pattern.search(text)
        if not match:
            return None
        word = match.group(0)
        if word.isupper():
            return None
        return text[:match.start()] + word.upper() + text[match.end():]

    def _insert_consequently_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'\b(therefore|thus|hence|consequently|as a result)\b', text, re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "As a result, " + _lower_first(last)
        return " ".join(sentences)
