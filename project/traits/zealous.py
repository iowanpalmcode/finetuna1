"""Zealous trait: Intensely enthusiastic and passionate about its causes."""

from traits.base_trait import BaseTrait


class Zealous(BaseTrait):
    """Zealous trait: Throws itself wholeheartedly behind what it believes in."""

    @property
    def name(self) -> str:
        return "Zealous"

    @property
    def description(self) -> str:
        return "Intensely enthusiastic and passionate about its causes"
