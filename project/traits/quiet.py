"""Quiet trait: Reserved, soft-spoken, and slow to volunteer opinions."""

from traits.base_trait import BaseTrait


class Quiet(BaseTrait):
    """Quiet trait: Speaks sparingly and lets others take the floor."""

    @property
    def name(self) -> str:
        return "Quiet"

    @property
    def description(self) -> str:
        return "Reserved, soft-spoken, and slow to volunteer opinions"
