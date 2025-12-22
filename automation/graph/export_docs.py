#!/usr/bin/env python3
"""
Export documentation files with git history to JSON format.

This script extracts markdown documentation files along with their complete
git history, including commits, authors, dates, and change statistics.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class GitHistoryExtractor:
    """Extract git history for documentation files."""

    def __init__(self, repo_root: Path):
        """
        Initialize the git history extractor.

        Args:
            repo_root: Root directory of the git repository
        """
        self.repo_root = repo_root

    def get_file_history(self, file_path: Path) -> List[Dict]:
        """
        Get complete git history for a file using git log --follow.

        Args:
            file_path: Path to the file (relative to repo root)

        Returns:
            List of commit dictionaries with metadata
        """
        try:
            # Use git log with --follow to track file renames
            # Format: hash|author|email|date|subject
            cmd = [
                'git',
                'log',
                '--follow',
                '--pretty=format:%H|%an|%ae|%aI|%s',
                '--',
                str(file_path)
            ]

            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|', 4)
                if len(parts) != 5:
                    continue

                commit_hash, author, email, date, message = parts

                # Get stats for this commit
                stats = self._get_commit_stats(commit_hash, file_path)

                commits.append({
                    'hash': commit_hash,
                    'short_hash': commit_hash[:7],
                    'author': author,
                    'email': email,
                    'date': date,
                    'message': message,
                    'stats': stats
                })

            return commits

        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to get history for {file_path}: {e}", file=sys.stderr)
            return []

    def _get_commit_stats(self, commit_hash: str, file_path: Path) -> Dict[str, int]:
        """
        Get file change statistics for a specific commit.

        Args:
            commit_hash: Git commit hash
            file_path: Path to the file

        Returns:
            Dictionary with insertions and deletions counts
        """
        try:
            cmd = [
                'git',
                'show',
                '--numstat',
                '--pretty=format:',
                commit_hash,
                '--',
                str(file_path)
            ]

            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse numstat output: insertions\tdeletions\tfilename
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('\t')
                if len(parts) >= 2:
                    insertions = parts[0]
                    deletions = parts[1]

                    return {
                        'insertions': int(insertions) if insertions.isdigit() else 0,
                        'deletions': int(deletions) if deletions.isdigit() else 0
                    }

        except subprocess.CalledProcessError:
            pass

        return {'insertions': 0, 'deletions': 0}

    def is_git_repo(self) -> bool:
        """Check if the directory is a git repository."""
        try:
            subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_root,
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False


class DocsExporter:
    """Export documentation files with git history to JSON."""

    def __init__(self, docs_dir: Path, repo_root: Path):
        """
        Initialize the documentation exporter.

        Args:
            docs_dir: Directory containing documentation files
            repo_root: Root directory of the git repository
        """
        self.docs_dir = docs_dir
        self.repo_root = repo_root
        self.git_extractor = GitHistoryExtractor(repo_root)

    def find_markdown_files(self) -> List[Path]:
        """
        Find all markdown files in the docs directory.

        Returns:
            List of markdown file paths (relative to repo root)
        """
        markdown_files = []
        for root, _, files in os.walk(self.docs_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = Path(root) / file
                    # Get path relative to repo root
                    rel_path = file_path.relative_to(self.repo_root)
                    markdown_files.append(rel_path)
        return sorted(markdown_files)

    def read_file_content(self, file_path: Path) -> str:
        """
        Read content of a markdown file.

        Args:
            file_path: Path to the file (relative to repo root)

        Returns:
            File content as string
        """
        full_path = self.repo_root / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Failed to read {file_path}: {e}", file=sys.stderr)
            return ""

    def export_docs(self) -> Dict:
        """
        Export all documentation files with their git history.

        Returns:
            Dictionary containing docs array and metadata
        """
        if not self.git_extractor.is_git_repo():
            print("Error: Not a git repository", file=sys.stderr)
            sys.exit(1)

        markdown_files = self.find_markdown_files()

        if not markdown_files:
            print(f"Warning: No markdown files found in {self.docs_dir}", file=sys.stderr)

        docs = []
        total_commits = 0

        for file_path in markdown_files:
            print(f"Processing {file_path}...", file=sys.stderr)

            content = self.read_file_content(file_path)
            history = self.git_extractor.get_file_history(file_path)

            # Get relative path from docs directory for cleaner display
            try:
                display_path = file_path.relative_to(self.docs_dir.relative_to(self.repo_root))
            except ValueError:
                display_path = file_path

            doc = {
                'path': str(file_path),
                'display_path': str(display_path),
                'name': file_path.name,
                'content': content,
                'history': history,
                'commit_count': len(history),
                'last_modified': history[0]['date'] if history else None,
                'last_author': history[0]['author'] if history else None
            }

            docs.append(doc)
            total_commits += len(history)

        # Calculate statistics - deduplicate commits by hash
        seen_hashes = set()
        unique_commits = []
        for doc in docs:
            for commit in doc['history']:
                if commit['hash'] not in seen_hashes:
                    seen_hashes.add(commit['hash'])
                    unique_commits.append(commit)

        # Sort by date descending
        unique_commits.sort(key=lambda c: c['date'], reverse=True)

        # Get recent changes (last 10 unique commits across all files)
        recent_changes = unique_commits[:10]

        # Get unique authors
        authors = set(c['author'] for c in unique_commits)

        result = {
            'docs': docs,
            'metadata': {
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'doc_count': len(docs),
                'total_commits': total_commits,
                'author_count': len(authors),
                'docs_directory': str(self.docs_dir.relative_to(self.repo_root))
            },
            'recent_changes': recent_changes,
            'statistics': {
                'total_docs': len(docs),
                'total_commits': total_commits,
                'unique_authors': len(authors),
                'authors': sorted(list(authors))
            }
        }

        return result


def main():
    """Main entry point for the export script."""
    parser = argparse.ArgumentParser(
        description='Export documentation files with git history to JSON'
    )
    parser.add_argument(
        '--docs',
        required=True,
        help='Path to docs directory (relative or absolute)'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output JSON file path'
    )

    args = parser.parse_args()

    # Resolve paths
    docs_dir = Path(args.docs).resolve()
    output_file = Path(args.output).resolve()

    # Find git repository root
    current_dir = docs_dir
    repo_root = None

    while current_dir != current_dir.parent:
        if (current_dir / '.git').exists():
            repo_root = current_dir
            break
        current_dir = current_dir.parent

    if not repo_root:
        print("Error: Could not find git repository root", file=sys.stderr)
        sys.exit(1)

    # Validate docs directory
    if not docs_dir.exists():
        print(f"Error: Docs directory does not exist: {docs_dir}", file=sys.stderr)
        sys.exit(1)

    if not docs_dir.is_dir():
        print(f"Error: Docs path is not a directory: {docs_dir}", file=sys.stderr)
        sys.exit(1)

    # Create output directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Export documentation
    print(f"Exporting docs from: {docs_dir}", file=sys.stderr)
    print(f"Repository root: {repo_root}", file=sys.stderr)
    print(f"Output file: {output_file}", file=sys.stderr)

    exporter = DocsExporter(docs_dir, repo_root)
    result = exporter.export_docs()

    # Write JSON output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nExport complete:", file=sys.stderr)
    print(f"  - {result['metadata']['doc_count']} documents", file=sys.stderr)
    print(f"  - {result['metadata']['total_commits']} total commits", file=sys.stderr)
    print(f"  - {result['metadata']['author_count']} unique authors", file=sys.stderr)
    print(f"  - Output: {output_file}", file=sys.stderr)


if __name__ == '__main__':
    main()
