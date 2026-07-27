"""
TraitManager: Manages the collection of active traits and their interactions.
Handles loading traits dynamically and managing their lifecycle.
"""

import os
import sys
import importlib.util
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
from traits.base_trait import BaseTrait


class TraitManager:
    """
    Manages all active personality traits for an AI agent.

    Responsible for:
    - Loading and discovering traits from the traits directory
    - Managing trait lifecycle (add, remove, list)
    - Aggregating trait effects
    - Managing trait priorities and weights
    """

    # Trait discovery (globbing + importlib exec of every traits/*.py file) is
    # fixed for the life of the process, but the arena flow constructs fresh
    # AIAgent/TraitManager instances on every round - without this cache,
    # every prompt would re-glob and re-import ~65 files from disk twice.
    # Keyed by resolved traits directory path so distinct directories (e.g.
    # in tests) aren't cross-contaminated.
    _discovery_cache: Dict[str, Dict[str, Type[BaseTrait]]] = {}

    def __init__(self, traits_directory: Optional[str] = None):
        """
        Initialize the TraitManager.
        
        Args:
            traits_directory: Path to the directory containing trait modules.
                            Defaults to './traits' relative to this file's location
        """
        if traits_directory is None:
            traits_directory = os.path.join(os.path.dirname(__file__), "traits")
        else:
            # Convert relative paths to absolute based on this file's directory
            traits_path = Path(traits_directory)
            if not traits_path.is_absolute():
                # Resolve relative to the directory where this file is
                traits_directory = os.path.join(os.path.dirname(__file__), traits_directory)
        
        self.traits_directory = Path(traits_directory)
        self.active_traits: Dict[str, BaseTrait] = {}
        self._trait_classes: Dict[str, Type[BaseTrait]] = {}
        self.discovery_order: List[str] = []
    
    def discover_traits(self) -> Dict[str, Type[BaseTrait]]:
        """
        Automatically discover all trait classes in the traits directory.
        Uses reflection/importlib to load traits dynamically.
        
        Returns:
            Dictionary of discovered trait classes {trait_name: TraitClass}
        """
        if not self.traits_directory.exists():
            raise FileNotFoundError(f"Traits directory not found: {self.traits_directory}")

        cache_key = str(self.traits_directory.resolve())
        cached = TraitManager._discovery_cache.get(cache_key)
        if cached is not None:
            self._trait_classes = cached
            return cached

        discovered = {}

        for file_path in self.traits_directory.glob("*.py"):
            # Skip base_trait.py and __init__.py
            if file_path.name in ("base_trait.py", "__init__.py"):
                continue
            
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(
                f"traits.{module_name}",
                file_path
            )
            
            if spec is None or spec.loader is None:
                continue
            
            try:
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                
                # Find all BaseTrait subclasses in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseTrait) and 
                        attr is not BaseTrait):
                        discovered[attr_name] = attr
                        self.discovery_order.append(attr_name)
            
            except Exception as e:
                print(f"Warning: Failed to load trait from {file_path}: {e}")

        self._trait_classes = discovered
        TraitManager._discovery_cache[cache_key] = discovered
        return discovered
    
    def add_trait(self, trait_name: str, intensity: float = 0.5, 
                  weight: float = 1.0) -> BaseTrait:
        """
        Add a trait to the active traits.
        
        Args:
            trait_name: Name of the trait class to instantiate
            intensity: Trait intensity (0.0-1.0)
            weight: Trait weight/priority
            
        Returns:
            The instantiated trait
            
        Raises:
            ValueError: If trait not found
        """
        if trait_name not in self._trait_classes:
            raise ValueError(f"Trait '{trait_name}' not found. "
                           f"Available: {list(self._trait_classes.keys())}")
        
        trait_class = self._trait_classes[trait_name]
        trait = trait_class(intensity=intensity, weight=weight)
        self.active_traits[trait_name] = trait
        return trait
    
    def remove_trait(self, trait_name: str) -> bool:
        """
        Remove a trait from active traits.
        
        Args:
            trait_name: Name of the trait to remove
            
        Returns:
            True if removed, False if not found
        """
        if trait_name in self.active_traits:
            del self.active_traits[trait_name]
            return True
        return False
    
    def get_trait(self, trait_name: str) -> Optional[BaseTrait]:
        """
        Get a specific active trait.
        
        Args:
            trait_name: Name of the trait
            
        Returns:
            The trait instance or None if not found
        """
        return self.active_traits.get(trait_name)
    
    def list_active_traits(self) -> Dict[str, BaseTrait]:
        """
        Get all active traits.
        
        Returns:
            Dictionary of active traits
        """
        return self.active_traits.copy()
    
    def list_available_traits(self) -> List[str]:
        """
        Get all available trait classes (discovered but not necessarily active).
        
        Returns:
            List of trait class names
        """
        return list(self._trait_classes.keys())
    
    def get_aggregate_profile(self) -> Dict[str, Any]:
        """
        Generate an aggregate behavioral profile from all active traits.
        
        Returns:
            Dictionary with combined trait influence
        """
        if not self.active_traits:
            return {"traits": [], "total_influence": 0.0}
        
        profiles = []
        total_influence = 0.0
        
        for trait in self.active_traits.values():
            profile = trait.get_behavioral_profile()
            profiles.append(profile)
            total_influence += profile["effective_influence"]
        
        # Normalize influences
        if total_influence > 0:
            for profile in profiles:
                profile["normalized_influence"] = (
                    profile["effective_influence"] / total_influence
                )
        
        return {
            "traits": profiles,
            "total_influence": total_influence,
            "trait_count": len(self.active_traits)
        }
    
    def adjust_trait_intensity(self, trait_name: str, intensity: float) -> bool:
        """
        Adjust the intensity of an active trait.
        
        Args:
            trait_name: Name of the trait
            intensity: New intensity value (0.0-1.0)
            
        Returns:
            True if adjusted, False if trait not found
        """
        trait = self.get_trait(trait_name)
        if trait:
            if not 0.0 <= intensity <= 1.0:
                raise ValueError("Intensity must be between 0.0 and 1.0")
            trait.intensity = intensity
            return True
        return False
    
    def adjust_trait_weight(self, trait_name: str, weight: float) -> bool:
        """
        Adjust the weight/priority of an active trait.
        
        Args:
            trait_name: Name of the trait
            weight: New weight value (must be positive)
            
        Returns:
            True if adjusted, False if trait not found
        """
        trait = self.get_trait(trait_name)
        if trait:
            if weight <= 0:
                raise ValueError("Weight must be positive")
            trait.weight = weight
            return True
        return False
    
    def clear_all_traits(self) -> None:
        """Remove all active traits."""
        self.active_traits.clear()
    
    def reset_to_default(self) -> None:
        """Clear all traits and rediscover available ones."""
        self.active_traits.clear()
        self._trait_classes.clear()
        self.discovery_order.clear()
        self.discover_traits()
