#!/usr/bin/env python3
"""
Export Knowledge Graph to JSON for vis.js visualization.

Usage:
    python export_json.py --db automation/graph/data/graph.db --output web/data/graph.json
"""

import argparse
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class GraphExporter:
    """Export SQLite knowledge graph to JSON format for vis.js."""

    # Node type styling configuration
    NODE_STYLES = {
        'Document': {
            'color': '#4A90E2',
            'shape': 'box',
            'icon': '📄'
        },
        'Issue': {
            'color': '#E74C3C',
            'shape': 'diamond',
            'icon': '🐛'
        },
        'PullRequest': {
            'color': '#27AE60',
            'shape': 'diamond',
            'icon': '🔀'
        },
        'Concept': {
            'color': '#F39C12',
            'shape': 'ellipse',
            'icon': '💡'
        },
        'Skill': {
            'color': '#9B59B6',
            'shape': 'star',
            'icon': '🎯'
        }
    }

    # Edge type styling configuration
    EDGE_STYLES = {
        'ABOUT': {'color': '#95A5A6', 'dashes': False},
        'FIXED_BY': {'color': '#27AE60', 'dashes': False},
        'MODIFIES': {'color': '#E67E22', 'dashes': False},
        'GENERATES': {'color': '#3498DB', 'dashes': True},
        'EXPLAINS': {'color': '#9B59B6', 'dashes': True},
        'INCLUDES': {'color': '#1ABC9C', 'dashes': True}
    }

    def __init__(self):
        self.nodes = []
        self.edges = []

    def connect_db(self, db_path: Path) -> sqlite3.Connection:
        """Connect to SQLite database."""
        print(f"🔌 Connecting to database: {db_path}")

        if not db_path.exists():
            print(f"⚠️  Database not found: {db_path}")
            print("   Creating empty graph for initial deployment")
            return None

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def export_nodes(self, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        """Export all nodes from the graph."""
        if conn is None:
            return []

        print("📦 Exporting nodes...")

        cursor = conn.execute("SELECT * FROM nodes ORDER BY created_at")
        nodes = []

        for row in cursor:
            node_id = row['id']
            node_type = row['type']
            properties = json.loads(row['properties'])

            # Get node styling
            style = self.NODE_STYLES.get(node_type, {
                'color': '#95A5A6',
                'shape': 'dot',
                'icon': '⚪'
            })

            # Build node label
            label = self._build_node_label(node_type, properties)

            # Build vis.js node
            vis_node = {
                'id': node_id,
                'label': label,
                'type': node_type,
                'shape': style['shape'],
                'color': {
                    'background': style['color'],
                    'border': self._darken_color(style['color']),
                    'highlight': {
                        'background': style['color'],
                        'border': '#000000'
                    }
                },
                'font': {
                    'color': '#333333',
                    'size': 14
                },
                'title': self._build_node_tooltip(node_type, properties),
                'properties': properties
            }

            nodes.append(vis_node)

        print(f"  ✓ Exported {len(nodes)} nodes")
        return nodes

    def export_edges(self, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        """Export all edges from the graph."""
        if conn is None:
            return []

        print("🔗 Exporting edges...")

        cursor = conn.execute("SELECT * FROM edges ORDER BY created_at")
        edges = []

        for row in cursor:
            edge_id = row['id']
            from_id = row['from_id']
            to_id = row['to_id']
            relationship = row['relationship']

            # Get edge styling
            style = self.EDGE_STYLES.get(relationship, {
                'color': '#95A5A6',
                'dashes': False
            })

            # Build vis.js edge
            vis_edge = {
                'id': edge_id,
                'from': from_id,
                'to': to_id,
                'label': relationship.replace('_', ' '),
                'arrows': 'to',
                'color': {
                    'color': style['color'],
                    'highlight': '#000000'
                },
                'dashes': style['dashes'],
                'font': {
                    'size': 11,
                    'color': '#666666',
                    'align': 'middle'
                },
                'smooth': {
                    'type': 'continuous'
                }
            }

            edges.append(vis_edge)

        print(f"  ✓ Exported {len(edges)} edges")
        return edges

    def _build_node_label(self, node_type: str, properties: Dict) -> str:
        """Build display label for a node."""
        if node_type == 'Document':
            # Use filename from path
            path = properties.get('path', 'Unknown')
            return Path(path).stem

        elif node_type == 'Issue':
            number = properties.get('number', '?')
            return f"Issue #{number}"

        elif node_type == 'PullRequest':
            number = properties.get('number', '?')
            return f"PR #{number}"

        elif node_type == 'Concept':
            return properties.get('name', 'Unknown Concept')

        elif node_type == 'Skill':
            return properties.get('name', 'Unknown Skill')

        else:
            return properties.get('name') or properties.get('title') or 'Unknown'

    def _build_node_tooltip(self, node_type: str, properties: Dict) -> str:
        """Build HTML tooltip for a node."""
        lines = [f"<b>{node_type}</b>"]

        if node_type == 'Document':
            lines.append(f"Path: {properties.get('path', 'Unknown')}")

        elif node_type == 'Issue':
            lines.append(f"#{properties.get('number', '?')}: {properties.get('title', 'Untitled')}")
            lines.append(f"Status: {properties.get('status', 'unknown')}")

        elif node_type == 'PullRequest':
            lines.append(f"#{properties.get('number', '?')}: {properties.get('title', 'Untitled')}")
            lines.append(f"Status: {properties.get('status', 'unknown')}")

        elif node_type == 'Concept':
            lines.append(properties.get('name', 'Unknown'))

        elif node_type == 'Skill':
            lines.append(properties.get('name', 'Unknown'))

        return '<br>'.join(lines)

    def _darken_color(self, hex_color: str, percent: int = 20) -> str:
        """Darken a hex color by a percentage."""
        # Simple darkening - reduce RGB values
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

        r = max(0, int(r * (1 - percent / 100)))
        g = max(0, int(g * (1 - percent / 100)))
        b = max(0, int(b * (1 - percent / 100)))

        return f'#{r:02x}{g:02x}{b:02x}'

    def export(self, db_path: Path, output_path: Path):
        """Main export process."""
        print("=" * 70)
        print("📊 Knowledge Graph JSON Exporter")
        print("=" * 70)
        print()

        # Connect to database
        conn = self.connect_db(db_path)

        # Export nodes and edges
        nodes = self.export_nodes(conn)
        edges = self.export_edges(conn)

        # Close connection
        if conn:
            conn.close()

        # Build output JSON
        graph_data = {
            'metadata': {
                'exported_at': datetime.utcnow().isoformat() + 'Z',
                'node_count': len(nodes),
                'edge_count': len(edges),
                'version': '1.0',
                'generator': 'export_json.py'
            },
            'nodes': nodes,
            'edges': edges
        }

        # Write to output file
        print(f"💾 Writing to: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(graph_data, indent=2), encoding='utf-8')

        print(f"  ✓ File size: {len(json.dumps(graph_data))} bytes")
        print()

        # Summary
        print("=" * 70)
        print("✅ Export complete!")
        print("=" * 70)
        print(f"Nodes: {len(nodes)}")
        print(f"Edges: {len(edges)}")
        print(f"Output: {output_path}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Export Knowledge Graph to JSON for vis.js',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python export_json.py --db automation/graph/data/graph.db --output web/data/graph.json
  python export_json.py --output web/data/graph.json  # Uses default DB path
        """
    )

    parser.add_argument(
        '--db',
        default='automation/graph/data/graph.db',
        help='Path to SQLite database (default: automation/graph/data/graph.db)'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output path for JSON file'
    )

    args = parser.parse_args()

    # Validate inputs
    db_path = Path(args.db)
    output_path = Path(args.output)

    # Export
    try:
        exporter = GraphExporter()
        exporter.export(db_path, output_path)
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
