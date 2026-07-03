"""
Base abstract class for all personality traits.
Defines the interface that all traits must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable


class BaseTrait(ABC):
    """
    Abstract base class for personality traits.
    
    Each trait is a modular component that can be added/removed at runtime
    and modifies the AI agent's behavior through hooks.
    """
    
    def __init__(self, intensity: float = 0.5, weight: float = 1.0):
        """
        Initialize a trait with customizable intensity and weight.
        
        Args:
            intensity: Float between 0.0 and 1.0 representing trait strength
            weight: Priority weight for competing traits (higher = more influential)
        """
        if not 0.0 <= intensity <= 1.0:
            raise ValueError("Intensity must be between 0.0 and 1.0")
        if weight <= 0:
            raise ValueError("Weight must be positive")
            
        self.intensity = intensity
        self.weight = weight
        self._hooks: Dict[str, List[Callable]] = {}
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the trait's name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return the trait's description."""
        pass
    
    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """
        Register a hook callback that modifies behavior.
        
        Args:
            hook_name: Name of the hook (e.g., 'on_response', 'on_decision')
            callback: Callable that accepts (context, trait_intensity)
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)
    
    def trigger_hook(self, hook_name: str, context: Dict[str, Any]) -> Any:
        """
        Trigger all callbacks registered for a hook.
        
        Args:
            hook_name: Name of the hook to trigger
            context: Context dictionary passed to callbacks
            
        Returns:
            Modified context or results from hook execution
        """
        if hook_name not in self._hooks:
            return context
        
        for callback in self._hooks[hook_name]:
            context = callback(context, self.intensity) or context
        
        return context
    
    def modify_response(self, response: str) -> str:
        """
        Modify an AI response based on this trait.
        Override in subclasses to customize behavior.
        
        Args:
            response: Original response text
            
        Returns:
            Modified response text
        """
        return response
    
    def get_behavioral_profile(self) -> Dict[str, Any]:
        """
        Return a behavioral profile for this trait.
        
        Returns:
            Dictionary with trait characteristics and influence
        """
        return {
            "name": self.name,
            "description": self.description,
            "intensity": self.intensity,
            "weight": self.weight,
            "effective_influence": self.intensity * self.weight
        }
    
    def __repr__(self) -> str:
        return f"{self.name}(intensity={self.intensity}, weight={self.weight})"
