"""
Web UI Server for AI Agent Framework
Provides REST API and serves interactive UI for the personality trait system.
"""

from flask import Flask, render_template, request, jsonify, session, url_for
from flask_limiter import Limiter
from dotenv import load_dotenv
import base64
import binascii
import json
import os
import random
import re
import secrets
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

import analytics_store
import glicko
import quota_store
from agent import AIAgent
from llm_client import DEFAULT_MODEL_ID, MODEL_CHOICES, LLMEmptyReplyError, LLMNotConfiguredError

LLM_UNAVAILABLE_MESSAGE = "The AI service isn't working right now. Please try again later."

# Initialize Flask app
app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# Signs the session cookie that scopes each browser to its own agents below.
# Falls back to a fresh random key per process start (existing sessions are
# invalidated on restart) unless SECRET_KEY is set in the environment.
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(days=30)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Hard backstop on request body size (covers the ~33% base64 inflation of a
# 4MB image upload plus JSON overhead - see IMAGE_MAX_BYTES below).
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024

def _get_or_create_session_uid() -> str:
    """Stable id for this browser, backed by the signed session cookie.
    Shared by rate limiting and the agents/chats stores below so they all
    scope to the same identity."""
    if 'uid' not in session:
        session['uid'] = uuid.uuid4().hex
        session.permanent = True
    return session['uid']


# Per-browser rate limiting, keyed off the same session cookie the
# agents/chats stores use below - a sturdier unit than IP, which can be
# shared by many unrelated users (NAT/CGNAT/VPN/office network) or split
# across several IPs for one user (mobile networks). In-memory storage is
# process-local (fine for a single dev/demo instance; a multi-process
# deployment would need a shared backend like Redis instead). The default
# covers every route; chat/regenerate get a tighter limit since those are the
# ones that actually cost LLM API calls.
limiter = Limiter(
    key_func=_get_or_create_session_uid,
    app=app,
    default_limits=["60 per minute"],
    storage_uri="memory://",
)


@limiter.request_filter
def _exempt_static_files():
    return request.path.startswith('/static/')


@app.errorhandler(429)
def handle_rate_limit(e):
    """Return the same {success, error} JSON shape the frontend already expects."""
    return jsonify({'success': False, 'error': 'Too many requests - please slow down and try again shortly.'}), 429


@app.errorhandler(413)
def handle_payload_too_large(e):
    """Return the same {success, error} JSON shape for oversized request bodies (e.g. a huge image)."""
    return jsonify({'success': False, 'error': 'Request too large.'}), 413

# Store active agents in memory, keyed by browser session id so different
# browsers/users never see each other's agents (in production, use a database).
agents_by_session = {}
agent_counter = 0

# Arena chats: a separate in-memory, session-scoped store from agents_by_session
# above (which /classic still owns exclusively). Each chat holds an ordered
# list of arena rounds so the UI can offer switching between a handful of
# recent conversations, same "lost on restart, never written to disk" model
# as everything else in this app.
chats_by_session = {}
chat_counter = 0
MAX_ARENA_CHATS_PER_SESSION = 4
MAX_ROUNDS_PER_CHAT = 30

# Basic resource limits to avoid unbounded memory growth from repeated requests
MAX_AGENTS = 500
MAX_AGENT_NAME_LENGTH = 100
MAX_PROMPT_LENGTH = 5000
MAX_ACTIVE_TRAITS = 5
MAX_CHATS_PER_SESSION = 20

# Arena mode: each side gets a random 1-3 traits at a fixed, noticeably
# strong intensity (the manual UI's 0.5 default is too subtle to make two
# options feel meaningfully different when the user has no control over it).
ARENA_MIN_TRAITS = 1
ARENA_MAX_TRAITS = 3
ARENA_TRAIT_INTENSITY = 0.7

# Active learning: instead of picking both sides fully at random, generate a
# handful of candidate team pairs (each team weighted toward high-RD /
# under-sampled traits - see _weighted_random_team) and keep the pair whose
# aggregate ratings are closest. A near-even matchup is the most informative
# vote a user can cast under Glicko, and RD-weighting means traits Glicko is
# already confident about get asked about less often over time. A small
# fraction of rounds stay fully random so the pool never over-narrows onto
# only the traits that have played before.
ARENA_CANDIDATE_POOL_SIZE = 6
ARENA_EXPLORATION_PROB = 0.15

# XOR "raw" mechanic: with this probability, exactly one of the two sides
# (never both, never neither) skips traits entirely and answers as a plain,
# neutral assistant - a baseline for "does adding any personality trait at
# all help?" rather than just "which traits work best." Which side (A or B)
# goes raw is chosen with equal probability each time this triggers.
ARENA_RAW_PROB = 0.15

# After a vote, 1 in 5 rounds ask the user what made their pick better - a
# lightweight, occasional prompt rather than one on every single vote (which
# would get old fast and tank response rates).
FEEDBACK_PROMPT_PROB = 0.2
MAX_FEEDBACK_LENGTH = analytics_store.MAX_FEEDBACK_LENGTH

# Image uploads: validated but never decoded/resized server-side (no Pillow)
# so a crafted "tiny file, huge dimensions" image can't exhaust server memory
# here - the raw bytes are only ever inspected for size and a magic-number
# header, then passed straight through to OpenRouter. SVG is deliberately not
# in the allow-list since it can carry embedded scripts.
IMAGE_MAX_BYTES = 4 * 1024 * 1024
_IMAGE_DATA_URL_RE = re.compile(r'^data:image/(png|jpe?g|webp|gif);base64,(.+)$', re.DOTALL)
_IMAGE_MAGIC_BYTES = {
    'png': (b'\x89PNG\r\n\x1a\n',),
    'jpeg': (b'\xff\xd8\xff',),
    'jpg': (b'\xff\xd8\xff',),
    'gif': (b'GIF87a', b'GIF89a'),
    'webp': (b'RIFF',),  # full check (bytes 8-11 == b'WEBP') done in code below
}

analytics_store.init_db()
_arena_executor = ThreadPoolExecutor(max_workers=2)


def get_session_agents():
    """Return the agents dict belonging to the current browser session."""
    return agents_by_session.setdefault(_get_or_create_session_uid(), {})


def get_session_chats():
    """Return the arena chats dict belonging to the current browser session."""
    return chats_by_session.setdefault(_get_or_create_session_uid(), {})


class ImageValidationError(ValueError):
    """Raised when an uploaded image data URL fails validation."""


def _validate_image_data_url(data_url: str) -> str:
    """
    Validate a `data:image/...;base64,...` URL: allow-listed mime type, size
    cap, and a magic-byte check against the claimed type (catches a
    mislabeled/disguised file). Returns the same data URL unchanged if valid
    (it's passed straight through to the LLM provider - never decoded further
    here, deliberately, to avoid any server-side image-decompression risk).
    """
    match = _IMAGE_DATA_URL_RE.match(data_url or '')
    if not match:
        raise ImageValidationError('Unsupported image type. Use PNG, JPEG, WEBP, or GIF.')

    subtype, b64_payload = match.group(1).lower(), match.group(2)

    try:
        raw = base64.b64decode(b64_payload, validate=True)
    except (binascii.Error, ValueError):
        raise ImageValidationError('Image data is corrupted.')

    if len(raw) > IMAGE_MAX_BYTES:
        raise ImageValidationError(f'Image is too large (max {IMAGE_MAX_BYTES // (1024 * 1024)}MB).')
    if len(raw) == 0:
        raise ImageValidationError('Image data is empty.')

    if subtype == 'webp':
        magic_ok = raw[:4] == b'RIFF' and raw[8:12] == b'WEBP'
    else:
        magic_ok = any(raw.startswith(sig) for sig in _IMAGE_MAGIC_BYTES.get(subtype, ()))

    if not magic_ok:
        raise ImageValidationError('Image data does not match its declared type.')

    return data_url


@app.after_request
def set_security_headers(response):
    """Apply baseline hardening headers to every response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'

    # Static assets have no cache-busting filenames, so force revalidation on
    # every load rather than a long max-age - Flask's static handler already
    # sets ETag/Last-Modified, so a fresh asset costs a cheap 304, not a full
    # re-download, while a changed one is never served stale.
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-cache'

    return response


@app.route('/')
def index():
    """Serve the main UI page."""
    return render_template('index.html', shared_round_token='')


@app.route('/shared/<share_token>')
def shared_round_page(share_token):
    """Open the Arena with a shared round pre-loaded for voting."""
    return render_template('index.html', shared_round_token=share_token)


@app.route('/classic')
def classic():
    """Serve the original drag-and-drop trait builder UI."""
    return render_template('classic.html')


@app.route('/terms')
def terms():
    """Serve the Terms of Service page."""
    return render_template('terms.html')


@app.route('/privacy')
def privacy():
    """Serve the Privacy Policy page."""
    return render_template('privacy.html')


@app.route('/about')
def about():
    """Serve the About page (project intro + author info)."""
    return render_template('about.html')


@app.route('/traits-guide')
def traits_guide():
    """Serve a glossary of every personality trait and what it does."""
    agent = AIAgent(name="TraitsGuide")
    traits = sorted(agent.trait_manager.list_trait_details(), key=lambda t: t['name'].lower())
    return render_template('traits_guide.html', traits=traits)


@app.route('/analytics')
def analytics_page():
    """Serve the public Arena analytics page."""
    return render_template('analytics.html')


@app.route('/bulletin')
def bulletin_page():
    """Serve the daily top-voted shared rounds board."""
    return render_template('bulletin.html')


_traits_cache = None


@app.route('/api/traits', methods=['GET'])
def get_available_traits():
    """Get all available traits.

    Trait discovery (filesystem glob + importlib exec of every traits/*.py
    file) is fixed for the life of the process, but this endpoint is hit on
    nearly every page load and panel render - so memoize it instead of
    re-running discovery on every request.
    """
    try:
        global _traits_cache
        if _traits_cache is None:
            temp_agent = AIAgent(name="temp")
            traits = temp_agent.list_available_traits()

            trait_info = []
            for trait_name in traits:
                trait = temp_agent.trait_manager._trait_classes[trait_name]
                instance = trait()
                trait_info.append({
                    'name': trait_name,
                    'description': instance.description,
                    'icon': get_trait_emoji(trait_name)
                })

            _traits_cache = sorted(trait_info, key=lambda x: x['name'])

        return jsonify({
            'success': True,
            'traits': _traits_cache
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/agents', methods=['GET'])
def list_agents():
    """List all agents created in this session."""
    try:
        agents = get_session_agents()
        agent_list = [
            {
                'agent_id': agent_id,
                'agent_name': agent.name,
                'trait_count': len(agent.trait_manager.list_active_traits())
            }
            for agent_id, agent in agents.items()
        ]
        return jsonify({'success': True, 'agents': agent_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/agents', methods=['POST'])
@limiter.limit("20 per minute")
def create_agent():
    """Create a new agent."""
    try:
        global agent_counter
        agents = get_session_agents()

        if len(agents) >= MAX_AGENTS:
            return jsonify({'success': False, 'error': 'Agent limit reached. Delete an existing agent first.'}), 400

        data = request.json
        agent_name = data.get('name', f'Agent_{agent_counter}')

        if not isinstance(agent_name, str) or len(agent_name) > MAX_AGENT_NAME_LENGTH:
            return jsonify({'success': False, 'error': f'Agent name must be a string of at most {MAX_AGENT_NAME_LENGTH} characters'}), 400

        # Cap chats per session like a typical chat platform: rather than
        # blocking new chats, quietly drop the oldest one to make room. Dict
        # insertion order tracks creation order, so the first key is oldest.
        if len(agents) >= MAX_CHATS_PER_SESSION:
            oldest_id = next(iter(agents))
            del agents[oldest_id]

        agent = AIAgent(name=agent_name)
        agent_id = f"agent_{agent_counter}"
        agents[agent_id] = agent
        agent_counter += 1
        
        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'agent_name': agent_name
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/agents/<agent_id>/traits', methods=['POST'])
def add_trait_to_agent(agent_id):
    """Add a trait to an agent."""
    try:
        agents = get_session_agents()
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        
        data = request.json
        trait_name = data.get('trait')
        intensity = float(data.get('intensity', 0.7))

        agent = agents[agent_id]

        if trait_name not in agent.trait_manager.list_active_traits() and \
                len(agent.trait_manager.list_active_traits()) >= MAX_ACTIVE_TRAITS:
            return jsonify({'success': False, 'error': f'Trait limit reached ({MAX_ACTIVE_TRAITS} max)'}), 400

        agent.add_trait(trait_name, intensity=intensity, weight=1.0)
        
        # Get updated profile
        profile = agent.get_behavioral_profile()
        
        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'traits': profile['traits']['traits'],
            'summary': profile['behavioral_summary']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/agents/<agent_id>/traits/<trait_name>', methods=['PATCH'])
def adjust_trait_on_agent(agent_id, trait_name):
    """Adjust the intensity (and/or weight) of a trait already on an agent."""
    try:
        agents = get_session_agents()
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404

        data = request.json or {}
        intensity = data.get('intensity')
        weight = data.get('weight')
        intensity = float(intensity) if intensity is not None else None
        weight = float(weight) if weight is not None else None

        agent = agents[agent_id]
        if not agent.adjust_trait(trait_name, intensity=intensity, weight=weight):
            return jsonify({'success': False, 'error': f"Trait '{trait_name}' not found on agent"}), 404

        # Get updated profile
        profile = agent.get_behavioral_profile()

        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'traits': profile['traits']['traits'],
            'summary': profile['behavioral_summary']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/agents/<agent_id>/traits/<trait_name>', methods=['DELETE'])
def remove_trait_from_agent(agent_id, trait_name):
    """Remove a trait from an agent."""
    try:
        agents = get_session_agents()
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        
        agent = agents[agent_id]
        if not agent.remove_trait(trait_name):
            return jsonify({'success': False, 'error': f"Trait '{trait_name}' not found on agent"}), 404

        # Get updated profile
        profile = agent.get_behavioral_profile()

        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'traits': profile['traits']['traits'],
            'summary': profile['behavioral_summary']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/agents/<agent_id>/profile', methods=['GET'])
def get_agent_profile(agent_id):
    """Get agent's behavioral profile."""
    try:
        agents = get_session_agents()
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        
        agent = agents[agent_id]
        profile = agent.get_behavioral_profile()
        profile['message_history'] = agent.message_history

        return jsonify({
            'success': True,
            'profile': profile
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/agents/<agent_id>/generate', methods=['POST'])
def generate_response(agent_id):
    """Generate a response through the agent's personality."""
    try:
        agents = get_session_agents()
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404
        
        data = request.json
        base_response = data.get('prompt', '')

        if not base_response:
            return jsonify({'success': False, 'error': 'Prompt is required'}), 400

        if not isinstance(base_response, str) or len(base_response) > MAX_PROMPT_LENGTH:
            return jsonify({'success': False, 'error': f'Prompt must be a string of at most {MAX_PROMPT_LENGTH} characters'}), 400

        agent = agents[agent_id]
        
        # Process response through agent's personality
        modified_response = agent.process_response(base_response)
        
        # Get profile for reference
        profile = agent.get_behavioral_profile()
        
        return jsonify({
            'success': True,
            'original': base_response,
            'modified': modified_response,
            'personality_summary': profile['behavioral_summary'],
            'traits': profile['traits']['traits']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/agents/<agent_id>/chat', methods=['POST'])
@limiter.limit("15 per minute")
def chat_with_agent(agent_id):
    """Send a chat message to the agent and get an LLM-generated, personality-aware reply."""
    try:
        agents = get_session_agents()
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404

        data = request.json or {}
        message = data.get('message', '')

        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400

        if not isinstance(message, str) or len(message) > MAX_PROMPT_LENGTH:
            return jsonify({'success': False, 'error': f'Message must be a string of at most {MAX_PROMPT_LENGTH} characters'}), 400

        # Same signed session-cookie uid the rate limiter above uses - see
        # quota_store's module docstring for why this is per-browser, not per-IP.
        uid = _get_or_create_session_uid()
        if not quota_store.has_budget(uid):
            return jsonify({'success': False, 'error': 'Daily testing limit reached.', 'quota_exceeded': True}), 429

        agent = agents[agent_id]
        reply, tokens_charged = agent.generate_llm_reply(message, model_id=_resolve_model_id(data))
        quota_store.charge(uid, tokens_charged)

        profile = agent.get_behavioral_profile()

        return jsonify({
            'success': True,
            'reply': reply,
            'traits': profile['traits']['traits']
        })
    except LLMNotConfiguredError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except (APIConnectionError, APITimeoutError, RateLimitError, APIStatusError, LLMEmptyReplyError):
        return jsonify({'success': False, 'error': LLM_UNAVAILABLE_MESSAGE}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/agents/<agent_id>/regenerate', methods=['POST'])
@limiter.limit("15 per minute")
def regenerate_agent_reply(agent_id):
    """Regenerate the agent's most recent reply using its current active traits."""
    try:
        agents = get_session_agents()
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404

        data = request.json or {}

        uid = _get_or_create_session_uid()
        if not quota_store.has_budget(uid):
            return jsonify({'success': False, 'error': 'Daily testing limit reached.', 'quota_exceeded': True}), 429

        agent = agents[agent_id]
        reply, tokens_charged = agent.regenerate_last_reply(model_id=_resolve_model_id(data))
        quota_store.charge(uid, tokens_charged)

        profile = agent.get_behavioral_profile()

        return jsonify({
            'success': True,
            'reply': reply,
            'traits': profile['traits']['traits']
        })
    except LLMNotConfiguredError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except APIStatusError as e:
        print(f"LLM ERROR: {type(e).__name__}: {e}", flush=True)
        print(f"STATUS: {e.status_code}", flush=True)
        print(f"RESPONSE: {e.response}", flush=True)
        return jsonify({'success': False, 'error': f'{type(e).__name__}: {str(e)}'}), 503
    except (APIConnectionError, APITimeoutError, LLMEmptyReplyError) as e:
        print(f"LLM ERROR: {type(e).__name__}: {e}", flush=True)
        return jsonify({'success': False, 'error': f'{type(e).__name__}: {str(e)}'}), 503
    except Exception as e:
        print(f"ARENA UNEXPECTED ERROR: {type(e).__name__}: {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def _build_arena_agent(name: str, trait_names: list[str]) -> AIAgent:
    """Create an ephemeral agent carrying the given traits at a fixed intensity."""
    agent = AIAgent(name=name)
    for trait_name in trait_names:
        agent.add_trait(trait_name, intensity=ARENA_TRAIT_INTENSITY, weight=1.0)
    return agent


def _weighted_sample_without_replacement(items: list[str], weights: list[float], k: int) -> list[str]:
    """random.choices is with-replacement and random.sample doesn't take
    weights - trait lists are small, so repeatedly drawing-and-removing is
    simple and fast enough."""
    pool = list(items)
    pool_weights = list(weights)
    picked = []
    for _ in range(min(k, len(pool))):
        [choice] = random.choices(pool, weights=pool_weights, k=1)
        idx = pool.index(choice)
        pool.pop(idx)
        pool_weights.pop(idx)
        picked.append(choice)
    return picked


def _weighted_random_team(available: list[str], ratings: dict) -> list[str]:
    """Pick 1-3 traits, weighted toward high-RD (uncertain) traits so Arena
    naturally asks less about traits Glicko is already confident about.
    Traits with no history yet default to the maximum RD, so new traits are
    prioritized too."""
    count = min(random.randint(ARENA_MIN_TRAITS, ARENA_MAX_TRAITS), len(available))
    weights = [ratings.get(t, {}).get("rd", glicko.DEFAULT_RD) for t in available]
    return _weighted_sample_without_replacement(available, weights, count)


def _team_rating(traits: list[str], ratings: dict) -> float:
    values = [ratings.get(t, {}).get("rating", glicko.DEFAULT_RATING) for t in traits]
    return sum(values) / len(values) if values else glicko.DEFAULT_RATING


def _select_arena_teams(available: list[str], ratings: dict) -> tuple[list[str], list[str], Optional[str]]:
    """Pick this round's two trait teams (see ARENA_CANDIDATE_POOL_SIZE/
    ARENA_EXPLORATION_PROB/ARENA_RAW_PROB above for the reasoning).

    Returns (traits_a, traits_b, emotion_option), where emotion_option is
    'A' or 'B' naming which side carries traits when the raw/no-emotion XOR
    mechanic triggers this round, or None when both sides are trait-bearing
    as usual.
    """
    if available and random.random() < ARENA_RAW_PROB:
        emotion_team = _weighted_random_team(available, ratings)
        emotion_option = random.choice(('A', 'B'))
        if emotion_option == 'A':
            return emotion_team, [], emotion_option
        return [], emotion_team, emotion_option

    if random.random() < ARENA_EXPLORATION_PROB:
        return _weighted_random_team(available, ratings), _weighted_random_team(available, ratings), None

    best_pair = None
    best_gap = None
    for _ in range(ARENA_CANDIDATE_POOL_SIZE):
        team_a = _weighted_random_team(available, ratings)
        team_b = _weighted_random_team(available, ratings)
        gap = abs(_team_rating(team_a, ratings) - _team_rating(team_b, ratings))
        if best_gap is None or gap < best_gap:
            best_pair, best_gap = (team_a, team_b), gap
    return best_pair[0], best_pair[1], None


def _resolve_model_id(data: dict) -> str:
    """Validate the client-supplied model choice against the server-side
    allow-list, falling back to the default rather than trusting an
    arbitrary string through to the OpenRouter API."""
    model_id = data.get('model_id')
    return model_id if model_id in MODEL_CHOICES else DEFAULT_MODEL_ID


def _find_chat_and_round(chats, chat_id, round_id):
    """Look up a round dict by id within one of this session's chats, or (None, None)."""
    chat = chats.get(chat_id)
    if not chat:
        return None, None
    for round_record in chat['rounds']:
        if round_record['round_id'] == round_id:
            return chat, round_record
    return None, None


@app.route('/api/arena/round', methods=['POST'])
@limiter.limit("8 per minute")
def create_arena_round():
    """
    Generate one AI Arena round: two independently, randomly trait-tagged
    replies to the same prompt from two ephemeral agents (never stored in
    agents_by_session - each round is stateless). Optionally attaches an
    image (validated, never stored server-side) and appends the round to a
    session-owned chat (optional chat_id) for later switching/reload.
    """
    try:
        data = request.json or {}
        message = data.get('message', '')
        chat_id = data.get('chat_id')
        image_data_url = data.get('image')
        model_id = _resolve_model_id(data)

        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400

        if not isinstance(message, str) or len(message) > MAX_PROMPT_LENGTH:
            return jsonify({'success': False, 'error': f'Message must be a string of at most {MAX_PROMPT_LENGTH} characters'}), 400

        if image_data_url is not None:
            if not isinstance(image_data_url, str):
                return jsonify({'success': False, 'error': 'Invalid image data'}), 400
            try:
                image_data_url = _validate_image_data_url(image_data_url)
            except ImageValidationError as e:
                return jsonify({'success': False, 'error': str(e)}), 400

        uid = _get_or_create_session_uid()
        if not quota_store.has_budget(uid):
            return jsonify({'success': False, 'error': 'Daily testing limit reached.', 'quota_exceeded': True}), 429

        ratings = analytics_store.get_trait_ratings()
        available = AIAgent(name="Arena").list_available_traits()
        traits_a, traits_b, emotion_option = _select_arena_teams(available, ratings)
        agent_a = _build_arena_agent("Arena Option A", traits_a)
        agent_b = _build_arena_agent("Arena Option B", traits_b)

        future_a = _arena_executor.submit(agent_a.generate_llm_reply, message, False, image_data_url, model_id)
        future_b = _arena_executor.submit(agent_b.generate_llm_reply, message, False, image_data_url, model_id)
        reply_a, tokens_a = future_a.result()
        reply_b, tokens_b = future_b.result()
        quota_store.charge(uid, tokens_a + tokens_b)

        round_id = analytics_store.record_round(traits_a, reply_a, traits_b, reply_b)
        if emotion_option is not None:
            analytics_store.record_emotion_round(round_id, emotion_option)

        chats = get_session_chats()
        if chat_id in chats:
            chat = chats[chat_id]
            chat['rounds'].append({
                'round_id': round_id,
                'message': message,
                'option_a': {'reply': reply_a, 'traits': traits_a},
                'option_b': {'reply': reply_b, 'traits': traits_b},
                'voted_option': None,
                'had_image': image_data_url is not None,
                'share_token': None,
            })
            if len(chat['rounds']) > MAX_ROUNDS_PER_CHAT:
                chat['rounds'].pop(0)
            if chat['name'] is None:
                chat['name'] = message[:40]

        return jsonify({
            'success': True,
            'round_id': round_id,
            'option_a': {'reply': reply_a, 'traits': traits_a},
            'option_b': {'reply': reply_b, 'traits': traits_b},
        })
    except LLMNotConfiguredError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except (APIConnectionError, APITimeoutError, RateLimitError, APIStatusError, LLMEmptyReplyError):
        return jsonify({'success': False, 'error': LLM_UNAVAILABLE_MESSAGE}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/arena/round/<int:round_id>/vote', methods=['POST'])
@limiter.limit("30 per minute")
def vote_arena_round(round_id):
    """Record which option the user preferred for a round. First vote wins."""
    try:
        data = request.json or {}
        option = data.get('option')
        chat_id = data.get('chat_id')

        if option not in ('A', 'B'):
            return jsonify({'success': False, 'error': "option must be 'A' or 'B'"}), 400

        recorded = analytics_store.record_vote(round_id, option)
        if not recorded:
            return jsonify({'success': False, 'error': 'Round not found or already voted on'}), 409

        if chat_id:
            chats = get_session_chats()
            _, round_record = _find_chat_and_round(chats, chat_id, round_id)
            if round_record is not None:
                round_record['voted_option'] = option

        return jsonify({'success': True, 'show_feedback_prompt': random.random() < FEEDBACK_PROMPT_PROB})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/arena/round/<int:round_id>/feedback', methods=['POST'])
@limiter.limit("10 per minute")
def submit_arena_feedback(round_id):
    """Record optional free-text feedback on why the voted-for option was better."""
    try:
        data = request.json or {}
        feedback_text = data.get('feedback', '')

        if not isinstance(feedback_text, str) or not feedback_text.strip():
            return jsonify({'success': False, 'error': 'Feedback text is required'}), 400
        if len(feedback_text) > MAX_FEEDBACK_LENGTH:
            return jsonify({'success': False, 'error': f'Feedback must be at most {MAX_FEEDBACK_LENGTH} characters'}), 400

        saved = analytics_store.record_feedback(round_id, feedback_text.strip())
        if not saved:
            return jsonify({'success': False, 'error': 'Round not found, not yet voted on, or already has feedback'}), 409

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/arena/round/<int:round_id>/share', methods=['POST'])
@limiter.limit("20 per minute")
def share_arena_round(round_id):
    """Create (or return) a public share link for a round in this session chat."""
    try:
        data = request.json or {}
        chat_id = data.get('chat_id')
        if not chat_id:
            return jsonify({'success': False, 'error': 'chat_id is required'}), 400

        chats = get_session_chats()
        _, round_record = _find_chat_and_round(chats, chat_id, round_id)
        if round_record is None:
            return jsonify({'success': False, 'error': 'Round not found in this chat'}), 404

        share_token = round_record.get('share_token')
        if not share_token:
            share_token = analytics_store.create_shared_round(
                source_round_id=round_id,
                prompt_text=round_record['message'],
                option_a_reply=round_record['option_a']['reply'],
                option_b_reply=round_record['option_b']['reply'],
                option_a_traits=round_record['option_a']['traits'],
                option_b_traits=round_record['option_b']['traits'],
            )
            round_record['share_token'] = share_token

        share_url = url_for('shared_round_page', share_token=share_token, _external=True)
        return jsonify({'success': True, 'share_token': share_token, 'share_url': share_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/shared-rounds/<share_token>', methods=['GET'])
def get_shared_round(share_token):
    """Return a shared round and live vote totals."""
    try:
        round_data = analytics_store.get_shared_round(share_token, voter_uid=_get_or_create_session_uid())
        if not round_data:
            return jsonify({'success': False, 'error': 'Shared round not found'}), 404
        return jsonify({'success': True, 'round': round_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/shared-rounds/<share_token>/vote', methods=['POST'])
@limiter.limit("60 per minute")
def vote_shared_round(share_token):
    """Record this browser's vote for a shared round (one vote per browser)."""
    try:
        data = request.json or {}
        option = data.get('option')
        if option not in ('A', 'B'):
            return jsonify({'success': False, 'error': "option must be 'A' or 'B'"}), 400

        status = analytics_store.record_shared_round_vote(share_token, option, _get_or_create_session_uid())
        if status == 'not_found':
            return jsonify({'success': False, 'error': 'Shared round not found'}), 404

        round_data = analytics_store.get_shared_round(share_token, voter_uid=_get_or_create_session_uid())
        if not round_data:
            return jsonify({'success': False, 'error': 'Shared round not found'}), 404

        return jsonify({
            'success': True,
            'already_voted': status == 'already_voted',
            'round': round_data,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/bulletin/today', methods=['GET'])
def get_today_bulletin():
    """Top shared rounds by votes cast today."""
    try:
        limit_raw = request.args.get('limit', '10')
        try:
            limit = int(limit_raw)
        except ValueError:
            return jsonify({'success': False, 'error': 'limit must be an integer'}), 400

        rows = analytics_store.list_top_shared_rounds_today(limit=limit)
        return jsonify({'success': True, 'rounds': rows})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/warmup', methods=['GET'])
def warmup():
    """
    Fired by the frontend on page load, before the user has typed anything -
    a cheap way to absorb Render's free-tier spin-down cold start (and
    Neon's own separate cold start) outside the critical path of the user's
    first real Arena request, which otherwise has to eat that latency on top
    of its own LLM budget and can blow past gunicorn's timeout (see
    render.yaml). Best-effort: local dev without DATABASE_URL configured
    still returns success, since Flask itself being up is the main thing
    this needs to confirm in that case.
    """
    try:
        analytics_store.ping()
    except Exception:
        # Best-effort only - a slow/unreachable DB here shouldn't fail page
        # load or get surfaced as an error the user has to react to. Not
        # configured locally, a cold Neon endpoint being briefly outright
        # unreachable, transient network hiccups - all fine to just swallow.
        pass
    return jsonify({'success': True})


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Public, global aggregate stats for the Analytics page."""
    try:
        return jsonify({'success': True, 'summary': analytics_store.get_analytics_summary()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# Rough tokens-per-round estimate for the Settings modal's "X replies left"
# figure - matches quota_store's own "roughly 800-1000 tokens combined" note
# for a text round. An estimate, not a guarantee: actual usage varies with
# reply length (bounded by llm_client._MAX_REPLY_TOKENS) and image rounds
# cost far more.
_ESTIMATED_TOKENS_PER_ROUND = 900


@app.route('/api/quota', methods=['GET'])
def get_quota():
    """This browser's daily token usage/remaining, for the Settings modal."""
    try:
        uid = _get_or_create_session_uid()
        used = quota_store.used(uid)
        remaining = quota_store.remaining(uid)
        return jsonify({
            'success': True,
            'used_tokens': used,
            'remaining_tokens': remaining,
            'daily_budget': quota_store.DAILY_TOKEN_BUDGET,
            'estimated_rounds_remaining': remaining // _ESTIMATED_TOKENS_PER_ROUND,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/chats', methods=['GET'])
def list_chats():
    """List this session's arena chats, newest first."""
    try:
        chats = get_session_chats()
        chat_list = [
            {
                'chat_id': chat['chat_id'],
                'name': chat['name'] or 'New Chat',
                'round_count': len(chat['rounds']),
                'created_at': chat['created_at'],
            }
            for chat in chats.values()
        ]
        chat_list.reverse()
        return jsonify({'success': True, 'chats': chat_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/chats', methods=['POST'])
@limiter.limit("20 per minute")
def create_chat():
    """Create a new arena chat, evicting the oldest if already at the cap."""
    try:
        global chat_counter
        chats = get_session_chats()

        if len(chats) >= MAX_ARENA_CHATS_PER_SESSION:
            oldest_id = next(iter(chats))
            del chats[oldest_id]

        chat_id = f"chat_{chat_counter}"
        chat_counter += 1
        chats[chat_id] = {
            'chat_id': chat_id,
            'name': None,
            'created_at': datetime.utcnow().isoformat(),
            'rounds': [],
        }

        return jsonify({'success': True, 'chat_id': chat_id, 'name': 'New Chat'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get the full round history for one of this session's chats."""
    try:
        chats = get_session_chats()
        if chat_id not in chats:
            return jsonify({'success': False, 'error': 'Chat not found'}), 404

        return jsonify({'success': True, 'chat': chats[chat_id]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete one of this session's chats."""
    try:
        chats = get_session_chats()
        if chat_id not in chats:
            return jsonify({'success': False, 'error': 'Chat not found'}), 404

        del chats[chat_id]
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/chats', methods=['DELETE'])
def clear_chats():
    """Delete every arena chat belonging to the current browser session."""
    try:
        chats = get_session_chats()
        chats.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/agents/<agent_id>/delete', methods=['DELETE'])
def delete_agent(agent_id):
    """Delete an agent."""
    try:
        agents = get_session_agents()
        if agent_id not in agents:
            return jsonify({'success': False, 'error': 'Agent not found'}), 404

        del agents[agent_id]
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/agents', methods=['DELETE'])
def clear_agents():
    """Delete every agent belonging to the current browser session."""
    try:
        agents = get_session_agents()
        agents.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


def get_trait_emoji(trait_name: str) -> str:
    """Get a compact ASCII emoticon/label for a trait."""
    icon_map = {
        'Happy': ':-)',
        'Sad': ':-(',
        'Confident': 'B-)',
        'Calm': ':-|',
        'Anxious': ':-S',
        'Witty': ';-)',
        'Skeptical': ':-/',
        'Playful': ':-P',
        'Serious': ':-I',
        'Jealous': '>:-(',
        'Aggressive': '>:-|',
        'Kind': '<3',
    }
    if trait_name in icon_map:
        return icon_map[trait_name]
    return f"({trait_name[:2].upper()})"


if __name__ == '__main__':
    # Debug mode enables Werkzeug's interactive debugger, which allows arbitrary
    # code execution from the browser. Keep it off unless explicitly requested.
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'

    print("\n" + "="*70)
    print("AI Agent Framework - Web UI Server")
    print("="*70)
    print("\n(^_^) Starting server...")
    print("Open your browser and go to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server.\n")
    print("="*70 + "\n")

    app.run(debug=debug_mode, host='localhost', port=5000)

