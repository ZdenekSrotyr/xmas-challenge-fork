#!/usr/bin/env python3
"""
Generate Claude Code SKILL.md from Markdown documentation.

Usage:
    python claude_generator.py --input docs/keboola/ --output claude/keboola-core/SKILL.md
"""

import argparse
import json
from pathlib import Path
from datetime import datetime


class ClaudeSkillGenerator:
    def __init__(self):
        self.sections = []

    def parse_docs(self, docs_path: Path) -> dict:
        """Parse all Markdown files and extract content."""
        print(f"📖 Reading documentation from: {docs_path}")

        content = {
            'title': 'Keboola Platform Knowledge',
            'sections': [],
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'source_path': str(docs_path),
                'generator': 'claude_generator.py v1.0'
            }
        }

        # Read all .md files in sorted order
        md_files = sorted(docs_path.glob('*.md'))

        if not md_files:
            raise ValueError(f"No .md files found in {docs_path}")

        for md_file in md_files:
            print(f"  📄 Processing: {md_file.name}")
            section_content = md_file.read_text(encoding='utf-8')

            content['sections'].append({
                'filename': md_file.name,
                'content': section_content
            })

        print(f"✓ Processed {len(md_files)} documentation files")
        return content

    def generate_skill(self, content: dict) -> str:
        """Generate SKILL.md from parsed content."""
        print("🔨 Generating Claude SKILL.md...")

        # Build SKILL.md
        skill = []

        # Header
        skill.append("# Keboola Platform Knowledge for Claude Code")
        skill.append("")
        skill.append("> **⚠️ POC NOTICE**: This skill was automatically generated from documentation.")
        skill.append("> Source: `docs/keboola/`")
        skill.append("> Generator: `scripts/generators/claude_generator.py`")
        skill.append(f"> Generated: {content['metadata']['generated_at']}")
        skill.append("")
        skill.append("---")
        skill.append("")

        # Introduction
        skill.append("## Overview")
        skill.append("")
        skill.append("This skill provides comprehensive knowledge about the Keboola platform,")
        skill.append("including API usage, best practices, and common pitfalls.")
        skill.append("")
        skill.append("**When to activate this skill:**")
        skill.append("- User asks about Keboola Storage API")
        skill.append("- User needs help with Keboola Jobs API")
        skill.append("- User asks about regional stacks or Stack URLs")
        skill.append("- User encounters Keboola-related errors")
        skill.append("")
        skill.append("---")
        skill.append("")

        # Add all sections
        for section in content['sections']:
            skill.append(f"<!-- Source: {section['filename']} -->")
            skill.append("")
            skill.append(section['content'])
            skill.append("")
            skill.append("---")
            skill.append("")

        # Footer
        skill.append("## Metadata")
        skill.append("")
        skill.append("```json")
        skill.append(json.dumps(content['metadata'], indent=2))
        skill.append("```")
        skill.append("")
        skill.append("---")
        skill.append("")
        skill.append("**End of Skill**")

        return '\n'.join(skill)

    def generate(self, docs_path: Path, output_path: Path):
        """Main generation process."""
        print("=" * 70)
        print("Claude SKILL.md Generator")
        print("=" * 70)
        print()

        # Parse documentation
        content = self.parse_docs(docs_path)

        # Generate skill
        skill_content = self.generate_skill(content)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(skill_content, encoding='utf-8')

        print(f"✓ Generated: {output_path}")
        print(f"  Size: {len(skill_content)} characters")
        print(f"  Sections: {len(content['sections'])}")

        # Write metadata
        metadata_path = output_path.parent / '.skill-metadata.json'
        metadata_path.write_text(
            json.dumps(content['metadata'], indent=2),
            encoding='utf-8'
        )
        print(f"✓ Metadata: {metadata_path}")
        print()
        print("=" * 70)
        print("Generation complete!")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Generate Claude SKILL.md from Markdown documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python claude_generator.py --input docs/keboola/ --output claude/keboola-core/SKILL.md
        """
    )

    parser.add_argument(
        '--input',
        required=True,
        help='Input directory containing .md files'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output path for SKILL.md file'
    )

    args = parser.parse_args()

    # Validate inputs
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Input directory not found: {input_path}")
        return 1

    if not input_path.is_dir():
        print(f"❌ Error: Input path is not a directory: {input_path}")
        return 1

    output_path = Path(args.output)

    # Generate
    try:
        generator = ClaudeSkillGenerator()
        generator.generate(input_path, output_path)
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
