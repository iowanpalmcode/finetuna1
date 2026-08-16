let activeToken = null;

document.addEventListener('DOMContentLoaded', async () => {
    setupModalHandlers();
    await loadBulletin();
});

function setupModalHandlers() {
    document.getElementById('bulletinVoteCloseBtn').addEventListener('click', closeVoteModal);
    document.getElementById('bulletinVoteModal').addEventListener('click', (e) => {
        if (e.target.id === 'bulletinVoteModal') closeVoteModal();
    });
}

async function loadBulletin() {
    const list = document.getElementById('bulletinList');
    const empty = document.getElementById('bulletinEmpty');
    const error = document.getElementById('bulletinError');

    list.innerHTML = '<p class="settings-hint">Loading top rounds...</p>';
    empty.style.display = 'none';
    error.style.display = 'none';

    try {
        const response = await fetch('/api/bulletin/today?limit=10');
        const data = await parseJsonResponse(response);

        if (!data.success) {
            throw new Error(data.error || 'Failed to load bulletin');
        }

        const rounds = data.rounds || [];
        if (!rounds.length) {
            list.innerHTML = '';
            empty.style.display = 'block';
            return;
        }

        list.innerHTML = '';
        rounds.forEach((round, idx) => {
            const item = document.createElement('div');
            item.className = 'bulletin-item';
            item.innerHTML = `
                <div class="bulletin-rank">#${idx + 1}</div>
                <div class="bulletin-body">
                    <h3>${escapeHtml(round.prompt)}</h3>
                    <p class="settings-hint">${round.votes_today} vote${round.votes_today === 1 ? '' : 's'} today · ${round.total_votes} total</p>
                </div>
                <button type="button" class="btn btn-primary bulletin-open-btn">Open & Vote</button>
            `;

            item.querySelector('.bulletin-open-btn').addEventListener('click', () => {
                openVoteModal(round.share_token);
            });

            list.appendChild(item);
        });
    } catch (err) {
        list.innerHTML = '';
        error.textContent = 'Could not load bulletin: ' + err.message;
        error.style.display = 'block';
    }
}

async function openVoteModal(shareToken) {
    activeToken = shareToken;
    document.getElementById('bulletinVoteModal').style.display = 'flex';
    document.getElementById('bulletinVotePrompt').textContent = 'Loading round...';
    document.getElementById('bulletinVoteMeta').textContent = '';
    document.getElementById('bulletinVoteNudge').textContent = '';
    document.getElementById('bulletinVoteOptions').innerHTML = '';

    try {
        const response = await fetch(`/api/shared-rounds/${encodeURIComponent(shareToken)}`);
        const data = await parseJsonResponse(response);
        if (!data.success) {
            throw new Error(data.error || 'Failed to load shared round');
        }
        renderVoteModal(data.round);
    } catch (err) {
        showError('Could not load round: ' + err.message);
        closeVoteModal();
    }
}

function renderVoteModal(round) {
    document.getElementById('bulletinVotePrompt').textContent = `Prompt: ${round.prompt}`;
    document.getElementById('bulletinVoteMeta').textContent =
        `Votes so far: ${round.total_votes} (A: ${round.option_a.votes}, B: ${round.option_b.votes})`;

    const optionsEl = document.getElementById('bulletinVoteOptions');
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
        voteBtn.addEventListener('click', () => castVote(label));

        optionsEl.appendChild(card);
    });

    document.getElementById('bulletinVoteNudge').textContent = round.viewer_vote
        ? 'Vote captured. After this, create your own round in the Arena.'
        : 'Choose your favorite reply, then create your own round.';
}

async function castVote(option) {
    if (!activeToken) return;

    const buttons = document.querySelectorAll('.shared-round-vote-btn');
    buttons.forEach(btn => { btn.disabled = true; });

    try {
        const response = await fetch(`/api/shared-rounds/${encodeURIComponent(activeToken)}/vote`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ option })
        });
        const data = await parseJsonResponse(response);
        if (!data.success) {
            throw new Error(data.error || 'Failed to submit vote');
        }

        renderVoteModal(data.round);
        showSuccess(data.already_voted ? 'You already voted on this round.' : 'Vote recorded.');
        await loadBulletin();
    } catch (err) {
        showError('Could not submit vote: ' + err.message);
        buttons.forEach(btn => { btn.disabled = false; });
    }
}

function closeVoteModal() {
    activeToken = null;
    document.getElementById('bulletinVoteModal').style.display = 'none';
}

async function parseJsonResponse(response) {
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
        throw new Error(`Server returned non-JSON response (status ${response.status}).`);
    }
    return response.json();
}

function renderTraitChips(traits) {
    if (!Array.isArray(traits) || traits.length === 0) {
        return '<span class="trait-chip trait-chip-empty">No traits (neutral)</span>';
    }
    return traits.map(name => `<span class="trait-chip">${escapeHtml(name)}</span>`).join('');
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function renderInline(text) {
    let out = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
    return out;
}

function renderMarkdown(raw) {
    const lines = escapeHtml(String(raw || '')).split('\n');
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
    if (inCode) html += '</code></pre>';

    return html;
}

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

    setTimeout(() => alert.remove(), 3500);
}
