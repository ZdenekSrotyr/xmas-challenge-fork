#!/usr/bin/env python3
"""Track user satisfaction."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "memory.db"

def add_feedback(interaction_id, rating, comment=None):
    """Add user feedback to interaction."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE interactions SET user_feedback = ? WHERE id = ?",
        (f"Rating: {rating}/5. {comment or ''}", interaction_id)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--interaction-id", type=int, required=True)
    parser.add_argument("--rating", type=int, choices=[1,2,3,4,5], required=True)
    parser.add_argument("--comment", default=None)

    args = parser.parse_args()
    add_feedback(args.interaction_id, args.rating, args.comment)
    print(f"✅ Feedback recorded")
