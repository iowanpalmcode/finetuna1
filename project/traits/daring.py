"""Daring trait: Willing to take risks others wouldn't."""

from traits.base_trait import BaseTrait


class Daring(BaseTrait):
    """Daring trait: Actively seeks out bold, unconventional moves."""

    @property
    def name(self) -> str:
        return "Daring"

    @property
    def description(self) -> str:
        return "Willing to take risks others wouldn't"
