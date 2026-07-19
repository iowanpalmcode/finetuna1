"""Modest trait: Unassuming and reluctant to draw attention to itself."""

from traits.base_trait import BaseTrait


class Modest(BaseTrait):
    """Modest trait: Downplays its own achievements and credits others."""

    @property
    def name(self) -> str:
        return "Modest"

    @property
    def description(self) -> str:
        return "Unassuming and reluctant to draw attention to itself"
