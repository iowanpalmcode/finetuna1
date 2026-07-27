// Global state
const STARTER_TRAITS = ['Happy', 'Sad', 'Analytical'];
const MAX_ACTIVE_TRAITS = 5;
const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
const TOUR_KEY = 'aimotional_tour_done';
const THINKING_MESSAGES = [
    'Thinking…',
    'Weighing the personality traits…',
    'Considering how to phrase this…',
    'Drafting a reply…',
    'Putting it all together…'
];

let currentAgentId = null;
let availableTraits = [];
let activeTraitNames = new Set();
let onboardingPending = false; // true from a fresh chat until the user regenerates/skips
let onboardingSelection = new Set();
let hasAssistantReply = false;
let regenerationInFlight = false; // guards against overlapping /regenerate calls
let selectedLetter = null; // A-Z tab filter; null = nothing browsed yet
let chatListOpen = false;
let deleteConfirmStage = 0; // 0 = closed, 1 = first warning, 2 = typed confirmation

// Initialize on page load. Theme is already applied by theme.js (loaded
// synchronously in <head>, before this file), so there's nothing to do here
// beyond syncing the settings modal's radio buttons to the saved choice.
document.addEventListener('DOMContentLoaded', async () => {
    await loadTraits();
    await startNewChat();
    setupEventListeners();
    setupThemeControls();
    maybeRunTour();
});

function setupEventListeners() {
    document.getElementById('chatForm').addEventListener('submit', (e) => {
        e.preventDefault();
        sendMessage();
    });

    const chatInput = document.getElementById('chatInput');
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    chatInput.addEventListener('input', () => autoGrow(chatInput));

    document.getElementById('newChatBtn').addEventListener('click', () => {
        closeChatListPanel();
        startNewChat();
    });

    document.getElementById('traitSearch').addEventListener('input', () => {
        renderTraitList();
    });

    document.getElementById('onboardingRegenerateBtn').addEventListener('click', completeOnboarding);
    document.getElementById('onboardingSkipBtn').addEventListener('click', skipOnboarding);

    // Chat list dropdown
    document.getElementById('chatListToggle').addEventListener('click', (e) => {
        e.stopPropagation();
        toggleChatListPanel();
    });
    document.addEventListener('click', (e) => {
        if (chatListOpen && !e.target.closest('.chat-list-wrap')) {
            closeChatListPanel();
        }
    });

    // Settings modal
    document.getElementById('settingsBtn').addEventListener('click', openSettingsModal);
    document.getElementById('settingsCloseBtn').addEventListener('click', closeSettingsModal);
    document.getElementById('settingsModal').addEventListener('click', (e) => {
        if (e.target.id === 'settingsModal') closeSettingsModal();
    });
    document.getElementById('deleteAllBtn').addEventListener('click', startDeleteAllFlow);

    // Delete-all confirmation
    document.getElementById('deleteConfirmCancelBtn').addEventListener('click', cancelDeleteAllFlow);
    document.getElementById('deleteConfirmActionBtn').addEventListener('click', advanceDeleteAllFlow);
    document.getElementById('deleteConfirmModal').addEventListener('click', (e) => {
        if (e.target.id === 'deleteConfirmModal') cancelDeleteAllFlow();
    });

    // Tour
    document.getElementById('tourNextBtn').addEventListener('click', nextTourStep);
    document.getElementById('tourSkipBtn').addEventListener('click', endTour);
}

function autoGrow(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

function isAgentMissing(data) {
    return !data.success && typeof data.error === 'string' && data.error.toLowerCase().includes('agent not found');
}

async function recoverFromMissingAgent() {
    showError("This chat isn't available on the server anymore — starting a fresh one.");
    await startNewChat();
}

// ----- Agent / chat lifecycle -----

async function startNewChat() {
    try {
        const name = `Chat ${new Date().toLocaleString()}`;
        const response = await fetch('/api/agents', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await response.json();

        if (!data.success) {
            showError('Failed to start chat: ' + data.error);
            return;
        }

        currentAgentId = data.agent_id;
        activeTraitNames = new Set();
        onboardingPending = true;
        onboardingSelection = new Set();
        hasAssistantReply = false;

        resetChatUI();
    } catch (error) {
        showError('Error starting chat: ' + error.message);
    }
}

async function loadAgent(agentId) {
    try {
        const response = await fetch(`/api/agents/${agentId}/profile`);
        const data = await response.json();

        if (!data.success) {
            if (isAgentMissing(data)) {
                showError('That chat no longer exists.');
                return;
            }
            showError('Failed to load chat: ' + data.error);
            return;
        }

        currentAgentId = agentId;
        activeTraitNames = new Set(data.profile.traits.traits.map(t => t.name));
        onboardingPending = false; // returning to an existing conversation skips onboarding
        onboardingSelection = new Set();
        hasAssistantReply = data.profile.message_history.some(m => m.role === 'assistant');

        resetChatUI();
        (data.profile.message_history || []).forEach(m => {
            appendBubble(m.role === 'user' ? 'user' : 'assistant', m.content);
        });
        if (data.profile.message_history.length > 0) {
            document.getElementById('chatMessages').querySelector('.chat-empty-state')?.remove();
        }

        revealPanelAndTray(false);
        renderTraitPanel();
        renderEmojiTray();
    } catch (error) {
        showError('Error loading chat: ' + error.message);
    }
}

function resetChatUI() {
    const messages = document.getElementById('chatMessages');
    messages.innerHTML = '<div class="chat-empty-state"><div class="chat-empty-icon">💬</div><p>Send a message to start chatting.</p></div>';

    document.getElementById('onboardingWidget').style.display = 'none';
    document.getElementById('onboardingWidget').classList.remove('fading-out');
    document.getElementById('traitPanel').style.display = 'none';
    document.getElementById('emojiTray').style.display = 'none';
    document.getElementById('appMain').classList.add('single-column');
    document.getElementById('chatInput').value = '';

    renderTraitPanel();
    renderEmojiTray();
}

// ----- Chat messaging -----

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message || !currentAgentId) return;

    document.getElementById('chatMessages').querySelector('.chat-empty-state')?.remove();
    appendBubble('user', message);
    input.value = '';
    autoGrow(input);

    await sendToAgent(message, true);
}

async function sendToAgent(message, allowRecovery) {
    const typingEl = appendTypingIndicator();
    setSendingState(true);

    try {
        const response = await fetch(`/api/agents/${currentAgentId}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        const data = await response.json();
        removeTypingIndicator(typingEl);

        if (!data.success) {
            if (allowRecovery && isAgentMissing(data)) {
                await recoverFromMissingAgent();
                await sendToAgent(message, false); // one retry against the fresh agent
                return;
            }
            showError('Failed to get a reply: ' + data.error);
            return;
        }

        appendBubble('assistant', data.reply);
        activeTraitNames = new Set(data.traits.map(t => t.name));

        if (onboardingPending && !hasAssistantReply) {
            showOnboardingWidget();
        }
        hasAssistantReply = true;
    } catch (error) {
        removeTypingIndicator(typingEl);
        showError('Error sending message: ' + error.message);
    } finally {
        setSendingState(false);
    }
}

function setSendingState(sending) {
    document.getElementById('sendBtn').disabled = sending;
    document.getElementById('chatInput').disabled = sending;
}

function appendBubble(role, text) {
    const messages = document.getElementById('chatMessages');
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble chat-bubble-${role}`;
    bubble.textContent = text;
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
    return bubble;
}

function thinkingIndicatorHTML() {
    return `
        <span class="typing-dots"><span></span><span></span><span></span></span>
        <span class="typing-label">${THINKING_MESSAGES[0]}</span>
    `;
}

function startThinkingRotation(bubble) {
    let i = 0;
    const label = bubble.querySelector('.typing-label');
    return setInterval(() => {
        i = (i + 1) % THINKING_MESSAGES.length;
        if (label) label.textContent = THINKING_MESSAGES[i];
    }, 1700);
}

function appendTypingIndicator() {
    const messages = document.getElementById('chatMessages');
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble chat-bubble-assistant chat-bubble-typing';
    bubble.innerHTML = thinkingIndicatorHTML();
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;

    bubble._thinkingTimer = startThinkingRotation(bubble);
    return bubble;
}

function removeTypingIndicator(bubble) {
    if (!bubble) return;
    if (bubble._thinkingTimer) clearInterval(bubble._thinkingTimer);
    bubble.remove();
}

function lastAssistantBubble() {
    const bubbles = document.querySelectorAll('#chatMessages .chat-bubble-assistant:not(.chat-bubble-typing)');
    return bubbles.length ? bubbles[bubbles.length - 1] : null;
}

async function regenerateLastReply() {
    // Trait toggles fire fetches independently; without this guard, clicking a
    // second trait before the first regenerate resolves races the backend's
    // pop-last-exchange logic and fails with "No previous exchange to regenerate".
    if (regenerationInFlight) return;
    regenerationInFlight = true;
    setPanelBusy(true);

    const bubble = lastAssistantBubble();
    let originalHTML = null;
    let timer = null;

    if (bubble) {
        originalHTML = bubble.innerHTML;
        bubble.classList.add('chat-bubble-typing');
        bubble.innerHTML = thinkingIndicatorHTML();
        timer = startThinkingRotation(bubble);
    }

    try {
        const response = await fetch(`/api/agents/${currentAgentId}/regenerate`, { method: 'POST' });
        const data = await response.json();

        if (!data.success) {
            if (isAgentMissing(data)) {
                await recoverFromMissingAgent();
                return;
            }
            showError('Failed to regenerate: ' + data.error);
            if (bubble) bubble.innerHTML = originalHTML;
            return;
        }

        if (bubble) bubble.textContent = data.reply;
        activeTraitNames = new Set(data.traits.map(t => t.name));
    } catch (error) {
        showError('Error regenerating reply: ' + error.message);
        if (bubble) bubble.innerHTML = originalHTML;
    } finally {
        if (timer) clearInterval(timer);
        if (bubble) bubble.classList.remove('chat-bubble-typing');
        regenerationInFlight = false;
        setPanelBusy(false);
    }
}

function setPanelBusy(busy) {
    document.getElementById('traitPanel').classList.toggle('panel-busy', busy);
    document.getElementById('emojiTray').classList.toggle('panel-busy', busy);
}

// ----- Onboarding (first 3 starter emotions) -----

function showOnboardingWidget() {
    const chipsContainer = document.getElementById('onboardingChips');
    chipsContainer.innerHTML = '';
    onboardingSelection = new Set();

    STARTER_TRAITS.forEach(name => {
        const trait = availableTraits.find(t => t.name === name);
        if (!trait) return;

        const chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'onboarding-chip';
        chip.innerHTML = `<span class="trait-emoji">${trait.icon}</span> ${trait.name}`;
        chip.addEventListener('click', () => {
            if (onboardingSelection.has(name)) {
                onboardingSelection.delete(name);
                chip.classList.remove('selected');
            } else {
                onboardingSelection.add(name);
                chip.classList.add('selected');
            }
        });
        chipsContainer.appendChild(chip);
    });

    document.getElementById('onboardingWidget').style.display = 'block';
}

async function completeOnboarding() {
    if (regenerationInFlight) return;

    const regenBtn = document.getElementById('onboardingRegenerateBtn');
    const skipBtn = document.getElementById('onboardingSkipBtn');
    regenBtn.disabled = true;
    skipBtn.disabled = true;

    try {
        for (const name of onboardingSelection) {
            const res = await fetch(`/api/agents/${currentAgentId}/traits`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ trait: name, intensity: 0.7 })
            });
            const data = await res.json();
            if (!data.success && isAgentMissing(data)) {
                await recoverFromMissingAgent();
                return;
            }
        }

        if (onboardingSelection.size > 0) {
            await regenerateLastReply();
        }

        finishOnboarding();
    } catch (error) {
        showError('Error applying emotions: ' + error.message);
    } finally {
        regenBtn.disabled = false;
        skipBtn.disabled = false;
    }
}

function skipOnboarding() {
    finishOnboarding();
}

function finishOnboarding() {
    onboardingPending = false;
    hideOnboardingWidget();
    showSuccess('✨ Personality panel unlocked!');
    revealPanelAndTray(true);
    renderTraitPanel();
    renderEmojiTray();
}

function hideOnboardingWidget() {
    const widget = document.getElementById('onboardingWidget');
    widget.classList.add('fading-out');
    setTimeout(() => {
        widget.style.display = 'none';
        widget.classList.remove('fading-out');
    }, 250);
}

function revealPanelAndTray(animate) {
    const panel = document.getElementById('traitPanel');
    const tray = document.getElementById('emojiTray');

    panel.style.display = 'flex';
    tray.style.display = 'flex';
    document.getElementById('appMain').classList.remove('single-column');

    if (!animate) return;

    panel.classList.add('revealing');
    tray.classList.add('revealing');
    // Double rAF so the browser paints the "revealing" (hidden) state first,
    // otherwise removing the class in the same frame skips the transition.
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            panel.classList.remove('revealing');
            tray.classList.remove('revealing');
        });
    });
}

// ----- Trait side panel + emoji tray -----

async function loadTraits() {
    try {
        const response = await fetch('/api/traits');
        const data = await response.json();

        if (data.success) {
            availableTraits = data.traits;
            renderTraitPanel();
        } else {
            showError('Failed to load traits: ' + data.error);
        }
    } catch (error) {
        showError('Error loading traits: ' + error.message);
    }
}

function renderTraitPanel() {
    renderLetterTabs();
    renderTraitList();
}

// A-Z tab bar: all 26 letters always render so newly-added traits slot in
// automatically; a letter with no matching traits is shown but inert.
function renderLetterTabs() {
    const container = document.getElementById('traitLetterTabs');
    if (!container) return;
    container.innerHTML = '';

    LETTERS.forEach(letter => {
        const hasTraits = availableTraits.some(t => t.name.toUpperCase().startsWith(letter));

        const tab = document.createElement('button');
        tab.type = 'button';
        tab.className = `letter-tab${selectedLetter === letter ? ' active' : ''}`;
        tab.textContent = letter;
        tab.disabled = !hasTraits;
        tab.addEventListener('click', () => {
            selectedLetter = selectedLetter === letter ? null : letter;
            document.getElementById('traitSearch').value = '';
            renderTraitPanel();
        });

        container.appendChild(tab);
    });
}

// Shows matches for the search box if there's a query (search checks every
// trait regardless of the selected letter), otherwise the selected letter's
// traits, otherwise a prompt to pick a letter or search - no default full list.
function renderTraitList() {
    const container = document.getElementById('traitsContainer');
    if (!container) return;
    container.innerHTML = '';

    const query = document.getElementById('traitSearch').value.trim().toLowerCase();

    let matches = null;
    if (query) {
        matches = availableTraits.filter(t =>
            t.name.toLowerCase().includes(query) ||
            (t.description || '').toLowerCase().includes(query)
        );
    } else if (selectedLetter) {
        matches = availableTraits.filter(t => t.name.toUpperCase().startsWith(selectedLetter));
    }

    if (matches === null) {
        container.innerHTML = '<p class="traits-placeholder">Pick a letter above, or search, to browse emotions.</p>';
        return;
    }

    if (matches.length === 0) {
        container.innerHTML = '<p class="traits-placeholder">No matches.</p>';
        return;
    }

    matches.forEach(trait => container.appendChild(createTraitToggle(trait)));
}

function createTraitToggle(trait) {
    const isActive = activeTraitNames.has(trait.name);
    const atLimit = !isActive && activeTraitNames.size >= MAX_ACTIVE_TRAITS;

    const badge = document.createElement('button');
    badge.type = 'button';
    badge.className = `trait-badge${isActive ? ' active' : ''}${atLimit ? ' disabled' : ''}`;
    badge.innerHTML = `
        <span class="trait-emoji">${trait.icon}</span>
        <span>${trait.name}</span>
        ${isActive ? '<span class="trait-check">✓</span>' : ''}
    `;

    badge.addEventListener('click', () => toggleTrait(trait.name));

    return badge;
}

async function toggleTrait(traitName) {
    if (!currentAgentId || regenerationInFlight) return;

    const isActive = activeTraitNames.has(traitName);

    if (!isActive && activeTraitNames.size >= MAX_ACTIVE_TRAITS) {
        showError(`Trait limit reached (${MAX_ACTIVE_TRAITS} max)`);
        return;
    }

    try {
        let response;
        if (isActive) {
            response = await fetch(`/api/agents/${currentAgentId}/traits/${traitName}`, { method: 'DELETE' });
        } else {
            response = await fetch(`/api/agents/${currentAgentId}/traits`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ trait: traitName, intensity: 0.7 })
            });
        }

        const data = await response.json();
        if (!data.success) {
            if (isAgentMissing(data)) {
                await recoverFromMissingAgent();
                return;
            }
            showError('Failed to update trait: ' + data.error);
            return;
        }

        activeTraitNames = new Set(data.traits.map(t => t.name));
        renderTraitPanel();
        renderEmojiTray();

        if (hasAssistantReply) {
            await regenerateLastReply();
        }
    } catch (error) {
        showError('Error updating trait: ' + error.message);
    }
}

function renderEmojiTray() {
    const list = document.getElementById('emojiTrayList');
    if (!list) return;
    list.innerHTML = '';

    if (activeTraitNames.size === 0) {
        list.innerHTML = '<p class="emoji-tray-empty">None selected</p>';
        return;
    }

    activeTraitNames.forEach(name => {
        const trait = availableTraits.find(t => t.name === name);
        const icon = trait ? trait.icon : '✨';

        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'emoji-tray-item';
        item.title = `Remove ${name}`;
        item.innerHTML = `<span class="trait-emoji">${icon}</span>`;
        item.addEventListener('click', () => toggleTrait(name));

        list.appendChild(item);
    });
}

// ----- Chat list (past chats: switch / delete) -----

async function refreshChatList() {
    try {
        const response = await fetch('/api/agents');
        const data = await response.json();
        if (!data.success) return;
        renderChatList(data.agents);
    } catch (error) {
        showError('Error loading past chats: ' + error.message);
    }
}

function renderChatList(agents) {
    const container = document.getElementById('chatListItems');
    container.innerHTML = '';

    if (!agents.length) {
        container.innerHTML = '<p class="chat-list-empty">No past chats yet</p>';
        return;
    }

    // Newest first - agent ids are created in increasing order server-side.
    [...agents].reverse().forEach(agent => {
        const row = document.createElement('div');
        row.className = `chat-list-item${agent.agent_id === currentAgentId ? ' active' : ''}`;

        const label = document.createElement('button');
        label.type = 'button';
        label.className = 'chat-list-item-label';
        label.textContent = `${agent.agent_name} (${agent.trait_count})`;
        label.addEventListener('click', () => {
            closeChatListPanel();
            loadAgent(agent.agent_id);
        });

        const del = document.createElement('button');
        del.type = 'button';
        del.className = 'chat-list-item-delete';
        del.title = 'Delete this chat';
        del.textContent = '🗑️';
        del.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteSingleChat(agent.agent_id, agent.agent_name);
        });

        row.appendChild(label);
        row.appendChild(del);
        container.appendChild(row);
    });
}

function toggleChatListPanel() {
    chatListOpen = !chatListOpen;
    document.getElementById('chatListPanel').style.display = chatListOpen ? 'block' : 'none';
    if (chatListOpen) refreshChatList();
}

function closeChatListPanel() {
    chatListOpen = false;
    document.getElementById('chatListPanel').style.display = 'none';
}

async function deleteSingleChat(agentId, agentName) {
    if (!confirm(`Delete "${agentName}"? This can't be undone.`)) return;

    try {
        const response = await fetch(`/api/agents/${agentId}/delete`, { method: 'DELETE' });
        const data = await response.json();

        if (!data.success) {
            showError('Failed to delete chat: ' + data.error);
            return;
        }

        closeChatListPanel();
        if (agentId === currentAgentId) {
            await startNewChat();
        }
    } catch (error) {
        showError('Error deleting chat: ' + error.message);
    }
}

// ----- Settings: theme (application logic lives in theme.js, shared with
// the classic UI and the legal pages so a chosen theme applies everywhere) -----

function setupThemeControls() {
    const saved = window.AIMotionalTheme.get();
    const radio = document.querySelector(`input[name="theme"][value="${saved}"]`);
    if (radio) radio.checked = true;

    document.querySelectorAll('input[name="theme"]').forEach(input => {
        input.addEventListener('change', () => {
            if (!input.checked) return;
            window.AIMotionalTheme.set(input.value);
        });
    });
}

function openSettingsModal() {
    document.getElementById('settingsModal').style.display = 'flex';
}

function closeSettingsModal() {
    document.getElementById('settingsModal').style.display = 'none';
}

// ----- Settings: delete all chats (asks twice, second time requires typing DELETE) -----

function startDeleteAllFlow() {
    closeSettingsModal();
    deleteConfirmStage = 1;
    document.getElementById('deleteConfirmTitle').textContent = 'Delete all chats?';
    document.getElementById('deleteConfirmText').textContent =
        'This permanently deletes every chat in this session. This cannot be undone.';
    const input = document.getElementById('deleteConfirmInput');
    input.style.display = 'none';
    input.value = '';
    document.getElementById('deleteConfirmActionBtn').textContent = 'Continue';
    document.getElementById('deleteConfirmModal').style.display = 'flex';
}

function advanceDeleteAllFlow() {
    if (deleteConfirmStage === 1) {
        deleteConfirmStage = 2;
        document.getElementById('deleteConfirmTitle').textContent = 'Are you absolutely sure?';
        document.getElementById('deleteConfirmText').textContent =
            'Type DELETE below to permanently erase every chat. There is no undo.';
        const input = document.getElementById('deleteConfirmInput');
        input.style.display = 'block';
        input.value = '';
        input.focus();
        document.getElementById('deleteConfirmActionBtn').textContent = 'Delete Everything';
    } else if (deleteConfirmStage === 2) {
        const input = document.getElementById('deleteConfirmInput');
        if (input.value.trim() !== 'DELETE') {
            showError('Type DELETE exactly to confirm.');
            return;
        }
        performDeleteAll();
    }
}

function cancelDeleteAllFlow() {
    deleteConfirmStage = 0;
    document.getElementById('deleteConfirmModal').style.display = 'none';
}

async function performDeleteAll() {
    try {
        const response = await fetch('/api/agents', { method: 'DELETE' });
        const data = await response.json();

        if (!data.success) {
            showError('Failed to delete chats: ' + data.error);
            return;
        }

        cancelDeleteAllFlow();
        closeSettingsModal();
        showSuccess('All chats deleted.');
        await startNewChat();
    } catch (error) {
        showError('Error deleting chats: ' + error.message);
    }
}

// ----- First-run guided tour -----

const TOUR_STEPS = [
    { target: 'chatInput', title: 'Say something', body: 'Type your first message here, just like you would with any chatbot.' },
    { target: 'sendBtn', title: 'Send it', body: 'Click Send (or press Enter) to get a reply.' },
    { target: 'newChatBtn', title: 'Start fresh anytime', body: 'Click here to start a brand-new chat whenever you want. Your old ones are kept.' },
    { target: 'chatListToggle', title: 'Jump back to old chats', body: 'Every chat you start is saved here (up to 20) so you can switch back to it anytime.' },
    { target: 'appFooter', title: "That's it!", body: 'One more thing: the About, Terms of Service, Privacy Policy, and Research links live down here.' }
];

let tourStepIndex = 0;

function maybeRunTour() {
    if (localStorage.getItem(TOUR_KEY)) return;
    tourStepIndex = 0;
    document.getElementById('tourOverlay').style.display = 'block';
    showTourStep(0);
    window.addEventListener('resize', repositionTourSpotlight);
}

function showTourStep(index) {
    tourStepIndex = index;
    const step = TOUR_STEPS[index];
    const target = document.getElementById(step.target);

    document.getElementById('tourStepCount').textContent = `Step ${index + 1} of ${TOUR_STEPS.length}`;
    document.getElementById('tourTitle').textContent = step.title;
    document.getElementById('tourBody').textContent = step.body;
    document.getElementById('tourNextBtn').textContent = index === TOUR_STEPS.length - 1 ? 'Done' : 'Next';

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
    localStorage.setItem(TOUR_KEY, '1');
}

// ----- Toasts -----

function showError(message) {
    showToast(message, '#ff6b6b');
}

function showSuccess(message) {
    showToast(message, '#4caf50');
}

function showToast(message, color) {
    const alert = document.createElement('div');
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${color};
        color: white;
        padding: 15px 20px;
        border-radius: 6px;
        z-index: 2000;
        animation: slideIn 0.3s ease;
        max-width: 400px;
    `;
    alert.textContent = message;
    document.body.appendChild(alert);

    setTimeout(() => alert.remove(), 4000);
}
