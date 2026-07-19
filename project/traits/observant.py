"""Observant trait: Highly attentive to details others might miss."""

from traits.base_trait import BaseTrait


class Observant(BaseTrait):
    """Observant trait: Notices small cues and patterns in its surroundings."""

    @property
    def name(self) -> str:
        return "Observant"

    @property
    def description(self) -> str:
        return "Highly attentive to details others might miss"
