// Documentation Browser - Main Application

// Global state
let docsData = null;
let currentDoc = null;

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

// Export for testing
export { initApp, docsData, currentDoc };
