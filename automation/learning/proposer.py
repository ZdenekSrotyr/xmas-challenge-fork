#!/usr/bin/env python3
"""Propose documentation updates from learnings."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "memory.db"

def get_pending_learnings():
    """Get learnings that need issues."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        """SELECT l.id, l.concept, l.gap_type, l.proposed_fix, i.user_context
           FROM learnings l
           JOIN interactions i ON l.interaction_id = i.id
           WHERE l.status = 'pending'"""
    )

    learnings = cursor.fetchall()
    conn.close()

    return learnings

def create_issue_for_learning(learning_id, issue_number):
    """Mark learning as issued."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """UPDATE learnings SET status = 'issued' WHERE id = ?""",
        (learning_id,)
    )
    # TODO: Link to GitHub issue
    conn.commit()
    conn.close()

if __name__ == "__main__":
    learnings = get_pending_learnings()

    for learning in learnings:
        print(f"Learning #{learning[0]}: {learning[1]} - {learning[3]}")
