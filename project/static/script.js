// Global state
const THINKING_MESSAGES = [
    'Thinking…',
    'Weighing the personality traits…',
    'Considering how to phrase this…',
    'Drafting a reply…',
    'Putting it all together…'
];
const TOUR_KEY = 'aimotional_arena_tour_done';

// Must match llm_client.DEFAULT_MODEL_ID and the <option> values in the
// Settings modal's #modelSelect - there's no server round-trip for this
// small, rarely-changing list (same approach as the theme picker).
const MODEL_STORAGE_KEY = 'aimotional_model_id';
const DEFAULT_MODEL_ID = 'nemotron-3-nano';

function getSelectedModelId() {
    return localStorage.getItem(MODEL_STORAGE_KEY) || DEFAULT_MODEL_ID;
}

// Parses a fetch Response as JSON, but fails with a clear message instead of
// the cryptic "Unexpected token '<'" crash when the server (or a hosting
// platform's proxy, on a slow/timed-out request) returns an HTML error page
// instead of JSON.
async function parseJsonResponse(response) {
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
        throw new Error(`The server took too long to respond (status ${response.status}). Please try again.`);
    }
    return response.json();
}
const IMAGE_MAX_BYTES = 4 * 1024 * 1024;
const ALLOWED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/webp', 'image/gif'];
const PROMPT_SUGGESTIONS = [
    "You accidentally send “I love you” to your teacher. What do you do?",
    "Your friend says pineapple belongs on pizza. Respond.",
    "You have $1,000 and 24 hours to spend it. What do you do?",
    "Explain why you were late to school.",
    "Convince me that pigeons are secretly intelligent.",
    "What's the best way to learn a new language?",
    'Write a short story about a robot who discovers music.',
    "Explain quantum computing like I'm five.",
    'Give me a recipe using only five ingredients.',
    'What are three tips for staying productive while working from home?',
    'Describe your ideal vacation destination.',
    'Help me write a birthday message for a friend.',
    "What's a fun fact about space that most people don't know?",
    'Make the case: cats vs. dogs as pets.',
    'How would you explain the internet to someone from the 1800s?',
    'Suggest a beginner-friendly workout routine.',
    "What's a creative way to say thank you?",
    "What's the best way to handle a difficult conversation?",
    "I failed an important test. What should I do?",
    "Should I quit something I've worked on for two years?",
    "I have to choose between two colleges. How should I decide?",
    "I don't know what I want to do with my life. What should I do?",
    "Is AI going to make programmers obsolete?",
    "Is college worth it?",
    "Should school start later?",
    "Are grades actually important?",
    "Is money more important than happiness?",
    "Should humans colonize Mars?",
    "Your best friend is dating someone you don't trust. What should you do?",
    "Someone hasn't responded to your text for three days. What do you do?",
    "Your friend asks you for brutally honest feedback. How do you respond?",
    "You discover your friend lied to you. What do you do?",
    "Someone takes credit for your work. How do you handle it?",
    "You have one chance to become famous. What do you do?",
    "Your best friend betrays you. What's your next move?",
    "You wake up with $10 million in your bank account. What's the first thing you do?",
    "You can delete one invention from human history. Which one?",
    "You have 30 days to completely reinvent yourself. What's your plan?",
    "You're the president for one day. What's the first law you pass?",
    "You can know the exact date you will die, but nothing else. Would you find out?",
    "You can instantly become world-class at one skill. Which skill do you choose?",
    "You are given a time machine that can only travel once. Where and when do you go? You can ask your future self one question, and they must answer honestly. What do you ask?",
    "What's the best way to learn a new language?",
    'Write a short story about a robot who discovers music.',
    "Explain quantum computing like I'm five.",
    'Give me a recipe using only five ingredients.',
    'What are three tips for staying productive while working from home?',
    'Describe your ideal vacation destination.',
    'Help me write a birthday message for a friend.',
    "What's a fun fact about space that most people don't know?",
    'Make the case: cats vs. dogs as pets.',
    'How would you explain the internet to someone from the 1800s?',
    'Suggest a beginner-friendly workout routine.',
    "What's a creative way to say thank you?"
];

let currentChatId = null;
let roundInFlight = false; // a request to /api/arena/round is out
let roundPending = false;  // a round has rendered but hasn't been voted on yet
let quotaExceeded = false; // true once the daily quota modal has fired
let chatListOpen = false;
let deleteConfirmStage = 0; // 0 = closed, 1 = first warning, 2 = typed confirmation
let pendingImage = null;   // { dataUrl, name } - session-only, never sent anywhere but the next round
let suggestionIndex = 0;
let pendingFeedbackRoundId = null; // round awaiting the "what made it better" popup, if any
let activeSharedRoundToken = null;

// Theme is already applied by theme.js (loaded synchronously in <head>,
// before this file), so there's nothing to do here beyond wiring up events.
document.addEventListener('DOMContentLoaded', async () => {
    // Fire-and-forget: nudges a spun-down Render instance (and cold Neon
    // compute) awake now, while the user is still reading/typing, instead
    // of that cold-start latency landing on their first real Arena request
    // and competing with its own LLM timeout budget. Nothing here depends
    // on the result, so failures are silently ignored.
    fetch('/api/warmup').catch(() => {});

    setupEventListeners();
    setupThemeControls();
    setupModelControls();
    setupSuggestions();
    setupImageHandlers();
    await initChats();
    maybeOpenSharedRoundFromPage();
    maybeRunTour();
});

function setupEventListeners() {
    document.getElementById('chatForm').addEventListener('submit', (e) => {
        e.preventDefault();
        submitPrompt();
    });

    const chatInput = document.getElementById('chatInput');
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitPrompt();
        }
    });
    chatInput.addEventListener('input', () => autoGrow(chatInput));

    document.getElementById('newChatBtn').addEventListener('click', () => {
        closeChatListPanel();
        createNewChat();
    });

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

    // Quota modal
    document.getElementById('quotaModalCloseBtn').addEventListener('click', () => {
        document.getElementById('quotaModal').style.display = 'none';
    });

    // Feedback modal (shown after ~1 in 5 votes)
    document.getElementById('feedbackSkipBtn').addEventListener('click', closeFeedbackModal);
    document.getElementById('feedbackSubmitBtn').addEventListener('click', submitFeedback);
    document.getElementById('feedbackModal').addEventListener('click', (e) => {
        if (e.target.id === 'feedbackModal') closeFeedbackModal();
    });

    // Shared-round modal
    document.getElementById('sharedRoundCloseBtn').addEventListener('click', closeSharedRoundModal);
    document.getElementById('sharedRoundModal').addEventListener('click', (e) => {
        if (e.target.id === 'sharedRoundModal') closeSharedRoundModal();
    });
    document.getElementById('sharedRoundMakeOwnBtn').addEventListener('click', () => {
        closeSharedRoundModal();
        if (!quotaExceeded) document.getElementById('chatInput').focus();
    });

    // Tour
    document.getElementById('tourNextBtn').addEventListener('click', nextTourStep);
    document.getElementById('tourSkipBtn').addEventListener('click', endTour);
}

function autoGrow(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

function isChatMissing(data) {
    return !data.success && typeof data.error === 'string' && data.error.toLowerCase().includes('chat not found');
}

// ----- Chat lifecycle (up to 4 per session, oldest evicted automatically) -----

async function initChats() {
    // Every page load starts a fresh chat rather than resuming the last one -
    // older chats aren't deleted, just left in place for the switcher
    // (createNewChat's eviction cap still applies, same as clicking "New Chat").
    await createNewChat();
}

async function createNewChat() {
    try {
        const response = await fetch('/api/chats', { method: 'POST' });
        const data = await response.json();

        if (!data.success) {
            showError('Failed to start chat: ' + data.error);
            return;
        }

        currentChatId = data.chat_id;
        resetChatUI();
        refreshChatList();
    } catch (error) {
        showError('Error starting chat: ' + error.message);
    }
}

async function switchToChat(chatId) {
    try {
        const response = await fetch(`/api/chats/${chatId}`);
        const data = await response.json();

        if (!data.success) {
            if (isChatMissing(data)) {
                await initChats();
                return;
            }
            showError('Failed to load chat: ' + data.error);
            return;
        }

        currentChatId = chatId;
        roundPending = false;
        clearPendingImage();

        const messages = document.getElementById('chatMessages');
        messages.innerHTML = '';

        const rounds = data.chat.rounds || [];
        if (rounds.length === 0) {
            messages.innerHTML = emptyStateHTML();
        } else {
            rounds.forEach((round, index) => {
                const turnEl = document.createElement('div');
                turnEl.className = 'chat-turn';
                messages.appendChild(turnEl);

                appendBubble('user', round.message, turnEl);
                renderHistoricalRound(round, turnEl);

                // Every turn except the most recent one is "past" the moment
                // history loads, so it's eligible to auto-minimize right away.
                if (index < rounds.length - 1) {
                    maybeCollapseTurn(turnEl);
                }
            });
        }
        messages.scrollTop = messages.scrollHeight;

        document.getElementById('chatInput').value = '';
        autoGrow(document.getElementById('chatInput'));
        setSendingState(quotaExceeded);
        closeChatListPanel();
        refreshChatList();
    } catch (error) {
        showError('Error loading chat: ' + error.message);
    }
}

function emptyStateHTML() {
    return `
        <div class="chat-empty-state">
            <div class="chat-empty-icon">&gt;:-&lt;</div>
            <p>Send a message. Two AI replies with random personality traits will face off — pick the one you like better.</p>
        </div>
    `;
}

function resetChatUI() {
    document.getElementById('chatMessages').innerHTML = emptyStateHTML();
    roundPending = false;
    clearPendingImage();
    document.getElementById('chatInput').value = '';
    autoGrow(document.getElementById('chatInput'));
    setSendingState(quotaExceeded);
}

// ----- Chat list dropdown (switch / delete) -----

async function refreshChatList() {
    try {
        const response = await fetch('/api/chats');
        const data = await response.json();
        if (!data.success) return;
        renderChatList(data.chats);
    } catch (error) {
        // Non-critical - the dropdown just won't update this time.
    }
}

function renderChatList(chats) {
    const container = document.getElementById('chatListItems');
    container.innerHTML = '';

    if (!chats.length) {
        container.innerHTML = '<p class="chat-list-empty">No chats yet</p>';
        return;
    }

    chats.forEach(chat => {
        const row = document.createElement('div');
        row.className = `chat-list-item${chat.chat_id === currentChatId ? ' active' : ''}`;

        const label = document.createElement('button');
        label.type = 'button';
        label.className = 'chat-list-item-label';
        label.textContent = `${chat.name} (${chat.round_count})`;
        label.addEventListener('click', () => switchToChat(chat.chat_id));

        const del = document.createElement('button');
        del.type = 'button';
        del.className = 'chat-list-item-delete';
        del.title = 'Delete this chat';
        del.textContent = 'x_x';
        del.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteSingleChat(chat.chat_id, chat.name);
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

async function deleteSingleChat(chatId, name) {
    if (!confirm(`Delete "${name}"? This can't be undone.`)) return;

    try {
        const response = await fetch(`/api/chats/${chatId}`, { method: 'DELETE' });
        const data = await response.json();

        if (!data.success) {
            showError('Failed to delete chat: ' + data.error);
            return;
        }

        closeChatListPanel();
        if (chatId === currentChatId) {
            await initChats();
        } else {
            refreshChatList();
        }
    } catch (error) {
        showError('Error deleting chat: ' + error.message);
    }
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
        const response = await fetch('/api/chats', { method: 'DELETE' });
        const data = await response.json();

        if (!data.success) {
            showError('Failed to delete chats: ' + data.error);
            return;
        }

        cancelDeleteAllFlow();
        closeSettingsModal();
        showSuccess('All chats deleted.');
        await initChats();
    } catch (error) {
        showError('Error deleting chats: ' + error.message);
    }
}

// ----- Daily quota -----

function showQuotaModal() {
    quotaExceeded = true;
    document.getElementById('quotaModal').style.display = 'flex';
    setSendingState(true);
}

// ----- Arena rounds -----

async function submitPrompt() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message || roundInFlight || roundPending || quotaExceeded) return;

    const messages = document.getElementById('chatMessages');
    messages.querySelector('.chat-empty-state')?.remove();

    // The turn that was previously "current" is now past - minimize it so
    // the window doesn't just keep growing turn after turn.
    maybeCollapseTurn(messages.querySelector('.chat-turn:last-of-type'));

    const turnEl = document.createElement('div');
    turnEl.className = 'chat-turn';
    messages.appendChild(turnEl);

    appendBubble('user', message, turnEl);

    const imageToSend = pendingImage ? pendingImage.dataUrl : null;
    if (imageToSend) appendUserImage(imageToSend, turnEl);
    clearPendingImage();

    input.value = '';
    autoGrow(input);

    const roundEl = appendArenaRoundPlaceholder(turnEl);
    setSendingState(true);
    roundInFlight = true;

    try {
        const response = await fetch('/api/arena/round', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, chat_id: currentChatId, image: imageToSend, model_id: getSelectedModelId() })
        });
        const data = await parseJsonResponse(response);

        if (!data.success) {
            roundEl.remove();
            if (data.quota_exceeded) {
                showQuotaModal();
            } else {
                showError('Failed to generate replies: ' + data.error);
            }
            return;
        }

        fillArenaRound(roundEl, data);
        roundPending = true;
        refreshChatList();
    } catch (error) {
        roundEl.remove();
        showError('Error generating replies: ' + error.message);
    } finally {
        roundInFlight = false;
        setSendingState(roundPending || quotaExceeded);
    }
}

function setSendingState(disabled) {
    document.getElementById('sendBtn').disabled = disabled;
    document.getElementById('chatInput').disabled = disabled;
}

function appendArenaRoundPlaceholder(turnEl) {
    const round = document.createElement('div');
    round.className = 'arena-round';
    round.innerHTML = `
        <div class="arena-options-grid">
            ${arenaOptionPlaceholderHTML('A')}
            ${arenaOptionPlaceholderHTML('B')}
        </div>
    `;
    turnEl.appendChild(round);
    const messages = document.getElementById('chatMessages');
    messages.scrollTop = messages.scrollHeight;

    round.querySelectorAll('.arena-option-body').forEach(bubble => {
        bubble._thinkingTimer = startThinkingRotation(bubble);
    });

    return round;
}

function arenaOptionPlaceholderHTML(label) {
    return `
        <div class="arena-option" data-option="${label}">
            <div class="arena-option-label">Option ${label}</div>
            <div class="arena-option-body chat-bubble chat-bubble-assistant chat-bubble-typing">${thinkingIndicatorHTML()}</div>
        </div>
    `;
}

function fillArenaRound(roundEl, data) {
    roundEl.dataset.roundId = data.round_id;
    fillArenaOption(roundEl, 'A', data.option_a.reply, data.option_a.traits);
    fillArenaOption(roundEl, 'B', data.option_b.reply, data.option_b.traits);
    appendRoundActions(roundEl);

    roundEl.querySelectorAll('.arena-vote-btn').forEach(btn => {
        btn.addEventListener('click', () => castVote(roundEl, btn.dataset.option));
    });

    document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
}

function fillArenaOption(roundEl, label, reply, traits) {
    const optionEl = roundEl.querySelector(`.arena-option[data-option="${label}"]`);
    const bubble = optionEl.querySelector('.arena-option-body');

    if (bubble._thinkingTimer) clearInterval(bubble._thinkingTimer);
    bubble.classList.remove('chat-bubble-typing');
    bubble.innerHTML = renderMarkdown(reply);

    optionEl.dataset.traits = JSON.stringify(traits);

    const voteRow = document.createElement('button');
    voteRow.type = 'button';
    voteRow.className = 'btn btn-primary arena-vote-btn';
    voteRow.dataset.option = label;
    voteRow.textContent = 'Choose this one';
    optionEl.appendChild(voteRow);

    const traitsEl = document.createElement('div');
    traitsEl.className = 'arena-option-traits';
    optionEl.appendChild(traitsEl);
}

// Renders an already-completed round loaded from chat history: fills both
// options immediately (no thinking state) and either reveals the result
// (already voted) or wires live vote buttons (left dangling from before) -
// which, unlike a freshly generated round, does not gate the input.
function renderHistoricalRound(round, turnEl) {
    const roundEl = document.createElement('div');
    roundEl.className = 'arena-round';
    roundEl.dataset.roundId = round.round_id;
    if (round.share_token) roundEl.dataset.shareToken = round.share_token;
    roundEl.innerHTML = `
        <div class="arena-options-grid">
            ${arenaOptionPlaceholderHTML('A')}
            ${arenaOptionPlaceholderHTML('B')}
        </div>
        ${round.had_image ? '<p class="arena-round-note">(:-]) An image was attached to this round.</p>' : ''}
    `;
    turnEl.appendChild(roundEl);

    fillArenaOption(roundEl, 'A', round.option_a.reply, round.option_a.traits);
    fillArenaOption(roundEl, 'B', round.option_b.reply, round.option_b.traits);
    appendRoundActions(roundEl);

    if (round.voted_option) {
        revealArenaResult(roundEl, round.voted_option);
    } else {
        roundEl.querySelectorAll('.arena-vote-btn').forEach(btn => {
            btn.addEventListener('click', () => castVote(roundEl, btn.dataset.option));
        });
    }

    return roundEl;
}

async function castVote(roundEl, option) {
    const roundId = roundEl.dataset.roundId;
    const buttons = roundEl.querySelectorAll('.arena-vote-btn');
    buttons.forEach(btn => btn.disabled = true);

    try {
        const response = await fetch(`/api/arena/round/${roundId}/vote`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ option, chat_id: currentChatId })
        });
        const data = await parseJsonResponse(response);

        if (!data.success) {
            showError('Failed to record vote: ' + data.error);
            buttons.forEach(btn => btn.disabled = false);
            return;
        }

        revealArenaResult(roundEl, option);
        roundPending = false;
        setSendingState(quotaExceeded);
        if (data.show_feedback_prompt) {
            openFeedbackModal(roundId, option);
        } else if (!quotaExceeded) {
            document.getElementById('chatInput').focus();
        }
        refreshChatList();
    } catch (error) {
        showError('Error recording vote: ' + error.message);
        buttons.forEach(btn => btn.disabled = false);
    }
}

function openFeedbackModal(roundId, option) {
    pendingFeedbackRoundId = roundId;
    document.getElementById('feedbackPrompt').textContent =
        `You picked Option ${option} - what made it better than the other reply? (optional)`;
    document.getElementById('feedbackText').value = '';
    document.getElementById('feedbackModal').style.display = 'flex';
}

function closeFeedbackModal() {
    pendingFeedbackRoundId = null;
    document.getElementById('feedbackModal').style.display = 'none';
    if (!quotaExceeded) document.getElementById('chatInput').focus();
}

async function submitFeedback() {
    const roundId = pendingFeedbackRoundId;
    const feedback = document.getElementById('feedbackText').value.trim();
    if (!roundId || !feedback) {
        closeFeedbackModal();
        return;
    }

    const submitBtn = document.getElementById('feedbackSubmitBtn');
    submitBtn.disabled = true;
    try {
        const response = await fetch(`/api/arena/round/${roundId}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ feedback })
        });
        const data = await parseJsonResponse(response);
        if (!data.success) {
            showError('Failed to save feedback: ' + data.error);
        }
    } catch (error) {
        showError('Error saving feedback: ' + error.message);
    } finally {
        submitBtn.disabled = false;
        closeFeedbackModal();
    }
}

function revealArenaResult(roundEl, winningOption) {
    ['A', 'B'].forEach(label => {
        const optionEl = roundEl.querySelector(`.arena-option[data-option="${label}"]`);
        const voteBtn = optionEl.querySelector('.arena-vote-btn');
        const traitsEl = optionEl.querySelector('.arena-option-traits');
        const traits = JSON.parse(optionEl.dataset.traits || '[]');

        optionEl.classList.add(label === winningOption ? 'is-winner' : 'is-loser');
        voteBtn?.remove();

        traitsEl.innerHTML = traits.length
            ? traits.map(name => `<span class="trait-chip">${name}</span>`).join('')
            : '<span class="trait-chip trait-chip-empty">No traits (neutral)</span>';
    });
}

function appendRoundActions(roundEl) {
    if (roundEl.querySelector('.arena-round-actions')) return;

    const actions = document.createElement('div');
    actions.className = 'arena-round-actions';

    const shareBtn = document.createElement('button');
    shareBtn.type = 'button';
    shareBtn.className = 'btn btn-text arena-share-btn';
    shareBtn.textContent = '(^_^) Share this round';
    shareBtn.addEventListener('click', () => shareRound(roundEl, shareBtn));

    actions.appendChild(shareBtn);
    roundEl.appendChild(actions);
}

async function shareRound(roundEl, btn) {
    if (!currentChatId) {
        showError('Open a chat before sharing a round.');
        return;
    }

    const roundId = roundEl.dataset.roundId;
    if (!roundId) return;

    btn.disabled = true;
    const originalLabel = btn.textContent;
    btn.textContent = 'Sharing...';

    try {
        const response = await fetch(`/api/arena/round/${roundId}/share`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: currentChatId })
        });
        const data = await parseJsonResponse(response);

        if (!data.success) {
            showError('Failed to create share link: ' + data.error);
            return;
        }

        roundEl.dataset.shareToken = data.share_token;
        // Also add the share token to the round actions so it can be copied later
        const actions = roundEl.querySelector('.arena-round-actions');
        // Add the round prompt to the share link for context
        const prompt = roundEl.closest('.chat-turn').querySelector('.chat-bubble-user')?.textContent || '';
        const shareLink = `${window.location.origin}/?share=${encodeURIComponent(data.share_token)}&prompt=${encodeURIComponent(prompt)}`;
        data.share_url = shareLink;
        await copyTextToClipboard(data.share_url);
        showSuccess('Share link copied. Your friends can vote this same round.');
    } catch (error) {
        showError('Error sharing round: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = originalLabel;
    }
}

async function copyTextToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
        return;
    }

    const input = document.createElement('input');
    input.value = text;
    document.body.appendChild(input);
    input.select();
    document.execCommand('copy');
    input.remove();
}

function maybeOpenSharedRoundFromPage() {
    const token = document.body.dataset.sharedRoundToken;
    if (!token) return;
    openSharedRoundModal(token);
}

async function openSharedRoundModal(shareToken) {
    activeSharedRoundToken = shareToken;
    document.getElementById('sharedRoundModal').style.display = 'flex';
    document.getElementById('sharedRoundPrompt').textContent = 'Loading shared round...';
    document.getElementById('sharedRoundMeta').textContent = '';
    document.getElementById('sharedRoundNudge').textContent = '';
    document.getElementById('sharedRoundOptions').innerHTML = '';

    try {
        const response = await fetch(`/api/shared-rounds/${encodeURIComponent(shareToken)}`);
        const data = await parseJsonResponse(response);
        if (!data.success) {
            showError('Could not load shared round: ' + data.error);
            closeSharedRoundModal();
            return;
        }
        renderSharedRoundModal(data.round);
    } catch (error) {
        showError('Error loading shared round: ' + error.message);
        closeSharedRoundModal();
    }
}

function renderSharedRoundModal(round) {
    document.getElementById('sharedRoundPrompt').textContent = `Prompt: ${round.prompt}`;
    document.getElementById('sharedRoundMeta').textContent =
        `Votes so far: ${round.total_votes} (A: ${round.option_a.votes}, B: ${round.option_b.votes})`;

    const optionsEl = document.getElementById('sharedRoundOptions');
    optionsEl.innerHTML = '';

    [['A', round.option_a], ['B', round.option_b]].forEach(([label, option]) => {
        const card = document.createElement('div');
        card.className = 'shared-round-option';
        if (round.viewer_vote === label) card.classList.add('is-winner');

        card.innerHTML = `
            <div class="arena-option-label">Option ${label}</div>
            <div class="arena-option-body chat-bubble chat-bubble-assistant">${renderMarkdown(option.reply)}</div>
            <div class="shared-round-vote-row">
                <button type="button" class="btn btn-primary shared-round-vote-btn" data-option="${label}">Vote for Option ${label}</button>
                <span class="settings-hint">${option.votes} vote${option.votes === 1 ? '' : 's'}</span>
            </div>
            <div class="arena-option-traits">${renderTraitChips(option.traits)}</div>
        `;

        const voteBtn = card.querySelector('.shared-round-vote-btn');
        voteBtn.disabled = !!round.viewer_vote;
        voteBtn.addEventListener('click', () => castSharedRoundVote(label));

        optionsEl.appendChild(card);
    });

    const nudgeEl = document.getElementById('sharedRoundNudge');
    if (round.viewer_vote) {
        nudgeEl.textContent = 'Vote captured. Nice. Now make your own round below.';
    } else {
        nudgeEl.textContent = 'Pick your favorite reply, then create your own round.';
    }
}

async function castSharedRoundVote(option) {
    if (!activeSharedRoundToken) return;

    const buttons = document.querySelectorAll('.shared-round-vote-btn');
    buttons.forEach(btn => { btn.disabled = true; });

    try {
        const response = await fetch(`/api/shared-rounds/${encodeURIComponent(activeSharedRoundToken)}/vote`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ option })
        });
        const data = await parseJsonResponse(response);
        if (!data.success) {
            showError('Failed to submit shared vote: ' + data.error);
            buttons.forEach(btn => { btn.disabled = false; });
            return;
        }
        renderSharedRoundModal(data.round);
        showSuccess(data.already_voted ? 'You already voted on this shared round.' : 'Vote recorded. Now make your own round.');
    } catch (error) {
        showError('Error submitting shared vote: ' + error.message);
        buttons.forEach(btn => { btn.disabled = false; });
    }
}

function closeSharedRoundModal() {
    activeSharedRoundToken = null;
    document.getElementById('sharedRoundModal').style.display = 'none';
}

function renderTraitChips(traits) {
    if (!Array.isArray(traits) || traits.length === 0) {
        return '<span class="trait-chip trait-chip-empty">No traits (neutral)</span>';
    }
    return traits.map(name => `<span class="trait-chip">${name}</span>`).join('');
}

// ----- Auto-minimize past turns (keeps the window from filling up as more
// prompts/replies pile up) - a turn only collapses once it's no longer the
// current one, and never fights a user who's explicitly expanded it back
// open. Collapsing just hides the turn's content behind a compact summary
// row; nothing is removed, so scrolling up and expanding it still works. -----

function maybeCollapseTurn(turnEl) {
    if (!turnEl || turnEl.classList.contains('is-collapsed') || turnEl.dataset.userExpanded === '1') return;

    turnEl.classList.add('is-collapsed');
    addTurnSummary(turnEl);
}

function addTurnSummary(turnEl) {
    let summary = turnEl.querySelector('.turn-summary');
    if (!summary) {
        summary = document.createElement('button');
        summary.type = 'button';
        summary.className = 'turn-summary';
        summary.innerHTML = `
            <span class="turn-summary-text"></span>
            <span class="turn-summary-chevron">▾</span>
        `;
        summary.addEventListener('click', () => toggleTurnCollapse(turnEl));
        turnEl.insertBefore(summary, turnEl.firstChild);
    }

    const promptBubble = turnEl.querySelector('.chat-bubble-user');
    summary.querySelector('.turn-summary-text').textContent = promptBubble ? promptBubble.textContent : 'Previous round';
}

function toggleTurnCollapse(turnEl) {
    const nowCollapsed = turnEl.classList.toggle('is-collapsed');
    turnEl.dataset.userExpanded = nowCollapsed ? '' : '1';

    const chevron = turnEl.querySelector('.turn-summary-chevron');
    if (chevron) chevron.textContent = nowCollapsed ? '▾' : '▴';
}

// ----- Rotating prompt suggestions -----

function setupSuggestions() {
    const btn = document.getElementById('promptSuggestion');
    const input = document.getElementById('chatInput');

    btn.textContent = PROMPT_SUGGESTIONS[0];
    setInterval(() => {
        // suggestionindex becomes random
        suggestionIndex = Math.floor(Math.random() * PROMPT_SUGGESTIONS.length);        btn.textContent = PROMPT_SUGGESTIONS[suggestionIndex];
    }, 3500);

    btn.addEventListener('click', () => {
        input.value = PROMPT_SUGGESTIONS[suggestionIndex];
        autoGrow(input);
        input.focus();
        updateSuggestionVisibility();
    });

    input.addEventListener('focus', updateSuggestionVisibility);
    input.addEventListener('blur', updateSuggestionVisibility);
    input.addEventListener('input', updateSuggestionVisibility);

    updateSuggestionVisibility();
}

function updateSuggestionVisibility() {
    const input = document.getElementById('chatInput');
    const btn = document.getElementById('promptSuggestion');
    const shouldShow = input.value.trim() === '' && document.activeElement !== input;
    btn.style.display = shouldShow ? 'block' : 'none';
}

// ----- Image attach (client-side only - never re-fetched from the server) -----

function setupImageHandlers() {
    document.getElementById('attachImageBtn').addEventListener('click', () => {
        document.getElementById('imageFileInput').click();
    });

    document.getElementById('imageFileInput').addEventListener('change', async (e) => {
        const file = e.target.files[0];
        e.target.value = ''; // allow re-selecting the same file later
        if (!file) return;

        if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
            showError('Unsupported image type. Use PNG, JPEG, WEBP, or GIF.');
            return;
        }
        if (file.size > IMAGE_MAX_BYTES) {
            showError(`Image is too large (max ${IMAGE_MAX_BYTES / (1024 * 1024)}MB).`);
            return;
        }

        try {
            const dataUrl = await readFileAsDataUrl(file);
            pendingImage = { dataUrl, name: file.name };
            showImagePreview(pendingImage);
        } catch (error) {
            showError('Error reading image: ' + error.message);
        }
    });

    document.getElementById('imageRemoveBtn').addEventListener('click', clearPendingImage);
}

function readFileAsDataUrl(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(reader.error || new Error('Failed to read file'));
        reader.readAsDataURL(file);
    });
}

function showImagePreview(image) {
    document.getElementById('imagePreviewThumb').src = image.dataUrl;
    document.getElementById('imagePreviewName').textContent = image.name;
    document.getElementById('imagePreviewChip').style.display = 'flex';
}

function clearPendingImage() {
    pendingImage = null;
    document.getElementById('imagePreviewChip').style.display = 'none';
    document.getElementById('imagePreviewThumb').src = '';
}

function appendUserImage(dataUrl, container) {
    const target = container || document.getElementById('chatMessages');
    const img = document.createElement('img');
    img.className = 'chat-image-bubble';
    img.src = dataUrl;
    img.alt = 'Attached image';
    target.appendChild(img);
    const messages = document.getElementById('chatMessages');
    messages.scrollTop = messages.scrollHeight;
}

// ----- Markdown rendering (assistant replies only) -----
//
// Security: the whole string is HTML-escaped FIRST, then a small whitelist of
// markdown patterns is turned into tags. Nothing from the model's output is
// ever passed through as raw HTML - this is what makes innerHTML safe here.

function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderInline(text) {
    let out = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
    return out;
}

function renderMarkdown(raw) {
    const lines = escapeHtml(raw).split('\n');
    let html = '';
    let inCode = false;
    let listOpen = false;
    let paraLines = [];

    const flushParagraph = () => {
        if (paraLines.length) {
            html += `<p>${paraLines.join('<br>')}</p>`;
            paraLines = [];
        }
    };
    const closeList = () => {
        if (listOpen) {
            html += '</ul>';
            listOpen = false;
        }
    };

    for (const line of lines) {
        if (line.startsWith('```')) {
            if (!inCode) {
                flushParagraph();
                closeList();
                inCode = true;
                html += '<pre><code>';
            } else {
                inCode = false;
                html += '</code></pre>';
            }
            continue;
        }

        if (inCode) {
            html += line + '\n';
            continue;
        }

        const headerMatch = line.match(/^(#{1,6})\s+(.*)$/);
        if (headerMatch) {
            flushParagraph();
            closeList();
            const level = headerMatch[1].length;
            html += `<h${level}>${renderInline(headerMatch[2])}</h${level}>`;
            continue;
        }

        const bulletMatch = line.match(/^[-*]\s+(.*)$/);
        if (bulletMatch) {
            flushParagraph();
            if (!listOpen) {
                html += '<ul>';
                listOpen = true;
            }
            html += `<li>${renderInline(bulletMatch[1])}</li>`;
            continue;
        }

        closeList();
        if (line.trim() === '') {
            flushParagraph();
        } else {
            paraLines.push(renderInline(line));
        }
    }

    flushParagraph();
    closeList();
    if (inCode) html += '</code></pre>'; // unterminated fence safety net

    return html;
}

// ----- First-run guided tour -----

const TOUR_STEPS = [
    { target: 'appTitle', title: 'Welcome to the Arena', body: 'Type a prompt and two AI replies — each shaped by a different, randomly assigned personality — go head-to-head.' },
    { target: 'chatInput', title: 'Say something', body: 'Type your message here, just like you would with any chatbot.' },
    { target: 'sendBtn', title: 'Send it', body: 'Click Send (or press Enter). Both replies generate at the same time, so it may take a few seconds.' },
    { target: 'chatMessages', title: 'Pick a winner', body: "Once both replies are ready, click \"Choose this one\" under whichever you like better. The traits behind each reply are revealed right after you vote." },
    { target: 'analyticsNavLink', title: 'See global results', body: 'Every vote feeds the public Analytics page, showing which traits win the most across everyone who has played.' }
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

// ----- Chat bubbles / typing indicator -----

function appendBubble(role, text, container) {
    const target = container || document.getElementById('chatMessages');
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble chat-bubble-${role}`;
    bubble.textContent = text;
    target.appendChild(bubble);
    const messages = document.getElementById('chatMessages');
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

function setupModelControls() {
    const select = document.getElementById('modelSelect');
    select.value = getSelectedModelId();
    select.addEventListener('change', () => {
        localStorage.setItem(MODEL_STORAGE_KEY, select.value);
    });
}

async function refreshUsage() {
    const usageText = document.getElementById('usageText');
    try {
        const response = await fetch('/api/quota');
        const data = await parseJsonResponse(response);
        if (!data.success) {
            usageText.textContent = 'Could not load usage: ' + data.error;
            return;
        }
        usageText.textContent =
            `${data.used_tokens.toLocaleString()} / ${data.daily_budget.toLocaleString()} tokens used today ` +
            `- about ${data.estimated_rounds_remaining.toLocaleString()} more Arena replies left ` +
            `(resets at midnight).`;
    } catch (error) {
        usageText.textContent = 'Could not load usage: ' + error.message;
    }
}

function openSettingsModal() {
    document.getElementById('settingsModal').style.display = 'flex';
    refreshUsage();
}

function closeSettingsModal() {
    document.getElementById('settingsModal').style.display = 'none';
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
