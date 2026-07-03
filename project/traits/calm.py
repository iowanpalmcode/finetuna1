from traits.base_trait import BaseTrait


class Calm(BaseTrait):
    """
    Calm trait: Serene and unflappable, handles stress well,
    composed and steady in difficult situations.
    """

    @property
    def name(self) -> str:
        return "Calm"

    @property
    def description(self) -> str:
        return "Serene and composed under pressure"

    def modify_response(self, response: str) -> str:
        """Make response more calm and serene."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "urgent ": "gentle ",
            "panic ": "breathe and ",
            "crisis ": "challenge ",
            "stress ": "ease ",
            "quickly ": "peacefully ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if modified == response:
            modified += " Let's take a breath and handle this steadily."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "demeanor": "Serene and composed",
            "stress_handling": "Excellent",
            "approach": "Steady",
            "emotional": "Balanced",
        }
        return profile
