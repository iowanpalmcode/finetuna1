"""
LLM Integration Guide for AI Agent Framework

This module provides utilities and patterns for integrating the personality
framework with Large Language Models (LLMs) like OpenAI, Anthropic, etc.
"""

import json
from typing import Dict, Any, Optional
from agent import AIAgent


class LLMIntegrationHelper:
    """
    Helper class for integrating AIAgent with LLM APIs.
    Provides utilities to build prompts, manage context, and apply personality.
    """
    
    @staticmethod
    def generate_system_prompt(agent: AIAgent, additional_context: str = "") -> str:
        """
        Generate a system prompt incorporating the agent's personality.
        
        Args:
            agent: AIAgent instance
            additional_context: Additional instructions for the LLM
            
        Returns:
            Formatted system prompt string
        """
        profile = agent.get_behavioral_profile()
        
        system_prompt = f"""You are an AI assistant with a distinct personality profile.

Agent Personality: {profile['behavioral_summary']}

Active Personality Traits:
"""
        
        for trait in profile['traits']['traits']:
            pct = trait['intensity'] * 100
            system_prompt += f"- {trait['name']}: {pct:.0f}%\n"
        
        if profile['traits']['traits']:
            system_prompt += f"\nTotal Personality Influence: {profile['traits']['total_influence']:.1f}/10\n"
        
        system_prompt += """
Trait Behavioral Guidelines:
"""
        
        # Add trait-specific guidelines
        trait_guidelines = {
            "Smart": "Provide detailed analysis and demonstrate logical reasoning.",
            "Creative": "Think outside the box and propose novel solutions.",
            "Curious": "Ask probing questions and explore topics deeply.",
            "Empathetic": "Consider others' feelings and show compassion.",
            "Efficient": "Be concise and focus on practical solutions.",
            "Analytical": "Use data and evidence to support conclusions.",
            "Happy": "Maintain a positive tone and highlight opportunities.",
            "Lazy": "Prefer direct, minimal solutions.",
            "RiskTaking": "Consider bold, unconventional approaches.",
            "Sad": "Acknowledge deeper emotional dimensions.",
        }
        
        active_traits = profile['traits']['traits']
        for trait in active_traits:
            trait_name = trait['name']
            if trait_name in trait_guidelines:
                system_prompt += f"- {trait_name}: {trait_guidelines[trait_name]}\n"
        
        if additional_context:
            system_prompt += f"\nAdditional Context:\n{additional_context}\n"
        
        system_prompt += "\nRespond in a way that authentically reflects this personality."
        
        return system_prompt
    
    @staticmethod
    def build_openai_messages(
        agent: AIAgent,
        user_message: str,
        system_context: str = "",
        conversation_history: Optional[list] = None
    ) -> list:
        """
        Build message list for OpenAI API.
        
        Args:
            agent: AIAgent instance
            user_message: User's current message
            system_context: Additional system context
            conversation_history: Previous messages (for context)
            
        Returns:
            Messages list ready for OpenAI API
        """
        messages = []
        
        # Add system message with personality
        system_prompt = LLMIntegrationHelper.generate_system_prompt(agent, system_context)
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    @staticmethod
    def build_anthropic_prompt(
        agent: AIAgent,
        user_message: str,
        system_context: str = ""
    ) -> tuple:
        """
        Build prompt for Anthropic Claude API.
        
        Args:
            agent: AIAgent instance
            user_message: User's current message
            system_context: Additional system context
            
        Returns:
            Tuple of (system_prompt, user_message)
        """
        system_prompt = LLMIntegrationHelper.generate_system_prompt(agent, system_context)
        return system_prompt, user_message
    
    @staticmethod
    def apply_personality_to_response(agent: AIAgent, response: str) -> str:
        """
        Apply agent personality to LLM response for final styling.
        
        Args:
            agent: AIAgent instance
            response: Response from LLM
            
        Returns:
            Response modified by agent personality
        """
        return agent.process_response(response)
    
    @staticmethod
    def create_personality_json_schema(agent: AIAgent) -> Dict[str, Any]:
        """
        Create JSON schema representing agent personality.
        Useful for function calling and structured responses.
        
        Args:
            agent: AIAgent instance
            
        Returns:
            JSON schema dictionary
        """
        profile = agent.get_behavioral_profile()
        
        return {
            "agent_name": profile['agent_name'],
            "behavioral_summary": profile['behavioral_summary'],
            "traits": {
                trait['name']: {
                    "description": trait['description'],
                    "intensity": trait['intensity'],
                    "weight": trait['weight'],
                    "influence": trait['effective_influence']
                }
                for trait in profile['traits']['traits']
            },
            "total_influence": profile['traits']['total_influence'],
            "interaction_count": len(profile['interactions'])
        }


# Integration Examples for Different LLM Providers

OPENAI_EXAMPLE = """
# OpenAI Integration Example

from openai import OpenAI
from agent import AIAgent
from llm_integration import LLMIntegrationHelper

client = OpenAI(api_key="your-api-key")

# Create agent with personality
agent = AIAgent(name="Creative Assistant")
agent.add_trait("Creative", intensity=0.9)
agent.add_trait("Curious", intensity=0.8)

# Build messages with personality
messages = LLMIntegrationHelper.build_openai_messages(
    agent=agent,
    user_message="Generate a creative product idea for a tech startup",
    system_context="Focus on sustainable and innovative solutions"
)

# Call OpenAI API
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    temperature=0.8,  # Higher for creative traits
    max_tokens=1000
)

# Extract and optionally refine response
llm_response = response.choices[0].message.content
final_response = LLMIntegrationHelper.apply_personality_to_response(
    agent, 
    llm_response
)

print(final_response)
"""

ANTHROPIC_EXAMPLE = """
# Anthropic Claude Integration Example

import anthropic
from agent import AIAgent
from llm_integration import LLMIntegrationHelper

client = anthropic.Anthropic(api_key="your-api-key")

# Create agent with personality
agent = AIAgent(name="Analytical Advisor")
agent.add_trait("Analytical", intensity=0.9)
agent.add_trait("Smart", intensity=0.85)

# Build prompt with personality
system_prompt, user_message = LLMIntegrationHelper.build_anthropic_prompt(
    agent=agent,
    user_message="Analyze the market opportunity for AI-powered healthcare solutions",
    system_context="Provide deep, evidence-based analysis"
)

# Call Claude API
response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=2000,
    system=system_prompt,
    messages=[
        {"role": "user", "content": user_message}
    ]
)

# Extract response
llm_response = response.content[0].text
final_response = LLMIntegrationHelper.apply_personality_to_response(
    agent,
    llm_response
)

print(final_response)
"""

LOCAL_OLLAMA_EXAMPLE = """
# Local Ollama Integration Example

import requests
import json
from agent import AIAgent
from llm_integration import LLMIntegrationHelper

# Create agent with personality
agent = AIAgent(name="Local Assistant")
agent.add_trait("Smart", intensity=0.8)
agent.add_trait("Helpful", intensity=0.9)  # Note: May not exist, add if needed

# Build messages
system_prompt = LLMIntegrationHelper.generate_system_prompt(agent)

# Call local Ollama instance
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "mistral",
        "system": system_prompt,
        "prompt": "What are best practices for Python development?",
        "stream": False
    }
)

llm_response = response.json()['response']
final_response = LLMIntegrationHelper.apply_personality_to_response(
    agent,
    llm_response
)

print(final_response)
"""

MULTI_AGENT_CONVERSATION = """
# Multi-Agent Conversation Example

from agent import AIAgent
from llm_integration import LLMIntegrationHelper
import openai

client = openai.OpenAI(api_key="your-api-key")

# Create agents with different personalities
devil_advocate = AIAgent(name="Devil's Advocate")
devil_advocate.add_trait("Analytical", 0.9)
devil_advocate.add_trait("Smart", 0.85)

optimist = AIAgent(name="Optimist")
optimist.add_trait("Happy", 0.9)
optimist.add_trait("Creative", 0.8)

# Topic for discussion
topic = "Should we invest in this new technology startup?"

# Get responses from each agent
perspectives = {}

for agent in [devil_advocate, optimist]:
    messages = LLMIntegrationHelper.build_openai_messages(
        agent=agent,
        user_message=f"Provide your perspective on: {topic}"
    )
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )
    
    perspectives[agent.name] = response.choices[0].message.content

# Print perspectives
for agent_name, perspective in perspectives.items():
    print(f"\n{agent_name}:")
    print(perspective)
"""

DYNAMIC_PERSONALITY_ADJUSTMENT = """
# Dynamic Personality Adjustment Based on Context

from agent import AIAgent
from llm_integration import LLMIntegrationHelper
import openai

client = openai.OpenAI(api_key="your-api-key")

agent = AIAgent(name="Adaptive Agent")
agent.add_trait("Smart", 0.5)
agent.add_trait("Creative", 0.5)

# Detect task type and adjust personality
task_type = "technical_problem"  # or "creative_brainstorm", "analysis", etc.

if task_type == "technical_problem":
    agent.adjust_trait("Smart", intensity=0.95)
    agent.adjust_trait("Creative", intensity=0.2)
    temperature = 0.3  # Lower for analytical
    
elif task_type == "creative_brainstorm":
    agent.adjust_trait("Smart", intensity=0.3)
    agent.adjust_trait("Creative", intensity=0.95)
    temperature = 0.9  # Higher for creative

# Get profile for this context
profile = agent.get_behavioral_profile()
print(f"Context: {task_type}")
print(f"Personality: {profile['behavioral_summary']}")

# Call LLM with adjusted temperature matching personality
messages = LLMIntegrationHelper.build_openai_messages(
    agent=agent,
    user_message="Generate ideas for our project"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    temperature=temperature
)

print(response.choices[0].message.content)
"""

PERSONALITY_PROMPT_ENGINEERING = """
# Advanced Prompt Engineering with Personality Framework

from agent import AIAgent
from llm_integration import LLMIntegrationHelper

# Create specialized agent
expert_agent = AIAgent(name="Expert Consultant")
expert_agent.add_trait("Smart", 0.95)
expert_agent.add_trait("Analytical", 0.90)

# Generate multi-layered system prompt
base_prompt = LLMIntegrationHelper.generate_system_prompt(
    expert_agent,
    additional_context=\"\"\"
    Your role: Strategic technology consultant
    Audience: C-level executives
    Tone: Professional, evidence-based
    Output: Actionable recommendations with business impact
    \"\"\"
)

# Add persona-specific instructions
persona_prompt = base_prompt + \"\"\"

RESPONSE FORMAT:
1. Executive Summary (2-3 sentences)
2. Key Findings (5-7 bullet points)
3. Strategic Recommendations (3-5 items)
4. Risk Assessment
5. Success Metrics

STYLE GUIDE:
- Use data and evidence to support all claims
- Anticipate counterarguments and address them
- Provide quantifiable metrics where possible
- Consider second and third-order effects
\"\"\"

print(persona_prompt)
"""


def demonstrate_llm_integration():
    """Show LLM integration examples."""
    print("\\n" + "="*70)
    print("LLM Integration Patterns for AI Agent Framework")
    print("="*70)
    
    print("\n1. OpenAI Integration:")
    print("-"*70)
    print(OPENAI_EXAMPLE)
    
    print("\n2. Anthropic Claude Integration:")
    print("-"*70)
    print(ANTHROPIC_EXAMPLE)
    
    print("\n3. Local Ollama Integration:")
    print("-"*70)
    print(LOCAL_OLLAMA_EXAMPLE)
    
    print("\n4. Multi-Agent Conversation:")
    print("-"*70)
    print(MULTI_AGENT_CONVERSATION)
    
    print("\n5. Dynamic Personality Adjustment:")
    print("-"*70)
    print(DYNAMIC_PERSONALITY_ADJUSTMENT)
    
    print("\n6. Advanced Prompt Engineering:")
    print("-"*70)
    print(PERSONALITY_PROMPT_ENGINEERING)


if __name__ == "__main__":
    demonstrate_llm_integration()
