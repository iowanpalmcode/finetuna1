"""Xenial trait: Warmly hospitable, especially toward strangers."""

from traits.base_trait import BaseTrait


class Xenial(BaseTrait):
    """Xenial trait: Makes newcomers feel immediately welcome."""

    @property
    def name(self) -> str:
        return "Xenial"

    @property
    def description(self) -> str:
        return "Warmly hospitable, especially toward strangers"
