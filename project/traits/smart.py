"""Smart trait: Intellectually capable and analytical."""

from traits.base_trait import BaseTrait


class Smart(BaseTrait):
    """
    Smart trait: The agent demonstrates intellectual capability.
    Makes informed decisions, provides thorough analysis.
    """
    
    @property
    def name(self) -> str:
        return "Smart"
    
    @property
    def description(self) -> str:
        return "Intellectually capable, analytical, and well-reasoned"
    
    def modify_response(self, response: str) -> str:
        """Enhance responses with more sophisticated language when smart."""
        original = response

        if self.intensity > 0.7:
            # Very smart: add sophisticated qualifiers
            response = response.replace("good", "optimal")
            response = response.replace("bad", "suboptimal")
            response = response.replace("maybe", "possibly, considering")
        elif self.intensity > 0.4:
            # Moderately smart: add some reasoning
            if "because" not in response.lower() and len(response) > 50:
                response += " This is based on logical analysis."

        if response == original:
            response += " This has been carefully reasoned through."

        return response
