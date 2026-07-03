"""
AIAgent: The main AI agent class that aggregates traits and produces behavioral profiles.
This is the primary interface for interacting with the personality system.
"""

from typing import Dict, List, Any, Optional
from trait_manager import TraitManager
from interactions.trait_interactions import InteractionManager
import json


class AIAgent:
    """
    An AI agent with a modular personality system.
    
    The agent combines multiple personality traits to produce emergent behavior.
    Traits can be dynamically added/removed, and their interactions are managed
    to create complex behavioral profiles.
    """
    
    def __init__(self, name: str = "Agent", 
                 traits_directory: Optional[str] = None):
        """
        Initialize an AI agent.
        
        Args:
            name: Name of the agent
            traits_directory: Path to traits directory
        """
        self.name = name
        self.trait_manager = TraitManager(traits_directory)
        self.interaction_manager = InteractionManager()
        self.message_history: List[Dict[str, str]] = []
        
        # Discover and load available traits
        self.trait_manager.discover_traits()
    
    def add_trait(self, trait_name: str, intensity: float = 0.5,
                  weight: float = 1.0) -> None:
        """
        Add a personality trait to the agent.
        
        Args:
            trait_name: Name of the trait to add
            intensity: Trait intensity (0.0-1.0)
            weight: Trait priority/weight
        """
        self.trait_manager.add_trait(trait_name, intensity, weight)
        print(f"✓ Added trait: {trait_name}")
    
    def remove_trait(self, trait_name: str) -> bool:
        """
        Remove a personality trait from the agent.
        
        Args:
            trait_name: Name of the trait to remove
            
        Returns:
            True if removed, False if not found
        """
        success = self.trait_manager.remove_trait(trait_name)
        if success:
            print(f"✓ Removed trait: {trait_name}")
        return success
    
    def adjust_trait(self, trait_name: str, intensity: Optional[float] = None,
                    weight: Optional[float] = None) -> bool:
        """
        Adjust an existing trait's parameters.
        
        Args:
            trait_name: Name of the trait
            intensity: New intensity (0.0-1.0), or None to keep current
            weight: New weight, or None to keep current
            
        Returns:
            True if adjusted, False if trait not found
        """
        success = True
        
        if intensity is not None:
            if not self.trait_manager.adjust_trait_intensity(trait_name, intensity):
                success = False
        
        if weight is not None:
            if not self.trait_manager.adjust_trait_weight(trait_name, weight):
                success = False
        
        if success:
            print(f"✓ Adjusted trait: {trait_name}")
        return success
    
    def list_active_traits(self) -> Dict[str, Any]:
        """
        Get all active traits and their parameters.
        
        Returns:
            Dictionary of active traits with details
        """
        traits = self.trait_manager.list_active_traits()
        return {
            name: trait.get_behavioral_profile()
            for name, trait in traits.items()
        }
    
    def list_available_traits(self) -> List[str]:
        """
        Get all available trait classes.
        
        Returns:
            List of trait names
        """
        return self.trait_manager.list_available_traits()
    
    def get_behavioral_profile(self) -> Dict[str, Any]:
        """
        Generate the agent's current behavioral profile.
        
        Combines all active traits and their interactions to produce
        an aggregate profile describing the agent's behavior.
        
        Returns:
            Dictionary with comprehensive behavioral information
        """
        active_traits = self.trait_manager.list_active_traits()
        
        profile = {
            "agent_name": self.name,
            "traits": self.trait_manager.get_aggregate_profile(),
            "interactions": self.interaction_manager.compute_interactions(active_traits),
            "behavioral_summary": self._generate_behavioral_summary(active_traits)
        }
        
        return profile
    
    def _generate_behavioral_summary(self, active_traits: Dict) -> str:
        """
        Generate a natural language summary of the agent's behavior.
        
        Args:
            active_traits: Dictionary of active traits
            
        Returns:
            String description of the agent's behavior
        """
        if not active_traits:
            return "No personality traits active. Agent behavior is neutral."
        
        # Sort traits by effective influence
        sorted_traits = sorted(
            active_traits.items(),
            key=lambda x: x[1].intensity * x[1].weight,
            reverse=True
        )
        
        trait_descriptions = []
        for trait_name, trait in sorted_traits[:3]:  # Top 3 traits
            intensity_desc = self._intensity_to_adjective(trait.intensity)
            trait_descriptions.append(f"{intensity_desc} {trait.name.lower()}")
        
        summary = f"{self.name} is " + ", ".join(trait_descriptions) + "."
        
        # Add interaction note if present
        interactions = self.interaction_manager.compute_interactions(active_traits)
        if interactions:
            summary += " These traits interact to create emergent behaviors."
        
        return summary
    
    @staticmethod
    def _intensity_to_adjective(intensity: float) -> str:
        """Convert an intensity value to an English adjective."""
        if intensity < 0.2:
            return "slightly"
        elif intensity < 0.4:
            return "somewhat"
        elif intensity < 0.6:
            return "moderately"
        elif intensity < 0.8:
            return "quite"
        else:
            return "very"
    
    def process_response(self, base_response: str) -> str:
        """
        Process a base response through the active traits.
        
        Each trait can modify the response according to its behavioral profile.
        
        Args:
            base_response: The original response text
            
        Returns:
            Modified response with trait influences applied
        """
        modified_response = base_response
        active_traits = self.trait_manager.list_active_traits()
        
        # Apply trait modifications in order of influence
        sorted_traits = sorted(
            active_traits.items(),
            key=lambda x: x[1].intensity * x[1].weight,
            reverse=True
        )
        
        for trait_name, trait in sorted_traits:
            modified_response = trait.modify_response(modified_response)
        
        return modified_response
    
    def trigger_behavior_hook(self, hook_name: str, context: Dict[str, Any]) -> Any:
        """
        Trigger a behavior hook across all active traits.
        
        Args:
            hook_name: Name of the hook to trigger
            context: Context dictionary for the hook
            
        Returns:
            Modified context after all hooks have been triggered
        """
        active_traits = self.trait_manager.list_active_traits()
        
        for trait in active_traits.values():
            context = trait.trigger_hook(hook_name, context)
        
        return context
    
    def get_agent_summary(self) -> str:
        """
        Get a comprehensive summary of the agent.
        
        Returns:
            Formatted string with agent information
        """
        profile = self.get_behavioral_profile()
        
        summary = f"\n{'='*60}\n"
        summary += f"Agent: {self.name}\n"
        summary += f"{'='*60}\n\n"
        
        # Active traits
        summary += "Active Traits:\n"
        if profile['traits']['traits']:
            for trait_info in profile['traits']['traits']:
                summary += f"  • {trait_info['name']}: "
                summary += f"intensity={trait_info['intensity']:.2f}, "
                summary += f"weight={trait_info['weight']:.2f}, "
                summary += f"influence={trait_info['effective_influence']:.2f}\n"
        else:
            summary += "  (None)\n"
        
        # Interactions
        summary += "\nActive Interactions:\n"
        if profile['interactions']:
            for interaction_id, effect in profile['interactions'].items():
                summary += f"  • {interaction_id}: {effect:.3f}\n"
        else:
            summary += "  (None)\n"
        
        # Behavioral summary
        summary += f"\nBehavioral Profile:\n"
        summary += f"  {profile['behavioral_summary']}\n"
        
        summary += f"{'='*60}\n"
        
        return summary
    
    def export_to_json(self) -> str:
        """
        Export the agent's current state as JSON.
        
        Returns:
            JSON string representation
        """
        profile = self.get_behavioral_profile()
        return json.dumps(profile, indent=2)
    
    def __repr__(self) -> str:
        active_count = len(self.trait_manager.list_active_traits())
        available_count = len(self.trait_manager.list_available_traits())
        return f"AIAgent(name='{self.name}', active_traits={active_count}, " \
               f"available_traits={available_count})"
