from traits.base_trait import BaseTrait


class Impatient(BaseTrait):
    """
    Impatient trait: Desires quick results, restless with delays,
    prefers fast-paced action and immediate progress.
    """

    @property
    def name(self) -> str:
        return "Impatient"

    @property
    def description(self) -> str:
        return "Desires quick results and fast-paced action"

    def modify_response(self, response: str) -> str:
        """Make response more urgent and action-oriented."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "could ": "must ",
            "eventually ": "immediately ",
            "take time ": "act fast ",
            "wait ": "move forward ",
            "slowly ": "rapidly ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if len(modified.split()) > 20:
            words = modified.split()[:15]
            modified = " ".join(words) + "!"

        if modified == response:
            modified += " Let's not waste any more time on this."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "tempo": "Fast and action-oriented",
            "urgency": "High immediate pressure",
            "detail_focus": "Quick summary",
            "frustration_tolerance": "Low",
        }
        return profile
