"""Lazy trait: Prefers minimal effort and shortcuts."""

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


class Lazy(BaseTrait):
    """
    Lazy trait: The agent prefers efficiency through minimal effort.
    When combined with intelligence, seeks smart shortcuts.
    """

    @property
    def name(self) -> str:
        return "Lazy"

    @property
    def description(self) -> str:
        return "Prefers minimal effort and efficient shortcuts"

    def modify_response(self, response: str) -> str:
        """Cut corners and trim effort out of responses, scaled by intensity."""
        if len(response.split()) < 5:
            return response

        return self.apply_modifications(response, self._modifications())

    def _modifications(self) -> List[Callable[[str], Optional[str]]]:
        return [
            self._trim_to_three_sentences,
            self._trim_to_two_sentences,
            self._drop_qualifiers,
            lambda t: _replace_word(t, "thoroughly", "quickly"),
            lambda t: _replace_word(t, "carefully", "loosely"),
            lambda t: _replace_word(t, "comprehensive", "quick"),
            lambda t: _replace_word(t, "investigate", "check"),
            self._strip_first_subordinate_clause,
            self._shrug_prefix,
            self._append_good_enough,
        ]

    def _trim_to_three_sentences(self, text: str) -> Optional[str]:
        sentences = text.split('. ')
        if len(sentences) <= 3:
            return None
        joined = '. '.join(sentences[:3])
        if not joined.endswith(('.', '!', '?')):
            joined += '.'
        return joined

    def _trim_to_two_sentences(self, text: str) -> Optional[str]:
        sentences = text.split('. ')
        if len(sentences) <= 2:
            return None
        joined = '. '.join(sentences[:2])
        if not joined.endswith(('.', '!', '?')):
            joined += '.'
        return joined

    def _drop_qualifiers(self, text: str) -> Optional[str]:
        pattern = re.compile(
            r'\b(essentially|actually|basically|in my opinion|to be honest|admittedly)\b,?\s*',
            re.IGNORECASE,
        )
        if not pattern.search(text):
            return None
        result = pattern.sub("", text, count=1)
        if not result:
            return None
        return result[0].upper() + result[1:]

    def _strip_first_subordinate_clause(self, text: str) -> Optional[str]:
        sentences = re.split(r'(?<=[.!?]) +', text.strip(), maxsplit=1)
        first = sentences[0]
        if ',' not in first:
            return None
        comma_index = first.index(',')
        before = first[:comma_index]
        after = first[comma_index + 1:].strip()
        # Only drop a trailing clause when there's a real clause on each side,
        # so we don't chop a leading connector down to a fragment.
        if len(before.split()) < 3 or len(after) < 4:
            return None
        end_punct = first.rstrip()[-1] if first.rstrip()[-1] in ".!?" else "."
        trimmed_first = before.rstrip() + end_punct
        rest = sentences[1] if len(sentences) > 1 else ""
        return (trimmed_first + " " + rest).strip() if rest else trimmed_first

    def _shrug_prefix(self, text: str) -> Optional[str]:
        if text.lower().startswith(("eh, ", "eh ")):
            return None
        return "Eh, " + _lower_first(text)

    def _append_good_enough(self, text: str) -> Optional[str]:
        if "good enough" in text.lower():
            return None
        return text.rstrip() + " Good enough, honestly."
