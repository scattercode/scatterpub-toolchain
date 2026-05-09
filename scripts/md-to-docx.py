#!/usr/bin/env python3
"""
md-to-docx.py

Converts a Markdown file to a Word document (.docx) using pandoc.

Markdown headings are mapped to Word heading styles:
  YAML front matter title  → Word Title style   (Vellum book title/metadata)
  YAML front matter author → Word Author style
  ## Chapter              → # Chapter → Heading 1 (Vellum chapter break)

The pipeline outputs YAML front matter (title, author) followed by ##
headings for each story/chapter.  Pre-processing promotes every ## heading
to # so they all become Heading 1 in Word and Vellum splits on each one.
pandoc maps the front matter fields to Word Title/Author styles automatically.

Usage:
  python3 scripts/md-to-docx.py "publishing/<title>/review/<slug>-clean.md"
  python3 scripts/md-to-docx.py "publishing/<title>/review/<slug>-clean.md" --output out.docx

If no output path is given, the .docx is written alongside the input file:
  publishing/<title>/review/<slug>-clean.docx

Prerequisites:
  pandoc  (brew install pandoc)
  Python 3.6+, standard library only
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Matches an italic-only line such as *Vahan Totovents* used as a by-line.
_BYLINE_RE = re.compile(r'^\*[^*\n]+\*\s*$')


def preprocess(text: str) -> str:
    """Strip book title/by-line and promote ## headings to # (Word Heading 1).

    The extract-vellum.py output starts with:
        # Book Title
        *Author Name*
        ## Chapter One
        ...

    The book-title block is stripped so Vellum's chapter list starts cleanly
    with the first story.  Every ## heading is promoted to # so Vellum splits
    on each one as a chapter break.
    """
    lines = text.splitlines(keepends=True)
    out = []
    i = 0

    # Skip leading blank lines
    while i < len(lines) and lines[i].strip() == '':
        i += 1

    # Drop the book-level # Title line
    if i < len(lines) and lines[i].startswith('# '):
        i += 1
        # Skip blank lines between title and by-line
        while i < len(lines) and lines[i].strip() == '':
            i += 1
        # Drop an italic-only by-line (*Author Name*)
        if i < len(lines) and _BYLINE_RE.match(lines[i]):
            i += 1

    for line in lines[i:]:
        out.append('# ' + line[3:] if line.startswith('## ') else line)

    return ''.join(out)


def main():
    parser = argparse.ArgumentParser(
        description='Convert a Markdown file to Word (.docx) via pandoc.'
    )
    parser.add_argument('input', help='Path to the Markdown file')
    parser.add_argument('--output', metavar='PATH', help='Output .docx path')
    args = parser.parse_args()

    if not shutil.which('pandoc'):
        sys.exit('Error: pandoc not found\n  brew install pandoc')

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f'Error: {input_path} not found')

    output_path = Path(args.output) if args.output else input_path.with_suffix('.docx')

    processed = preprocess(input_path.read_text(encoding='utf-8'))

    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.md', encoding='utf-8', delete=False
    ) as tmp:
        tmp.write(processed)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ['pandoc', tmp_path, '-o', str(output_path), '--wrap=none'],
            capture_output=True,
            text=True,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if result.returncode != 0:
        sys.exit(f'Error: pandoc failed:\n{result.stderr}')

    print(f'{input_path.name} → {output_path.name}')


if __name__ == '__main__':
    main()
