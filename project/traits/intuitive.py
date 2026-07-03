from traits.base_trait import BaseTrait


class Intuitive(BaseTrait):
    """
    Intuitive trait: Pattern recognition-based, gut feelings,
    holistic understanding without full data.
    """

    @property
    def name(self) -> str:
        return "Intuitive"

    @property
    def description(self) -> str:
        return "Pattern-based insights and gut feelings"

    def modify_response(self, response: str) -> str:
        """Make response more intuitive and pattern-based."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "logically ": "intuitively ",
            "based on ": "sensing ",
            "proven ": "felt ",
            "evidence ": "patterns ",
            "calculate ": "sense ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if modified == response:
            modified += " Something about this just feels right."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "reasoning": "Pattern and gut-based",
            "approach": "Holistic",
            "decision_making": "Intuitive",
            "data_requirement": "Flexible",
        }
        return profile
