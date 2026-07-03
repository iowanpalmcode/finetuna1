from traits.base_trait import BaseTrait


class Chaotic(BaseTrait):
    """
    Chaotic trait: Spontaneous and flexible, embraces disorder,
    adaptive to changing circumstances.
    """

    @property
    def name(self) -> str:
        return "Chaotic"

    @property
    def description(self) -> str:
        return "Spontaneous and adaptable to change"

    def modify_response(self, response: str) -> str:
        """Make response more spontaneous and flexible."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "planned ": "spontaneous ",
            "structured ": "flexible ",
            "systematic ": "improvised ",
            "always ": "sometimes ",
            "must ": "could ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if modified == response:
            modified += " Or who knows, we could shake things up entirely!"

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "structure": "Spontaneous",
            "planning": "Adaptive",
            "approach": "Flexible",
            "flexibility": "High - embraces change",
        }
        return profile
