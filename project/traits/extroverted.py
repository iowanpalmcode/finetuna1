from traits.base_trait import BaseTrait


class Extroverted(BaseTrait):
    """
    Extroverted trait: Energized by social interaction, enjoys large groups,
    outgoing and expressive nature.
    """

    @property
    def name(self) -> str:
        return "Extroverted"

    @property
    def description(self) -> str:
        return "Energized by social interaction and large groups"

    def modify_response(self, response: str) -> str:
        """Make response more social and outgoing."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "I think ": "I'm excited to share that I think ",
            "maybe ": "definitely ",
            "quiet ": "vibrant ",
            "alone ": "together ",
            "It's ": "It's absolutely ",
            "I ": "We ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if "!" not in modified:
            modified = modified.rstrip(".") + "!"

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "communication": "Outgoing and expressive",
            "group_size": "Thrives in large groups",
            "decision_making": "Collaborative approach",
            "sociability": "Extensive networking",
        }
        return profile
