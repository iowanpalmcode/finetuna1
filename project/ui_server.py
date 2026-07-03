"""
Web UI Server for AI Agent Framework
Provides REST API and serves interactive UI for the personality trait system.
"""

from flask import Flask, render_template, request, jsonify, session
import json
import os
import secrets
import sys
import uuid
from datetime import timedelta
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from agent import AIAgent

# Initialize Flask app
app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# Signs the session cookie that scopes each browser to its own agents below.
# Falls back to a fresh random key per process start (existing sessions are
# invalidated on restart) unless SECRET_KEY is set in the environment.
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(days=30)

# Store active agents in memory, keyed by browser session id so different
# browsers/users never see each other's agents (in production, use a database).
agents_by_session = {}
agent_counter = 0

# Basic resource limits to avoid unbounded memory growth from repeated requests
MAX_AGENTS = 500
MAX_AGENT_NAME_LENGTH = 100
MAX_PROMPT_LENGTH = 5000


def get_session_agents():
    """Return the agents dict belonging to the current browser session."""
    if 'uid' not in session:
        session['uid'] = uuid.uuid4().hex
        session.permanent = True
    return agents_by_session.setdefault(session['uid'], {})


@app.after_request
def set_security_headers(response):
    """Apply baseline hardening headers to every response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


@app.route('/')
def index():
    """Serve the main UI page."""
    return render_template('index.html')


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


@app.route('/api/traits', methods=['GET'])
def get_available_traits():
    """Get all available traits."""
    try:
        # Create a temporary agent to get available traits
        temp_agent = AIAgent(name="temp")
        traits = temp_agent.list_available_traits()
        
        # Get trait descriptions
        trait_info = []
        for trait_name in traits:
            trait = temp_agent.trait_manager._trait_classes[trait_name]
            instance = trait()
            trait_info.append({
                'name': trait_name,
                'description': instance.description,
                'icon': get_trait_emoji(trait_name)
            })
        
        return jsonify({
            'success': True,
            'traits': sorted(trait_info, key=lambda x: x['name'])
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
