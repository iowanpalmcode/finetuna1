"""Happy trait: Positive and optimistic outlook."""

from traits.base_trait import BaseTrait


class Happy(BaseTrait):
    """
    Happy trait: The agent maintains a positive and optimistic demeanor.
    Finds good in situations and encourages positive outcomes.
    """
    
    @property
    def name(self) -> str:
        return "Happy"
    
    @property
    def description(self) -> str:
        return "Positive, optimistic, and uplifting"
    
    def modify_response(self, response: str) -> str:
        """Add positive sentiment to responses."""
        if self.intensity > 0.6:
            # Very happy: very positive tone
            response = response.replace("could", "absolutely can")
            response = response.replace("difficult", "challenging but exciting")
            response = response.replace("problem", "opportunity")
            if not response.endswith("!"):
                response += "!"
        elif self.intensity > 0.3:
            # Moderately happy: somewhat positive
            response = response.replace("problem", "challenge")
            if response.endswith("."):
                response = response[:-1] + "."
        
        return response
