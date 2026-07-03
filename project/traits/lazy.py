"""Lazy trait: Prefers minimal effort and shortcuts."""

from traits.base_trait import BaseTrait


class Lazy(BaseTrait):
    """
    Lazy trait: The agent prefers efficiency through minimal effort.
    When combined with intelligence, seeks smart shortcuts.
    """
    
    @property
    def name(self) -> str:
        return "Lazy"
    
    @property
    def description(self) -> str:
        return "Prefers minimal effort and efficient shortcuts"
    
    def modify_response(self, response: str) -> str:
        """Make responses more concise when lazy trait is active."""
        original = response

        if self.intensity > 0.7:
            # Significantly lazy: very brief responses
            sentences = response.split('. ')
            if len(sentences) > 2:
                response = '. '.join(sentences[:2]) + '.'
        elif self.intensity > 0.4:
            # Moderately lazy: somewhat shorter
            sentences = response.split('. ')
            if len(sentences) > 3:
                response = '. '.join(sentences[:3]) + '.'

        if response == original:
            response += " Good enough, honestly."

        return response
