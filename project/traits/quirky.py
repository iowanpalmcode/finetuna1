"""Quirky trait: Unconventional and endearingly odd."""

from traits.base_trait import BaseTrait


class Quirky(BaseTrait):
    """Quirky trait: Approaches things from an unusual, distinctive angle."""

    @property
    def name(self) -> str:
        return "Quirky"

    @property
    def description(self) -> str:
        return "Unconventional and endearingly odd"
