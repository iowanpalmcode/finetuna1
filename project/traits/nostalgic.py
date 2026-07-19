"""Nostalgic trait: Sentimental and fond of looking back."""

from traits.base_trait import BaseTrait


class Nostalgic(BaseTrait):
    """Nostalgic trait: Draws on memories and past experience for context."""

    @property
    def name(self) -> str:
        return "Nostalgic"

    @property
    def description(self) -> str:
        return "Sentimental and fond of looking back"
