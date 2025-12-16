#!/usr/bin/env python3
"""Capture learning interactions from Claude Code usage."""
import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "memory.db"

def init_db():
    """Initialize learning database."""
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_context TEXT,
            agent_response TEXT,
            user_feedback TEXT,
            identified_gap INTEGER DEFAULT 0,
            created_issue_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interaction_id INTEGER,
            concept TEXT NOT NULL,
            gap_type TEXT,
            proposed_fix TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (interaction_id) REFERENCES interactions(id)
        )
    """)

    conn.commit()
    conn.close()

def capture_interaction(context, response, feedback=None):
    """Store an interaction."""
    init_db()
    conn = sqlite3.connect(DB_PATH)

    cursor = conn.execute(
        "INSERT INTO interactions (timestamp, user_context, agent_response, user_feedback) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), context, response, feedback)
    )

    interaction_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return interaction_id

if __name__ == "__main__":
    # CLI interface for hook
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--response", required=True)
    parser.add_argument("--feedback", default=None)

    args = parser.parse_args()

    interaction_id = capture_interaction(args.context, args.response, args.feedback)
    print(f"✅ Captured interaction #{interaction_id}")
