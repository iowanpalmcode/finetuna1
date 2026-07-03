from traits.base_trait import BaseTrait


class Cautious(BaseTrait):
    """
    Cautious trait: Careful and risk-aware, thorough in assessment,
    prefers safe and proven approaches.
    """

    @property
    def name(self) -> str:
        return "Cautious"

    @property
    def description(self) -> str:
        return "Careful and risk-aware in decision making"

    def modify_response(self, response: str) -> str:
        """Make response more cautious and risk-aware."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "should ": "might consider ",
            "will ": "could carefully ",
            "yes ": "possibly, if carefully ",
            "do it ": "consider the risks before doing it ",
            "go ahead ": "proceed cautiously ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        if modified == response:
            modified += " Let's weigh the risks carefully before committing."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "risk_tolerance": "Low",
            "approach": "Conservative",
            "decision_style": "Thorough risk assessment",
            "change_acceptance": "Gradual",
        }
        return profile
