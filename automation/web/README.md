# Knowledge Graph UI

Interactive visualization of the knowledge graph showing relationships between documentation, issues, pull requests, concepts, and skills.

## Overview

This is a static HTML/CSS/JavaScript web application that visualizes the knowledge graph using [vis.js](https://visjs.org/). The UI provides:

- **Interactive Graph Visualization** - Explore nodes and their relationships
- **Type-Based Filtering** - Show/hide specific node types (Documents, Issues, PRs, Concepts, Skills)
- **Search Functionality** - Find nodes by name or properties
- **Detail Panel** - Click any node to see detailed information
- **Real-time Updates** - Automatically updates when issues/PRs change (via GitHub Actions)

## Features

### Graph Visualization
- **5 Node Types** with distinct visual styles:
  - **Documents** (📄) - Blue boxes for documentation files
  - **Issues** (🐛) - Red diamonds for GitHub issues
  - **Pull Requests** (🔀) - Green diamonds for PRs
  - **Concepts** (💡) - Orange ellipses for knowledge concepts
  - **Skills** (🎯) - Purple stars for Claude skills

- **Edge Types** showing different relationships:
  - `ABOUT` - Documents about concepts
  - `FIXED_BY` - Issues fixed by PRs
  - `MODIFIES` - PRs modifying documents
  - `GENERATES` - Skills generating documents
  - `EXPLAINS` - Documents explaining concepts

### Interactive Controls
- **Type Filters** - Checkboxes to show/hide node types
- **Search Bar** - Find nodes by name, title, or properties
- **Reset View** - Return to default zoom and filters
- **Statistics Display** - Live counts of visible nodes and edges

### Detail Panel
Click any node to see:
- Type-specific information (number, title, status, etc.)
- Links to GitHub for issues and PRs
- Change statistics for PRs (additions/deletions)
- Related nodes (incoming and outgoing connections)
- Timestamps (created, updated, closed, merged)

## Local Testing

To run the UI locally:

```bash
# Navigate to the web directory
cd web

# Start a simple HTTP server
python -m http.server 8000

# Or use Python 2
python -m SimpleHTTPServer 8000

# Or use Node.js
npx http-server -p 8000
```

Then open your browser to: `http://localhost:8000`

### Testing with Sample Data

If you don't have a populated graph database, you can create sample data:

```bash
# From the repository root
cd automation/graph

# Generate sample graph.json
python export_json.py --output ../../web/data/graph.json
```

## Architecture

### Data Flow

```
┌─────────────────────┐
│  GitHub Events      │
│  (Issues, PRs)      │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  GitHub Actions     │
│  (track workflows)  │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  SQLite Database    │
│  (graph.db)         │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  export_json.py     │
│  (Python script)    │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  web/data/graph.json│
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  GitHub Pages       │
│  (Static Site)      │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  User's Browser     │
│  (vis.js rendering) │
└─────────────────────┘
```

### Update Flow

1. **Event Triggers**: Issue created/updated or PR opened/merged
2. **Workflow Runs**: `track-issues.yml` or `track-prs.yml` executes
3. **Database Updated**: Knowledge graph database updated
4. **JSON Export**: `export_json.py` generates fresh `graph.json`
5. **Deployment**: `deploy-ui.yml` publishes to GitHub Pages
6. **UI Updates**: Browser refreshes show new graph (60-90 second delay)

### Component Structure

```
web/
├── index.html              # Main HTML structure
├── css/
│   └── styles.css         # All styles (graph, panels, responsive)
├── js/
│   ├── app.js             # Main application logic
│   ├── graph-renderer.js  # vis.js graph rendering
│   ├── filters.js         # Type filters and search
│   └── node-details.js    # Detail panel rendering
└── data/
    └── graph.json         # Graph data (generated)
```

### Module Responsibilities

#### `app.js`
- Application initialization
- Data loading from `graph.json`
- Module coordination
- Error handling
- Loading states

#### `graph-renderer.js`
- vis.js Network initialization
- Node and edge transformation
- Visual styling
- Physics simulation
- Interaction handlers

#### `filters.js`
- Type-based filtering
- Search functionality
- Statistics updates
- View reset
- Visibility management

#### `node-details.js`
- Detail panel display
- Type-specific rendering
- Connection visualization
- Click handlers for related nodes

## File Structure

### HTML Structure (`index.html`)

```html
<body>
  <header>           <!-- Title and description -->
  <div class="controls">
    <filters>        <!-- Type checkboxes -->
    <search>         <!-- Search input -->
    <stats>          <!-- Node/edge counts -->
  </div>
  <main>
    <div id="graph"> <!-- vis.js container -->
    <aside id="panel"> <!-- Detail panel (hidden by default) -->
  </main>
  <loading>          <!-- Loading spinner -->
  <error>            <!-- Error message -->
</body>
```

### Data Format (`graph.json`)

```json
{
  "metadata": {
    "version": "1.0",
    "exported_at": "2025-12-16T10:30:00Z",
    "total_nodes": 42,
    "total_edges": 87
  },
  "nodes": [
    {
      "id": "Document:doc-123",
      "type": "Document",
      "properties": {
        "title": "Storage API Guide",
        "path": "docs/keboola/storage-api.md",
        "created_at": "2025-12-15T08:00:00Z"
      }
    }
  ],
  "edges": [
    {
      "id": 1,
      "from": "Issue:1",
      "to": "PullRequest:3",
      "relationship": "FIXED_BY",
      "properties": {}
    }
  ]
}
```

## Customization

### Styling

All styles are in `css/styles.css`. Key customization points:

**Node Colors**: Change node type colors in `graph-renderer.js`:
```javascript
const NODE_STYLES = {
    Document: { color: '#4A90E2', shape: 'box' },
    Issue: { color: '#E74C3C', shape: 'diamond' },
    // ... modify colors here
};
```

**Layout**: Adjust panel sizes in `styles.css`:
```css
#graph-container {
    width: 70%;  /* Change graph width */
}

#detail-panel {
    width: 30%;  /* Change panel width */
}
```

**Responsive Breakpoint**: Change mobile breakpoint:
```css
@media (max-width: 768px) {
    /* Modify mobile styles */
}
```

### Adding Features

#### Add New Node Type

1. **Update `graph-renderer.js`**:
   ```javascript
   const NODE_STYLES = {
       // ... existing types
       NewType: { color: '#123456', shape: 'triangle', icon: '🎨' }
   };
   ```

2. **Add filter checkbox in `index.html`**:
   ```html
   <label class="filter-label">
       <input type="checkbox" class="filter-checkbox" data-type="NewType" checked>
       <span>🎨 New Types</span>
   </label>
   ```

3. **Add rendering logic in `node-details.js`**:
   ```javascript
   renderNewType(node, props) {
       // Custom rendering logic
   }
   ```

#### Add New Relationship Type

1. **Update edge styling in `graph-renderer.js`**:
   ```javascript
   const EDGE_STYLES = {
       // ... existing types
       NEW_REL: { color: '#123456', dashes: false }
   };
   ```

### Extending Functionality

#### Add Advanced Search
- Modify `filters.js` `searchNodes()` to support regex or advanced queries
- Add filter by date range
- Add filter by status

#### Add Export Features
- Add button to export visible graph as image (use vis.js `network.canvas.frame.toDataURL()`)
- Export filtered data as JSON

#### Add Statistics Dashboard
- Create new page `stats.html`
- Use Chart.js for visualizations
- Show trends over time

## Troubleshooting

### Empty Graph

**Problem**: Graph loads but shows no nodes

**Solutions**:
1. Check browser console for errors (F12)
2. Verify `graph.json` exists and has valid data:
   ```bash
   curl http://localhost:8000/data/graph.json
   ```
3. Check if database has data:
   ```bash
   python automation/graph/knowledge_graph.py --stats
   ```
4. Regenerate JSON:
   ```bash
   python automation/graph/export_json.py --output web/data/graph.json
   ```

### Slow Loading

**Problem**: Graph takes too long to load or is laggy

**Solutions**:
1. **Reduce physics iterations**: Edit `graph-renderer.js`:
   ```javascript
   physics: {
       stabilization: {
           iterations: 100  // Reduce from 200
       }
   }
   ```

2. **Disable physics after stabilization**:
   ```javascript
   network.once('stabilizationIterationsDone', function() {
       network.setOptions({ physics: false });
   });
   ```

3. **Limit visible nodes**: Use filters to show fewer nodes at once

### Mobile Display Issues

**Problem**: Layout broken on mobile devices

**Solutions**:
1. Check viewport meta tag in `index.html`:
   ```html
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   ```

2. Test responsive breakpoint:
   - Open DevTools (F12)
   - Toggle device toolbar
   - Test at 768px width

3. Adjust mobile styles in `styles.css`

### CORS Errors (Local Development)

**Problem**: `graph.json` fails to load with CORS error

**Solutions**:
1. Always use a web server (not `file://` protocol)
2. Use `python -m http.server` or similar
3. If using custom server, ensure proper CORS headers

### Graph Data Not Updating

**Problem**: Made changes but graph doesn't reflect them

**Solutions**:
1. **Clear browser cache**: Ctrl+Shift+R (hard refresh)
2. **Verify workflow ran**: Check GitHub Actions tab
3. **Check deployment status**:
   ```bash
   gh workflow view deploy-ui
   ```
4. **Manually trigger deployment**:
   ```bash
   gh workflow run deploy-ui.yml
   ```

### Nodes Overlapping

**Problem**: Nodes are too close together or overlapping

**Solutions**:
1. Adjust physics settings in `graph-renderer.js`:
   ```javascript
   physics: {
       barnesHut: {
           gravitationalConstant: -2000,
           centralGravity: 0.3,
           springLength: 200,  // Increase this
           springConstant: 0.04
       }
   }
   ```

2. Manually arrange and disable physics:
   ```javascript
   network.setOptions({ physics: false });
   // Drag nodes to desired positions
   ```

### Search Not Working

**Problem**: Search returns no results or wrong results

**Solutions**:
1. Check search is case-insensitive (it should be)
2. Verify active filters aren't hiding results
3. Check browser console for JavaScript errors
4. Try resetting view (Reset View button)

## Production Deployment

The UI is automatically deployed to GitHub Pages when:
- Graph database is updated
- Any files in `web/` directory change
- Workflow is manually triggered

**GitHub Pages URL**: `https://<username>.github.io/<repository>/`

### Manual Deployment

```bash
# Trigger deployment workflow
gh workflow run deploy-ui.yml

# Check deployment status
gh run list --workflow=deploy-ui.yml
```

### Deployment Configuration

GitHub Pages settings (in repository settings):
- **Source**: GitHub Actions
- **Custom domain**: Optional
- **HTTPS**: Enabled (recommended)

## Performance Considerations

### Optimization Tips

1. **Lazy Loading**: For large graphs (>1000 nodes), consider:
   - Loading nodes in chunks
   - Showing only connected subgraphs initially
   - Progressive rendering

2. **Physics Optimization**:
   - Disable physics after stabilization
   - Reduce `barnesHut` complexity for large graphs

3. **Caching**:
   - Browser caches `graph.json` appropriately
   - Use ETags for efficient updates
   - Set cache headers in GitHub Pages config

### Scale Limits

Tested performance:
- **Excellent**: <100 nodes, <200 edges
- **Good**: 100-500 nodes, 200-1000 edges
- **Acceptable**: 500-1000 nodes, 1000-2000 edges
- **Needs optimization**: >1000 nodes

## Development Workflow

### Making Changes

1. **Edit files locally**:
   ```bash
   cd web
   # Edit HTML/CSS/JS files
   ```

2. **Test locally**:
   ```bash
   python -m http.server 8000
   # Open http://localhost:8000
   ```

3. **Commit changes**:
   ```bash
   git add web/
   git commit -m "Update UI: description of changes"
   git push
   ```

4. **Automatic deployment**: GitHub Actions deploys to Pages

### Testing Checklist

Before committing UI changes:

- [ ] Graph renders correctly
- [ ] All node types display properly
- [ ] Filters work (show/hide nodes)
- [ ] Search finds nodes correctly
- [ ] Detail panel shows information
- [ ] Related nodes are clickable
- [ ] Mobile layout works (test at 768px and below)
- [ ] No JavaScript console errors
- [ ] Links to GitHub open correctly
- [ ] Reset view button works

## Browser Compatibility

**Supported Browsers**:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

**Required Features**:
- ES6+ JavaScript support
- CSS Grid and Flexbox
- Canvas (for vis.js)
- Fetch API

**Not Supported**:
- Internet Explorer (any version)

## Resources

### Documentation
- [vis.js Network Documentation](https://visjs.github.io/vis-network/docs/network/)
- [vis.js Examples](https://visjs.github.io/vis-network/examples/)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)

### Related Files
- [Main README](../README.md) - Repository overview
- [Knowledge Graph Schema](../automation/graph/knowledge_graph.py) - Database structure
- [Export Script](../automation/graph/export_json.py) - JSON generation
- [Deployment Workflow](../.github/workflows/deploy-ui.yml) - CI/CD config

### Live Demo
- GitHub Pages URL: `https://<username>.github.io/<repository>/`

## License

Same license as the parent repository.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

For major changes, please open an issue first to discuss what you would like to change.

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Search existing [GitHub Issues](../issues)
3. Create a new issue with:
   - Browser version
   - Console errors (if any)
   - Steps to reproduce
   - Expected vs actual behavior

---

**Last Updated**: 2025-12-16
**Version**: 1.0.0
