#!/usr/bin/env python3
"""
extract-vellum.py

Extracts text content from a Vellum (.vellum) ebook project file into Markdown.

A .vellum file is either:
  - A macOS package directory containing content.vellumcontent (older format)
  - A ZIP archive containing content.vellumcontent at its root (newer format)

In both cases the content file is an NSKeyedArchiver binary property list.
This script decodes the object graph and emits one Markdown section per
chapter with full paragraph text.

The output starts with YAML front matter (title, author).  If a book.md file
exists alongside the .vellum file, its front matter is used verbatim; otherwise
front matter is generated from the metadata stored inside the Vellum project.

Prerequisites:
  Python 3.6+ with standard library only (plistlib, zipfile)

Usage:
  python3 scripts/extract-vellum.py "publishing/<title>/<title>.vellum"
  python3 scripts/extract-vellum.py "publishing/<title>/<title>.vellum" output.md

If no output path is given, the file is written to:
  publishing/<title>/review/<book-slug>.md
"""

import io
import plistlib
import re
import sys
import zipfile
from pathlib import Path

CHAPTER_TYPES = {
    'foreword', 'introduction', 'prologue',
    'chapter',
    'epilogue', 'afterword', 'conclusion',
    'part',
}


def deref(objects, ref):
    """Resolve a plistlib.UID reference to its object."""
    if isinstance(ref, plistlib.UID):
        return objects[ref.data]
    return ref


def get_string(objects, ref):
    """Resolve a reference and return it if it is a plain string."""
    val = deref(objects, ref)
    return val if isinstance(val, str) and val != '$null' else ''


def get_chapter_text(objects, chapter):
    """Extract plain text from a chapter node's NSAttributedString."""
    text_ref = chapter.get('text')
    if not text_ref:
        return ''
    text_obj = deref(objects, text_ref)
    if not isinstance(text_obj, dict):
        return ''
    return get_string(objects, text_obj.get('NSString', ''))


def paragraphs_to_markdown(raw_text):
    """Convert newline-delimited paragraphs to double-spaced Markdown."""
    return '\n\n'.join(p.strip() for p in raw_text.split('\n') if p.strip())


def slugify(text):
    return re.sub(r'[^\w]+', '-', text.strip().lower()).strip('-')


def _build_front_matter(title: str, author: str) -> str:
    """Return a minimal YAML front matter block."""
    lines = ['---', f'title: "{title}"']
    if author:
        lines.append(f'author: {author}')
    lines.append('---')
    return '\n'.join(lines)


def _load_plist(vellum_path: Path) -> dict:
    """Read content.vellumcontent from a package directory or ZIP archive."""
    if vellum_path.is_dir():
        content_path = vellum_path / 'content.vellumcontent'
        if not content_path.exists():
            sys.exit(f'Error: content.vellumcontent not found in {vellum_path}')
        with open(content_path, 'rb') as f:
            return plistlib.load(f)
    else:
        if not zipfile.is_zipfile(vellum_path):
            sys.exit(f'Error: {vellum_path} is neither a directory nor a ZIP archive')
        with zipfile.ZipFile(vellum_path) as z:
            if 'content.vellumcontent' not in z.namelist():
                sys.exit(f'Error: content.vellumcontent not found inside {vellum_path}')
            with z.open('content.vellumcontent') as f:
                return plistlib.load(io.BytesIO(f.read()))


def extract(vellum_path: Path) -> str:
    plist = _load_plist(vellum_path)

    objects = plist['$objects']

    def d(ref):
        return deref(objects, ref)

    def s(ref):
        return get_string(objects, ref)

    root_key = 'root' if 'root' in plist['$top'] else 'book'
    root = deref(objects, plist['$top'][root_key])
    container = d(root['rootElementContainer'])
    children = [d(c) for c in d(container['children'])['NS.objects']]

    # Use book.md front matter if present; fall back to Vellum metadata.
    book_md = vellum_path.parent / 'book.md'
    if book_md.exists():
        front_matter = book_md.read_text(encoding='utf-8').strip()
    else:
        book_title = s(root.get('title')) or vellum_path.stem
        first = s(root.get('authorFirstName'))
        last = s(root.get('authorLastName'))
        author = f'{first} {last}'.strip()
        front_matter = _build_front_matter(book_title, author)

    lines = [front_matter]

    for child in children:
        type_name = s(child.get('typeName'))
        if type_name not in CHAPTER_TYPES:
            continue

        title = s(child.get('title')) or type_name.capitalize()
        raw_text = get_chapter_text(objects, child)
        md_text = paragraphs_to_markdown(raw_text)

        lines.append(f'\n## {title}\n')
        if md_text:
            lines.append(md_text)

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: python3 scripts/extract-vellum.py "publishing/<title>/<title>.vellum" [output.md]')

    vellum_path = Path(sys.argv[1])
    if not vellum_path.exists():
        sys.exit(f'Error: {vellum_path} not found')

    content = extract(vellum_path)

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        # Default: publishing/<title>/review/<slug>.md
        # vellum_path.parent is publishing/<title>/
        output_dir = vellum_path.parent / 'review'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f'{slugify(vellum_path.stem)}.md'

    output_path.write_text(content, encoding='utf-8')
    print(f'Extracted to {output_path}')


if __name__ == '__main__':
    main()
