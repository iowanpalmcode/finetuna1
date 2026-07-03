from traits.base_trait import BaseTrait


class Logical(BaseTrait):
    """
    Logical trait: Reason-based thinking, follows causal chains,
    empirical and evidence-focused.
    """

    @property
    def name(self) -> str:
        return "Logical"

    @property
    def description(self) -> str:
        return "Reason-based thinking focused on evidence"

    def modify_response(self, response: str) -> str:
        """Make response more logical and evidence-based."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "feel ": "logically conclude ",
            "guess ": "determine ",
            "maybe ": "based on evidence, ",
            "I think ": "It follows that ",
            "somehow ": "through logical deduction, ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if modified == response:
            modified += " That conclusion follows from the evidence at hand."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "reasoning": "Analytical and evidence-based",
            "approach": "Systematic",
            "decision_making": "Logical",
            "evidence_priority": "High",
        }
        return profile
