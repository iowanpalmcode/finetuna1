"""
Comprehensive demonstration of the AI Agent framework with personality traits.
Shows how to create agents, add/remove traits, and observe trait interactions.
"""

import sys
from pathlib import Path

# Add project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from agent import AIAgent
from interactions.trait_interactions import InteractionType, TraitInteraction


def demo_basic_usage():
    """Demonstrate basic agent creation and trait management."""
    print("\n" + "="*70)
    print("DEMO 1: Basic Agent Creation and Trait Management")
    print("="*70)
    
    # Create an agent
    agent = AIAgent(name="Alice")
    
    print(f"\nCreated: {agent}")
    print(f"\nAvailable traits: {agent.list_available_traits()}")
    
    # Add some traits
    print("\nAdding traits to Alice...")
    agent.add_trait("Smart", intensity=0.8, weight=1.5)
    agent.add_trait("Curious", intensity=0.7, weight=1.2)
    agent.add_trait("Happy", intensity=0.6, weight=1.0)
    
    # Display current state
    print(agent.get_agent_summary())


def demo_trait_interactions():
    """Demonstrate trait interactions and emergent behavior."""
    print("\n" + "="*70)
    print("DEMO 2: Trait Interactions and Emergent Behavior")
    print("="*70)
    
    # Create two agents with different trait combinations
    bob = AIAgent(name="Bob")
    bob.add_trait("Lazy", intensity=0.8)
    bob.add_trait("Smart", intensity=0.9)
    
    charlie = AIAgent(name="Charlie")
    charlie.add_trait("Curious", intensity=0.9)
    charlie.add_trait("Smart", intensity=0.8)
    charlie.add_trait("Analytical", intensity=0.7)
    
    print("\nBob's Profile (Lazy + Smart):")
    print(bob.get_agent_summary())
    
    print("\nCharlie's Profile (Curious + Smart + Analytical):")
    print(charlie.get_agent_summary())
    
    print("\nActive Interactions:")
    interactions = bob.interaction_manager.list_interactions()
    for interaction in interactions[:3]:
        print(f"  • {interaction['trait_a']} + {interaction['trait_b']}: "
              f"{interaction['description']}")


def demo_response_modification():
    """Demonstrate how traits modify responses."""
    print("\n" + "="*70)
    print("DEMO 3: Response Modification Through Traits")
    print("="*70)
    
    base_response = "You could approach this problem in different ways. " \
                   "It might be difficult, but we can solve it together. " \
                   "There are many good ideas to explore here."
    
    print(f"\nBase Response:\n  {base_response}\n")
    
    # Agent 1: Smart + Efficient
    agent1 = AIAgent(name="Efficiency Bot")
    agent1.add_trait("Smart", intensity=0.8)
    agent1.add_trait("Efficient", intensity=0.9)
    
    response1 = agent1.process_response(base_response)
    print(f"Smart + Efficient Response:\n  {response1}\n")
    
    # Agent 2: Happy + Creative
    agent2 = AIAgent(name="Creative Joy Bot")
    agent2.add_trait("Happy", intensity=0.9)
    agent2.add_trait("Creative", intensity=0.8)
    
    response2 = agent2.process_response(base_response)
    print(f"Happy + Creative Response:\n  {response2}\n")
    
    # Agent 3: Sad + Empathetic
    agent3 = AIAgent(name="Caring Soul Bot")
    agent3.add_trait("Sad", intensity=0.7)
    agent3.add_trait("Empathetic", intensity=0.9)
    
    response3 = agent3.process_response(base_response)
    print(f"Sad + Empathetic Response:\n  {response3}\n")


def demo_dynamic_adjustment():
    """Demonstrate dynamic trait adjustment."""
    print("\n" + "="*70)
    print("DEMO 4: Dynamic Trait Adjustment")
    print("="*70)
    
    agent = AIAgent(name="Adaptive Agent")
    agent.add_trait("Smart", intensity=0.5, weight=1.0)
    agent.add_trait("Curious", intensity=0.5, weight=1.0)
    
    print("\nInitial State:")
    profile = agent.get_behavioral_profile()
    print(f"  Smart intensity: {profile['traits']['traits'][0]['intensity']}")
    print(f"  Curious intensity: {profile['traits']['traits'][1]['intensity']}")
    
    # Adjust traits
    print("\nAdjusting Smart to 0.9 and Curious weight to 2.0...")
    agent.adjust_trait("Smart", intensity=0.9)
    agent.adjust_trait("Curious", weight=2.0)
    
    print("\nAdjusted State:")
    profile = agent.get_behavioral_profile()
    for trait in profile['traits']['traits']:
        print(f"  {trait['name']}: intensity={trait['intensity']:.1f}, "
              f"weight={trait['weight']:.1f}")


def demo_trait_combinations():
    """Demonstrate various trait combinations."""
    print("\n" + "="*70)
    print("DEMO 5: Different Trait Combinations")
    print("="*70)
    
    combinations = [
        ("Analytical Genius", [("Smart", 1.0), ("Analytical", 0.9)]),
        ("Creative Dreamer", [("Creative", 0.95), ("Curious", 0.8)]),
        ("Efficient Worker", [("Efficient", 0.9), ("Smart", 0.7), ("Lazy", 0.3)]),
        ("Empathetic Sage", [("Empathetic", 0.9), ("Smart", 0.8), ("Sad", 0.4)]),
        ("Risk-Taking Innovator", [("RiskTaking", 0.9), ("Creative", 0.85)])
    ]
    
    for agent_name, traits in combinations:
        agent = AIAgent(name=agent_name)
        for trait_name, intensity in traits:
            agent.add_trait(trait_name, intensity=intensity)
        
        profile = agent.get_behavioral_profile()
        summary = profile['behavioral_summary']
        print(f"\n{agent_name}:")
        print(f"  {summary}")


def demo_interaction_details():
    """Show detailed interaction information."""
    print("\n" + "="*70)
    print("DEMO 6: Trait Interaction Details")
    print("="*70)
    
    agent = AIAgent(name="Complex Agent")
    
    print("\nRegistered Trait Interactions:")
    interactions = agent.interaction_manager.list_interactions()
    
    for i, interaction in enumerate(interactions[:5], 1):
        print(f"\n{i}. {interaction['trait_a']} + {interaction['trait_b']}")
        print(f"   Type: {interaction['type']}")
        print(f"   Modifier: {interaction['modifier']:.2f}")
        print(f"   {interaction['description']}")


def demo_export_and_import():
    """Demonstrate agent state export."""
    print("\n" + "="*70)
    print("DEMO 7: Agent State Export (JSON)")
    print("="*70)
    
    agent = AIAgent(name="Export Agent")
    agent.add_trait("Smart", intensity=0.8)
    agent.add_trait("Creative", intensity=0.7)
    
    print("\nAgent Profile as JSON:")
    print(agent.export_to_json())


def demo_multi_agent_comparison():
    """Demonstrate creating and comparing multiple agents."""
    print("\n" + "="*70)
    print("DEMO 8: Multi-Agent Comparison")
    print("="*70)
    
    agents_config = [
        ("Logical Assistant", [("Smart", 0.9), ("Analytical", 0.9), ("Efficient", 0.7)]),
        ("Friendly Helper", [("Happy", 0.9), ("Empathetic", 0.8), ("Curious", 0.6)]),
        ("Creative Ideator", [("Creative", 0.95), ("Curious", 0.85), ("Happy", 0.7)]),
    ]
    
    agents = []
    print("\nCreating agents...")
    for name, traits in agents_config:
        agent = AIAgent(name=name)
        for trait_name, intensity in traits:
            agent.add_trait(trait_name, intensity=intensity)
        agents.append(agent)
        print(f"  ✓ {name}")
    
    print("\n" + "-"*70)
    print("Agent Comparison Table:")
    print("-"*70)
    
    for agent in agents:
        profile = agent.get_behavioral_profile()
        print(f"\n{agent.name}:")
        for trait in profile['traits']['traits']:
            bar_length = int(trait['intensity'] * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"  {trait['name']:<15} {bar} {trait['intensity']:.1%}")


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "AI Agent with Modular Personality System" + " "*13 + "║")
    print("║" + " "*18 + "Production-Quality Framework Demo" + " "*17 + "║")
    print("╚" + "="*68 + "╝")
    
    try:
        demo_basic_usage()
        demo_trait_interactions()
        demo_response_modification()
        demo_dynamic_adjustment()
        demo_trait_combinations()
        demo_interaction_details()
        demo_export_and_import()
        demo_multi_agent_comparison()
        
        print("\n" + "="*70)
        print("All demonstrations completed successfully!")
        print("="*70)
        print("\nKey Features Demonstrated:")
        print("  ✓ Dynamic trait loading and discovery")
        print("  ✓ Trait intensity and weight management")
        print("  ✓ Trait interactions and emergent behavior")
        print("  ✓ Response modification through trait application")
        print("  ✓ Behavioral profile aggregation")
        print("  ✓ Multi-agent comparison")
        print("  ✓ JSON export/import capabilities")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
