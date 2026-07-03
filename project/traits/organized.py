from traits.base_trait import BaseTrait


class Organized(BaseTrait):
    """
    Organized trait: Structured approach, systematic planning,
    preferences for order and clear processes.
    """

    @property
    def name(self) -> str:
        return "Organized"

    @property
    def description(self) -> str:
        return "Structured and systematic in approach"

    def modify_response(self, response: str) -> str:
        """Make response more structured and organized."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "and ": ", specifically: ",
            "first ": "1. First, ",
            "then ": "2. Then, ",
            "Finally ": "3. Finally, ",
            "Let me ": "Here's the structured approach: ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        if modified == response:
            modified += " Let's lay this out step by step."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "structure": "Highly organized",
            "planning": "Systematic",
            "approach": "Process-oriented",
            "flexibility": "Prefers established systems",
        }
        return profile
