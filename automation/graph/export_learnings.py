#!/usr/bin/env python3
"""
Export learnings and interactions from memory.db to JSON for web UI.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "learning" / "data" / "memory.db"
OUTPUT_PATH = Path(__file__).parent.parent / "web" / "data" / "learnings.json"

def export_learnings():
    """Export learnings and interactions to JSON."""

    # Check if database exists
    if not DB_PATH.exists():
        print(f"⚠️  Database not found at {DB_PATH}")
        print("   Creating empty learnings.json...")
        create_empty_export()
        return

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Query interactions
    interactions_cursor = conn.execute("""
        SELECT id, timestamp, user_context, agent_response, user_feedback,
               identified_gap, created_issue_id, created_at
        FROM interactions
        ORDER BY created_at DESC
    """)

    interactions = [dict(row) for row in interactions_cursor.fetchall()]

    # Query learnings with interaction context
    learnings_cursor = conn.execute("""
        SELECT l.id, l.interaction_id, l.concept, l.gap_type,
               l.proposed_fix, l.status, l.created_at,
               i.user_context
        FROM learnings l
        LEFT JOIN interactions i ON l.interaction_id = i.id
        ORDER BY l.created_at DESC
    """)

    learnings = [dict(row) for row in learnings_cursor.fetchall()]

    conn.close()

    # Prepare export data
    export_data = {
        "metadata": {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "interaction_count": len(interactions),
            "learning_count": len(learnings),
            "version": "1.0"
        },
        "interactions": interactions,
        "learnings": learnings
    }

    # Write to file
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(export_data, indent=2), encoding='utf-8')

    print(f"✅ Exported {len(interactions)} interactions and {len(learnings)} learnings")
    print(f"   Output: {OUTPUT_PATH}")

def create_empty_export():
    """Create empty learnings.json for when database doesn't exist yet."""
    export_data = {
        "metadata": {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "interaction_count": 0,
            "learning_count": 0,
            "version": "1.0",
            "note": "No learnings captured yet. Use the learning capture hook to record interactions."
        },
        "interactions": [],
        "learnings": []
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(export_data, indent=2), encoding='utf-8')

    print(f"✅ Created empty learnings.json at {OUTPUT_PATH}")

if __name__ == "__main__":
    export_learnings()
