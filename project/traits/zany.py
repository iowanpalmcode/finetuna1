"""Zany trait: Wildly funny, eccentric, and unpredictable in a comedic way."""

from traits.base_trait import BaseTrait


class Zany(BaseTrait):
    """Zany trait: Leans into the absurd for a laugh."""

    @property
    def name(self) -> str:
        return "Zany"

    @property
    def description(self) -> str:
        return "Wildly funny, eccentric, and unpredictable in a comedic way"
