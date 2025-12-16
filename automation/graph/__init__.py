"""
Knowledge Graph module for tracking documentation relationships.
"""

from .knowledge_graph import KnowledgeGraph
from .event_handler import GitHubEventHandler

__all__ = ["KnowledgeGraph", "GitHubEventHandler"]
