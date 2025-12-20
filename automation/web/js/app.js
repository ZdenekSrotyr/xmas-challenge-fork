// Documentation Browser - Main Application
// Combined app.js + learning.js (no ES modules for GitHub Pages compatibility)

// Global state
let docsData = null;
let currentDoc = null;
let learningInitialized = false;

// Learning module state
let learningsData = null;
let currentFilters = {
    gapType: 'all',
    status: 'all'
};

// Initialize the application
async function initApp() {
    try {
        console.log('Initializing Documentation Browser...');

        // Show loading overlay
        showLoading();

        // Load documentation data
        docsData = await loadDocs();
        console.log(`Loaded ${docsData.docs.length} documents`);

        // Render UI components
        renderDocsList(docsData.docs);
        renderStatistics(docsData.statistics);
        renderRecentChanges(docsData.recent_changes);

        // Setup tab switching
        setupTabs();

        // Hide loading overlay
        hideLoading();

        console.log('Documentation Browser initialized successfully');

    } catch (error) {
        console.error('Failed to initialize app:', error);
        showError('Failed to load documentation. The docs.json file may not exist yet.');
    }
}

// Load documentation data from JSON
async function loadDocs() {
    try {
        const response = await fetch('data/docs.json');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Validate data structure
        if (!data.docs || !data.metadata) {
            throw new Error('Invalid documentation data structure');
        }

        return data;

    } catch (error) {
        console.error('Failed to load documentation:', error);
        throw error;
    }
}

// Render the list of documents in the sidebar
function renderDocsList(docs) {
    const docsList = document.getElementById('docs-list');

    if (!docs || docs.length === 0) {
        docsList.innerHTML = '<div class="loading">No documents found</div>';
        return;
    }

    docsList.innerHTML = '';

    docs.forEach((doc, index) => {
        const docItem = document.createElement('div');
        docItem.className = 'doc-item';
        docItem.dataset.index = index;

        const docName = document.createElement('div');
        docName.className = 'doc-item-name';
        docName.textContent = doc.name;

        const docMeta = document.createElement('div');
        docMeta.className = 'doc-item-meta';
        docMeta.textContent = `${doc.commit_count} commits`;

        docItem.appendChild(docName);
        docItem.appendChild(docMeta);

        // Click handler to view document
        docItem.addEventListener('click', () => {
            selectDocument(index);
        });

        docsList.appendChild(docItem);
    });
}

// Select and display a document
function selectDocument(index) {
    const doc = docsData.docs[index];
    currentDoc = doc;

    // Update active state in docs list
    const allItems = document.querySelectorAll('.doc-item');
    allItems.forEach((item, i) => {
        if (i === index) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Render document content
    renderDocContent(doc);

    // Render document history
    renderHistory(doc.history);
}

// Render document content with markdown
function renderDocContent(doc) {
    const docViewer = document.getElementById('doc-viewer');

    // Create content container
    docViewer.innerHTML = '';

    const docContent = document.createElement('div');
    docContent.className = 'doc-content';

    // Parse markdown and render as HTML
    try {
        const html = marked.parse(doc.content);
        docContent.innerHTML = html;
    } catch (error) {
        console.error('Failed to parse markdown:', error);
        docContent.innerHTML = `<pre>${escapeHtml(doc.content)}</pre>`;
    }

    docViewer.appendChild(docContent);
}

// Render document history in the right panel
function renderHistory(history) {
    const historyList = document.getElementById('history-list');

    if (!history || history.length === 0) {
        historyList.innerHTML = '<div class="empty-state"><p>No history available</p></div>';
        return;
    }

    historyList.innerHTML = '';

    history.forEach(commit => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';

        // Commit hash
        const hash = document.createElement('div');
        hash.className = 'history-item-hash';
        hash.textContent = commit.short_hash;

        // Commit message
        const message = document.createElement('div');
        message.className = 'history-item-message';
        message.textContent = commit.message;

        // Author
        const author = document.createElement('div');
        author.className = 'history-item-author';
        author.textContent = commit.author;

        // Date
        const date = document.createElement('div');
        date.className = 'history-item-date';
        date.textContent = formatDate(commit.date);

        // Stats
        if (commit.stats && (commit.stats.insertions > 0 || commit.stats.deletions > 0)) {
            const stats = document.createElement('div');
            stats.className = 'history-item-stats';

            const additions = commit.stats.insertions > 0
                ? `<span class="stat-add">+${commit.stats.insertions}</span>`
                : '';
            const deletions = commit.stats.deletions > 0
                ? `<span class="stat-del">-${commit.stats.deletions}</span>`
                : '';

            stats.innerHTML = `${additions} ${deletions}`.trim();

            historyItem.appendChild(hash);
            historyItem.appendChild(message);
            historyItem.appendChild(author);
            historyItem.appendChild(date);
            historyItem.appendChild(stats);
        } else {
            historyItem.appendChild(hash);
            historyItem.appendChild(message);
            historyItem.appendChild(author);
            historyItem.appendChild(date);
        }

        historyList.appendChild(historyItem);
    });
}

// Render statistics in the sidebar
function renderStatistics(stats) {
    document.getElementById('doc-count').textContent = stats.total_docs || 0;
    document.getElementById('commit-count').textContent = stats.total_commits || 0;
    document.getElementById('author-count').textContent = stats.unique_authors || 0;
}

// Render recent changes in the sidebar
function renderRecentChanges(recentChanges) {
    const recentChangesList = document.getElementById('recent-changes');

    if (!recentChanges || recentChanges.length === 0) {
        recentChangesList.innerHTML = '<div class="loading">No recent changes</div>';
        return;
    }

    recentChangesList.innerHTML = '';

    recentChanges.forEach(change => {
        const recentItem = document.createElement('div');
        recentItem.className = 'recent-item';

        const message = document.createElement('div');
        message.className = 'recent-item-message';
        message.textContent = change.message;

        const meta = document.createElement('div');
        meta.className = 'recent-item-meta';
        meta.textContent = `${change.author} - ${formatDate(change.date)}`;

        recentItem.appendChild(message);
        recentItem.appendChild(meta);

        recentChangesList.appendChild(recentItem);
    });
}

// Format date to relative time or absolute date
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) {
        return 'just now';
    } else if (diffMins < 60) {
        return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
        return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
        // Format as date
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return date.toLocaleDateString(undefined, options);
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show loading overlay
function showLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.remove('hidden');
}

// Hide loading overlay
function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.add('hidden');
}

// Show error overlay
function showError(message) {
    const errorOverlay = document.getElementById('error-overlay');
    const errorMessage = document.getElementById('error-message');
    const loadingOverlay = document.getElementById('loading-overlay');

    errorMessage.textContent = message;
    errorOverlay.classList.remove('hidden');
    loadingOverlay.classList.add('hidden');
}

// Hide error overlay
function hideError() {
    const errorOverlay = document.getElementById('error-overlay');
    errorOverlay.classList.add('hidden');
}

// Retry loading
function retryLoad() {
    hideError();
    initApp();
}

// Setup tab switching
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;

            // Update button states
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // Update content visibility
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`${tabName}-view`).classList.add('active');

            // Lazy load learning dashboard
            if (tabName === 'learning' && !learningInitialized) {
                initLearningDashboard();
                learningInitialized = true;
            }
        });
    });
}

// =====================================================
// LEARNING DASHBOARD FUNCTIONS
// =====================================================

async function initLearningDashboard() {
    try {
        // Load learnings data
        const response = await fetch('data/learnings.json');
        learningsData = await response.json();

        // Render components
        renderLearningStats(learningsData);
        renderLearnings(learningsData.learnings);
        renderInteractions(learningsData.interactions);

        // Setup filters
        setupLearningFilters();

    } catch (error) {
        console.error('Failed to load learnings:', error);
        showLearningError();
    }
}

function renderLearningStats(data) {
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

function extractRating(feedback) {
    if (!feedback) return null;
    const match = feedback.match(/Rating: (\d)/);
    return match ? parseInt(match[1]) : null;
}

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
                <span>📅 ${formatLearningDate(learning.created_at)}</span>
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
            <div class="interaction-time">${formatLearningDate(interaction.timestamp)}</div>
            <div class="interaction-context">${truncate(escapeHtml(interaction.user_context), 100)}</div>
            ${interaction.identified_gap ? '<div class="interaction-feedback">🎯 Gap Identified</div>' : ''}
            ${interaction.user_feedback ? `<div class="interaction-feedback">⭐ ${extractRating(interaction.user_feedback)}/5</div>` : ''}
        </div>
    `).join('');
}

function setupLearningFilters() {
    document.getElementById('gap-filter').addEventListener('change', (e) => {
        currentFilters.gapType = e.target.value;
        renderLearnings(learningsData.learnings);
    });

    document.getElementById('status-filter').addEventListener('change', (e) => {
        currentFilters.status = e.target.value;
        renderLearnings(learningsData.learnings);
    });
}

function showLearningError() {
    document.getElementById('learning-list').innerHTML = `
        <div class="welcome">
            <h2>⚠️ Failed to Load Learnings</h2>
            <p>Could not load learnings data. Make sure learnings.json exists.</p>
        </div>
    `;
}

function formatGapType(type) {
    return type.replace('_', ' ').toUpperCase();
}

function formatLearningDate(isoString) {
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
    if (!str) return '';
    if (str.length <= length) return str;
    return str.substring(0, length) + '...';
}

// =====================================================
// INITIALIZATION
// =====================================================

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Retry button handler
document.addEventListener('DOMContentLoaded', () => {
    const retryButton = document.getElementById('retry-button');
    if (retryButton) {
        retryButton.addEventListener('click', retryLoad);
    }
});
