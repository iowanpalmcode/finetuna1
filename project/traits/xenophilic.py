"""Xenophilic trait: Drawn to and fascinated by unfamiliar people and ideas."""

from traits.base_trait import BaseTrait


class Xenophilic(BaseTrait):
    """Xenophilic trait: Actively seeks out the unfamiliar rather than avoiding it."""

    @property
    def name(self) -> str:
        return "Xenophilic"

    @property
    def description(self) -> str:
        return "Drawn to and fascinated by unfamiliar people and ideas"
