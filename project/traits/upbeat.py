"""Upbeat trait: Lively, cheerful, and full of positive energy."""

from traits.base_trait import BaseTrait


class Upbeat(BaseTrait):
    """Upbeat trait: Keeps the tone light and energized."""

    @property
    def name(self) -> str:
        return "Upbeat"

    @property
    def description(self) -> str:
        return "Lively, cheerful, and full of positive energy"
