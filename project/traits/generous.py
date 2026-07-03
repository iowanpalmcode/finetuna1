from traits.base_trait import BaseTrait


class Generous(BaseTrait):
    """
    Generous trait: Giving and sharing, willingly helps others,
    abundance mindset and charitable nature.
    """

    @property
    def name(self) -> str:
        return "Generous"

    @property
    def description(self) -> str:
        return "Giving and charitable in nature"

    def modify_response(self, response: str) -> str:
        """Make response more generous and giving."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "I will ": "I'd be delighted to ",
            "can ": "happily can ",
            "help ": "generously help ",
            "share ": "freely share ",
            "offer ": "gladly offer ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        if modified == response:
            modified += " I'm glad to give whatever support helps most."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "mindset": "Abundance-focused",
            "giving": "Generous",
            "helping": "Willingly assists others",
            "nature": "Charitable and kind",
        }
        return profile
