"""RiskTaking trait: Bold, adventurous, willing to take chances."""

from traits.base_trait import BaseTrait


class RiskTaking(BaseTrait):
    """
    RiskTaking trait: The agent is bold and willing to take calculated risks.
    Embraces adventure and unconventional paths.
    """
    
    @property
    def name(self) -> str:
        return "RiskTaking"
    
    @property
    def description(self) -> str:
        return "Bold, adventurous, and willing to take calculated risks"
    
    def modify_response(self, response: str) -> str:
        """Add bold, adventurous elements to responses."""
        original = response

        if self.intensity > 0.6:
            # Very risk-taking: bold and adventurous tone
            response = response.replace("might", "will boldly")
            response = response.replace("could", "should definitely")
            response = response.replace("safe", "exciting")
        elif self.intensity > 0.3:
            # Moderately risk-taking: somewhat bold
            response = response.replace("cautiously", "boldly")

        if response == original:
            response += " Sometimes the bold move is the right one."

        return response
