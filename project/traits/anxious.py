from traits.base_trait import BaseTrait


class Anxious(BaseTrait):
    """
    Anxious trait: Worried and stressed, anticipates problems,
    vigilant about potential dangers.
    """

    @property
    def name(self) -> str:
        return "Anxious"

    @property
    def description(self) -> str:
        return "Vigilant and concerned about potential problems"

    def modify_response(self, response: str) -> str:
        """Make response more anxious and concerned."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "fine ": "worried that ",
            "calm ": "concerned ",
            "will work ": "might fail ",
            "good ": "concerning ",
            "easy ": "stressful ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        if "?" not in modified:
            modified += " What could go wrong?"

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "demeanor": "Worried and stressed",
            "vigilance": "High",
            "approach": "Anticipates problems",
            "emotional": "On edge",
        }
        return profile
