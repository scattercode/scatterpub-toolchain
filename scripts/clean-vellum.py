#!/usr/bin/env python3
"""
clean-vellum.py

Removes invisible text artefacts from a .vellum ebook project file by
modifying the text strings stored in its NSKeyedArchiver binary plist
(content.vellumcontent) directly.

Artefacts removed:
  - Soft hyphens (U+00AD)         — invisible, corrupt text comparisons
  - Zero-width spaces (U+200B)    — invisible
  - Zero-width non-joiners (U+200C)
  - Zero-width joiners (U+200D)
  - Word joiners (U+2060)
  - BOM / zero-width no-break space (U+FEFF)

Artefacts normalised:
  - No-break spaces (U+00A0)      → regular space
  - Narrow no-break spaces (U+202F) → regular space
  - Thin spaces (U+2009)          → regular space
  - Unicode ligatures (ﬁ ﬂ ﬀ ﬃ ﬄ) → ASCII equivalents

A new .vellum package is written alongside the original; the original is
not modified.

Usage:
  python3 scripts/clean-vellum.py "publishing/<title>/<title>.vellum"
  python3 scripts/clean-vellum.py "publishing/<title>/<title>.vellum" --output path/to/output.vellum

If no output path is given, the cleaned package is written to:
  <original-stem>-clean.vellum  (alongside the original)

Prerequisites:
  Python 3.6+, standard library only; macOS required (NSKeyedArchiver format)
"""

import argparse
import plistlib
import shutil
import sys
from pathlib import Path


REMOVE = [
    '­',  # SOFT HYPHEN
    '​',  # ZERO WIDTH SPACE
    '‌',  # ZERO WIDTH NON-JOINER
    '‍',  # ZERO WIDTH JOINER
    '⁠',  # WORD JOINER
    '﻿',  # BOM / ZERO WIDTH NO-BREAK SPACE
]

REPLACE = {
    ' ': ' ',  # NO-BREAK SPACE
    ' ': ' ',  # NARROW NO-BREAK SPACE
    ' ': ' ',  # THIN SPACE
}

LIGATURES = {
    'ﬀ': 'ff',
    'ﬁ': 'fi',
    'ﬂ': 'fl',
    'ﬃ': 'ffi',
    'ﬄ': 'ffl',
    'ﬅ': 'st',
    'ﬆ': 'st',
}


def clean_string(s):
    for ch in REMOVE:
        s = s.replace(ch, '')
    for ch, rep in REPLACE.items():
        s = s.replace(ch, rep)
    for ch, rep in LIGATURES.items():
        s = s.replace(ch, rep)
    return s


def walk_and_clean(obj):
    """Recursively walk a plist object graph, cleaning all strings in-place.

    Returns (modified_obj, change_count).
    """
    if isinstance(obj, str):
        cleaned = clean_string(obj)
        return cleaned, (0 if cleaned == obj else 1)

    if isinstance(obj, list):
        total = 0
        for i, item in enumerate(obj):
            obj[i], n = walk_and_clean(item)
            total += n
        return obj, total

    if isinstance(obj, dict):
        total = 0
        for key in obj:
            obj[key], n = walk_and_clean(obj[key])
            total += n
        return obj, total

    # plistlib.UID, int, float, bool, bytes, datetime — leave untouched
    return obj, 0


def main():
    parser = argparse.ArgumentParser(
        description='Remove invisible text artefacts from a .vellum package.'
    )
    parser.add_argument('vellum_path', help='Path to the .vellum package')
    parser.add_argument('--output', metavar='PATH', help='Output .vellum path')
    args = parser.parse_args()

    src = Path(args.vellum_path)
    if not src.exists():
        sys.exit(f'Error: {src} not found')
    if not src.is_dir():
        sys.exit(f'Error: {src} is not a directory — .vellum files are macOS packages')

    content_path = src / 'content.vellumcontent'
    if not content_path.exists():
        sys.exit(f'Error: content.vellumcontent not found inside {src}')

    if args.output:
        dst = Path(args.output)
    else:
        dst = src.with_name(src.stem + '-clean' + src.suffix)

    if dst.exists():
        shutil.rmtree(dst)

    # Copy the entire package so all non-content files are preserved
    shutil.copytree(src, dst)

    dst_content = dst / 'content.vellumcontent'
    with open(dst_content, 'rb') as f:
        plist = plistlib.load(f)

    plist, changes = walk_and_clean(plist)

    with open(dst_content, 'wb') as f:
        plistlib.dump(plist, f, fmt=plistlib.FMT_BINARY)

    print(f'Cleaned {src.name} → {dst.name}')
    print(f'  {changes}  string{"s" if changes != 1 else ""} modified')


if __name__ == '__main__':
    main()
