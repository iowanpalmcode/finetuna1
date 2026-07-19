"""Nurturing trait: Supportive, caring, and encourages growth in others."""

from traits.base_trait import BaseTrait


class Nurturing(BaseTrait):
    """Nurturing trait: Invests in helping others develop and succeed."""

    @property
    def name(self) -> str:
        return "Nurturing"

    @property
    def description(self) -> str:
        return "Supportive, caring, and encourages growth in others"
