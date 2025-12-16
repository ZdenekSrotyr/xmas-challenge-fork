#!/usr/bin/env python3
"""
Knowledge Graph for tracking documentation, skills, issues, and PRs.

This is a lightweight SQLite-based graph database for the POC.
In production, could migrate to Neo4j or similar.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any


class KnowledgeGraph:
    """Graph database for tracking relationships between documentation entities."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = Path(__file__).parent / "data" / "graph.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Initialize graph schema."""
        self.conn.executescript("""
            -- Nodes table
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                properties JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Edges table (relationships)
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                properties JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_id) REFERENCES nodes(id),
                FOREIGN KEY (to_id) REFERENCES nodes(id),
                UNIQUE(from_id, to_id, relationship)
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
            CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id);
            CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_id);
            CREATE INDEX IF NOT EXISTS idx_edges_relationship ON edges(relationship);
        """)
        self.conn.commit()

    def add_node(self, node_type: str, node_id: str, **properties) -> str:
        """
        Add or update a node in the graph.

        Args:
            node_type: Type of node (Document, Concept, Skill, Issue, PullRequest)
            node_id: Unique identifier for the node
            **properties: Additional properties to store

        Returns:
            The node ID
        """
        full_id = f"{node_type}:{node_id}"

        self.conn.execute("""
            INSERT OR REPLACE INTO nodes (id, type, properties, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (full_id, node_type, json.dumps(properties)))

        self.conn.commit()
        return full_id

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM nodes WHERE id = ?",
            (node_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "type": row["type"],
            "properties": json.loads(row["properties"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

    def update_node(self, node_id: str, **properties):
        """Update node properties."""
        node = self.get_node(node_id)
        if node is None:
            raise ValueError(f"Node not found: {node_id}")

        # Merge properties
        current_props = node["properties"]
        current_props.update(properties)

        self.conn.execute("""
            UPDATE nodes
            SET properties = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (json.dumps(current_props), node_id))

        self.conn.commit()

    def add_edge(self, from_id: str, to_id: str, relationship: str, **properties):
        """
        Add a relationship between two nodes.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            relationship: Type of relationship (EXPLAINS, INCLUDES, FIXED_BY, etc.)
            **properties: Additional edge properties
        """
        self.conn.execute("""
            INSERT OR IGNORE INTO edges (from_id, to_id, relationship, properties)
            VALUES (?, ?, ?, ?)
        """, (from_id, to_id, relationship, json.dumps(properties)))

        self.conn.commit()

    def find_related(self, node_id: str, relationship: Optional[str] = None) -> List[Dict]:
        """Find all nodes related to this node."""
        if relationship:
            query = """
                SELECT n.* FROM nodes n
                JOIN edges e ON (e.to_id = n.id OR e.from_id = n.id)
                WHERE (e.from_id = ? OR e.to_id = ?)
                  AND e.relationship = ?
            """
            params = (node_id, node_id, relationship)
        else:
            query = """
                SELECT n.* FROM nodes n
                JOIN edges e ON (e.to_id = n.id OR e.from_id = n.id)
                WHERE (e.from_id = ? OR e.to_id = ?)
            """
            params = (node_id, node_id)

        cursor = self.conn.execute(query, params)

        results = []
        for row in cursor:
            results.append({
                "id": row["id"],
                "type": row["type"],
                "properties": json.loads(row["properties"])
            })

        return results

    def find_dependents(self, node_id: str, max_depth: int = 3) -> List[str]:
        """
        Find all nodes that depend on this node (recursive).

        Example: If a Document changes, find all Skills that include it.
        """
        visited = set()
        to_visit = [(node_id, 0)]
        dependents = []

        while to_visit:
            current_id, depth = to_visit.pop(0)

            if current_id in visited or depth >= max_depth:
                continue

            visited.add(current_id)

            # Find outgoing edges (nodes that depend on this one)
            cursor = self.conn.execute("""
                SELECT to_id FROM edges WHERE from_id = ?
            """, (current_id,))

            for row in cursor:
                dependent_id = row["to_id"]
                if dependent_id not in visited:
                    dependents.append(dependent_id)
                    to_visit.append((dependent_id, depth + 1))

        return dependents

    def query_by_type(self, node_type: str) -> List[Dict]:
        """Get all nodes of a specific type."""
        cursor = self.conn.execute(
            "SELECT * FROM nodes WHERE type = ? ORDER BY created_at DESC",
            (node_type,)
        )

        results = []
        for row in cursor:
            results.append({
                "id": row["id"],
                "type": row["type"],
                "properties": json.loads(row["properties"]),
                "created_at": row["created_at"]
            })

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        node_count = self.conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edge_count = self.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

        type_counts = {}
        cursor = self.conn.execute("""
            SELECT type, COUNT(*) as count
            FROM nodes
            GROUP BY type
        """)

        for row in cursor:
            type_counts[row["type"]] = row["count"]

        return {
            "total_nodes": node_count,
            "total_edges": edge_count,
            "nodes_by_type": type_counts
        }

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """CLI for testing the graph."""
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Graph CLI")
    parser.add_argument("--stats", action="store_true", help="Show graph statistics")
    parser.add_argument("--list", choices=["documents", "skills", "issues", "prs"], help="List nodes")

    args = parser.parse_args()

    with KnowledgeGraph() as graph:
        if args.stats:
            stats = graph.get_stats()
            print("📊 Knowledge Graph Statistics")
            print(f"Total nodes: {stats['total_nodes']}")
            print(f"Total edges: {stats['total_edges']}")
            print("\nNodes by type:")
            for node_type, count in stats['nodes_by_type'].items():
                print(f"  {node_type}: {count}")

        elif args.list:
            type_map = {
                "documents": "Document",
                "skills": "Skill",
                "issues": "Issue",
                "prs": "PullRequest"
            }

            nodes = graph.query_by_type(type_map[args.list])
            print(f"📋 {args.list.title()}:")
            for node in nodes:
                props = node["properties"]
                title = props.get("title") or props.get("path") or props.get("name")
                print(f"  • {title} ({node['id']})")


if __name__ == "__main__":
    main()
