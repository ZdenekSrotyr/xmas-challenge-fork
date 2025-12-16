// filters.js - Filters and search functionality

/**
 * Update statistics display
 * @param {Array} nodes - Visible nodes
 * @param {Array} edges - All edges
 */
export function updateStats(nodes, edges) {
    const nodeCount = document.getElementById('node-count');
    const edgeCount = document.getElementById('edge-count');

    if (nodeCount) {
        nodeCount.textContent = nodes.length;
    }

    if (edgeCount) {
        // Count edges that connect visible nodes
        const visibleNodeIds = new Set(nodes.map(n => n.id));
        const visibleEdges = edges.filter(e =>
            visibleNodeIds.has(e.from) && visibleNodeIds.has(e.to)
        );
        edgeCount.textContent = visibleEdges.length;
    }
}

/**
 * Initialize filters
 * @param {vis.Network} network - The vis.js network instance
 * @param {Object} graphData - Graph data with nodes and edges
 */
export function initFilters(network, graphData) {
    // Type filter checkboxes
    const filterCheckboxes = document.querySelectorAll('.filter-checkbox input[type="checkbox"]');

    filterCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            applyFilters(network, graphData);
        });
    });

    // Search input
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchNodes(network, graphData, e.target.value);
            }, 300);
        });
    }

    // Reset button
    const resetButton = document.getElementById('reset-button');
    if (resetButton) {
        resetButton.addEventListener('click', () => {
            resetFilters(network, graphData);
        });
    }
}

/**
 * Apply current filters to the network
 * @param {vis.Network} network - The vis.js network instance
 * @param {Object} graphData - Graph data with nodes and edges
 */
export function applyFilters(network, graphData) {
    // Get active node types
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
    const filteredNodes = graphData.nodes.filter(node =>
        visibleTypes.includes(node.type)
    );

    // Update stats
    updateStats(filteredNodes, graphData.edges);
}

/**
 * Search nodes by query
 * @param {vis.Network} network - The vis.js network instance
 * @param {Object} graphData - Graph data with nodes and edges
 * @param {string} query - Search query
 */
export function searchNodes(network, graphData, query) {
    if (!query || !query.trim()) {
        // Clear search
        network.unselectAll();
        return;
    }

    const lowerQuery = query.toLowerCase();

    // Find matching nodes
    const matchingNodes = graphData.nodes.filter(node => {
        const title = (node.properties.title || node.properties.name || node.id).toLowerCase();
        const path = (node.properties.path || '').toLowerCase();
        const description = (node.properties.description || '').toLowerCase();

        return title.includes(lowerQuery) ||
               path.includes(lowerQuery) ||
               description.includes(lowerQuery);
    });

    if (matchingNodes.length > 0) {
        const matchingNodeIds = matchingNodes.map(node => node.id);

        // Select and focus on matching nodes
        network.selectNodes(matchingNodeIds);
        network.fit({
            nodes: matchingNodeIds,
            animation: {
                duration: 500,
                easingFunction: 'easeInOutQuad'
            }
        });
    } else {
        // No matches
        network.unselectAll();
    }
}

/**
 * Reset all filters and search
 * @param {vis.Network} network - The vis.js network instance
 * @param {Object} graphData - Graph data with nodes and edges
 */
export function resetFilters(network, graphData) {
    // Check all filter checkboxes
    const filterCheckboxes = document.querySelectorAll('.filter-checkbox input[type="checkbox"]');
    filterCheckboxes.forEach(checkbox => {
        checkbox.checked = true;
    });

    // Clear search input
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.value = '';
    }

    // Reset network view
    network.unselectAll();
    network.fit({
        animation: {
            duration: 500,
            easingFunction: 'easeInOutQuad'
        }
    });

    // Update stats
    updateStats(graphData.nodes, graphData.edges);
}
