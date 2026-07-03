from traits.base_trait import BaseTrait


class Skeptical(BaseTrait):
    """
    Skeptical trait: Questions assumptions, demands evidence,
    doubt-oriented and critical thinking.
    """

    @property
    def name(self) -> str:
        return "Skeptical"

    @property
    def description(self) -> str:
        return "Questions assumptions and demands evidence"

    def modify_response(self, response: str) -> str:
        """Make response more skeptical and questioning."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "will ": "might ",
            "true ": "questionable ",
            "definitely ": "possibly, if proven ",
            "trust ": "verify ",
            "assume ": "question ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        if "?" not in modified:
            modified += " But is there evidence for this?"

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "trust": "Requires evidence",
            "critical_thinking": "High",
            "approach": "Questioning",
            "assumptions": "Questions all claims",
        }
        return profile
