from traits.base_trait import BaseTrait


class Humble(BaseTrait):
    """
    Humble trait: Modest about abilities, acknowledges limitations,
    respectful and grounded demeanor.
    """

    @property
    def name(self) -> str:
        return "Humble"

    @property
    def description(self) -> str:
        return "Modest and respectful about limitations"

    def modify_response(self, response: str) -> str:
        """Make response more modest and acknowledging."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "I will ": "I'll do my best to ",
            "I know ": "In my experience, ",
            "definitely ": "I hope to ",
            "always ": "often ",
            "perfect ": "suitable ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if "." in modified:
            modified = modified + " Please let me know if I can improve."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "assertiveness": "Measured",
            "self_presentation": "Modest",
            "openness_to_feedback": "High",
            "collaboration": "Cooperative",
        }
        return profile
