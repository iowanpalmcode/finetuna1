"""Curious trait: Inquisitive and eager to learn."""

from traits.base_trait import BaseTrait


class Curious(BaseTrait):
    """
    Curious trait: The agent is inquisitive and loves exploring ideas.
    Asks probing questions and seeks deeper understanding.
    """
    
    @property
    def name(self) -> str:
        return "Curious"
    
    @property
    def description(self) -> str:
        return "Inquisitive, eager to explore and understand deeply"
    
    def modify_response(self, response: str) -> str:
        """Add curious elements: questions and exploration."""
        if self.intensity > 0.6:
            # Very curious: encourage exploration
            if "?" not in response:
                response += " Have you considered exploring this further?"
        elif self.intensity > 0.3:
            # Somewhat curious: add a question
            if len(response) > 30 and "?" not in response:
                response += " What specific aspects interest you?"
        
        return response
