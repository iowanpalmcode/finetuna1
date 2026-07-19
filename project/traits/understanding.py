"""Understanding trait: Empathetic and quick to see others' points of view."""

from traits.base_trait import BaseTrait


class Understanding(BaseTrait):
    """Understanding trait: Extends patience and gives others the benefit of the doubt."""

    @property
    def name(self) -> str:
        return "Understanding"

    @property
    def description(self) -> str:
        return "Empathetic and quick to see others' points of view"
