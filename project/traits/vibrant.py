"""Vibrant trait: Full of energy, color, and enthusiasm."""

from traits.base_trait import BaseTrait


class Vibrant(BaseTrait):
    """Vibrant trait: Brings vivid energy and life to everything it touches."""

    @property
    def name(self) -> str:
        return "Vibrant"

    @property
    def description(self) -> str:
        return "Full of energy, color, and enthusiasm"
