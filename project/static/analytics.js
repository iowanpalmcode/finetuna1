// Public Arena analytics page: fetch global aggregate stats and render them
// as hand-built HTML/CSS bars (no chart library, no CDN - consistent with
// the rest of the app) driven entirely by the theme's CSS custom properties.
//
// The page ships with static skeleton placeholders already in the HTML (see
// templates/analytics.html) so there's something on screen instantly; this
// script swaps each container's content for the real thing once data loads.

const ITEMS_PER_PAGE = 7;
const paginationState = { glicko: 0, winRate: 0, length: 0, combos: 0 };

document.addEventListener('DOMContentLoaded', loadAnalytics);

async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics');
        const data = await response.json();

        if (!data.success) {
            showStatus('analyticsError', 'Failed to load analytics: ' + data.error);
            return;
        }

        renderAnalytics(data.summary);
    } catch (error) {
        showStatus('analyticsError', 'Error loading analytics: ' + error.message);
    }
}

function showStatus(id, message) {
    document.getElementById('analyticsContent').style.display = 'none';
    const el = document.getElementById(id);
    if (message) el.textContent = message;
    el.style.display = 'block';
}

function renderAnalytics(summary) {
    if (summary.total_votes === 0) {
        document.getElementById('analyticsContent').style.display = 'none';
        document.getElementById('analyticsEmpty').style.display = 'block';
        return;
    }

    renderStatTiles(summary);
    renderGlickoChart(summary);
    renderWinRateChart(summary);
    renderLengthChart(summary);
    renderComboTable(summary);
}

function renderStatTiles(summary) {
    const tiles = [
        { label: 'Total Rounds', value: summary.total_rounds.toLocaleString() },
        { label: 'Total Votes', value: summary.total_votes.toLocaleString() },
        { label: 'Traits in Play', value: summary.distinct_traits_used.toLocaleString() },
        { label: 'Avg Reply Length', value: `${Math.round(summary.overall_avg_response_length)} chars` },
    ];

    const container = document.getElementById('statTiles');
    container.innerHTML = tiles.map(tile => `
        <div class="stat-tile">
            <div class="stat-tile-value">${tile.value}</div>
            <div class="stat-tile-label">${tile.label}</div>
        </div>
    `).join('');
}

// ----- Generic pagination for a bar-chart or table body -----
//
// items: the FULL, already-sorted list (normalization/sorting must happen
// against the full list before this runs, not just the visible page).
// rowRenderFn: (item) => HTML string for one row.
function renderPaginatedSection(key, items, containerId, paginationId, rowRenderFn, emptyHtml) {
    const container = document.getElementById(containerId);
    const paginationEl = document.getElementById(paginationId);

    if (!items.length) {
        container.innerHTML = emptyHtml;
        paginationEl.innerHTML = '';
        return;
    }

    const totalPages = Math.ceil(items.length / ITEMS_PER_PAGE);
    paginationState[key] = Math.max(0, Math.min(paginationState[key], totalPages - 1));
    const page = paginationState[key];
    const pageItems = items.slice(page * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE + ITEMS_PER_PAGE);

    container.innerHTML = pageItems.map(rowRenderFn).join('');

    if (totalPages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }

    paginationEl.innerHTML = `
        <button type="button" class="pagination-btn" data-action="prev" ${page === 0 ? 'disabled' : ''}>‹ Prev</button>
        <span class="pagination-label">Page ${page + 1} of ${totalPages}</span>
        <button type="button" class="pagination-btn" data-action="next" ${page === totalPages - 1 ? 'disabled' : ''}>Next ›</button>
    `;

    const rerender = () => renderPaginatedSection(key, items, containerId, paginationId, rowRenderFn, emptyHtml);
    paginationEl.querySelector('[data-action="prev"]')?.addEventListener('click', () => {
        paginationState[key] -= 1;
        rerender();
    });
    paginationEl.querySelector('[data-action="next"]')?.addEventListener('click', () => {
        paginationState[key] += 1;
        rerender();
    });
}

const NOT_ENOUGH_TRAIT_VOTES_HTML =
    '<p class="chart-empty">Not enough votes yet for any trait to reach the minimum sample size.</p>';

function renderGlickoChart(summary) {
    document.getElementById('glickoSubtitle').textContent =
        `Glicko rating (accounts for opponent strength, not just raw win rate) — traits used at least ${summary.min_sample_size} times, sorted strongest first. ± is the rating's uncertainty; it shrinks as a trait plays more rounds.`;

    // summary.traits already arrives sorted by glicko_rating descending.
    const ratings = summary.traits.map(t => t.glicko_rating);
    const minRating = Math.min(...ratings);
    const maxRating = Math.max(...ratings);
    const range = maxRating - minRating;

    const rowFn = (t) => {
        const pct = range > 0 ? ((t.glicko_rating - minRating) / range) * 100 : 100;
        return barRowHTML(
            t.name,
            Math.max(4, pct), // keep the lowest bar visibly non-zero
            `${Math.round(t.glicko_rating)} ± ${Math.round(t.glicko_rd)}`
        );
    };

    renderPaginatedSection('glicko', summary.traits, 'glickoChart', 'glickoPagination', rowFn, NOT_ENOUGH_TRAIT_VOTES_HTML);
}

function renderWinRateChart(summary) {
    document.getElementById('winRateSubtitle').textContent =
        `Share of voted rounds a trait's side won (traits used at least ${summary.min_sample_size} times)`;

    const byWinRate = [...summary.traits].sort((a, b) => b.win_rate - a.win_rate);
    const rowFn = (t) => barRowHTML(t.name, t.win_rate * 100, `${Math.round(t.win_rate * 100)}% (n=${t.times_used})`);

    renderPaginatedSection('winRate', byWinRate, 'winRateChart', 'winRatePagination', rowFn, NOT_ENOUGH_TRAIT_VOTES_HTML);
}

function renderLengthChart(summary) {
    const byLength = [...summary.traits].sort((a, b) => b.avg_response_length - a.avg_response_length);
    const maxLength = Math.max(...byLength.map(t => t.avg_response_length));

    const rowFn = (t) => barRowHTML(
        t.name,
        maxLength > 0 ? (t.avg_response_length / maxLength) * 100 : 0,
        `${Math.round(t.avg_response_length)} chars`
    );

    renderPaginatedSection('length', byLength, 'lengthChart', 'lengthPagination', rowFn, NOT_ENOUGH_TRAIT_VOTES_HTML);
}

function barRowHTML(label, widthPercent, valueLabel) {
    const clamped = Math.max(0, Math.min(100, widthPercent));
    return `
        <div class="bar-row">
            <div class="bar-row-label">${label}</div>
            <div class="bar-track"><div class="bar-fill" style="width: ${clamped}%"></div></div>
            <div class="bar-row-value">${valueLabel}</div>
        </div>
    `;
}

function renderComboTable(summary) {
    const rowFn = (combo) => `
        <tr>
            <td>${combo.label}</td>
            <td>${combo.times_used}</td>
            <td>${Math.round(combo.win_rate * 100)}%</td>
        </tr>
    `;
    const emptyHtml = '<tr><td colspan="3" class="chart-empty">Not enough votes yet for any combination to reach the minimum sample size.</td></tr>';

    renderPaginatedSection('combos', summary.top_combos, 'comboTableBody', 'comboPagination', rowFn, emptyHtml);
}
