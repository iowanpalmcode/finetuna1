Create a Python framework for an AI agent with a modular personality system.

Requirements:

1. The AI should be built using a component-based architecture similar to a game engine (Unity ECS-style or mixin-based design).

2. Personality traits should be independent modules that can be added, removed, or adjusted at runtime.

3. Each trait should exist as its own class/file and expose:

   * a name
   * a description
   * an intensity value (0.0–1.0)
   * hooks that can modify the AI's behavior

4. Example traits:

   * Lazy
   * Efficient
   * Smart
   * Curious
   * Happy
   * Sad
   * Creative
   * Analytical
   * RiskTaking
   * Empathetic

5. The framework should allow drag-and-drop extensibility:

   * adding a new trait should only require creating a new Python file in a traits folder
   * the system should automatically discover and load traits at startup using reflection/importlib

6. The core AI class should aggregate all active traits and produce a final behavioral profile.

7. Trait interactions should be supported. Example:

   * Lazy + Smart → prefers shortcuts
   * Curious + Smart → asks exploratory questions
   * Happy + Creative → generates more novel ideas

8. Provide a priority/weight system so traits can compete or cooperate.

9. Include:

   * base Trait abstract class
   * TraitManager
   * AIAgent class
   * plugin auto-loader
   * example traits
   * demonstration script

10. The architecture should make it easy to eventually connect the system to an LLM API (OpenAI, Anthropic, local models).

Focus heavily on maintainability, extensibility, and clean object-oriented design.

The final project structure should resemble:

project/
├── agent.py
├── trait_manager.py
├── traits/
│   ├── base_trait.py
│   ├── lazy.py
│   ├── smart.py
│   ├── efficient.py
│   └── ...
├── interactions/
├── examples/
└── main.py

Generate complete, production-quality Python code.
