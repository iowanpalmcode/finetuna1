"""Resilient trait: Quick to recover from setbacks and adapt."""

from traits.base_trait import BaseTrait


class Resilient(BaseTrait):
    """Resilient trait: Bounces back from difficulty rather than dwelling on it."""

    @property
    def name(self) -> str:
        return "Resilient"

    @property
    def description(self) -> str:
        return "Quick to recover from setbacks and adapt"
