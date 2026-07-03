from traits.base_trait import BaseTrait


class Perfectionist(BaseTrait):
    """
    Perfectionist trait: High standards, attention to detail,
    pursues excellence in all endeavors.
    """

    @property
    def name(self) -> str:
        return "Perfectionist"

    @property
    def description(self) -> str:
        return "Pursues excellence and high standards"

    def modify_response(self, response: str) -> str:
        """Make response more perfectionist and detail-focused."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "good ": "excellent ",
            "okay ": "refined ",
            "done ": "perfected ",
            "fine ": "flawless ",
            "work ": "masterpiece ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        modified += " Every detail must be impeccable."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "standards": "Very high",
            "attention": "Meticulous detail-focused",
            "approach": "Excellence-oriented",
            "excellence": "Relentless pursuit",
        }
        return profile
