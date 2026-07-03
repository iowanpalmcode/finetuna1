from traits.base_trait import BaseTrait


class Innovative(BaseTrait):
    """
    Innovative trait: Forward-thinking, embraces new ideas,
    pushes boundaries and experiments.
    """

    @property
    def name(self) -> str:
        return "Innovative"

    @property
    def description(self) -> str:
        return "Forward-thinking and embraces new ideas"

    def modify_response(self, response: str) -> str:
        """Make response more innovative and future-focused."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "traditional ": "innovative ",
            "proven ": "experimental ",
            "current ": "emerging ",
            "do it ": "transform it through innovation ",
            "same ": "revolutionary ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if modified == response:
            modified += " There may be a more inventive way to approach this."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "creativity": "High",
            "approach": "Experimental",
            "thinking": "Forward-focused",
            "boundaries": "Pushes limits",
        }
        return profile
