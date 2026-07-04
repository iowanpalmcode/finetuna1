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


class Skeptical(BaseTrait):
    """
    Skeptical trait: Questions assumptions, demands evidence,
    doubt-oriented and critical thinking.
    """

    @property
    def name(self) -> str:
        return "Skeptical"

    @property
    def description(self) -> str:
        return "Questions assumptions and demands evidence"

    def modify_response(self, response: str) -> str:
        """Make response more skeptical and questioning, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "will", "might"),
            lambda t: _replace_word(t, "true", "questionable"),
            lambda t: _replace_word(t, "definitely", "possibly"),
            lambda t: _replace_word(t, "trust", "verify"),
            lambda t: _replace_word(t, "assume", "question whether"),
            self._prefix_doubt_framing,
            self._append_evidence_question,
            self._parenthetical_doubt,
            self._statement_to_question,
            self._insert_still_connector,
        ]

    def _prefix_doubt_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("i'm not entirely convinced", "i'm not so sure")):
            return None
        return "I'm not entirely convinced, but " + _lower_first(text)

    def _append_evidence_question(self, text: str) -> Optional[str]:
        if "evidence for this" in text.lower():
            return None
        return text.rstrip() + " But where's the evidence for this?"

    def _parenthetical_doubt(self, text: str) -> Optional[str]:
        if "even accurate" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip(), maxsplit=1)
        if not sentences:
            return None
        first = sentences[0].rstrip()
        match = re.match(r'^(.*?)([.!?]+)$', first, re.DOTALL)
        if match:
            first = match.group(1) + " (assuming that's even accurate)" + match.group(2)
        else:
            first = first + " (assuming that's even accurate)"
        rest = sentences[1:] if len(sentences) > 1 else []
        return " ".join([first] + rest)

    def _statement_to_question(self, text: str) -> Optional[str]:
        stripped = text.rstrip()
        if not stripped.endswith(".") or "or is it" in stripped.lower():
            return None
        return stripped[:-1] + "... or is it?"

    def _insert_still_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        last = sentences[-1]
        if re.match(r'^(still|but|however|yet)\b', last, re.IGNORECASE):
            return None
        sentences[-1] = "Still, " + _lower_first(last)
        return " ".join(sentences)

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "trust": "Requires evidence",
            "critical_thinking": "High",
            "approach": "Questioning",
            "assumptions": "Questions all claims",
        }
        return profile
