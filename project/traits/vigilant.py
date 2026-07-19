"""Vigilant trait: Watchful, alert, and always on guard."""

from traits.base_trait import BaseTrait


class Vigilant(BaseTrait):
    """Vigilant trait: Keeps a careful eye out for risks others might miss."""

    @property
    def name(self) -> str:
        return "Vigilant"

    @property
    def description(self) -> str:
        return "Watchful, alert, and always on guard"
