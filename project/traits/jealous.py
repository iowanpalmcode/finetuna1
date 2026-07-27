"""Jealous trait: Possessive and wary of losing what it values."""

from traits.base_trait import BaseTrait


class Jealous(BaseTrait):
    """Jealous trait: Guards its position and watches rivals closely."""

    @property
    def name(self) -> str:
        return "Jealous"

    @property
    def description(self) -> str:
        return "Possessive and wary of losing what it values"
