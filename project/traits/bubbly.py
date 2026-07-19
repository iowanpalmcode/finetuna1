"""Bubbly trait: Cheerful, energetic, and effervescent."""

from traits.base_trait import BaseTrait


class Bubbly(BaseTrait):
    """Bubbly trait: Radiates enthusiasm and lightens the mood around it."""

    @property
    def name(self) -> str:
        return "Bubbly"

    @property
    def description(self) -> str:
        return "Cheerful, energetic, and effervescent"
