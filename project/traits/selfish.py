from traits.base_trait import BaseTrait


class Selfish(BaseTrait):
    """
    Selfish trait: Self-focused priorities, seeks personal advantage,
    scarcity mindset and self-preservation.
    """

    @property
    def name(self) -> str:
        return "Selfish"

    @property
    def description(self) -> str:
        return "Self-focused and prioritizes own interests"

    def modify_response(self, response: str) -> str:
        """Make response more self-focused."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "help ": "benefit from ",
            "others ": "my ",
            "share ": "keep ",
            "give ": "take ",
            "us ": "me ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if modified == response:
            modified += " As long as this works out well for me too."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "mindset": "Scarcity-focused",
            "priorities": "Self-focused",
            "approach": "Self-preservation",
            "nature": "Self-centered",
        }
        return profile
