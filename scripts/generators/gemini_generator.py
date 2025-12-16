#!/usr/bin/env python3
"""
Generate Gemini skill.yaml from Markdown documentation.

Usage:
    python gemini_generator.py --input docs/keboola/ --output gemini/keboola-core/skill.yaml
"""

import argparse
import yaml
from pathlib import Path
from datetime import datetime


class GeminiSkillGenerator:
    def parse_docs(self, docs_path: Path) -> dict:
        """Parse all Markdown files."""
        print(f"📖 Reading documentation from: {docs_path}")

        skill = {
            'name': 'keboola-core',
            'version': '1.0.0',
            'description': 'Keboola platform knowledge for Gemini',
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'source_path': str(docs_path),
                'generator': 'gemini_generator.py v1.0',
                'poc_notice': 'This is a POC. Not production-ready.'
            },
            'knowledge_base': []
        }

        # Read all .md files
        md_files = sorted(docs_path.glob('*.md'))

        if not md_files:
            raise ValueError(f"No .md files found in {docs_path}")

        for md_file in md_files:
            print(f"  📄 Processing: {md_file.name}")
            content = md_file.read_text(encoding='utf-8')

            skill['knowledge_base'].append({
                'source': md_file.name,
                'content': content,
                'format': 'markdown'
            })

        print(f"✓ Processed {len(md_files)} documentation files")
        return skill

    def generate(self, docs_path: Path, output_path: Path):
        """Main generation process."""
        print("=" * 70)
        print("Gemini skill.yaml Generator")
        print("=" * 70)
        print()

        # Parse documentation
        skill = self.parse_docs(docs_path)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(skill, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        print(f"✓ Generated: {output_path}")
        print(f"  Sections: {len(skill['knowledge_base'])}")
        print()
        print("=" * 70)
        print("Generation complete!")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Generate Gemini skill.yaml from Markdown documentation'
    )

    parser.add_argument('--input', required=True, help='Input directory containing .md files')
    parser.add_argument('--output', required=True, help='Output path for skill.yaml file')

    args = parser.parse_args()

    # Validate inputs
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Input directory not found: {input_path}")
        return 1

    output_path = Path(args.output)

    # Generate
    try:
        generator = GeminiSkillGenerator()
        generator.generate(input_path, output_path)
        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
