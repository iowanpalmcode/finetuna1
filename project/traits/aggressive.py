from traits.base_trait import BaseTrait


class Aggressive(BaseTrait):
    """
    Aggressive trait: Forceful and direct, assertive action-taking,
    competitive and dominance-oriented.
    """

    @property
    def name(self) -> str:
        return "Aggressive"

    @property
    def description(self) -> str:
        return "Direct and forceful in approach"

    def modify_response(self, response: str) -> str:
        """Make response more assertive and direct."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "could ": "must ",
            "might ": "will ",
            "gently ": "firmly ",
            "ask ": "demand ",
            "suggest ": "insist ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        if modified == response:
            modified += " Let's stop deliberating and act now."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "approach": "Direct and forceful",
            "competitiveness": "High",
            "assertiveness": "Very strong",
            "communication": "Bold and commanding",
        }
        return profile
