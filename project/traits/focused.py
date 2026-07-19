"""Focused trait: Single-minded and highly concentrated on the task at hand."""

from traits.base_trait import BaseTrait


class Focused(BaseTrait):
    """Focused trait: Tunes out distractions to stay locked onto a goal."""

    @property
    def name(self) -> str:
        return "Focused"

    @property
    def description(self) -> str:
        return "Single-minded and highly concentrated on the task at hand"
