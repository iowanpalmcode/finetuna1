"""Creative trait: Imaginative and innovative thinking."""

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


class Creative(BaseTrait):
    """
    Creative trait: The agent thinks outside the box and generates novel ideas.
    Embraces innovation and unconventional solutions.
    """

    @property
    def name(self) -> str:
        return "Creative"

    @property
    def description(self) -> str:
        return "Imaginative, innovative, and unconventional"

    def modify_response(self, response: str) -> str:
        """Enhance responses with creative flair, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "idea", "visionary concept"),
            lambda t: _replace_word(t, "approach", "creative strategy"),
            lambda t: _replace_word(t, "solution", "imaginative solution"),
            lambda t: _replace_word(t, "normal", "novel"),
            lambda t: _replace_word(t, "plan", "blueprint for something bold"),
            self._sharpen_ending,
            self._prefix_creative_opener,
            self._append_possibilities_suffix,
            self._insert_whatif_aside,
            self._insert_or_reframe_connector,
        ]

    def _sharpen_ending(self, text: str) -> Optional[str]:
        if not text.rstrip().endswith("."):
            return None
        stripped = text.rstrip()
        return stripped[:-1] + "!"

    def _prefix_creative_opener(self, text: str) -> Optional[str]:
        if text.lower().startswith(("here's an unconventional thought", "picture this")):
            return None
        return "Here's an unconventional thought: " + _lower_first(text)

    def _append_possibilities_suffix(self, text: str) -> Optional[str]:
        if "endless possibilities" in text.lower():
            return None
        return text.rstrip() + " There are endless possibilities here!"

    def _insert_whatif_aside(self, text: str) -> Optional[str]:
        if "flipped this entirely" in text.lower():
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if not sentences:
            return None
        first = sentences[0].rstrip()
        match = re.match(r'^(.*?)([.!?]+)$', first, re.DOTALL)
        if match:
            sentences[0] = match.group(1) + " (what if we flipped this entirely?)" + match.group(2)
        else:
            sentences[0] = first + " (what if we flipped this entirely?)"
        return " ".join(sentences)

    def _insert_or_reframe_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if "thinking outside the box" in text.lower():
            return None
        last = sentences[-1]
        sentences[-1] = "Or, thinking outside the box, " + _lower_first(last)
        return " ".join(sentences)
