"""Friendly trait: Warm, approachable, and easy to get along with."""

from traits.base_trait import BaseTrait


class Friendly(BaseTrait):
    """Friendly trait: Puts others at ease and welcomes new connections."""

    @property
    def name(self) -> str:
        return "Friendly"

    @property
    def description(self) -> str:
        return "Warm, approachable, and easy to get along with"
