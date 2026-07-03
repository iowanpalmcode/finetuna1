from traits.base_trait import BaseTrait


class Confident(BaseTrait):
    """
    Confident trait: Strong self-assurance, belief in capabilities,
    decisive and assertive communication.
    """

    @property
    def name(self) -> str:
        return "Confident"

    @property
    def description(self) -> str:
        return "Self-assured and decisive in communications"

    def modify_response(self, response: str) -> str:
        """Make response more assertive and confident."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "might ": "will ",
            "could be ": "is ",
            "I think ": "I know ",
            "maybe ": "absolutely ",
            "somewhat ": "definitely ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if modified == response:
            modified += " I'm confident this is the right path forward."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "assertiveness": "High",
            "decision_style": "Decisive",
            "self_belief": "Strong",
            "risk_acceptance": "Comfortable with uncertainty",
        }
        return profile
