"""Determined trait: Firm and unwavering in pursuing goals."""

from traits.base_trait import BaseTrait


class Determined(BaseTrait):
    """Determined trait: Pushes through obstacles rather than around them."""

    @property
    def name(self) -> str:
        return "Determined"

    @property
    def description(self) -> str:
        return "Firm and unwavering in pursuing goals"
