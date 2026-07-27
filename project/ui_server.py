"""
Web UI Server for AI Agent Framework
Provides REST API and serves interactive UI for the personality trait system.
"""

from flask import Flask, render_template, request, jsonify, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

import analytics_store
import quota_store
from agent import AIAgent
from llm_client import LLMNotConfiguredError

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

# Per-IP rate limiting. In-memory storage is process-local (fine for a single
# dev/demo instance; a multi-process deployment would need a shared backend
# like Redis instead). The default covers every route; chat/regenerate get a
# tighter limit since those are the ones that actually cost LLM API calls.
limiter = Limiter(
    key_func=get_remote_address,
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
    if 'uid' not in session:
        session['uid'] = uuid.uuid4().hex
        session.permanent = True
    return agents_by_session.setdefault(session['uid'], {})


def get_session_chats():
    """Return the arena chats dict belonging to the current browser session."""
    if 'uid' not in session:
        session['uid'] = uuid.uuid4().hex
        session.permanent = True
    return chats_by_session.setdefault(session['uid'], {})


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
    return render_template('index.html')


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


@app.route('/analytics')
def analytics_page():
    """Serve the public Arena analytics page."""
    return render_template('analytics.html')


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

        ip = get_remote_address()
        if not quota_store.has_budget(ip):
            return jsonify({'success': False, 'error': 'Daily testing limit reached.', 'quota_exceeded': True}), 429

        agent = agents[agent_id]
        reply, tokens_charged = agent.generate_llm_reply(message)
        quota_store.charge(ip, tokens_charged)

        profile = agent.get_behavioral_profile()

        return jsonify({
            'success': True,
            'reply': reply,
            'traits': profile['traits']['traits']
        })
    except LLMNotConfiguredError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except (APIConnectionError, APITimeoutError, RateLimitError, APIStatusError):
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

        ip = get_remote_address()
        if not quota_store.has_budget(ip):
            return jsonify({'success': False, 'error': 'Daily testing limit reached.', 'quota_exceeded': True}), 429

        agent = agents[agent_id]
        reply, tokens_charged = agent.regenerate_last_reply()
        quota_store.charge(ip, tokens_charged)

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
    except (APIConnectionError, APITimeoutError, RateLimitError, APIStatusError):
        return jsonify({'success': False, 'error': LLM_UNAVAILABLE_MESSAGE}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


def _build_arena_agent(name: str) -> tuple[AIAgent, list[str]]:
    """Create an ephemeral agent with a random 1-3 traits at a fixed intensity."""
    agent = AIAgent(name=name)
    available = agent.list_available_traits()
    count = min(random.randint(ARENA_MIN_TRAITS, ARENA_MAX_TRAITS), len(available))
    trait_names = random.sample(available, k=count)
    for trait_name in trait_names:
        agent.add_trait(trait_name, intensity=ARENA_TRAIT_INTENSITY, weight=1.0)
    return agent, trait_names


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

        ip = get_remote_address()
        if not quota_store.has_budget(ip):
            return jsonify({'success': False, 'error': 'Daily testing limit reached.', 'quota_exceeded': True}), 429

        agent_a, traits_a = _build_arena_agent("Arena Option A")
        agent_b, traits_b = _build_arena_agent("Arena Option B")

        future_a = _arena_executor.submit(agent_a.generate_llm_reply, message, False, image_data_url)
        future_b = _arena_executor.submit(agent_b.generate_llm_reply, message, False, image_data_url)
        reply_a, tokens_a = future_a.result()
        reply_b, tokens_b = future_b.result()
        quota_store.charge(ip, tokens_a + tokens_b)

        round_id = analytics_store.record_round(traits_a, reply_a, traits_b, reply_b)

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
    except (APIConnectionError, APITimeoutError, RateLimitError, APIStatusError):
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

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Public, global aggregate stats for the Analytics page."""
    try:
        return jsonify({'success': True, 'summary': analytics_store.get_analytics_summary()})
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
    """Get emoji representation for a trait."""
    emoji_map = {
        # Original 10 traits
        'Smart': '🧠',
        'Creative': '🎨',
        'Curious': '🔍',
        'Efficient': '⚡',
        'Happy': '😊',
        'Sad': '😢',
        'Lazy': '😴',
        'Analytical': '📊',
        'RiskTaking': '🎲',
        'Empathetic': '❤️',
        # New 28 traits
        'Introverted': '🤐',
        'Extroverted': '🎉',
        'Patient': '⏳',
        'Impatient': '⚡',
        'Confident': '💪',
        'Humble': '🙏',
        'Serious': '😐',
        'Playful': '😄',
        'Logical': '🧮',
        'Intuitive': '🎯',
        'Organized': '📋',
        'Chaotic': '🌪️',
        'Cautious': '🛡️',
        'Aggressive': '👊',
        'Innovative': '💡',
        'Traditional': '🏛️',
        'Pragmatic': '🔧',
        'Idealistic': '🌟',
        'Witty': '😏',
        'Sincere': '💯',
        'Generous': '🎁',
        'Selfish': '💸',
        'Trusting': '🤝',
        'Skeptical': '🤨',
        'Calm': '🧘',
        'Anxious': '😰',
        'Perfectionist': '💎',
        'Apathetic': '😒',
        # New 30 traits - added for full A-Z coverage in the trait panel
        'Bold': '🦁',
        'Bubbly': '🫧',
        'Daring': '🤺',
        'Determined': '🔥',
        'Friendly': '🤗',
        'Focused': '🔬',
        'Grateful': '🍀',
        'Jovial': '😆',
        'Jealous': '😤',
        'Kind': '💚',
        'Keen': '👀',
        'Meticulous': '🧵',
        'Modest': '🙈',
        'Nostalgic': '📼',
        'Nurturing': '🌱',
        'Observant': '🔭',
        'Quirky': '🤪',
        'Quiet': '🤫',
        'Resilient': '🌳',
        'Understanding': '🫂',
        'Upbeat': '🎶',
        'Vibrant': '🌈',
        'Vigilant': '🕵️',
        'Warm': '☀️',
        'Xenial': '🏡',
        'Xenophilic': '🌍',
        'Yielding': '🕊️',
        'Youthful': '🎈',
        'Zealous': '🙌',
        'Zany': '🤹',
    }
    return emoji_map.get(trait_name, '✨')


if __name__ == '__main__':
    # Debug mode enables Werkzeug's interactive debugger, which allows arbitrary
    # code execution from the browser. Keep it off unless explicitly requested.
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'

    print("\n" + "="*70)
    print("AI Agent Framework - Web UI Server")
    print("="*70)
    print("\n🚀 Starting server...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server.\n")
    print("="*70 + "\n")

    app.run(debug=debug_mode, host='localhost', port=5000)

