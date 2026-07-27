// Public Arena analytics page: fetch global aggregate stats and render them
// as hand-built HTML/CSS bars (no chart library, no CDN - consistent with
// the rest of the app) driven entirely by the theme's CSS custom properties.

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
    document.getElementById('analyticsLoading').style.display = 'none';
    const el = document.getElementById(id);
    if (message) el.textContent = message;
    el.style.display = 'block';
}

function renderAnalytics(summary) {
    document.getElementById('analyticsLoading').style.display = 'none';

    if (summary.total_votes === 0) {
        document.getElementById('analyticsEmpty').style.display = 'block';
        return;
    }

    document.getElementById('analyticsContent').style.display = 'block';

    renderStatTiles(summary);
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

function renderWinRateChart(summary) {
    const subtitle = document.getElementById('winRateSubtitle');
    subtitle.textContent = `Share of voted rounds a trait's side won (traits used at least ${summary.min_sample_size} times)`;

    const container = document.getElementById('winRateChart');
    if (!summary.traits.length) {
        container.innerHTML = '<p class="chart-empty">Not enough votes yet for any trait to reach the minimum sample size.</p>';
        return;
    }

    container.innerHTML = summary.traits.map(t => barRowHTML(
        t.name,
        t.win_rate * 100,
        `${Math.round(t.win_rate * 100)}% (n=${t.times_used})`
    )).join('');
}

function renderLengthChart(summary) {
    const container = document.getElementById('lengthChart');
    if (!summary.traits.length) {
        container.innerHTML = '<p class="chart-empty">Not enough votes yet for any trait to reach the minimum sample size.</p>';
        return;
    }

    const byLength = [...summary.traits].sort((a, b) => b.avg_response_length - a.avg_response_length);
    const maxLength = Math.max(...byLength.map(t => t.avg_response_length));

    container.innerHTML = byLength.map(t => barRowHTML(
        t.name,
        maxLength > 0 ? (t.avg_response_length / maxLength) * 100 : 0,
        `${Math.round(t.avg_response_length)} chars`
    )).join('');
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
    const body = document.getElementById('comboTableBody');

    if (!summary.top_combos.length) {
        body.innerHTML = '<tr><td colspan="3" class="chart-empty">Not enough votes yet for any combination to reach the minimum sample size.</td></tr>';
        return;
    }

    body.innerHTML = summary.top_combos.map(combo => `
        <tr>
            <td>${combo.label}</td>
            <td>${combo.times_used}</td>
            <td>${Math.round(combo.win_rate * 100)}%</td>
        </tr>
    `).join('');
}
