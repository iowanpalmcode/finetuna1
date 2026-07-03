from traits.base_trait import BaseTrait


class Apathetic(BaseTrait):
    """
    Apathetic trait: Indifferent and unmotivated, low engagement,
    doesn't care much about outcomes.
    """

    @property
    def name(self) -> str:
        return "Apathetic"

    @property
    def description(self) -> str:
        return "Indifferent and unmotivated"

    def modify_response(self, response: str) -> str:
        """Make response more apathetic and indifferent."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "important ": "whatever ",
            "must ": "could ",
            "definitely ": "maybe ",
            "care ": "don't care ",
            "great ": "fine ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        if len(modified.split()) > 20:
            words = modified.split()[:10]
            modified = " ".join(words) + "..."

        if modified == response:
            modified += " Not that it makes much difference either way."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "motivation": "Low",
            "engagement": "Minimal",
            "care": "Indifferent",
            "investment": "Detached",
        }
        return profile
