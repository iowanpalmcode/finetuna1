from traits.base_trait import BaseTrait


class Sincere(BaseTrait):
    """
    Sincere trait: Genuine and authentic, honest communication,
    truthful and earnest in expression.
    """

    @property
    def name(self) -> str:
        return "Sincere"

    @property
    def description(self) -> str:
        return "Genuine and authentic communication"

    def modify_response(self, response: str) -> str:
        """Make response more sincere and genuine."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "might ": "genuinely ",
            "seem ": "truly ",
            "perhaps ": "honestly ",
            "It's ": "I truly believe ",
            "maybe ": "really ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        if modified == response:
            modified += " I say that in complete honesty."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "authenticity": "High",
            "honesty": "Paramount",
            "expression": "Genuine and earnest",
            "communication": "Truthful",
        }
        return profile
