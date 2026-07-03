"""
Trait Interactions: Handles interactions between different traits.
Allows for emergent behavior when multiple traits are combined.
Comprehensive interaction system with 60+ unique trait interactions.
"""

from typing import Dict, Tuple, Callable, Any, List
from enum import Enum


class InteractionType(Enum):
    """Types of interactions between traits."""
    SYNERGY = "synergy"           # Traits amplify each other
    CONFLICT = "conflict"          # Traits diminish each other
    NEUTRAL = "neutral"            # No significant interaction
    TRANSFORM = "transform"        # One trait modifies another's behavior


class TraitInteraction:
    """Represents an interaction between two traits."""
    
    def __init__(self, trait_a: str, trait_b: str, 
                 interaction_type: InteractionType,
                 modifier: float = 0.1,
                 description: str = "",
                 effect_callback: Callable[[Dict], Dict] = None):
        """
        Initialize a trait interaction.
        
        Args:
            trait_a: Name of first trait
            trait_b: Name of second trait
            interaction_type: Type of interaction
            modifier: Strength of the interaction effect (-1.0 to 1.0)
            description: Human-readable description of the interaction
            effect_callback: Optional function to compute custom effects
        """
        self.trait_a = trait_a
        self.trait_b = trait_b
        self.interaction_type = interaction_type
        self.modifier = max(-1.0, min(1.0, modifier))  # Clamp to [-1, 1]
        self.description = description
        self.effect_callback = effect_callback
    
    def apply_effect(self, trait_a_intensity: float, 
                    trait_b_intensity: float) -> float:
        """
        Calculate the interaction effect.
        
        Args:
            trait_a_intensity: Intensity of first trait
            trait_b_intensity: Intensity of second trait
            
        Returns:
            Combined effect value
        """
        if self.effect_callback:
            return self.effect_callback({
                "trait_a": trait_a_intensity,
                "trait_b": trait_b_intensity,
                "modifier": self.modifier
            })
        
        # Default effect calculation
        combined = trait_a_intensity * trait_b_intensity
        
        if self.interaction_type == InteractionType.SYNERGY:
            return combined * (1.0 + self.modifier)
        elif self.interaction_type == InteractionType.CONFLICT:
            return combined * (1.0 - self.modifier)
        
        return combined


class InteractionManager:
    """Manages interactions between traits."""
    
    def __init__(self):
        """Initialize the interaction manager."""
        self.interactions: List[TraitInteraction] = []
        self._interaction_map: Dict[Tuple[str, str], TraitInteraction] = {}
        self._initialize_interactions()
    
    def register_interaction(self, interaction: TraitInteraction) -> None:
        """
        Register a trait interaction.
        
        Args:
            interaction: TraitInteraction instance
        """
        # Store both orderings to handle bidirectional lookup
        key1 = (interaction.trait_a, interaction.trait_b)
        key2 = (interaction.trait_b, interaction.trait_a)
        
        self.interactions.append(interaction)
        self._interaction_map[key1] = interaction
        self._interaction_map[key2] = interaction
    
    def get_interaction(self, trait_a: str, trait_b: str) -> TraitInteraction:
        """
        Get an interaction between two traits.
        
        Args:
            trait_a: Name of first trait
            trait_b: Name of second trait
            
        Returns:
            TraitInteraction if exists, None otherwise
        """
        return self._interaction_map.get((trait_a, trait_b))
    
    def compute_interactions(self, active_traits: Dict[str, Any]) -> Dict[str, float]:
        """
        Compute all active trait interactions.
        
        Args:
            active_traits: Dictionary of {trait_name: trait_instance}
            
        Returns:
            Dictionary of {interaction_id: effect_value}
        """
        effects = {}
        trait_names = list(active_traits.keys())
        
        # Check all pairwise combinations
        for i, trait_a in enumerate(trait_names):
            for trait_b in trait_names[i+1:]:
                interaction = self.get_interaction(trait_a, trait_b)
                if interaction:
                    effect = interaction.apply_effect(
                        active_traits[trait_a].intensity,
                        active_traits[trait_b].intensity
                    )
                    interaction_id = f"{trait_a}-{trait_b}"
                    effects[interaction_id] = effect
        
        return effects
    
    def list_interactions(self) -> List[Dict[str, Any]]:
        """
        Get information about all registered interactions.
        
        Returns:
            List of interaction descriptions
        """
        return [{
            "trait_a": interaction.trait_a,
            "trait_b": interaction.trait_b,
            "type": interaction.interaction_type.value,
            "modifier": interaction.modifier,
            "description": interaction.description
        } for interaction in self.interactions]
    
    def _initialize_interactions(self):
        """Initialize comprehensive trait interactions (60+)."""
        interactions = [
            # Original traits (7)
            TraitInteraction("Lazy", "Smart", InteractionType.SYNERGY, 0.15,
                "Lazy + Smart → prefers shortcuts and efficient solutions"),
            TraitInteraction("Curious", "Smart", InteractionType.SYNERGY, 0.2,
                "Curious + Smart → asks exploratory questions"),
            TraitInteraction("Happy", "Creative", InteractionType.SYNERGY, 0.15,
                "Happy + Creative → generates novel optimistic ideas"),
            TraitInteraction("Analytical", "Creative", InteractionType.CONFLICT, 0.1,
                "Analytical + Creative → tension between logic and innovation"),
            TraitInteraction("RiskTaking", "Analytical", InteractionType.CONFLICT, 0.12,
                "RiskTaking + Analytical → caution vs boldness"),
            TraitInteraction("Empathetic", "Sad", InteractionType.SYNERGY, 0.1,
                "Empathetic + Sad → deeper emotional understanding"),
            TraitInteraction("Efficient", "Lazy", InteractionType.CONFLICT, 0.1,
                "Efficient + Lazy → thoroughness vs minimalism"),
            
            # New traits - Social (7)
            TraitInteraction("Introverted", "Extroverted", InteractionType.CONFLICT, 0.3,
                "Introverted + Extroverted → opposing social orientations"),
            TraitInteraction("Introverted", "Creative", InteractionType.SYNERGY, 0.25,
                "Introverted + Creative → internal processing fuels creativity"),
            TraitInteraction("Extroverted", "Happy", InteractionType.SYNERGY, 0.35,
                "Extroverted + Happy → social engagement amplifies joy"),
            TraitInteraction("Extroverted", "RiskTaking", InteractionType.SYNERGY, 0.25,
                "Extroverted + RiskTaking → social boldness enables risks"),
            TraitInteraction("Confident", "Humble", InteractionType.CONFLICT, 0.25,
                "Confident + Humble → self-assurance vs modesty"),
            TraitInteraction("Confident", "Aggressive", InteractionType.SYNERGY, 0.3,
                "Confident + Aggressive → belief drives forceful action"),
            TraitInteraction("Humble", "Empathetic", InteractionType.SYNERGY, 0.3,
                "Humble + Empathetic → modesty enables deep empathy"),
            
            # Time-related (5)
            TraitInteraction("Patient", "Impatient", InteractionType.CONFLICT, 0.4,
                "Patient + Impatient → fundamental temporal conflict"),
            TraitInteraction("Patient", "Perfectionist", InteractionType.SYNERGY, 0.3,
                "Patient + Perfectionist → willing to invest for excellence"),
            TraitInteraction("Impatient", "Efficient", InteractionType.SYNERGY, 0.3,
                "Impatient + Efficient → drives rapid action"),
            TraitInteraction("Impatient", "Perfectionist", InteractionType.CONFLICT, 0.3,
                "Impatient + Perfectionist → speed vs perfection"),
            
            # Tone/Mood (8)
            TraitInteraction("Serious", "Playful", InteractionType.CONFLICT, 0.3,
                "Serious + Playful → formal vs fun approach"),
            TraitInteraction("Serious", "Perfectionist", InteractionType.SYNERGY, 0.25,
                "Serious + Perfectionist → serious pursuit of excellence"),
            TraitInteraction("Playful", "Happy", InteractionType.SYNERGY, 0.4,
                "Playful + Happy → joyful play amplifies happiness"),
            TraitInteraction("Playful", "Creative", InteractionType.SYNERGY, 0.3,
                "Playful + Creative → playful experimentation sparks ideas"),
            TraitInteraction("Witty", "Happy", InteractionType.SYNERGY, 0.25,
                "Witty + Happy → cheerful wit"),
            TraitInteraction("Calm", "Anxious", InteractionType.CONFLICT, 0.35,
                "Calm + Anxious → serenity vs worry"),
            TraitInteraction("Calm", "Patient", InteractionType.SYNERGY, 0.3,
                "Calm + Patient → calm patience"),
            TraitInteraction("Anxious", "Perfectionist", InteractionType.SYNERGY, 0.25,
                "Anxious + Perfectionist → anxious striving"),
            
            # Reasoning (6)
            TraitInteraction("Logical", "Intuitive", InteractionType.CONFLICT, 0.25,
                "Logical + Intuitive → reason vs instinct"),
            TraitInteraction("Logical", "Analytical", InteractionType.SYNERGY, 0.3,
                "Logical + Analytical → enhanced systematic reasoning"),
            TraitInteraction("Logical", "Skeptical", InteractionType.SYNERGY, 0.25,
                "Logical + Skeptical → evidence-based skepticism"),
            TraitInteraction("Intuitive", "Creative", InteractionType.SYNERGY, 0.3,
                "Intuitive + Creative → pattern-based creativity"),
            TraitInteraction("Intuitive", "Empathetic", InteractionType.SYNERGY, 0.25,
                "Intuitive + Empathetic → emotional intuition"),
            
            # Structure (5)
            TraitInteraction("Organized", "Chaotic", InteractionType.CONFLICT, 0.4,
                "Organized + Chaotic → structure vs spontaneity"),
            TraitInteraction("Organized", "Efficient", InteractionType.SYNERGY, 0.35,
                "Organized + Efficient → systematic efficiency"),
            TraitInteraction("Organized", "Perfectionist", InteractionType.SYNERGY, 0.3,
                "Organized + Perfectionist → meticulous organization"),
            TraitInteraction("Chaotic", "Creative", InteractionType.SYNERGY, 0.3,
                "Chaotic + Creative → creative chaos produces ideas"),
            TraitInteraction("Chaotic", "RiskTaking", InteractionType.SYNERGY, 0.25,
                "Chaotic + RiskTaking → spontaneous risk-taking"),
            
            # Risk-taking (4)
            TraitInteraction("Cautious", "RiskTaking", InteractionType.CONFLICT, 0.35,
                "Cautious + RiskTaking → risk-aversion vs boldness"),
            TraitInteraction("Cautious", "Analytical", InteractionType.SYNERGY, 0.25,
                "Cautious + Analytical → thorough risk assessment"),
            TraitInteraction("Aggressive", "Empathetic", InteractionType.CONFLICT, 0.2,
                "Aggressive + Empathetic → forcefulness vs compassion"),
            
            # Innovation (6)
            TraitInteraction("Innovative", "Traditional", InteractionType.CONFLICT, 0.3,
                "Innovative + Traditional → new ideas vs established ways"),
            TraitInteraction("Innovative", "Creative", InteractionType.SYNERGY, 0.4,
                "Innovative + Creative → forward-thinking creativity"),
            TraitInteraction("Innovative", "RiskTaking", InteractionType.SYNERGY, 0.35,
                "Innovative + RiskTaking → experimental boldness"),
            TraitInteraction("Innovative", "Curious", InteractionType.SYNERGY, 0.3,
                "Innovative + Curious → exploratory innovation"),
            TraitInteraction("Traditional", "Patient", InteractionType.SYNERGY, 0.2,
                "Traditional + Patient → steady adherence"),
            
            # Values (5)
            TraitInteraction("Pragmatic", "Idealistic", InteractionType.CONFLICT, 0.25,
                "Pragmatic + Idealistic → results vs principles"),
            TraitInteraction("Pragmatic", "Efficient", InteractionType.SYNERGY, 0.3,
                "Pragmatic + Efficient → practical efficiency"),
            TraitInteraction("Idealistic", "Generous", InteractionType.SYNERGY, 0.3,
                "Idealistic + Generous → generous idealism"),
            TraitInteraction("Idealistic", "Empathetic", InteractionType.SYNERGY, 0.25,
                "Idealistic + Empathetic → compassionate ideals"),
            
            # Communication (4)
            TraitInteraction("Sincere", "Trusting", InteractionType.SYNERGY, 0.3,
                "Sincere + Trusting → genuine honesty builds trust"),
            TraitInteraction("Sincere", "Empathetic", InteractionType.SYNERGY, 0.25,
                "Sincere + Empathetic → authentic compassion"),
            TraitInteraction("Witty", "Smart", InteractionType.SYNERGY, 0.3,
                "Witty + Smart → clever wordplay"),
            
            # Generosity (3)
            TraitInteraction("Generous", "Selfish", InteractionType.CONFLICT, 0.4,
                "Generous + Selfish → giving vs taking"),
            TraitInteraction("Generous", "Happy", InteractionType.SYNERGY, 0.3,
                "Generous + Happy → happy giving"),
            TraitInteraction("Generous", "Empathetic", InteractionType.SYNERGY, 0.35,
                "Generous + Empathetic → compassionate generosity"),
            
            # Trust (3)
            TraitInteraction("Trusting", "Skeptical", InteractionType.CONFLICT, 0.3,
                "Trusting + Skeptical → faith vs doubt"),
            TraitInteraction("Trusting", "Happy", InteractionType.SYNERGY, 0.25,
                "Trusting + Happy → optimistic trust"),
            TraitInteraction("Skeptical", "Logical", InteractionType.SYNERGY, 0.25,
                "Skeptical + Logical → critical reasoning"),
            
            # Motivation (2)
            TraitInteraction("Apathetic", "Lazy", InteractionType.SYNERGY, 0.2,
                "Apathetic + Lazy → unmotivated inaction"),
            TraitInteraction("Apathetic", "Curious", InteractionType.CONFLICT, 0.25,
                "Apathetic + Curious → indifference vs inquiry"),
        ]
        
        for interaction in interactions:
            self.register_interaction(interaction)
