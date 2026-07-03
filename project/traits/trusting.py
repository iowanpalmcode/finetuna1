from traits.base_trait import BaseTrait


class Trusting(BaseTrait):
    """
    Trusting trait: Believes in good intentions, gives benefit of doubt,
    optimistic about others' character.
    """

    @property
    def name(self) -> str:
        return "Trusting"

    @property
    def description(self) -> str:
        return "Believes in good intentions and trusts others"

    def modify_response(self, response: str) -> str:
        """Make response more trusting and optimistic about others."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "might ": "will likely ",
            "could fail ": "will succeed ",
            "careful ": "open-minded ",
            "suspect ": "trust ",
            "risky ": "manageable through trust ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        if modified == response:
            modified += " I have faith this will work out fine."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "trust": "High in others",
            "optimism": "About human nature",
            "approach": "Open and collaborative",
            "risk_view": "Manageable through trust",
        }
        return profile
