// graph-renderer.js - vis.js graph rendering module

/**
 * Node type configurations with styling
 */
const NODE_STYLES = {
    Document: {
        color: '#4A90E2',
        shape: 'box',
        icon: '📄',
        font: { color: '#ffffff' }
    },
    Issue: {
        color: '#E74C3C',
        shape: 'diamond',
        icon: '🐛',
        font: { color: '#ffffff' }
    },
    PullRequest: {
        color: '#27AE60',
        shape: 'diamond',
        icon: '🔀',
        font: { color: '#ffffff' }
    },
    Concept: {
        color: '#F39C12',
        shape: 'ellipse',
        icon: '💡',
        font: { color: '#ffffff' }
    },
    Skill: {
        color: '#9B59B6',
        shape: 'star',
        icon: '🎯',
        font: { color: '#ffffff' }
    }
};

/**
 * Edge type configurations with styling
 */
const EDGE_STYLES = {
    ABOUT: {
        color: '#95A5A6',
        dashes: false,
        arrows: 'to'
    },
    FIXED_BY: {
        color: '#27AE60',
        dashes: false,
        arrows: 'to'
    },
    MODIFIES: {
        color: '#E67E22',
        dashes: false,
        arrows: 'to'
    },
    GENERATES: {
        color: '#3498DB',
        dashes: true,
        arrows: 'to'
    },
    EXPLAINS: {
        color: '#9B59B6',
        dashes: true,
        arrows: 'to'
    }
};

/**
 * Transform raw JSON nodes to vis.js format
 * @param {Array} rawNodes - Array of node objects from graph.json
 * @returns {Array} vis.js formatted nodes
 */
export function transformNodes(rawNodes) {
    return rawNodes.map(node => {
        const style = NODE_STYLES[node.type] || {
            color: '#95A5A6',
            shape: 'box',
            icon: '📦'
        };

        // Create label with icon and title
        const label = `${style.icon} ${node.properties.title || node.properties.name || node.id}`;

        // Create tooltip with additional info
        let title = `<strong>${node.type}</strong><br>${node.properties.title || node.properties.name || node.id}`;
        if (node.properties.path) {
            title += `<br><em>${node.properties.path}</em>`;
        }
        if (node.properties.status) {
            title += `<br>Status: ${node.properties.status}`;
        }

        return {
            id: node.id,
            label: label,
            title: title,
            shape: style.shape,
            color: {
                background: style.color,
                border: style.color,
                highlight: {
                    background: style.color,
                    border: '#000000'
                },
                hover: {
                    background: style.color,
                    border: '#000000'
                }
            },
            font: style.font,
            // Store original data for detail panel
            originalData: node
        };
    });
}

/**
 * Transform raw JSON edges to vis.js format
 * @param {Array} rawEdges - Array of edge objects from graph.json
 * @returns {Array} vis.js formatted edges
 */
export function transformEdges(rawEdges) {
    return rawEdges.map(edge => {
        const style = EDGE_STYLES[edge.type] || {
            color: '#95A5A6',
            dashes: false,
            arrows: 'to'
        };

        return {
            id: edge.id,
            from: edge.from,
            to: edge.to,
            label: edge.type,
            color: {
                color: style.color,
                highlight: style.color,
                hover: style.color
            },
            dashes: style.dashes,
            arrows: style.arrows,
            font: {
                size: 10,
                align: 'middle',
                color: '#555555'
            },
            // Store original data
            originalData: edge
        };
    });
}

/**
 * vis.js network configuration options
 */
const VIS_OPTIONS = {
    nodes: {
        borderWidth: 2,
        borderWidthSelected: 4,
        size: 25,
        font: {
            size: 14,
            face: 'Arial'
        }
    },
    edges: {
        width: 2,
        smooth: {
            type: 'continuous',
            roundness: 0.5
        }
    },
    physics: {
        enabled: true,
        barnesHut: {
            gravitationalConstant: -2000,
            centralGravity: 0.3,
            springLength: 200,
            springConstant: 0.04,
            damping: 0.09,
            avoidOverlap: 0.5
        },
        stabilization: {
            enabled: true,
            iterations: 200,
            updateInterval: 25
        }
    },
    interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true,
        dragView: true,
        navigationButtons: true,
        keyboard: {
            enabled: true,
            speed: { x: 10, y: 10, zoom: 0.02 }
        }
    }
};

/**
 * Render the graph using vis.js
 * @param {Object} graphData - Graph data with nodes and edges
 * @param {HTMLElement} container - DOM element to render graph in
 * @param {Function} onNodeClick - Callback for node click events
 * @returns {vis.Network} The vis.js network instance
 */
export function renderGraph(graphData, container, onNodeClick) {
    // Transform data
    const nodes = transformNodes(graphData.nodes);
    const edges = transformEdges(graphData.edges);

    // Create vis.js DataSets
    const nodesDataSet = new vis.DataSet(nodes);
    const edgesDataSet = new vis.DataSet(edges);

    const data = {
        nodes: nodesDataSet,
        edges: edgesDataSet
    };

    // Create network
    const network = new vis.Network(container, data, VIS_OPTIONS);

    // Event handlers
    network.on('click', (params) => {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = nodesDataSet.get(nodeId);
            if (onNodeClick && node) {
                onNodeClick(node.originalData);
            }
        }
    });

    // Handle stabilization
    network.on('stabilizationProgress', (params) => {
        const percentage = Math.round((params.iterations / params.total) * 100);
        console.log(`Stabilization: ${percentage}%`);
    });

    network.on('stabilizationIterationsDone', () => {
        console.log('Graph stabilized');
        network.setOptions({ physics: { enabled: false } });
    });

    // Disable physics after initial stabilization for better performance
    network.once('stabilizationIterationsDone', () => {
        network.setOptions({ physics: { enabled: false } });
    });

    return network;
}

/**
 * Handle node hover events
 * @param {vis.Network} network - The vis.js network instance
 * @param {Function} onHover - Callback for hover events
 */
export function handleNodeHover(network, onHover) {
    network.on('hoverNode', (params) => {
        if (onHover) {
            onHover(params.node);
        }
    });
}

/**
 * Filter nodes by type
 * @param {vis.Network} network - The vis.js network instance
 * @param {Array} visibleTypes - Array of node types to show
 * @param {Array} allNodes - All graph nodes
 */
export function filterNodesByType(network, visibleTypes, allNodes) {
    const nodes = transformNodes(allNodes);
    const filteredNodes = nodes.filter(node =>
        visibleTypes.includes(node.originalData.type)
    );

    const nodesDataSet = network.body.data.nodes;
    nodesDataSet.clear();
    nodesDataSet.add(filteredNodes);
}

/**
 * Search and highlight nodes
 * @param {vis.Network} network - The vis.js network instance
 * @param {string} query - Search query
 * @param {Array} allNodes - All graph nodes
 * @returns {Array} Matching node IDs
 */
export function searchNodes(network, query, allNodes) {
    if (!query) {
        return [];
    }

    const lowerQuery = query.toLowerCase();
    const matchingNodes = allNodes.filter(node => {
        const title = (node.properties.title || node.properties.name || node.id).toLowerCase();
        const path = (node.properties.path || '').toLowerCase();
        return title.includes(lowerQuery) || path.includes(lowerQuery);
    });

    return matchingNodes.map(node => node.id);
}

/**
 * Highlight specific nodes
 * @param {vis.Network} network - The vis.js network instance
 * @param {Array} nodeIds - Array of node IDs to highlight
 */
export function highlightNodes(network, nodeIds) {
    network.selectNodes(nodeIds);
    if (nodeIds.length > 0) {
        network.fit({
            nodes: nodeIds,
            animation: {
                duration: 500,
                easingFunction: 'easeInOutQuad'
            }
        });
    }
}

/**
 * Reset view to show all nodes
 * @param {vis.Network} network - The vis.js network instance
 */
export function resetView(network) {
    network.unselectAll();
    network.fit({
        animation: {
            duration: 500,
            easingFunction: 'easeInOutQuad'
        }
    });
}
