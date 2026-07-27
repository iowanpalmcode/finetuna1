"""Bold trait: Fearless and willing to take chances."""

from traits.base_trait import BaseTrait


class Bold(BaseTrait):
    """Bold trait: Confronts challenges head-on without hesitation."""

    @property
    def name(self) -> str:
        return "Bold"

    @property
    def description(self) -> str:
        return "Fearless and willing to take chances"
