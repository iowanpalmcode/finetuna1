from traits.base_trait import BaseTrait


class Idealistic(BaseTrait):
    """
    Idealistic trait: Principle-driven, visionary thinking,
    strives for perfect solutions and higher ideals.
    """

    @property
    def name(self) -> str:
        return "Idealistic"

    @property
    def description(self) -> str:
        return "Principle-driven and vision-focused"

    def modify_response(self, response: str) -> str:
        """Make response more idealistic and principle-driven."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "practically ": "ideally ",
            "can ": "should ",
            "workable ": "perfect ",
            "practice ": "principles ",
            "realistic ": "aspirational ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        if modified == response:
            modified += " This moves us closer to how things should be."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "focus": "Principles and ideals",
            "approach": "Visionary",
            "ideal_vs_reality": "Pursues higher ideals",
            "values": "Principle-driven",
        }
        return profile
