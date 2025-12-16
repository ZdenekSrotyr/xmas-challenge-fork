#!/usr/bin/env python3
"""
Event handler for GitHub events (Issues, PRs).

This automatically tracks issues and PRs in the knowledge graph,
linking them to affected documents and concepts.
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Set, Dict, Optional

from knowledge_graph import KnowledgeGraph


class GitHubEventHandler:
    """Handle GitHub events and update knowledge graph."""

    def __init__(self, graph: Optional[KnowledgeGraph] = None):
        self.graph = graph or KnowledgeGraph()

    def extract_concepts_from_text(self, text: str) -> Set[str]:
        """
        Extract Keboola concepts mentioned in issue/PR text.

        This is a simple keyword-based extraction. In production,
        could use NLP or LLM-based extraction.
        """
        concepts = set()

        # Keywords to look for
        keywords = {
            "Storage API": "Concept:StorageAPI",
            "Jobs API": "Concept:JobsAPI",
            "Stack URL": "Concept:StackURL",
            "Project ID": "Concept:ProjectID",
            "Token": "Concept:Authentication",
            "Input Mapping": "Concept:InputMapping",
            "Output Mapping": "Concept:OutputMapping",
            "Custom Python": "Concept:CustomPython",
            "Streamlit": "Concept:Streamlit",
            "Flow": "Concept:Flows"
        }

        text_lower = text.lower()
        for keyword, concept_id in keywords.items():
            if keyword.lower() in text_lower:
                concepts.add(concept_id)

        return concepts

    def extract_files_from_text(self, text: str) -> Set[str]:
        """Extract file paths mentioned in text."""
        files = set()

        # Look for markdown file references
        # Pattern: docs/keboola/something.md or skills/claude/SKILL.md
        pattern = r'(?:docs|skills)/[\w/\-]+\.(?:md|py|yaml)'
        matches = re.findall(pattern, text)
        files.update(matches)

        return files

    def handle_issue_created(self, issue_number: int, issue_data: Dict):
        """
        Handle issue creation event.

        Args:
            issue_number: GitHub issue number
            issue_data: Issue data from GitHub API
        """
        print(f"📝 Handling Issue #{issue_number}: {issue_data['title']}")

        # Create issue node
        issue_id = self.graph.add_node(
            node_type="Issue",
            node_id=str(issue_number),
            number=issue_number,
            title=issue_data["title"],
            body=issue_data.get("body", ""),
            status="open",
            labels=[label["name"] for label in issue_data.get("labels", [])],
            url=issue_data["html_url"],
            created_at=issue_data["created_at"]
        )

        print(f"  ✓ Created node: {issue_id}")

        # Extract and link concepts
        full_text = f"{issue_data['title']} {issue_data.get('body', '')}"
        concepts = self.extract_concepts_from_text(full_text)

        for concept_id in concepts:
            # Create concept node if it doesn't exist
            concept_name = concept_id.split(":")[1]
            self.graph.add_node(
                node_type="Concept",
                node_id=concept_name,
                name=concept_name
            )

            # Link issue to concept
            self.graph.add_edge(issue_id, concept_id, "ABOUT")
            print(f"  ✓ Linked to concept: {concept_name}")

        # Extract and link files
        files = self.extract_files_from_text(full_text)

        for file_path in files:
            # Create document node if it doesn't exist
            self.graph.add_node(
                node_type="Document",
                node_id=file_path,
                path=file_path
            )

            doc_id = f"Document:{file_path}"
            self.graph.add_edge(issue_id, doc_id, "ABOUT")
            print(f"  ✓ Linked to document: {file_path}")

        print(f"  ✅ Issue #{issue_number} tracked in graph")

    def handle_issue_closed(self, issue_number: int):
        """Handle issue closure event."""
        print(f"🔒 Closing Issue #{issue_number}")

        issue_id = f"Issue:{issue_number}"
        self.graph.update_node(issue_id, status="closed")

        print(f"  ✅ Issue #{issue_number} marked as closed")

    def handle_pr_created(self, pr_number: int, pr_data: Dict):
        """
        Handle pull request creation event.

        Args:
            pr_number: GitHub PR number
            pr_data: PR data from GitHub API
        """
        print(f"🔀 Handling PR #{pr_number}: {pr_data['title']}")

        # Create PR node
        pr_id = self.graph.add_node(
            node_type="PullRequest",
            node_id=str(pr_number),
            number=pr_number,
            title=pr_data["title"],
            body=pr_data.get("body", ""),
            status="open",
            url=pr_data["html_url"],
            created_at=pr_data["created_at"],
            additions=pr_data.get("additions", 0),
            deletions=pr_data.get("deletions", 0)
        )

        print(f"  ✓ Created node: {pr_id}")

        # Extract "Fixes #N" from PR body/title
        full_text = f"{pr_data['title']} {pr_data.get('body', '')}"
        fixes_pattern = r'(?:fixes|closes|resolves)\s+#(\d+)'
        matches = re.findall(fixes_pattern, full_text.lower())

        for issue_num in matches:
            issue_id = f"Issue:{issue_num}"
            self.graph.add_edge(issue_id, pr_id, "FIXED_BY")
            print(f"  ✓ Links to Issue #{issue_num}")

        # Link to modified files (if available)
        if "changed_files" in pr_data:
            for file_info in pr_data["changed_files"]:
                file_path = file_info["filename"]

                # Create document node
                self.graph.add_node(
                    node_type="Document",
                    node_id=file_path,
                    path=file_path
                )

                doc_id = f"Document:{file_path}"
                self.graph.add_edge(pr_id, doc_id, "MODIFIES")
                print(f"  ✓ Modifies: {file_path}")

        print(f"  ✅ PR #{pr_number} tracked in graph")

    def handle_pr_merged(self, pr_number: int):
        """Handle PR merge event."""
        print(f"✅ Merging PR #{pr_number}")

        pr_id = f"PullRequest:{pr_number}"
        self.graph.update_node(pr_id, status="merged")

        # Find and close linked issues
        related = self.graph.find_related(pr_id, relationship="FIXED_BY")

        for node in related:
            if node["type"] == "Issue":
                issue_id = node["id"]
                self.graph.update_node(issue_id, status="closed")
                issue_num = node["properties"]["number"]
                print(f"  ✓ Closed Issue #{issue_num}")

        # Find modified documents
        modified_docs = self.graph.find_related(pr_id, relationship="MODIFIES")

        if modified_docs:
            print(f"  📄 Modified {len(modified_docs)} documents")

            # Find skills that depend on these documents
            affected_skills = set()
            for doc in modified_docs:
                dependents = self.graph.find_dependents(doc["id"])
                for dep_id in dependents:
                    if dep_id.startswith("Skill:"):
                        affected_skills.add(dep_id)

            if affected_skills:
                print(f"  🔄 Affected skills (should regenerate):")
                for skill_id in affected_skills:
                    print(f"    • {skill_id}")

        print(f"  ✅ PR #{pr_number} merged")


def main():
    """CLI for handling GitHub events."""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Event Handler")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Issue commands
    issue_parser = subparsers.add_parser("issue", help="Handle issue events")
    issue_parser.add_argument("action", choices=["created", "closed"])
    issue_parser.add_argument("number", type=int, help="Issue number")
    issue_parser.add_argument("--data", help="JSON data file")

    # PR commands
    pr_parser = subparsers.add_parser("pr", help="Handle PR events")
    pr_parser.add_argument("action", choices=["created", "merged", "closed"])
    pr_parser.add_argument("number", type=int, help="PR number")
    pr_parser.add_argument("--data", help="JSON data file")

    args = parser.parse_args()

    handler = GitHubEventHandler()

    try:
        if args.command == "issue":
            if args.action == "created":
                if not args.data:
                    print("❌ Error: --data required for issue creation")
                    return 1

                with open(args.data) as f:
                    issue_data = json.load(f)

                handler.handle_issue_created(args.number, issue_data)

            elif args.action == "closed":
                handler.handle_issue_closed(args.number)

        elif args.command == "pr":
            if args.action == "created":
                if not args.data:
                    print("❌ Error: --data required for PR creation")
                    return 1

                with open(args.data) as f:
                    pr_data = json.load(f)

                handler.handle_pr_created(args.number, pr_data)

            elif args.action == "merged":
                handler.handle_pr_merged(args.number)

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
