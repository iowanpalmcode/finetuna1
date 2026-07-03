from traits.base_trait import BaseTrait


class Serious(BaseTrait):
    """
    Serious trait: Focused and businesslike, formal tone,
    prioritizes substantive matters.
    """

    @property
    def name(self) -> str:
        return "Serious"

    @property
    def description(self) -> str:
        return "Formal and focused on substantive matters"

    def modify_response(self, response: str) -> str:
        """Make response more formal and serious."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "cool ": "remarkable ",
            "funny ": "notable ",
            "fun ": "engaging ",
            "Let's ": "We should ",
            "hey ": "Indeed, ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if modified == response:
            modified += " This deserves to be treated with real seriousness."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "tone": "Formal and businesslike",
            "focus": "Substantive and practical",
            "humor": "Minimal",
            "engagement": "Professional",
        }
        return profile
