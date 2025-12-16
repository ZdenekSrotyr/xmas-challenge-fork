// app.js - Main application logic

import { renderGraph, filterNodesByType, searchNodes, highlightNodes, resetView } from './graph-renderer.js';
import { initFilters, updateStats } from './filters.js';
import { showDetailPanel, hideDetailPanel } from './node-details.js';

// Global state
let networkInstance = null;
let graphData = null;

/**
 * Show loading state
 */
function showLoading() {
    const loading = document.getElementById('loading-state');
    const main = document.querySelector('main');
    const controls = document.querySelector('.controls');

    loading.classList.remove('hidden');
    main.classList.add('hidden');
    controls.classList.add('hidden');
}

/**
 * Hide loading state
 */
function hideLoading() {
    const loading = document.getElementById('loading-state');
    const main = document.querySelector('main');
    const controls = document.querySelector('.controls');

    loading.classList.add('hidden');
    main.classList.remove('hidden');
    controls.classList.remove('hidden');
}

/**
 * Show error state
 * @param {string} message - Error message to display
 */
function showError(message) {
    const errorState = document.getElementById('error-state');
    const errorMessage = document.getElementById('error-message');
    const loading = document.getElementById('loading-state');
    const main = document.querySelector('main');
    const controls = document.querySelector('.controls');

    errorMessage.textContent = message;
    errorState.classList.remove('hidden');
    loading.classList.add('hidden');
    main.classList.add('hidden');
    controls.classList.add('hidden');
}

/**
 * Hide error state
 */
function hideError() {
    const errorState = document.getElementById('error-state');
    errorState.classList.add('hidden');
}

/**
 * Fetch graph data from JSON file
 * @returns {Promise<Object>} Graph data
 */
async function fetchGraphData() {
    try {
        const response = await fetch('data/graph.json');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Validate data structure
        if (!data.nodes || !data.edges) {
            throw new Error('Invalid graph data structure');
        }

        return data;
    } catch (error) {
        console.error('Failed to fetch graph data:', error);
        throw error;
    }
}

/**
 * Update statistics display
 * @param {Object} data - Graph data with nodes and edges
 */
function updateStatsDisplay(data) {
    const nodeCount = document.getElementById('node-count');
    const edgeCount = document.getElementById('edge-count');
    const lastUpdated = document.getElementById('last-updated');

    nodeCount.textContent = data.nodes.length;
    edgeCount.textContent = data.edges.length;

    // Format last updated date
    if (data.metadata && data.metadata.generated_at) {
        const date = new Date(data.metadata.generated_at);
        lastUpdated.textContent = date.toLocaleString();
    } else {
        lastUpdated.textContent = new Date().toLocaleString();
    }
}

/**
 * Initialize filters and controls
 */
function initializeControls() {
    // Type filters
    const filterCheckboxes = [
        'filter-document',
        'filter-issue',
        'filter-pullrequest',
        'filter-concept',
        'filter-skill'
    ];

    filterCheckboxes.forEach(filterId => {
        const checkbox = document.getElementById(filterId);
        if (checkbox) {
            checkbox.addEventListener('change', handleFilterChange);
        }
    });

    // Search input
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                handleSearch(e.target.value);
            }, 300); // Debounce search
        });
    }

    // Reset button
    const resetButton = document.getElementById('reset-button');
    if (resetButton) {
        resetButton.addEventListener('click', handleReset);
    }

    // Close detail panel button
    const closeDetail = document.getElementById('close-detail');
    if (closeDetail) {
        closeDetail.addEventListener('click', () => {
            hideDetailPanel();
        });
    }
}

/**
 * Handle filter checkbox changes
 */
function handleFilterChange() {
    if (!networkInstance || !graphData) return;

    // Get active filters
    const visibleTypes = [];
    const typeMap = {
        'filter-document': 'Document',
        'filter-issue': 'Issue',
        'filter-pullrequest': 'PullRequest',
        'filter-concept': 'Concept',
        'filter-skill': 'Skill'
    };

    Object.entries(typeMap).forEach(([filterId, type]) => {
        const checkbox = document.getElementById(filterId);
        if (checkbox && checkbox.checked) {
            visibleTypes.push(type);
        }
    });

    // Filter nodes
    filterNodesByType(networkInstance, visibleTypes, graphData.nodes);

    // Update stats for visible nodes
    const visibleNodes = graphData.nodes.filter(node =>
        visibleTypes.includes(node.type)
    );
    updateStats(visibleNodes, graphData.edges);
}

/**
 * Handle search input
 * @param {string} query - Search query
 */
function handleSearch(query) {
    if (!networkInstance || !graphData) return;

    if (!query.trim()) {
        // Clear search - reset highlighting
        networkInstance.unselectAll();
        return;
    }

    // Search nodes
    const matchingNodeIds = searchNodes(networkInstance, query, graphData.nodes);

    if (matchingNodeIds.length > 0) {
        highlightNodes(networkInstance, matchingNodeIds);
    } else {
        // No matches found
        networkInstance.unselectAll();
    }
}

/**
 * Handle reset button click
 */
function handleReset() {
    if (!networkInstance) return;

    // Reset all filters
    const filterCheckboxes = document.querySelectorAll('.filter-checkbox input[type="checkbox"]');
    filterCheckboxes.forEach(checkbox => {
        checkbox.checked = true;
    });

    // Clear search
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.value = '';
    }

    // Reset view
    resetView(networkInstance);

    // Hide detail panel
    hideDetailPanel();

    // Update stats
    if (graphData) {
        updateStatsDisplay(graphData);
    }
}

/**
 * Handle node click - show detail panel
 * @param {Object} nodeData - Node data from graph
 */
function handleNodeClick(nodeData) {
    showDetailPanel(nodeData, graphData.edges, graphData.nodes);
}

/**
 * Initialize the application
 */
async function initApp() {
    try {
        console.log('Initializing Knowledge Graph UI...');

        // Show loading state
        showLoading();

        // Fetch graph data
        graphData = await fetchGraphData();
        console.log(`Loaded ${graphData.nodes.length} nodes and ${graphData.edges.length} edges`);

        // Initialize controls
        initializeControls();

        // Render graph
        const container = document.getElementById('graph-container');
        if (!container) {
            throw new Error('Graph container not found');
        }

        networkInstance = renderGraph(graphData, container, handleNodeClick);
        console.log('Graph rendered successfully');

        // Update stats
        updateStatsDisplay(graphData);

        // Hide loading state
        hideLoading();

        // Log success
        console.log('Knowledge Graph UI initialized successfully');

    } catch (error) {
        console.error('Failed to initialize app:', error);

        let errorMessage = 'An error occurred while loading the knowledge graph.';

        if (error.message.includes('HTTP error')) {
            errorMessage = 'Failed to load graph data. The data file may not exist yet.';
        } else if (error.message.includes('Invalid graph data')) {
            errorMessage = 'The graph data file is invalid or corrupted.';
        }

        showError(errorMessage);
    }
}

/**
 * Retry loading the graph
 */
function retryLoad() {
    hideError();
    initApp();
}

// Initialize app when DOM is ready
window.addEventListener('DOMContentLoaded', initApp);

// Retry button handler
document.addEventListener('DOMContentLoaded', () => {
    const retryButton = document.getElementById('retry-button');
    if (retryButton) {
        retryButton.addEventListener('click', retryLoad);
    }
});

// Export for testing
export { initApp, networkInstance, graphData };
