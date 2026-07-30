# AI Agent with Modular Personality System

A **production-quality Python framework** for building AI agents with dynamic, modular personality traits. This framework enables creating agents with complex behavioral profiles through composable trait combinations, including support for trait interactions and emergent behavior.

🎨 **NEW: Web-Based UI!** A beautiful drag-and-drop interface for creating and testing agents. See [UI_README.md](UI_README.md) for details!

## Features

✨ **Core Capabilities**
- **Component-Based Architecture**: ECS-style trait system with automatic discovery
- **Dynamic Trait Loading**: Auto-discover traits from the traits directory using reflection
- **Runtime Trait Management**: Add, remove, and adjust traits at runtime
- **Trait Interactions**: Support for synergistic and conflicting trait combinations
- **Behavioral Profiles**: Aggregate trait effects into comprehensive behavioral profiles
- **Response Modification**: Traits can modify agent responses based on personality
- **JSON Export**: Serialize agent state for persistence or analysis
- **LLM-Ready**: Designed to integrate with OpenAI, Anthropic, and local LLM APIs

🏗️ **Architecture**
- Clean object-oriented design with abstract base classes
- Modular plugin architecture for extensibility
- Hook-based system for behavioral customization
- Priority/weight system for trait competition
- Bidirectional trait interaction tracking

📊 **Included Traits**
1. **Smart** - Intellectually capable, analytical, well-reasoned
2. **Lazy** - Prefers minimal effort and shortcuts
3. **Efficient** - Maximizes output with minimal waste
4. **Curious** - Inquisitive, eager to explore
5. **Happy** - Positive, optimistic outlook
6. **Sad** - Melancholic, reflective nature
7. **Creative** - Imaginative, innovative thinking
8. **Analytical** - Logical, systematic, data-driven
9. **RiskTaking** - Bold, adventurous, willing to take chances
10. **Empathetic** - Compassionate, emotionally aware

## Project Structure

```
project/
├── agent.py                    # Main AIAgent class
├── trait_manager.py            # TraitManager for lifecycle management
├── traits/
│   ├── __init__.py
│   ├── base_trait.py          # Abstract BaseTrait class
│   ├── lazy.py                # Example traits...
│   ├── smart.py
│   ├── efficient.py
│   ├── curious.py
│   ├── happy.py
│   ├── sad.py
│   ├── creative.py
│   ├── analytical.py
│   ├── risk_taking.py
│   └── empathetic.py
├── interactions/
│   ├── __init__.py
│   └── trait_interactions.py   # Interaction manager & definitions
├── examples/                   # Example implementations
├── main.py                     # Comprehensive demonstration
└── docs/                       # Documentation (this file lives here)
```

## Quick Start

### Basic Usage

```python
from agent import AIAgent

# Create an agent
agent = AIAgent(name="Alice")

# Add personality traits
agent.add_trait("Smart", intensity=0.8, weight=1.5)
agent.add_trait("Curious", intensity=0.7, weight=1.2)
agent.add_trait("Happy", intensity=0.6)

# View behavioral profile
print(agent.get_agent_summary())

# Modify a response through personality
response = agent.process_response("This is a base response.")
print(response)
```

### Trait Management

```python
# List available traits
available = agent.list_available_traits()
print(f"Available: {available}")

# Adjust trait properties
agent.adjust_trait("Smart", intensity=0.9, weight=1.2)

# Remove a trait
agent.remove_trait("Happy")

# Get active traits
active = agent.list_active_traits()
```

### Behavioral Profiles

```python
# Get complete agent profile
profile = agent.get_behavioral_profile()

# Includes:
# - Trait details with intensity and weight
# - Active interactions between traits
# - Behavioral summary text
# - Normalized influence calculations

# Export to JSON
json_state = agent.export_to_json()
```

## Creating Custom Traits

Create a new file in the `traits/` directory:

```python
# traits/mystrait.py
from traits.base_trait import BaseTrait

class MyTrait(BaseTrait):
    @property
    def name(self) -> str:
        return "MyTrait"
    
    @property
    def description(self) -> str:
        return "Description of what this trait does"
    
    def modify_response(self, response: str) -> str:
        """Modify responses based on this trait."""
        if self.intensity > 0.7:
            # Make response more aligned with this trait
            response = response.replace("word", "replacement")
        return response
```

The framework automatically discovers and loads your trait on startup!

## Trait Interactions

The framework includes pre-defined interactions between traits:

- **Lazy + Smart** → Synergy: Prefers efficient shortcuts
- **Curious + Smart** → Synergy: Asks exploratory questions
- **Happy + Creative** → Synergy: Generates novel ideas
- **Analytical + Creative** → Conflict: Logic vs. innovation
- **RiskTaking + Analytical** → Conflict: Caution vs. boldness
- **Empathetic + Sad** → Synergy: Deeper emotional understanding

### Define Custom Interactions

```python
from interactions.trait_interactions import (
    TraitInteraction, InteractionType
)

interaction = TraitInteraction(
    trait_a="Smart",
    trait_b="Lazy",
    interaction_type=InteractionType.SYNERGY,
    modifier=0.15,
    description="Smart + Lazy → prefers shortcuts"
)

agent.interaction_manager.register_interaction(interaction)
```

## API Reference

### AIAgent Class

```python
class AIAgent:
    # Initialization
    __init__(name: str, traits_directory: str, auto_register_interactions: bool)
    
    # Trait Management
    add_trait(trait_name: str, intensity: float, weight: float) -> None
    remove_trait(trait_name: str) -> bool
    adjust_trait(trait_name: str, intensity: float, weight: float) -> bool
    
    # Queries
    list_active_traits() -> Dict[str, Any]
    list_available_traits() -> List[str]
    get_behavioral_profile() -> Dict[str, Any]
    
    # Response Processing
    process_response(base_response: str) -> str
    trigger_behavior_hook(hook_name: str, context: Dict) -> Any
    
    # Utilities
    get_agent_summary() -> str
    export_to_json() -> str
```

### BaseTrait Class

All traits inherit from `BaseTrait`:

```python
class BaseTrait(ABC):
    # Properties
    intensity: float          # 0.0-1.0, strength of trait
    weight: float            # Priority for competing traits
    
    # Abstract Properties (implement in subclasses)
    name: str               # Trait name
    description: str        # Trait description
    
    # Methods
    modify_response(response: str) -> str
    get_behavioral_profile() -> Dict[str, Any]
    register_hook(hook_name: str, callback: Callable) -> None
    trigger_hook(hook_name: str, context: Dict) -> Any
```

### TraitManager Class

```python
class TraitManager:
    # Discovery
    discover_traits() -> Dict[str, Type[BaseTrait]]
    
    # Management
    add_trait(trait_name: str, intensity: float, weight: float) -> BaseTrait
    remove_trait(trait_name: str) -> bool
    get_trait(trait_name: str) -> Optional[BaseTrait]
    
    # Queries
    list_active_traits() -> Dict[str, BaseTrait]
    list_available_traits() -> List[str]
    get_aggregate_profile() -> Dict[str, Any]
    
    # Adjustments
    adjust_trait_intensity(trait_name: str, intensity: float) -> bool
    adjust_trait_weight(trait_name: str, weight: float) -> bool
    clear_all_traits() -> None
    reset_to_default() -> None
```

## Demonstration

Run the comprehensive demonstration:

```bash
python main.py
```

This demonstrates:
1. Basic agent creation and trait management
2. Trait interactions and emergent behavior
3. Response modification through traits
4. Dynamic trait adjustment
5. Different trait combinations
6. Interaction details
7. Agent state export to JSON
8. Multi-agent comparison

## Use Cases

### 1. Personality-Driven AI Assistants
```python
# Customer service bot with empathy and efficiency
bot = AIAgent(name="CustomerService Bot")
bot.add_trait("Empathetic", intensity=0.9)
bot.add_trait("Efficient", intensity=0.8)
bot.add_trait("Smart", intensity=0.7)
```

### 2. Creative Content Generation
```python
# Blog writer with creativity and research curiosity
writer = AIAgent(name="Blog Writer")
writer.add_trait("Creative", intensity=0.95)
writer.add_trait("Curious", intensity=0.85)
writer.add_trait("Analytical", intensity=0.6)
```

### 3. Adaptive Problem Solver
```python
# Solver that adjusts based on problem type
solver = AIAgent(name="Problem Solver")
# Adjust traits based on problem characteristics
solver.adjust_trait("Analytical", intensity=problem_complexity)
solver.adjust_trait("Creative", intensity=1.0 - problem_complexity)
```

### 4. Multi-Agent Systems
```python
# Create teams with complementary personalities
team_lead = AIAgent(name="Team Lead")
team_lead.add_trait("Smart", 0.8)
team_lead.add_trait("Empathetic", 0.7)
team_lead.add_trait("Efficient", 0.9)

innovator = AIAgent(name="Innovator")
innovator.add_trait("Creative", 0.95)
innovator.add_trait("RiskTaking", 0.8)
```

## Integration with LLMs

The framework is designed to work seamlessly with LLM APIs:

```python
from agent import AIAgent
import openai

agent = AIAgent(name="GPT-Powered Agent")
agent.add_trait("Creative", intensity=0.8)
agent.add_trait("Analytical", intensity=0.7)

# Get profile to include in system prompt
profile = agent.get_behavioral_profile()

# Call LLM with personality-informed prompt
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{
        "role": "system",
        "content": f"You are {profile['behavioral_summary']}"
    }, {
        "role": "user",
        "content": "Generate a creative solution to this problem..."
    }]
)

# Process response through local traits
refined_response = agent.process_response(response['choices'][0]['message']['content'])
```

## Design Principles

1. **Modularity**: Each trait is independent and self-contained
2. **Extensibility**: Adding new traits requires only creating a new file
3. **Composition**: Complex behaviors emerge from trait combinations
4. **Clarity**: Clear separation of concerns with well-defined interfaces
5. **Performance**: Efficient trait discovery and management
6. **Type Safety**: Full type hints for IDE support and validation
7. **Testability**: Easy to unit test individual traits and interactions
8. **Documentation**: Comprehensive docstrings and examples

## Advanced Features

### Custom Hooks

```python
def my_hook(context, intensity):
    """Custom hook that modifies behavior."""
    context['custom_value'] = intensity * 100
    return context

trait = agent.get_trait("Smart")
trait.register_hook("on_response", my_hook)

# Trigger the hook
result = agent.trigger_behavior_hook("on_response", {})
```

### Behavioral Profiles as System Prompts

```python
profile = agent.get_behavioral_profile()
system_prompt = f"""
You are an AI agent with the following personality profile:

{profile['behavioral_summary']}

Active Traits:
{json.dumps([t['name'] for t in profile['traits']['traits']], indent=2)}

Behavioral Guidelines:
- Intensity levels indicate how strongly to embody each trait
- Traits may interact with each other to create emergent behaviors
- Adapt your responses to reflect these personality characteristics
"""
```

## Performance Characteristics

- **Trait Discovery**: O(n) where n = number of trait files
- **Trait Addition**: O(1) amortized
- **Response Processing**: O(t) where t = number of active traits
- **Behavioral Profile**: O(t² ) for interactions (n is small, typically ≤20)
- **Memory**: Minimal per trait (~1KB base, grows with hooks)

## Requirements

- Python 3.7+
- No external dependencies for core functionality
- Optional: OpenAI, Anthropic, or other LLM libraries for integration

## Testing

The main.py file includes comprehensive demonstrations that test all features:

```bash
python main.py
```

Expected output: All demonstrations pass with visual confirmation of:
- Trait loading
- Behavioral profile generation
- Response modification
- Interaction calculations
- JSON export

## Contributing

To extend this framework:

1. **Add New Traits**: Create new files in `traits/` following the BaseTrait pattern
2. **Define Interactions**: Register new interactions in trait_interactions.py
3. **Extend Hooks**: Add new hook types and register them in traits
4. **Enhance Profiles**: Extend behavioral_profile() methods for richer output

## License

This framework is provided as a complete, production-quality implementation.

## Future Enhancements

- 🔄 Trait learning and adaptation over time
- 📈 Personality evolution through interaction history
- 🎯 Goal-oriented trait adjustment
- 🧠 Memory system with trait-influenced recall
- 🌐 Network-based multi-agent personality synchronization
- 📊 Analytics and visualization of personality patterns
- 🔐 Personality persistence and versioning
- 🎮 Game-like personality progression systems

## Support

For questions or issues, refer to the included examples and demonstration script (main.py) for usage patterns.

---

**Built for production use with extensibility and maintainability in mind.**
