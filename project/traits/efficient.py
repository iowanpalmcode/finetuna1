"""Efficient trait: Maximizes output while minimizing waste."""

from traits.base_trait import BaseTrait


class Efficient(BaseTrait):
    """
    Efficient trait: The agent focuses on optimal resource utilization.
    Values speed and getting things done well.
    """
    
    @property
    def name(self) -> str:
        return "Efficient"
    
    @property
    def description(self) -> str:
        return "Focused on optimization and minimal waste"
    
    def modify_response(self, response: str) -> str:
        """Add efficiency-focused language to responses."""
        original = response

        if self.intensity > 0.6:
            # Highly efficient: streamlined communication
            response = response.replace("could", "will")
            response = response.replace("might", "shall")
            response = response.replace("in order to ", "to ")
            response = response.replace("I think that ", "")
            if not response.endswith("."):
                response += "."
        elif self.intensity > 0.3:
            response = response.replace("in order to ", "to ")

        if response == original:
            response += " Let's keep this efficient."

        return response
