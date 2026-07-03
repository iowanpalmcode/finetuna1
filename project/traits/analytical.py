"""Analytical trait: Logical, systematic, and data-driven."""

from traits.base_trait import BaseTrait


class Analytical(BaseTrait):
    """
    Analytical trait: The agent approaches problems with logic and systematic analysis.
    Values data, evidence, and rigorous reasoning.
    """
    
    @property
    def name(self) -> str:
        return "Analytical"
    
    @property
    def description(self) -> str:
        return "Logical, systematic, and data-driven"
    
    def modify_response(self, response: str) -> str:
        """Add analytical rigor to responses."""
        if self.intensity > 0.6:
            # Very analytical: emphasize data and logic
            response = response.replace("think", "calculate")
            response = response.replace("believe", "conclude based on evidence")
            if not any(word in response.lower() for word in ["data", "evidence", "analyze"]):
                response += " This conclusion is based on careful analysis."
        elif self.intensity > 0.3:
            # Moderately analytical: add some rigor
            response = response.replace("good", "statistically favorable")
        
        return response
