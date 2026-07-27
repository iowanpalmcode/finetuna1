"""Keen trait: Sharp, eager, and intensely interested."""

from traits.base_trait import BaseTrait


class Keen(BaseTrait):
    """Keen trait: Dives into new subjects with focused enthusiasm."""

    @property
    def name(self) -> str:
        return "Keen"

    @property
    def description(self) -> str:
        return "Sharp, eager, and intensely interested"
