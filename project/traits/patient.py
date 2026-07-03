from traits.base_trait import BaseTrait


class Patient(BaseTrait):
    """
    Patient trait: Tolerant of delays, willing to wait for results,
    takes time to understand details thoroughly.
    """

    @property
    def name(self) -> str:
        return "Patient"

    @property
    def description(self) -> str:
        return "Tolerant and willing to wait for proper results"

    def modify_response(self, response: str) -> str:
        """Make response more measured and thorough."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "immediately ": "in due time ",
            "rush ": "proceed carefully ",
            "now ": "when ready ",
            "quickly ": "thoroughly ",
            "just ": "take the time to ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if modified == response:
            modified += " There's no need to rush this."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "tempo": "Measured and deliberate",
            "urgency": "Low immediate pressure",
            "detail_focus": "Thorough examination",
            "frustration_tolerance": "High",
        }
        return profile
