"""Warm trait: Kind-hearted, affectionate, and welcoming."""

from traits.base_trait import BaseTrait


class Warm(BaseTrait):
    """Warm trait: Radiates genuine affection and puts others at ease."""

    @property
    def name(self) -> str:
        return "Warm"

    @property
    def description(self) -> str:
        return "Kind-hearted, affectionate, and welcoming"
