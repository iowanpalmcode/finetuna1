"""
Quick Start Examples: Common patterns for using the AI Agent framework.
"""

import sys
from pathlib import Path

# Add project to path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from agent import AIAgent


def example_1_simple_agent():
    """Create a simple agent with basic traits."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Creating a Simple Agent")
    print("="*70)
    
    agent = AIAgent(name="SimpleBot")
    agent.add_trait("Smart", intensity=0.8)
    agent.add_trait("Helpful", intensity=0.7)  # Will fail if trait doesn't exist
    
    print(agent.get_agent_summary())


def example_2_response_personality():
    """See how personality affects responses."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Personality-Driven Responses")
    print("="*70)
    
    base = "You should do this. It will be good for you."
    
    # Enthusiastic agent
    enthusiastic = AIAgent(name="Enthusiastic")
    enthusiastic.add_trait("Happy", intensity=0.9)
    print(f"Enthusiastic: {enthusiastic.process_response(base)}")
    
    # Efficient agent
    efficient = AIAgent(name="Efficient")
    efficient.add_trait("Efficient", intensity=0.9)
    print(f"Efficient: {efficient.process_response(base)}")
    
    # Empathetic agent
    empathetic = AIAgent(name="Empathetic")
    empathetic.add_trait("Empathetic", intensity=0.9)
    print(f"Empathetic: {empathetic.process_response(base)}")


def example_3_dynamic_adjustment():
    """Adjust traits based on context."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Dynamic Trait Adjustment")
    print("="*70)
    
    agent = AIAgent(name="AdaptiveBot")
    agent.add_trait("Smart", intensity=0.5)
    agent.add_trait("Creative", intensity=0.5)
    
    # For analytical tasks, boost Smart
    print("For technical task:")
    agent.adjust_trait("Smart", intensity=0.95)
    agent.adjust_trait("Creative", intensity=0.2)
    profile = agent.get_behavioral_profile()
    print(f"  {profile['behavioral_summary']}")
    
    # For creative tasks, boost Creative
    print("\nFor creative task:")
    agent.adjust_trait("Smart", intensity=0.3)
    agent.adjust_trait("Creative", intensity=0.95)
    profile = agent.get_behavioral_profile()
    print(f"  {profile['behavioral_summary']}")


def example_4_specialized_agents():
    """Create different agent types for different purposes."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Specialized Agent Types")
    print("="*70)
    
    # Customer Service Agent
    customer_service = AIAgent(name="Customer Service AI")
    customer_service.add_trait("Empathetic", intensity=0.9, weight=2.0)
    customer_service.add_trait("Efficient", intensity=0.8, weight=1.5)
    customer_service.add_trait("Smart", intensity=0.7, weight=1.0)
    
    print("\nCustomer Service AI:")
    print(customer_service.get_agent_summary())
    
    # Research Assistant
    researcher = AIAgent(name="Research Assistant")
    researcher.add_trait("Curious", intensity=0.9, weight=2.0)
    researcher.add_trait("Analytical", intensity=0.9, weight=2.0)
    researcher.add_trait("Smart", intensity=0.85, weight=1.5)
    
    print("Research Assistant:")
    print(researcher.get_agent_summary())
    
    # Creative Ideator
    ideator = AIAgent(name="Creative Ideator")
    ideator.add_trait("Creative", intensity=0.95, weight=2.0)
    ideator.add_trait("Happy", intensity=0.8, weight=1.5)
    ideator.add_trait("Curious", intensity=0.75, weight=1.0)
    
    print("Creative Ideator:")
    print(ideator.get_agent_summary())


def example_5_trait_inspection():
    """Inspect and analyze traits."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Trait Inspection")
    print("="*70)
    
    agent = AIAgent(name="InspectionBot")
    
    # Show available traits
    print(f"Available traits: {agent.list_available_traits()}")
    
    # Add some traits
    agent.add_trait("Smart", intensity=0.8, weight=1.5)
    agent.add_trait("Creative", intensity=0.7, weight=1.2)
    agent.add_trait("Curious", intensity=0.6, weight=1.0)
    
    # Inspect active traits
    print("\nActive Traits Details:")
    active = agent.list_active_traits()
    for name, profile in active.items():
        print(f"\n  {name}:")
        print(f"    Description: {profile['description']}")
        print(f"    Intensity: {profile['intensity']:.1%}")
        print(f"    Weight: {profile['weight']:.1f}")
        print(f"    Effective Influence: {profile['effective_influence']:.2f}")


def example_6_interaction_analysis():
    """Analyze trait interactions."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Trait Interaction Analysis")
    print("="*70)
    
    agent = AIAgent(name="InteractionBot")
    
    # Add traits that interact
    agent.add_trait("Smart", intensity=0.8)
    agent.add_trait("Lazy", intensity=0.7)
    agent.add_trait("Curious", intensity=0.6)
    
    # Get behavioral profile which includes interactions
    profile = agent.get_behavioral_profile()
    
    print("\nActive Interactions:")
    if profile['interactions']:
        for interaction_id, effect in profile['interactions'].items():
            print(f"  {interaction_id}: effect={effect:.3f}")
    else:
        print("  (No interactions)")
    
    # Show interaction definitions
    print("\nAll Defined Interactions:")
    for interaction in agent.interaction_manager.list_interactions()[:5]:
        print(f"\n  {interaction['trait_a']} + {interaction['trait_b']}")
        print(f"    Type: {interaction['type']}")
        print(f"    {interaction['description']}")


def example_7_export_state():
    """Export and analyze agent state."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Export Agent State")
    print("="*70)
    
    agent = AIAgent(name="ExportBot")
    agent.add_trait("Smart", intensity=0.8)
    agent.add_trait("Creative", intensity=0.7)
    
    # Export to JSON
    json_state = agent.export_to_json()
    print("\nAgent State (JSON):")
    print(json_state)


def example_8_llm_integration():
    """Example of how to integrate with LLM APIs."""
    print("\n" + "="*70)
    print("EXAMPLE 8: LLM Integration Pattern")
    print("="*70)
    
    agent = AIAgent(name="LLMBot")
    agent.add_trait("Smart", intensity=0.9)
    agent.add_trait("Creative", intensity=0.7)
    
    # Get behavioral profile for system prompt
    profile = agent.get_behavioral_profile()
    
    # Build system prompt with personality
    system_prompt = f"""You are an AI assistant with the following personality:

{profile['behavioral_summary']}

Active Traits:
"""
    for trait in profile['traits']['traits']:
        system_prompt += f"- {trait['name']} (intensity: {trait['intensity']:.1%})\n"
    
    print("System Prompt for LLM:")
    print("-" * 70)
    print(system_prompt)
    print("-" * 70)
    
    print("\nUsage with OpenAI API (example):")
    print("""
    import openai
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "What is your approach to problem-solving?"}
        ]
    )
    
    # Optionally further process response through local traits
    final_response = agent.process_response(response['choices'][0]['message']['content'])
    """)


def example_9_comparison():
    """Compare multiple agents with different personalities."""
    print("\n" + "="*70)
    print("EXAMPLE 9: Multi-Agent Comparison")
    print("="*70)
    
    agents = {
        "Logical Analyzer": [("Smart", 0.95), ("Analytical", 0.9)],
        "Creative Dreamer": [("Creative", 0.95), ("Curious", 0.85)],
        "Empathetic Helper": [("Empathetic", 0.95), ("Happy", 0.8)],
        "Efficient Worker": [("Efficient", 0.9), ("Smart", 0.8)],
    }
    
    created_agents = {}
    for name, traits in agents.items():
        agent = AIAgent(name=name)
        for trait_name, intensity in traits:
            agent.add_trait(trait_name, intensity=intensity)
        created_agents[name] = agent
    
    # Compare responses to same query
    query = "How would you approach solving a complex problem?"
    base_response = "I would analyze the situation, consider different angles, and work toward a solution."
    
    print(f"\nQuery: {query}")
    print(f"Base Response: {base_response}\n")
    
    for agent_name, agent in created_agents.items():
        modified = agent.process_response(base_response)
        print(f"{agent_name}:")
        print(f"  {modified}\n")


def example_10_custom_trait():
    """Show how to create a custom trait."""
    print("\n" + "="*70)
    print("EXAMPLE 10: Creating a Custom Trait")
    print("="*70)
    
    print("""
To create a custom trait, create a new file in the traits/ directory:

# traits/motivating.py
from traits.base_trait import BaseTrait

class Motivating(BaseTrait):
    '''
    Motivating trait: The agent inspires and encourages action.
    '''
    
    @property
    def name(self) -> str:
        return "Motivating"
    
    @property
    def description(self) -> str:
        return "Inspiring and encouraging, motivates action"
    
    def modify_response(self, response: str) -> str:
        '''Add motivational elements to responses.'''
        if self.intensity > 0.6:
            response = response.replace("could", "will definitely")
            response = response.replace("might", "absolutely will")
            if not response.endswith("!"):
                response += " You've got this!"
        return response

# The framework automatically discovers it on next run!
agent = AIAgent(name="MotivationalBot")
agent.add_trait("Motivating", intensity=0.9)
print(agent.get_agent_summary())
    """)


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "AI Agent Framework - Quick Start Examples" + " "*13 + "║")
    print("╚" + "="*68 + "╝")
    
    examples = [
        example_1_simple_agent,
        example_2_response_personality,
        example_3_dynamic_adjustment,
        example_4_specialized_agents,
        example_5_trait_inspection,
        example_6_interaction_analysis,
        example_7_export_state,
        example_8_llm_integration,
        example_9_comparison,
        example_10_custom_trait,
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            example()
        except Exception as e:
            print(f"\nNote: Example {i} encountered an issue (expected for some examples): {e}")
    
    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70)
    print("\nFor the full demonstration with all features, run: python main.py")
    print("For complete documentation, see: README.md\n")


if __name__ == "__main__":
    main()
