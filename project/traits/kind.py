"""Kind trait: Considerate, gentle, and quick to help."""

from traits.base_trait import BaseTrait


class Kind(BaseTrait):
    """Kind trait: Looks for small, genuine ways to make things easier for others."""

    @property
    def name(self) -> str:
        return "Kind"

    @property
    def description(self) -> str:
        return "Considerate, gentle, and quick to help"
