"""Jovial trait: Cheerful, hearty, and full of good humor."""

from traits.base_trait import BaseTrait


class Jovial(BaseTrait):
    """Jovial trait: Brings warmth and laughter to any exchange."""

    @property
    def name(self) -> str:
        return "Jovial"

    @property
    def description(self) -> str:
        return "Cheerful, hearty, and full of good humor"
