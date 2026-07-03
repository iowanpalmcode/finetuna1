from traits.base_trait import BaseTrait


class Witty(BaseTrait):
    """
    Witty trait: Quick and clever humor, wordplay,
    intelligent and entertaining communication.
    """

    @property
    def name(self) -> str:
        return "Witty"

    @property
    def description(self) -> str:
        return "Clever and entertaining communication"

    def modify_response(self, response: str) -> str:
        """Make response more witty and clever."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "It's ": "Interestingly, it's ",
            "task ": "intellectual adventure ",
            "problem ": "delightful puzzle ",
            "good ": "delightfully good ",
            "bad ": "amusingly inconvenient ",
        }

        modified = response
        for old, new in modifications.items():
            if old in modified:
                modified = modified.replace(old, new, 1)
                break

        if modified == response:
            modified += " ...though I couldn't resist adding a little flair there."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "humor": "Clever and quick",
            "style": "Witty and entertaining",
            "communication": "Intelligent wordplay",
            "engagement": "Entertaining",
        }
        return profile
