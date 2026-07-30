// Global state
let currentAgentId = null;
let availableTraits = [];
let draggedTrait = null;
let favoriteTraits = new Set(); // session-only, cleared on reload

// Touch/coarse-pointer devices can't do HTML5 drag-and-drop, and leaving
// draggable=true on those elements is known to make WebKit/Blink fight the
// browser's own touch-scroll gesture whenever a scroll happens to start on
// top of a trait badge. Tap-to-add (below) is the only interaction touch
// devices need, so drag is simply not wired up for them.
const isTouchDevice = window.matchMedia('(pointer: coarse)').matches || 'ontouchstart' in window;

// Rotating example prompts shown above the prompt textarea
const PROMPT_SUGGESTIONS = [
    "I will help you with this task.",
    "This is a good solution for your needs.",
    "The plan seems safe and should work well.",
    "I think we should proceed with this approach.",
    "Thank you for reaching out, I appreciate it.",
    "Let me know if you have any questions.",
    "We can complete this by the end of the week.",
    "I believe this is the right decision.",
];
let suggestionIndex = 0;
let suggestionTimer = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadTraits();
    setupEventListeners();
    loadPastAgents();
    startPromptSuggestions();
    maybeRunTour();
});

// Cycle through example prompts every 4 seconds; clicking one fills the textarea
function startPromptSuggestions() {
    const chip = document.getElementById('suggestionChip');
    const wrapper = document.getElementById('promptSuggestion');
    if (!chip || !wrapper) return;

    const showNext = () => {
        chip.textContent = PROMPT_SUGGESTIONS[suggestionIndex];
        suggestionIndex = (suggestionIndex + 1) % PROMPT_SUGGESTIONS.length;
    };

    showNext();
    suggestionTimer = setInterval(showNext, 4000);

    chip.addEventListener('click', () => {
        const promptInput = document.getElementById('promptInput');
        promptInput.value = chip.textContent;
        promptInput.focus();
    });

    // Pause rotation while the user is looking at/hovering the chip so it
    // doesn't change out from under them right as they go to click it.
    wrapper.addEventListener('mouseenter', () => clearInterval(suggestionTimer));
    wrapper.addEventListener('mouseleave', () => {
        suggestionTimer = setInterval(showNext, 4000);
    });
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('createAgentBtn').addEventListener('click', createAgent);
    document.getElementById('generateBtn').addEventListener('click', generateResponse);

    const dropZone = document.getElementById('dropZone');
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('drop', handleDrop);
    dropZone.addEventListener('dragleave', handleDragLeave);

    document.getElementById('traitSearch').addEventListener('input', (e) => {
        filterTraits(e.target.value);
    });

    document.getElementById('toggleTraitsBtn').addEventListener('click', toggleTraitsCollapse);

    document.getElementById('deleteAgentBtn').addEventListener('click', deleteSelectedAgent);
    document.getElementById('clearAgentsBtn').addEventListener('click', clearAllAgents);

    document.getElementById('pastAgentsSelect').addEventListener('change', (e) => {
        if (e.target.value) {
            loadAgent(e.target.value);
        }
    });

    document.getElementById('tourNextBtn').addEventListener('click', nextTourStep);
    document.getElementById('tourSkipBtn').addEventListener('click', endTour);
}

// Filter the available traits list by name or description
function filterTraits(query) {
    const normalized = query.trim().toLowerCase();
    const badges = document.querySelectorAll('#traitsContainer .trait-badge');

    badges.forEach(badge => {
        const matches = badge.dataset.name.includes(normalized) ||
                         badge.dataset.description.includes(normalized);
        badge.style.display = matches ? '' : 'none';
    });
}

// Load the list of past agents into the dropdown
async function loadPastAgents(selectAgentId = null) {
    try {
        const response = await fetch('/api/agents');
        const data = await response.json();

        if (!data.success) return;

        const select = document.getElementById('pastAgentsSelect');
        select.innerHTML = '<option value="">-- Select a past agent --</option>';

        data.agents.forEach(agent => {
            const option = document.createElement('option');
            option.value = agent.agent_id;
            option.textContent = `${agent.agent_name} (${agent.trait_count} traits)`;
            select.appendChild(option);
        });

        if (selectAgentId) {
            select.value = selectAgentId;
        }
    } catch (error) {
        showError('Error loading past agents: ' + error.message);
    }
}

// Switch to a previously created agent
async function loadAgent(agentId) {
    try {
        const response = await fetch(`/api/agents/${agentId}/profile`);
        const data = await response.json();

        if (!data.success) {
            showError('Failed to load agent: ' + data.error);
            return;
        }

        currentAgentId = agentId;
        const traits = data.profile.traits.traits;

        document.getElementById('agentName').value = data.profile.agent_name;
        renderAgentTraits(traits);
        updateAgentSummary(data.profile.behavioral_summary);
        document.getElementById('outputSection').style.display = 'none';
        document.getElementById('generateBtn').disabled = traits.length === 0;

        showSuccess(`Switched to agent "${data.profile.agent_name}"`);
    } catch (error) {
        showError('Error loading agent: ' + error.message);
    }
}

// Load available traits
async function loadTraits() {
    try {
        const response = await fetch('/api/traits');
        const data = await response.json();
        
        if (data.success) {
            availableTraits = data.traits;
            renderTraits();
        } else {
            showError('Failed to load traits: ' + data.error);
        }
    } catch (error) {
        showError('Error loading traits: ' + error.message);
    }
}

// Render available traits
function renderTraits() {
    const container = document.getElementById('traitsContainer');
    container.innerHTML = '';

    availableTraits.forEach(trait => {
        const badge = createTraitBadge(trait);
        container.appendChild(badge);
    });

    renderFavoritesBar();
}

// Build a single trait badge (draggable on desktop, tap-to-add on touch), including its favorite star toggle
function createTraitBadge(trait) {
    const badge = document.createElement('div');
    badge.className = 'trait-badge';
    badge.dataset.name = trait.name.toLowerCase();
    badge.dataset.description = (trait.description || '').toLowerCase();

    if (!isTouchDevice) {
        badge.draggable = true;
        badge.addEventListener('dragstart', (e) => {
            draggedTrait = trait;
            badge.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'copy';
        });

        badge.addEventListener('dragend', () => {
            badge.classList.remove('dragging');
        });
    }

    const isFavorite = favoriteTraits.has(trait.name);
    badge.innerHTML = `
        <span class="trait-emoji">${trait.icon}</span>
        <span>${trait.name}</span>
        <button type="button" class="trait-favorite-btn ${isFavorite ? 'active' : ''}" title="${isFavorite ? 'Remove from favorites' : 'Add to favorites'}">${isFavorite ? '★' : '☆'}</button>
    `;

    // A single tap/click adds the trait directly - this is the only way to add a
    // trait on touch devices (no drag), and is also just a quicker path on desktop.
    // On touch, this is driven off 'touchend' rather than 'click' so a tap can be
    // told apart from a scroll: a scroll also fires 'touchend' on whatever element
    // is under the finger when it lifts, so a real tap is only one where the touch
    // barely moved and didn't linger. preventDefault() on a genuine tap stops the
    // synthetic 'click' Android/iOS fire afterward, which would otherwise add the
    // trait a second time.
    let touchStartX = 0;
    let touchStartY = 0;
    let touchStartTime = 0;
    const TAP_MOVE_THRESHOLD = 10; // px
    const TAP_TIME_THRESHOLD = 500; // ms

    badge.addEventListener('touchstart', (e) => {
        const touch = e.touches[0];
        touchStartX = touch.clientX;
        touchStartY = touch.clientY;
        touchStartTime = Date.now();
    }, { passive: true });

    badge.addEventListener('touchend', (e) => {
        if (e.target.closest('.trait-favorite-btn')) return;

        const touch = e.changedTouches[0];
        const movedX = Math.abs(touch.clientX - touchStartX);
        const movedY = Math.abs(touch.clientY - touchStartY);
        const elapsed = Date.now() - touchStartTime;
        if (movedX > TAP_MOVE_THRESHOLD || movedY > TAP_MOVE_THRESHOLD || elapsed > TAP_TIME_THRESHOLD) {
            return; // was a scroll/long-press, not a tap
        }

        if (e.cancelable) e.preventDefault();
        addTraitOnTap(trait);
    });

    badge.addEventListener('click', (e) => {
        if (e.target.closest('.trait-favorite-btn')) return;
        addTraitOnTap(trait);
    });

    badge.querySelector('.trait-favorite-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        toggleFavoriteTrait(trait.name);
    });

    return badge;
}

function addTraitOnTap(trait) {
    if (!currentAgentId) {
        showError('Please create an agent first');
        return;
    }
    addTraitToAgent(trait.name);
}

// Toggle a trait's favorite status and refresh the badges/favorites bar
function toggleFavoriteTrait(traitName) {
    if (favoriteTraits.has(traitName)) {
        favoriteTraits.delete(traitName);
    } else {
        favoriteTraits.add(traitName);
    }

    const container = document.getElementById('traitsContainer');
    container.innerHTML = '';
    availableTraits.forEach(trait => container.appendChild(createTraitBadge(trait)));

    const searchQuery = document.getElementById('traitSearch').value;
    if (searchQuery) filterTraits(searchQuery);

    renderFavoritesBar();
}

// Render the compact favorites bar shown when the traits list is collapsed
function renderFavoritesBar() {
    const favBar = document.getElementById('favoritesBar');
    favBar.innerHTML = '';

    const favorites = availableTraits.filter(t => favoriteTraits.has(t.name));

    if (favorites.length === 0) {
        favBar.innerHTML = '<span class="favorites-empty">☆ a trait to pin it here when collapsed</span>';
        return;
    }

    favorites.forEach(trait => {
        favBar.appendChild(createTraitBadge(trait));
    });
}

// Collapse/expand the full traits list, swapping in the favorites-only bar
function toggleTraitsCollapse() {
    const container = document.getElementById('traitsContainer');
    const search = document.getElementById('traitSearch');
    const favBar = document.getElementById('favoritesBar');
    const btn = document.getElementById('toggleTraitsBtn');

    const collapsing = container.style.display !== 'none';

    container.style.display = collapsing ? 'none' : '';
    search.style.display = collapsing ? 'none' : '';
    favBar.style.display = collapsing ? 'flex' : 'none';
    btn.textContent = collapsing ? '▸' : '▾';
    btn.title = collapsing ? 'Expand' : 'Collapse';
}

// Handle drag over
function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    document.getElementById('dropZone').classList.add('drag-over');
}

// Handle drag leave
function handleDragLeave(e) {
    if (e.target.id === 'dropZone') {
        document.getElementById('dropZone').classList.remove('drag-over');
    }
}

// Handle drop
async function handleDrop(e) {
    e.preventDefault();
    document.getElementById('dropZone').classList.remove('drag-over');
    
    if (!draggedTrait || !currentAgentId) {
        showError('Please create an agent first');
        return;
    }
    
    await addTraitToAgent(draggedTrait.name);
    draggedTrait = null;
}

// Create a new agent
async function createAgent() {
    const agentName = document.getElementById('agentName').value || 'MyAgent';
    
    try {
        const response = await fetch('/api/agents', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: agentName })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentAgentId = data.agent_id;
            document.getElementById('agentTraits').innerHTML = '';
            document.getElementById('agentSummary').style.display = 'none';
            document.getElementById('outputSection').style.display = 'none';
            document.getElementById('generateBtn').disabled = true;

            await loadPastAgents(currentAgentId);
            showSuccess(`Agent "${data.agent_name}" created successfully!`);
        } else {
            showError('Failed to create agent: ' + data.error);
        }
    } catch (error) {
        showError('Error creating agent: ' + error.message);
    }
}

// Add trait to agent
async function addTraitToAgent(traitName) {
    if (!currentAgentId) return;
    
    try {
        const response = await fetch(`/api/agents/${currentAgentId}/traits`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                trait: traitName,
                intensity: 0.7
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderAgentTraits(data.traits);
            updateAgentSummary(data.summary);
            document.getElementById('generateBtn').disabled = false;
            document.getElementById('outputSection').style.display = 'none';
            await loadPastAgents(currentAgentId);
        } else {
            showError('Failed to add trait: ' + data.error);
        }
    } catch (error) {
        showError('Error adding trait: ' + error.message);
    }
}

// Render agent's traits
function renderAgentTraits(traits) {
    const container = document.getElementById('agentTraits');
    container.innerHTML = '';

    traits.forEach(trait => {
        const traitEl = document.createElement('div');
        traitEl.className = 'agent-trait';

        const traitObj = availableTraits.find(t => t.name === trait.name);
        const icon = traitObj ? traitObj.icon : '✨';
        const pct = Math.round(trait.intensity * 100);

        traitEl.innerHTML = `
            <span class="trait-emoji">${icon}</span>
            <span class="trait-name">${trait.name}</span>
            <input type="range" class="trait-intensity-slider" min="0" max="100" value="${pct}" data-trait="${trait.name}">
            <span class="trait-intensity-value">${pct}%</span>
            <button class="trait-remove" data-trait="${trait.name}">×</button>
        `;

        const slider = traitEl.querySelector('.trait-intensity-slider');
        const valueLabel = traitEl.querySelector('.trait-intensity-value');

        slider.addEventListener('input', () => {
            valueLabel.textContent = `${slider.value}%`;
        });

        slider.addEventListener('change', () => {
            adjustTraitIntensity(trait.name, Number(slider.value) / 100);
        });

        traitEl.querySelector('.trait-remove').addEventListener('click', () => {
            removeTraitFromAgent(trait.name);
        });

        container.appendChild(traitEl);
    });
}

// Adjust a trait's intensity on the agent
async function adjustTraitIntensity(traitName, intensity) {
    if (!currentAgentId) return;

    try {
        const response = await fetch(`/api/agents/${currentAgentId}/traits/${traitName}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ intensity })
        });

        const data = await response.json();

        if (data.success) {
            renderAgentTraits(data.traits);
            updateAgentSummary(data.summary);
        } else {
            showError('Failed to adjust trait: ' + data.error);
        }
    } catch (error) {
        showError('Error adjusting trait: ' + error.message);
    }
}

// Remove trait from agent
async function removeTraitFromAgent(traitName) {
    if (!currentAgentId) return;
    
    try {
        const response = await fetch(`/api/agents/${currentAgentId}/traits/${traitName}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderAgentTraits(data.traits);
            updateAgentSummary(data.summary);
            
            if (data.traits.length === 0) {
                document.getElementById('generateBtn').disabled = true;
                document.getElementById('outputSection').style.display = 'none';
            }
            await loadPastAgents(currentAgentId);
        } else {
            showError('Failed to remove trait: ' + data.error);
        }
    } catch (error) {
        showError('Error removing trait: ' + error.message);
    }
}

// Delete the agent currently selected in the Past Agents dropdown
async function deleteSelectedAgent() {
    const select = document.getElementById('pastAgentsSelect');
    const agentId = select.value;

    if (!agentId) {
        showError('Select a past agent to delete');
        return;
    }

    try {
        const response = await fetch(`/api/agents/${agentId}/delete`, { method: 'DELETE' });
        const data = await response.json();

        if (data.success) {
            if (agentId === currentAgentId) {
                resetAgentBuilder();
            }
            await loadPastAgents();
            showSuccess('Agent deleted');
        } else {
            showError('Failed to delete agent: ' + data.error);
        }
    } catch (error) {
        showError('Error deleting agent: ' + error.message);
    }
}

// Delete every agent for this browser
async function clearAllAgents() {
    if (!confirm('Delete all agents? This cannot be undone.')) return;

    try {
        const response = await fetch('/api/agents', { method: 'DELETE' });
        const data = await response.json();

        if (data.success) {
            resetAgentBuilder();
            await loadPastAgents();
            showSuccess('All agents cleared');
        } else {
            showError('Failed to clear agents: ' + data.error);
        }
    } catch (error) {
        showError('Error clearing agents: ' + error.message);
    }
}

// Reset the builder UI back to its empty/no-agent state
function resetAgentBuilder() {
    currentAgentId = null;
    document.getElementById('agentName').value = 'MyAgent';
    document.getElementById('agentTraits').innerHTML = '';
    document.getElementById('agentSummary').style.display = 'none';
    document.getElementById('outputSection').style.display = 'none';
    document.getElementById('generateBtn').disabled = true;
}

// Update agent summary
function updateAgentSummary(summary) {
    const summaryEl = document.getElementById('agentSummary');
    const summaryText = document.getElementById('summaryText');
    
    summaryText.textContent = summary;
    summaryEl.style.display = 'block';
}

// Generate response
async function generateResponse() {
    const prompt = document.getElementById('promptInput').value;
    
    if (!prompt.trim()) {
        showError('Please enter a prompt');
        return;
    }
    
    if (!currentAgentId) {
        showError('Please create an agent first');
        return;
    }
    
    try {
        document.getElementById('generateBtn').disabled = true;
        document.getElementById('generateBtn').textContent = '⏳ Generating...';
        
        const response = await fetch(`/api/agents/${currentAgentId}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayOutput(data);
        } else {
            showError('Failed to generate response: ' + data.error);
        }
    } catch (error) {
        showError('Error generating response: ' + error.message);
    } finally {
        document.getElementById('generateBtn').disabled = false;
        document.getElementById('generateBtn').textContent = '✨ Generate Personality Response';
    }
}

// Display generated output
function displayOutput(data) {
    document.getElementById('originalText').textContent = data.original;
    document.getElementById('modifiedText').textContent = data.modified;
    
    const traitsContainer = document.getElementById('outputTraits');
    traitsContainer.innerHTML = '';
    
    data.traits.forEach(trait => {
        const traitObj = availableTraits.find(t => t.name === trait.name);
        const icon = traitObj ? traitObj.icon : '✨';
        
        const traitEl = document.createElement('div');
        traitEl.className = 'trait-display';
        traitEl.textContent = `${icon} ${trait.name} (${Math.round(trait.intensity * 100)}%)`;
        traitsContainer.appendChild(traitEl);
    });
    
    document.getElementById('outputSection').style.display = 'block';
    
    // Scroll to output
    document.getElementById('outputSection').scrollIntoView({ behavior: 'smooth' });
}

// Show error message
function showError(message) {
    const alert = document.createElement('div');
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ff6b6b;
        color: white;
        padding: 15px 20px;
        border-radius: 6px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        max-width: 400px;
    `;
    alert.textContent = message;
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Show success message
function showSuccess(message) {
    const alert = document.createElement('div');
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4caf50;
        color: white;
        padding: 15px 20px;
        border-radius: 6px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        max-width: 400px;
    `;
    alert.textContent = message;
    document.body.appendChild(alert);

    setTimeout(() => {
        alert.remove();
    }, 3000);
}

// ----- First-run guided tour -----

const TOUR_KEY = 'aimotional_classic_tour_done';

const TOUR_STEPS = [
    {
        target: 'classicTitle',
        title: 'Welcome to the Classic Builder',
        body: 'Combine trait badges into a custom AI personality, then generate a response and see it change side-by-side with the original.'
    },
    {
        target: 'createAgentBtn',
        title: 'Create your agent',
        body: "Give it a name and click Create Agent. You'll need one before you can add any traits."
    },
    {
        target: 'traitsContainer',
        title: 'Add emotions & traits',
        body: 'Tap or click any trait below to add it to your agent instantly - one click is all it takes. On desktop you can also drag a trait into the box below instead.'
    },
    {
        target: 'dropZone',
        title: 'Fine-tune the mix',
        body: 'Each trait you add appears here with a slider - use it to control how strongly that trait comes through, or remove a trait with the × next to it.'
    },
    {
        target: 'generateBtn',
        title: 'Generate a response',
        body: "Type a prompt and click Generate to compare the original wording side-by-side with your agent's personality-shaped version."
    }
];

let tourStepIndex = 0;

function maybeRunTour() {
    if (localStorage.getItem(TOUR_KEY)) return;
    tourStepIndex = 0;
    document.getElementById('tourOverlay').style.display = 'block';
    showTourStep(0);
    window.addEventListener('resize', repositionTourSpotlight);
    window.addEventListener('scroll', repositionTourSpotlight, { passive: true });
}

function showTourStep(index) {
    tourStepIndex = index;
    const step = TOUR_STEPS[index];
    const target = document.getElementById(step.target);

    document.getElementById('tourStepCount').textContent = `Step ${index + 1} of ${TOUR_STEPS.length}`;
    document.getElementById('tourTitle').textContent = step.title;
    document.getElementById('tourBody').textContent = step.body;
    document.getElementById('tourNextBtn').textContent = index === TOUR_STEPS.length - 1 ? 'Done' : 'Next';

    if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    positionTourSpotlight(target);
}

function positionTourSpotlight(target) {
    const spotlight = document.getElementById('tourSpotlight');
    const tooltip = document.getElementById('tourTooltip');
    if (!target) {
        spotlight.style.display = 'none';
        return;
    }
    spotlight.style.display = 'block';

    const rect = target.getBoundingClientRect();
    const pad = 8;
    spotlight.style.top = `${rect.top - pad}px`;
    spotlight.style.left = `${rect.left - pad}px`;
    spotlight.style.width = `${rect.width + pad * 2}px`;
    spotlight.style.height = `${rect.height + pad * 2}px`;

    const tooltipWidth = 300;
    const tooltipTop = rect.bottom + 16;
    const wouldOverflowBottom = tooltipTop + 170 > window.innerHeight;

    tooltip.style.left = `${Math.min(Math.max(rect.left, 16), window.innerWidth - tooltipWidth - 16)}px`;
    tooltip.style.top = wouldOverflowBottom
        ? `${Math.max(rect.top - 180, 16)}px`
        : `${tooltipTop}px`;
}

function repositionTourSpotlight() {
    const step = TOUR_STEPS[tourStepIndex];
    if (!step) return;
    positionTourSpotlight(document.getElementById(step.target));
}

function nextTourStep() {
    if (tourStepIndex >= TOUR_STEPS.length - 1) {
        endTour();
        return;
    }
    showTourStep(tourStepIndex + 1);
}

function endTour() {
    document.getElementById('tourOverlay').style.display = 'none';
    window.removeEventListener('resize', repositionTourSpotlight);
    window.removeEventListener('scroll', repositionTourSpotlight);
    localStorage.setItem(TOUR_KEY, '1');
}
