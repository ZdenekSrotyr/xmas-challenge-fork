// node-details.js - Detail panel functionality

/**
 * Show the detail panel with node information
 * @param {Object} node - Node data
 * @param {Array} edges - All edges in the graph
 * @param {Array} allNodes - All nodes in the graph
 */
export function showDetailPanel(node, edges, allNodes) {
    const panel = document.getElementById('detail-panel');
    const content = document.getElementById('detail-content');

    if (!panel || !content) return;

    // Generate detail HTML based on node type
    const detailHTML = renderNodeDetails(node, edges, allNodes);
    content.innerHTML = detailHTML;

    // Show panel
    panel.classList.remove('hidden');
}

/**
 * Hide the detail panel
 */
export function hideDetailPanel() {
    const panel = document.getElementById('detail-panel');
    if (panel) {
        panel.classList.add('hidden');
    }
}

/**
 * Render node details based on type
 * @param {Object} node - Node data
 * @param {Array} edges - All edges in the graph
 * @param {Array} allNodes - All nodes in the graph
 * @returns {string} HTML string
 */
function renderNodeDetails(node, edges, allNodes) {
    const type = node.type;
    const props = node.properties;

    // Get icon based on type
    const icons = {
        'Document': '📄',
        'Issue': '🐛',
        'PullRequest': '🔀',
        'Concept': '💡',
        'Skill': '🎯'
    };
    const icon = icons[type] || '📦';

    let html = `
        <div class="detail-header">
            <div class="detail-icon">${icon}</div>
            <h2 class="detail-title">${props.title || props.name || node.id}</h2>
    `;

    // Type-specific rendering
    switch (type) {
        case 'Document':
            html += renderDocumentDetails(props);
            break;
        case 'Issue':
            html += renderIssueDetails(props);
            break;
        case 'PullRequest':
            html += renderPullRequestDetails(props);
            break;
        case 'Concept':
            html += renderConceptDetails(props);
            break;
        case 'Skill':
            html += renderSkillDetails(props);
            break;
        default:
            html += `<p class="detail-subtitle">Type: ${type}</p>`;
    }

    html += '</div>';

    // Add related nodes section
    html += renderConnections(node.id, edges, allNodes);

    return html;
}

/**
 * Render Document-specific details
 */
function renderDocumentDetails(props) {
    let html = '';

    if (props.path) {
        html += `<p class="detail-subtitle"><strong>Path:</strong> ${props.path}</p>`;
    }

    if (props.created_at) {
        const date = new Date(props.created_at);
        html += `<p class="detail-subtitle"><strong>Created:</strong> ${date.toLocaleDateString()}</p>`;
    }

    if (props.description) {
        html += `
            <div class="detail-section">
                <h3>Description</h3>
                <p>${props.description}</p>
            </div>
        `;
    }

    return html;
}

/**
 * Render Issue-specific details
 */
function renderIssueDetails(props) {
    let html = '';

    if (props.number) {
        html += `<p class="detail-subtitle"><strong>Issue #${props.number}</strong></p>`;
    }

    if (props.status) {
        const badgeClass = props.status === 'open' ? 'open' : 'closed';
        html += `<span class="badge ${badgeClass}">${props.status}</span>`;
    }

    if (props.url) {
        html += `<p class="detail-subtitle"><a href="${props.url}" target="_blank" class="detail-link">View on GitHub</a></p>`;
    }

    if (props.description) {
        html += `
            <div class="detail-section">
                <h3>Description</h3>
                <p>${props.description}</p>
            </div>
        `;
    }

    if (props.created_at) {
        const date = new Date(props.created_at);
        html += `<p class="detail-subtitle"><strong>Created:</strong> ${date.toLocaleDateString()}</p>`;
    }

    return html;
}

/**
 * Render PullRequest-specific details
 */
function renderPullRequestDetails(props) {
    let html = '';

    if (props.number) {
        html += `<p class="detail-subtitle"><strong>PR #${props.number}</strong></p>`;
    }

    if (props.status) {
        const badgeClass = props.status === 'merged' ? 'merged' : props.status === 'open' ? 'open' : 'closed';
        html += `<span class="badge ${badgeClass}">${props.status}</span>`;
    }

    if (props.additions !== undefined && props.deletions !== undefined) {
        html += `<p class="detail-subtitle"><strong>Changes:</strong> +${props.additions} -${props.deletions}</p>`;
    }

    if (props.url) {
        html += `<p class="detail-subtitle"><a href="${props.url}" target="_blank" class="detail-link">View on GitHub</a></p>`;
    }

    if (props.description) {
        html += `
            <div class="detail-section">
                <h3>Description</h3>
                <p>${props.description}</p>
            </div>
        `;
    }

    if (props.created_at) {
        const date = new Date(props.created_at);
        html += `<p class="detail-subtitle"><strong>Created:</strong> ${date.toLocaleDateString()}</p>`;
    }

    if (props.merged_at) {
        const date = new Date(props.merged_at);
        html += `<p class="detail-subtitle"><strong>Merged:</strong> ${date.toLocaleDateString()}</p>`;
    }

    return html;
}

/**
 * Render Concept-specific details
 */
function renderConceptDetails(props) {
    let html = '';

    if (props.description) {
        html += `
            <div class="detail-section">
                <h3>Description</h3>
                <p>${props.description}</p>
            </div>
        `;
    }

    if (props.category) {
        html += `<p class="detail-subtitle"><strong>Category:</strong> ${props.category}</p>`;
    }

    return html;
}

/**
 * Render Skill-specific details
 */
function renderSkillDetails(props) {
    let html = '';

    if (props.description) {
        html += `
            <div class="detail-section">
                <h3>Description</h3>
                <p>${props.description}</p>
            </div>
        `;
    }

    if (props.category) {
        html += `<p class="detail-subtitle"><strong>Category:</strong> ${props.category}</p>`;
    }

    if (props.level) {
        html += `<p class="detail-subtitle"><strong>Level:</strong> ${props.level}</p>`;
    }

    return html;
}

/**
 * Render connections (related nodes)
 * @param {string} nodeId - Current node ID
 * @param {Array} edges - All edges
 * @param {Array} allNodes - All nodes
 * @returns {string} HTML string
 */
function renderConnections(nodeId, edges, allNodes) {
    // Find all edges connected to this node
    const incomingEdges = edges.filter(e => e.to === nodeId);
    const outgoingEdges = edges.filter(e => e.from === nodeId);

    if (incomingEdges.length === 0 && outgoingEdges.length === 0) {
        return '<div class="detail-section"><h3>Connections</h3><p>No connections</p></div>';
    }

    let html = '<div class="detail-section"><h3>Connections</h3><ul class="detail-list">';

    // Create a map of node IDs to node objects for quick lookup
    const nodeMap = new Map(allNodes.map(n => [n.id, n]));

    // Incoming connections
    if (incomingEdges.length > 0) {
        incomingEdges.forEach(edge => {
            const fromNode = nodeMap.get(edge.from);
            if (fromNode) {
                const title = fromNode.properties.title || fromNode.properties.name || fromNode.id;
                const icon = getNodeIcon(fromNode.type);
                html += `<li>${icon} <strong>${title}</strong> → ${edge.type}</li>`;
            }
        });
    }

    // Outgoing connections
    if (outgoingEdges.length > 0) {
        outgoingEdges.forEach(edge => {
            const toNode = nodeMap.get(edge.to);
            if (toNode) {
                const title = toNode.properties.title || toNode.properties.name || toNode.id;
                const icon = getNodeIcon(toNode.type);
                html += `<li>${edge.type} → ${icon} <strong>${title}</strong></li>`;
            }
        });
    }

    html += '</ul></div>';
    return html;
}

/**
 * Get icon for node type
 * @param {string} type - Node type
 * @returns {string} Icon emoji
 */
function getNodeIcon(type) {
    const icons = {
        'Document': '📄',
        'Issue': '🐛',
        'PullRequest': '🔀',
        'Concept': '💡',
        'Skill': '🎯'
    };
    return icons[type] || '📦';
}
