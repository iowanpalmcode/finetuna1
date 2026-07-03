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


class Organized(BaseTrait):
    """
    Organized trait: Structured approach, systematic planning,
    preferences for order and clear processes.
    """

    @property
    def name(self) -> str:
        return "Organized"

    @property
    def description(self) -> str:
        return "Structured and systematic in approach"

    def modify_response(self, response: str) -> str:
        """Make response more structured and organized, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "plan", "structured plan"),
            lambda t: _replace_word(t, "list", "checklist"),
            lambda t: _replace_word(t, "messy", "disorganized"),
            lambda t: _replace_word(t, "handle", "methodically handle"),
            lambda t: _replace_word(t, "figure out", "systematically work through"),
            self._prefix_structured_framing,
            self._append_step_by_step_suffix,
            self._parenthetical_priority_aside,
            self._emphasize_structure_word,
            self._numbered_list_sentences,
        ]

    def _prefix_structured_framing(self, text: str) -> Optional[str]:
        if text.lower().startswith(("here's the structured approach", "step 1", "1.")):
            return None
        return "Here's the structured approach: " + _lower_first(text)

    def _append_step_by_step_suffix(self, text: str) -> Optional[str]:
        if "step by step" in text.lower() or "step-by-step" in text.lower():
            return None
        return text.rstrip() + " Let's lay this out step by step."

    def _parenthetical_priority_aside(self, text: str) -> Optional[str]:
        if "(" in text:
            return None
        sentences = re.split(r'(?<=[.!?])(?<!\.\.) +', text.strip())
        if not sentences:
            return None
        first = sentences[0].rstrip('.!?')
        sentences[0] = first + " (in priority order)."
        return " ".join(sentences)

    def _emphasize_structure_word(self, text: str) -> Optional[str]:
        pattern = re.compile(r'\b(structure|organized|system|process)\b', re.IGNORECASE)
        m = pattern.search(text)
        if not m or m.group().isupper():
            return None
        word = m.group()
        return text[:m.start()] + word.upper() + text[m.end():]

    def _numbered_list_sentences(self, text: str) -> Optional[str]:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])(?<!\.\.) +', text.strip()) if s.strip()]
        if len(sentences) < 3:
            return None
        if re.match(r'^\d+\.', sentences[0]):
            return None
        return " ".join(f"{i + 1}. {s}" for i, s in enumerate(sentences))

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "structure": "Highly organized",
            "planning": "Systematic",
            "approach": "Process-oriented",
            "flexibility": "Prefers established systems",
        }
        return profile
