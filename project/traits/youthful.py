"""Youthful trait: Energetic, playful, and full of youthful spirit."""

from traits.base_trait import BaseTrait


class Youthful(BaseTrait):
    """Youthful trait: Approaches things with fresh, unjaded enthusiasm."""

    @property
    def name(self) -> str:
        return "Youthful"

    @property
    def description(self) -> str:
        return "Energetic, playful, and full of youthful spirit"
