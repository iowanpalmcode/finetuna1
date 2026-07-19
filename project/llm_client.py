"""
LLM client: turns an agent's active traits into a personality system prompt
and generates chat replies through OpenRouter's OpenAI-compatible API.

Replaces the old regex-based BaseTrait.modify_response approach - traits now
describe themselves in natural language and the LLM does the actual writing.
"""

import hashlib
import json
import os
import time
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from traits.base_trait import BaseTrait

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
PLACEHOLDER_KEY = "your-api-key-here"
DEFAULT_MODEL = "openai/gpt-oss-20b:free"

# In-memory cache for identical (system prompt, history, message) requests -
# avoids burning free-tier rate limits and API latency on repeats. Keyed by a
# hash rather than the raw text so cache entries stay a fixed, small size.
_response_cache: Dict[str, tuple] = {}  # key -> (cached_at, reply)
_CACHE_TTL_SECONDS = 600
_CACHE_MAX_ENTRIES = 200


def _cache_key(system_prompt: str, history: List[Dict[str, str]], user_message: str) -> str:
    payload = json.dumps(
        {"system": system_prompt, "history": history, "message": user_message},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class LLMNotConfiguredError(Exception):
    """Raised when no real OpenRouter API key is available."""


def _intensity_to_adverb(intensity: float) -> str:
    """Convert an intensity value to an English adverb."""
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


def build_system_prompt(active_traits: Dict[str, BaseTrait]) -> str:
    """Build a system prompt describing the assistant's active personality traits."""
    lines = ["You are a helpful, concise AI assistant."]

    for trait in active_traits.values():
        adverb = _intensity_to_adverb(trait.intensity)
        lines.append(f"You are {adverb} {trait.name.lower()}: {trait.description}.")

    if active_traits:
        lines.append(
            "Let these personality traits come through naturally in your tone and "
            "word choice, without explicitly announcing them."
        )

    return " ".join(lines)


def _get_client_and_model() -> tuple[OpenAI, str]:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key or api_key == PLACEHOLDER_KEY:
        raise LLMNotConfiguredError(
            "OPENROUTER_API_KEY is not configured. Add a real key to project/.env."
        )

    model = os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODEL
    client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
    return client, model


def generate_reply(
    system_prompt: str,
    history: List[Dict[str, str]],
    user_message: str,
    bypass_cache: bool = False,
) -> str:
    """
    Generate an assistant reply given a system prompt, prior turns, and a new
    user message.

    Args:
        system_prompt: Personality-aware system prompt from build_system_prompt.
        history: Prior turns as [{"role": "user"|"assistant", "content": str}, ...]
        user_message: The new user message to respond to.
        bypass_cache: Skip the cache read (used for regeneration, where a
            repeat of the exact cached answer would defeat the point of
            asking for a new attempt). The fresh result still gets cached.

    Returns:
        The assistant's reply text.
    """
    key = _cache_key(system_prompt, history, user_message)
    now = time.time()

    if not bypass_cache:
        cached = _response_cache.get(key)
        if cached is not None and now - cached[0] < _CACHE_TTL_SECONDS:
            return cached[1]

    client, model = _get_client_and_model()

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(model=model, messages=messages)
    reply = completion.choices[0].message.content

    _response_cache[key] = (now, reply)
    if len(_response_cache) > _CACHE_MAX_ENTRIES:
        oldest_key = min(_response_cache, key=lambda k: _response_cache[k][0])
        del _response_cache[oldest_key]

    return reply
