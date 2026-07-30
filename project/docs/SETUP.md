# Installation & Setup Guide

## Project Overview

The AI Agent Framework is a complete, production-quality Python system for building AI agents with modular, dynamic personality traits. This guide will help you get started quickly.

## Prerequisites

- **Python 3.7+** (Python 3.9+ recommended)
- **pip** (Python package manager)
- No external dependencies required for core functionality
- Optional: OpenAI, Anthropic, or other LLM libraries for integration

## Installation

### Option 1: Direct Usage (Recommended for Development)

1. **Navigate to the project directory:**
   ```bash
   cd project/
   ```

2. **Verify Python installation:**
   ```bash
   python --version
   # Should show Python 3.7 or higher
   ```

3. **Run the demonstration:**
   ```bash
   python main.py
   ```

### Option 2: Create a Virtual Environment

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies (optional, for LLM integration):**
   ```bash
   pip install openai anthropic
   ```

4. **Run the framework:**
   ```bash
   python main.py
   ```

## Project Structure

```
project/
├── agent.py                      # Main AIAgent class
├── trait_manager.py              # Trait management system
├── traits/                       # Personality traits
│   ├── __init__.py
│   ├── base_trait.py            # Abstract base class
│   ├── analytical.py
│   ├── creative.py
│   ├── curious.py
│   ├── efficient.py
│   ├── empathetic.py
│   ├── happy.py
│   ├── lazy.py
│   ├── risk_taking.py
│   └── smart.py
│   └── sad.py
├── interactions/                 # Trait interactions
│   ├── __init__.py
│   └── trait_interactions.py     # Interaction definitions
├── examples/                     # Usage examples
│   ├── quick_start.py           # Quick start guide
│   └── llm_integration_guide.py  # LLM integration patterns
├── main.py                       # Comprehensive demonstration
└── docs/                         # Documentation (README.md, SETUP.md, ...)
```

## Quick Start

### 1. Create Your First Agent

```python
from agent import AIAgent

# Create an agent
agent = AIAgent(name="MyAgent")

# Add personality traits
agent.add_trait("Smart", intensity=0.8)
agent.add_trait("Creative", intensity=0.7)

# View the profile
print(agent.get_agent_summary())
```

### 2. See Personality in Action

```python
# Process a response through personality
base = "You could try this approach."
modified = agent.process_response(base)
print(modified)
```

### 3. Explore Available Traits

```python
# List all available traits
available = agent.list_available_traits()
print(available)
# Output: ['Analytical', 'Creative', 'Curious', 'Efficient', 'Empathetic', 
#          'Happy', 'Lazy', 'RiskTaking', 'Sad', 'Smart']
```

## Common Tasks

### Add Multiple Traits

```python
from agent import AIAgent

agent = AIAgent(name="MultiTraitBot")
traits = [
    ("Smart", 0.9, 1.5),
    ("Curious", 0.8, 1.2),
    ("Happy", 0.7, 1.0),
]

for trait_name, intensity, weight in traits:
    agent.add_trait(trait_name, intensity, weight)

print(agent.get_agent_summary())
```

### Adjust Traits Dynamically

```python
# Boost one trait for a specific task
agent.adjust_trait("Smart", intensity=0.95)
agent.adjust_trait("Creative", intensity=0.2)

# View the profile
profile = agent.get_behavioral_profile()
print(profile['behavioral_summary'])
```

### Create Specialized Agents

```python
# Technical support agent
support = AIAgent(name="Support Bot")
support.add_trait("Empathetic", 0.9)
support.add_trait("Smart", 0.8)
support.add_trait("Efficient", 0.85)

# Analysis agent
analyst = AIAgent(name="Analysis Bot")
analyst.add_trait("Analytical", 0.95)
analyst.add_trait("Smart", 0.9)
analyst.add_trait("Curious", 0.7)
```

### Export Agent Configuration

```python
import json

agent = AIAgent(name="ExportBot")
agent.add_trait("Smart", 0.8)
agent.add_trait("Creative", 0.7)

# Export to JSON
json_config = agent.export_to_json()
print(json_config)

# Save to file
with open("agent_config.json", "w") as f:
    f.write(json_config)
```

## Creating Custom Traits

### Step 1: Create a New Trait File

Create `project/traits/your_trait.py`:

```python
from traits.base_trait import BaseTrait

class YourTrait(BaseTrait):
    @property
    def name(self) -> str:
        return "YourTrait"
    
    @property
    def description(self) -> str:
        return "Description of your trait"
    
    def modify_response(self, response: str) -> str:
        """Modify responses based on this trait."""
        if self.intensity > 0.7:
            # Strong implementation
            response = response.replace("word", "replacement")
        elif self.intensity > 0.3:
            # Moderate implementation
            pass
        return response
```

### Step 2: Use Your Trait

```python
from agent import AIAgent

agent = AIAgent(name="CustomBot")
agent.add_trait("YourTrait", intensity=0.8)
print(agent.get_agent_summary())
```

The framework automatically discovers your trait!

## Integration with LLM APIs

### OpenAI Example

```python
from openai import OpenAI
from agent import AIAgent
from examples.llm_integration_guide import LLMIntegrationHelper

client = OpenAI(api_key="sk-...")

agent = AIAgent(name="GPT Bot")
agent.add_trait("Smart", 0.9)
agent.add_trait("Creative", 0.7)

# Build messages with personality
messages = LLMIntegrationHelper.build_openai_messages(
    agent=agent,
    user_message="Generate a creative product idea"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=messages
)

print(response.choices[0].message.content)
```

### Anthropic Claude Example

```python
import anthropic
from agent import AIAgent
from examples.llm_integration_guide import LLMIntegrationHelper

client = anthropic.Anthropic(api_key="sk-ant-...")

agent = AIAgent(name="Claude Bot")
agent.add_trait("Analytical", 0.9)
agent.add_trait("Smart", 0.85)

system_prompt, user_msg = LLMIntegrationHelper.build_anthropic_prompt(
    agent=agent,
    user_message="Analyze market trends"
)

response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=2000,
    system=system_prompt,
    messages=[{"role": "user", "content": user_msg}]
)

print(response.content[0].text)
```

## Running Examples

### Comprehensive Demo

```bash
python main.py
```

Shows all features with 8 detailed demonstrations.

### Quick Start Examples

```bash
python examples/quick_start.py
```

10 focused examples for common use cases.

### LLM Integration Guide

```bash
python examples/llm_integration_guide.py
```

Shows patterns for integrating with various LLM providers.

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'agent'`

**Solution**: Make sure you're running from the `project/` directory:
```bash
cd project
python your_script.py
```

### Traits Not Discovered

**Problem**: `ValueError: Trait 'MyTrait' not found`

**Solution**: Ensure your trait file is in `project/traits/` with proper naming.

### Python Version Issues

**Problem**: Syntax errors or compatibility issues

**Solution**: Upgrade Python:
```bash
python --version  # Should be 3.7+
python -m pip install --upgrade python
```

## Performance Tips

1. **Minimize Active Traits**: Keep 3-5 active traits for optimal performance
2. **Reuse Agents**: Create agents once and adjust traits rather than recreating
3. **Batch Operations**: Process multiple responses in loops rather than one-by-one
4. **Cache Profiles**: Store behavioral profiles if queried repeatedly

## Next Steps

1. **Explore Examples**: Run `examples/quick_start.py` for practical patterns
2. **Read Full Docs**: See `README.md` for comprehensive documentation
3. **Create Traits**: Build custom traits for your use cases
4. **Integrate LLMs**: Use `examples/llm_integration_guide.py` for API integration
5. **Build Applications**: Create agents for your specific needs

## Support & Resources

- **Full Documentation**: See [README.md](README.md)
- **Examples**: Check `examples/` directory
- **Quick Start**: Run `examples/quick_start.py`
- **LLM Integration**: See `examples/llm_integration_guide.py`
- **Main Demo**: Run `main.py` to see all features

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         AIAgent (Main Interface)        │
├─────────────────────────────────────────┤
│  ├─ TraitManager (Trait Lifecycle)      │
│  │   ├─ Discover traits                 │
│  │   ├─ Add/Remove traits               │
│  │   └─ Adjust intensity/weight         │
│  │                                      │
│  ├─ InteractionManager (Trait Effects) │
│  │   ├─ Synergies                      │
│  │   ├─ Conflicts                      │
│  │   └─ Custom interactions            │
│  │                                      │
│  └─ Response Processing                │
│      └─ Apply trait modifications      │
├─────────────────────────────────────────┤
│   Traits (Modular Components)           │
│   ├─ BaseTrait (Abstract Base)          │
│   ├─ Smart, Creative, Curious, ...      │
│   └─ Custom Traits (Auto-discovered)    │
├─────────────────────────────────────────┤
│   Integration Layer (Optional)          │
│   ├─ OpenAI API                         │
│   ├─ Anthropic API                      │
│   ├─ Local LLMs                         │
│   └─ Custom LLM APIs                    │
└─────────────────────────────────────────┘
```

## System Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.7+ (3.9+ recommended) |
| Memory | 50MB minimum (100MB+ recommended) |
| Disk Space | 5MB for framework + traits |
| External Deps | None required (optional for LLM APIs) |

## License & Usage

This is a complete, production-quality implementation provided for direct use.

---

**You're ready to build amazing AI agents with dynamic personalities!**

Start with: `python main.py`
