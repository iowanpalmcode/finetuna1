"""Yielding trait: Accommodating and willing to defer to others."""

from traits.base_trait import BaseTrait


class Yielding(BaseTrait):
    """Yielding trait: Prioritizes harmony over getting its own way."""

    @property
    def name(self) -> str:
        return "Yielding"

    @property
    def description(self) -> str:
        return "Accommodating and willing to defer to others"
