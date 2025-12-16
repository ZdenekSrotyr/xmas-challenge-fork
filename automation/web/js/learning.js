/**
 * Learning Dashboard Module
 * Displays interactions and learnings from the memory database
 */

let learningsData = null;
let currentFilters = {
    gapType: 'all',
    status: 'all'
};

/**
 * Initialize learning dashboard
 */
export async function initLearningDashboard() {
    try {
        // Load learnings data
        const response = await fetch('data/learnings.json');
        learningsData = await response.json();

        // Render components
        renderLearningStats(learningsData);
        renderLearnings(learningsData.learnings);
        renderInteractions(learningsData.interactions);

        // Setup filters
        setupFilters();

    } catch (error) {
        console.error('Failed to load learnings:', error);
        showLearningError();
    }
}

/**
 * Render learning statistics
 */
function renderLearningStats(data) {
    // Support both old format (direct arrays) and new format (with metadata)
    const interactionCount = data.metadata ? data.metadata.interaction_count : data.interactions.length;
    const gapCount = data.interactions.filter(i => i.identified_gap).length;
    const pendingCount = data.learnings.filter(l => l.status === 'pending').length;

    document.getElementById('interaction-count').textContent = interactionCount;
    document.getElementById('gap-count').textContent = gapCount;
    document.getElementById('pending-count').textContent = pendingCount;

    // Calculate average satisfaction
    const ratings = data.interactions
        .map(i => extractRating(i.user_feedback))
        .filter(r => r !== null);

    const avgRating = ratings.length > 0
        ? (ratings.reduce((a, b) => a + b, 0) / ratings.length).toFixed(1)
        : 'N/A';

    document.getElementById('avg-satisfaction').textContent =
        avgRating !== 'N/A' ? `${avgRating}/5` : avgRating;
}

/**
 * Extract rating from feedback string
 */
function extractRating(feedback) {
    if (!feedback) return null;
    const match = feedback.match(/Rating: (\d)/);
    return match ? parseInt(match[1]) : null;
}

/**
 * Render learnings list
 */
function renderLearnings(learnings) {
    const container = document.getElementById('learning-list');

    // Apply filters
    const filtered = learnings.filter(learning => {
        if (currentFilters.gapType !== 'all' && learning.gap_type !== currentFilters.gapType) {
            return false;
        }
        if (currentFilters.status !== 'all' && learning.status !== currentFilters.status) {
            return false;
        }
        return true;
    });

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="welcome">
                <h2>No learnings found</h2>
                <p>Adjust filters or wait for new interactions to generate learnings.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(learning => `
        <div class="learning-item">
            <div class="learning-header">
                <div class="learning-concept">${escapeHtml(learning.concept)}</div>
                <div>
                    <span class="learning-badge badge-${learning.gap_type}">${formatGapType(learning.gap_type)}</span>
                    <span class="learning-badge badge-${learning.status}">${learning.status}</span>
                </div>
            </div>

            <div class="learning-meta">
                <span>📅 ${formatDate(learning.created_at)}</span>
                ${learning.interaction_id ? `<span>🔗 Interaction #${learning.interaction_id}</span>` : ''}
            </div>

            <div class="learning-proposed-fix">
                <strong>Proposed Fix:</strong><br>
                ${escapeHtml(learning.proposed_fix)}
            </div>

            ${learning.user_context ? `
                <div class="learning-context">
                    Context: ${escapeHtml(learning.user_context)}
                </div>
            ` : ''}
        </div>
    `).join('');
}

/**
 * Render recent interactions
 */
function renderInteractions(interactions) {
    const container = document.getElementById('interaction-list');

    // Show most recent 10
    const recent = interactions.slice(0, 10);

    if (recent.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No interactions yet</p>
            </div>
        `;
        return;
    }

    container.innerHTML = recent.map(interaction => `
        <div class="interaction-item">
            <div class="interaction-time">${formatDate(interaction.timestamp)}</div>
            <div class="interaction-context">${truncate(escapeHtml(interaction.user_context), 100)}</div>
            ${interaction.identified_gap ? '<div class="interaction-feedback">🎯 Gap Identified</div>' : ''}
            ${interaction.user_feedback ? `<div class="interaction-feedback">⭐ ${extractRating(interaction.user_feedback)}/5</div>` : ''}
        </div>
    `).join('');
}

/**
 * Setup filter event listeners
 */
function setupFilters() {
    document.getElementById('gap-filter').addEventListener('change', (e) => {
        currentFilters.gapType = e.target.value;
        renderLearnings(learningsData.learnings);
    });

    document.getElementById('status-filter').addEventListener('change', (e) => {
        currentFilters.status = e.target.value;
        renderLearnings(learningsData.learnings);
    });
}

/**
 * Show error state
 */
function showLearningError() {
    document.getElementById('learning-list').innerHTML = `
        <div class="welcome">
            <h2>⚠️ Failed to Load Learnings</h2>
            <p>Could not load learnings data. Make sure learnings.json exists.</p>
        </div>
    `;
}

/**
 * Utility functions
 */

function formatGapType(type) {
    return type.replace('_', ' ').toUpperCase();
}

function formatDate(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;

    return date.toLocaleDateString();
}

function truncate(str, length) {
    if (str.length <= length) return str;
    return str.substring(0, length) + '...';
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
