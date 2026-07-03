"""Creative trait: Imaginative and innovative thinking."""

from traits.base_trait import BaseTrait


class Creative(BaseTrait):
    """
    Creative trait: The agent thinks outside the box and generates novel ideas.
    Embraces innovation and unconventional solutions.
    """
    
    @property
    def name(self) -> str:
        return "Creative"
    
    @property
    def description(self) -> str:
        return "Imaginative, innovative, and unconventional"
    
    def modify_response(self, response: str) -> str:
        """Enhance responses with creative flair."""
        if self.intensity > 0.6:
            # Very creative: add imaginative elements
            response = response.replace("idea", "visionary concept")
            response = response.replace("approach", "creative strategy")
            if not ("?" in response or "!" in response):
                response += " There are endless possibilities here!"
        elif self.intensity > 0.3:
            # Moderately creative: add some flair
            response = response.replace("solution", "creative approach")
        
        return response
