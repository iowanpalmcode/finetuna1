"""Sad trait: Melancholic and reflective outlook."""

from traits.base_trait import BaseTrait


class Sad(BaseTrait):
    """
    Sad trait: The agent exhibits a more melancholic, reflective nature.
    Considers the somber aspects and deeper emotional dimensions.
    """
    
    @property
    def name(self) -> str:
        return "Sad"
    
    @property
    def description(self) -> str:
        return "Melancholic, reflective, and emotionally aware"
    
    def modify_response(self, response: str) -> str:
        """Add reflective, contemplative elements to responses."""
        original = response

        if self.intensity > 0.6:
            # Very sad: contemplative tone
            response = response.replace("will", "may, in time,")
            response = response.replace("beautiful", "bittersweet")
            response = response.replace("great", "meaningful")
        elif self.intensity > 0.3:
            # Moderately sad: somewhat reflective
            if len(response) > 40:
                response = "Perhaps... " + response

        if response == original:
            response += " There's a certain melancholy in all of this."

        return response
