"""Curious trait: Inquisitive and eager to learn."""

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


class Curious(BaseTrait):
    """
    Curious trait: The agent is inquisitive and loves exploring ideas.
    Asks probing questions and seeks deeper understanding.
    """

    @property
    def name(self) -> str:
        return "Curious"

    @property
    def description(self) -> str:
        return "Inquisitive, eager to explore and understand deeply"

    def modify_response(self, response: str) -> str:
        """Add curious elements: questions and exploration, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            lambda t: _replace_word(t, "think", "wonder if"),
            lambda t: _replace_word(t, "know", "am curious about whether"),
            lambda t: _replace_word(t, "good", "intriguing"),
            lambda t: _replace_word(t, "interesting", "fascinating"),
            lambda t: _replace_word(t, "look at", "dig into"),
            self._prefix_curiosity,
            self._append_wondering_question,
            self._add_pondering_pause,
            self._emphasize_key_word,
            self._insert_wondering_connector,
        ]

    def _prefix_curiosity(self, text: str) -> Optional[str]:
        if text.lower().startswith(("i wonder", "i'm curious", "curiously")):
            return None
        return "I'm curious — " + _lower_first(text)

    def _append_wondering_question(self, text: str) -> Optional[str]:
        if "?" in text:
            return None
        return text.rstrip() + " What's really driving this, I wonder?"

    def _add_pondering_pause(self, text: str) -> Optional[str]:
        if "..." in text or "…" in text:
            return None
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        sentences[0] = sentences[0].rstrip(".!?") + "..."
        return " ".join(sentences)

    def _emphasize_key_word(self, text: str) -> Optional[str]:
        for word in ["fascinating", "interesting", "curious", "intriguing"]:
            pattern = re.compile(r'\b' + word + r'\b', re.IGNORECASE)
            match = pattern.search(text)
            if match and text[max(0, match.start() - 1):match.start()] != "*":
                return text[:match.start()] + "*" + match.group(0) + "*" + text[match.end():]
        return None

    def _insert_wondering_connector(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if len(sentences) < 2:
            return None
        if re.search(r'\bwonder\b', text, re.IGNORECASE):
            return None
        last = sentences[-1]
        sentences[-1] = "Which makes me wonder — " + _lower_first(last)
        return " ".join(sentences)
