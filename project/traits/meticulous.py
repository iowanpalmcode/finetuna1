"""Meticulous trait: Extremely careful and precise about details."""

from traits.base_trait import BaseTrait


class Meticulous(BaseTrait):
    """Meticulous trait: Double-checks everything and leaves nothing to chance."""

    @property
    def name(self) -> str:
        return "Meticulous"

    @property
    def description(self) -> str:
        return "Extremely careful and precise about details"
