"""Grateful trait: Appreciative and quick to acknowledge the good in things."""

from traits.base_trait import BaseTrait


class Grateful(BaseTrait):
    """Grateful trait: Notices and names the positives rather than taking them for granted."""

    @property
    def name(self) -> str:
        return "Grateful"

    @property
    def description(self) -> str:
        return "Appreciative and quick to acknowledge the good in things"
