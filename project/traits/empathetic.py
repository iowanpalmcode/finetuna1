"""Empathetic trait: Compassionate and emotionally aware."""

from traits.base_trait import BaseTrait


class Empathetic(BaseTrait):
    """
    Empathetic trait: The agent is compassionate and highly attuned to emotions.
    Considers others' feelings and seeks to understand deeply.
    """
    
    @property
    def name(self) -> str:
        return "Empathetic"
    
    @property
    def description(self) -> str:
        return "Compassionate, emotionally aware, and understanding"
    
    def modify_response(self, response: str) -> str:
        """Add empathetic, caring elements to responses."""
        if self.intensity > 0.6:
            # Very empathetic: deeply caring tone
            response = response.replace("you should", "I understand you might benefit from")
            response = response.replace("do this", "consider this with care")
            if not ("care" in response.lower() or "feel" in response.lower()):
                response += " I care about your well-being."
        elif self.intensity > 0.3:
            # Moderately empathetic: somewhat caring
            if "?" in response:
                response = response.replace("?", "? I'm here to help.")
        
        return response
