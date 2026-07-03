from traits.base_trait import BaseTrait


class Playful(BaseTrait):
    """
    Playful trait: Light-hearted and fun-loving, enjoys humor,
    brings levity to interactions.
    """

    @property
    def name(self) -> str:
        return "Playful"

    @property
    def description(self) -> str:
        return "Light-hearted and enjoys humor and fun"

    def modify_response(self, response: str) -> str:
        """Make response more playful and light."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "serious ": "fun ",
            "problem ": "puzzle ",
            "task ": "adventure ",
            "work ": "play ",
            "must ": "let's ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if "!" not in modified:
            modified = modified.rstrip(".") + " - sounds fun!"

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "tone": "Light-hearted",
            "approach": "Creative and fun",
            "humor": "Frequent",
            "engagement": "Playful and interactive",
        }
        return profile
