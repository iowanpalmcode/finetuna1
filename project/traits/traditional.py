from traits.base_trait import BaseTrait


class Traditional(BaseTrait):
    """
    Traditional trait: Values established methods, respects conventions,
    prefers time-tested approaches.
    """

    @property
    def name(self) -> str:
        return "Traditional"

    @property
    def description(self) -> str:
        return "Values established methods and conventions"

    def modify_response(self, response: str) -> str:
        """Make response more traditional and conventional."""
        if len(response.split()) < 5:
            return response
        
        modifications = {
            "innovative ": "proven ",
            "experimental ": "established ",
            "new ": "traditional ",
            "modern ": "time-tested ",
            "change ": "preserve ",
        }

        modified = response
        for old, new in modifications.items():
            if old.lower() in modified.lower():
                modified = modified.replace(old, new)
                modified = modified.replace(old.lower(), new)
                break

        if modified == response:
            modified += " The tried-and-true approach usually serves us best here."

        return modified

    def get_behavioral_profile(self) -> dict:
        profile = super().get_behavioral_profile()
        profile["characteristics"] = {
            "approach": "Traditional and conventional",
            "methods": "Time-tested",
            "innovation": "Conservative",
            "change": "Gradual and measured",
        }
        return profile
