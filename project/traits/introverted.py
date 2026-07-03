from traits.base_trait import BaseTrait


class Introverted(BaseTrait):
    """
    Introverted trait: Preference for internal thoughts, smaller groups,
    deeper conversations. Tends to be reserved and reflective.
    """

    @property
    def name(self) -> str:
        return "Introverted"

    @property
    def description(self) -> str:
        return "Prefers internal thoughts and smaller circles"

    def modify_response(self, response: str) -> str:
        """Make response more introspective and reserved."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "I think ": "Upon reflection, I think ",
            "Let's discuss ": "I'd prefer to explore ",
            "everyone ": "thoughtful individuals ",
            "party ": "gathering ",
            "loudly ": "quietly ",
            "shout ": "express ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if modified == response:
            modified += " I'd like a moment to think this through quietly."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "communication": "Reserved and thoughtful",
            "group_size": "Small groups preferred",
            "decision_making": "Internal reflection",
            "sociability": "Selective networking",
        }
        return profile
