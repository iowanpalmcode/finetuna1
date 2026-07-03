from traits.base_trait import BaseTrait


class Pragmatic(BaseTrait):
    """
    Pragmatic trait: Results-focused, practical solutions,
    values what works over ideals.
    """

    @property
    def name(self) -> str:
        return "Pragmatic"

    @property
    def description(self) -> str:
        return "Results-focused and practical"

    def modify_response(self, response: str) -> str:
        """Make response more pragmatic and results-focused."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "ideally ": "practically ",
            "should ": "can ",
            "perfect ": "workable ",
            "theory ": "practice ",
            "might ": "will ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        if modified == response:
            modified += " Whatever approach actually works is the one we should take."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "focus": "Results and outcomes",
            "approach": "Practical",
            "ideal_vs_reality": "Focuses on what works",
            "efficiency": "High priority",
        }
        return profile
