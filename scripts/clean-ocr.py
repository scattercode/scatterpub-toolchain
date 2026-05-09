#!/usr/bin/env python3
"""
clean-ocr.py

Post-processes assembled OCR Markdown (output of ocr-to-markdown.py) to
remove common OCR artefacts. Writes a cleaned copy of the file.

Always applied:
  - Soft hyphens (U+00AD) and other invisible characters removed
  - Non-breaking spaces normalised to regular spaces
  - Unicode ligatures (fi fl ff ffi ffl) expanded to ASCII
  - Unnecessary Markdown backslash escapes removed: pandoc escapes \' \" \--
    in its Markdown output but these are not needed in plain prose Markdown
  - Trailing whitespace stripped from every line
  - Three or more consecutive blank lines collapsed to two
  - Running headers removed: the first short line after each page marker
    (<!-- N -->) that contains an isolated page number (e.g. "62 Tell Me,
    Bella" or "Tell Me. Bella 70") is detected and dropped

Optional:
  --join-hyphens  Join lines that end with a hyphen to the following line,
                  preserving the hyphen. Handles typeset word-breaks such as
                  "news-\\npaper" -> "news-paper". The hyphen is kept rather
                  than removed because it is not always a word-break (e.g.
                  "many-\\ncoloured" is a real compound). Review joined hyphens
                  in the output and remove the hyphen manually where
                  appropriate.

Usage:
  python3 scripts/clean-ocr.py "publishing/<title>/ocr/<slug>.md"
  python3 scripts/clean-ocr.py "publishing/<title>/ocr/<slug>.md" --output out.md
  python3 scripts/clean-ocr.py "publishing/<title>/ocr/<slug>.md" --join-hyphens

If no output path is given, the file is written to:
  publishing/<title>/ocr/<slug>-clean.md

Prerequisites:
  Python 3.6+, standard library only
"""

import argparse
import re
import sys
from pathlib import Path


# Invisible / non-printing characters to remove entirely
REMOVE_CHARS = [
    '­',  # SOFT HYPHEN
    '​',  # ZERO WIDTH SPACE
    '‌',  # ZERO WIDTH NON-JOINER
    '‍',  # ZERO WIDTH JOINER
    '﻿',  # ZERO WIDTH NO-BREAK SPACE / BOM
    '⁠',  # WORD JOINER
]

# Characters to replace with a regular space
SPACE_CHARS = [
    ' ',  # NO-BREAK SPACE
    ' ',  # NARROW NO-BREAK SPACE
    ' ',  # THIN SPACE
]

# Unicode typographic ligatures -> ASCII equivalents
LIGATURES = {
    'ﬀ': 'ff',
    'ﬁ': 'fi',
    'ﬂ': 'fl',
    'ﬃ': 'ffi',
    'ﬄ': 'ffl',
    'ﬅ': 'st',
    'ﬆ': 'st',
}

# Running header detection: the first non-blank line after a <!-- N --> marker
# is a running header if it is short and contains an isolated page number at
# the start or end (with optional leading capital letter for OCR noise like
# "I09" -> 109).
_HEADER_NUM_START = re.compile(r'^\s*[A-Z]?\d{1,3}[\s.,]+\S')
_HEADER_NUM_END   = re.compile(r'\S[\s.,]+[A-Z]?\d{1,3}\s*$')
_HEADER_BARE_NUM  = re.compile(r'^\s*[A-Z]?\d{1,3}\s*$')
MAX_HEADER_LEN    = 70
HEADER_SCAN_LINES = 3


def _is_running_header(line):
    s = line.strip()
    if not s or len(s) > MAX_HEADER_LEN:
        return False
    if _HEADER_BARE_NUM.match(s):
        return True
    if _HEADER_NUM_START.search(s) or _HEADER_NUM_END.search(s):
        return True
    return False


def remove_running_headers(lines):
    result = []
    removed = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        result.append(line)
        if line.strip().startswith('<!-- ') and line.strip().endswith(' -->'):
            i += 1
            # Skip blank lines between the marker and the first content line,
            # then check if that first content line is a running header.
            blanks_seen = []
            while i < len(lines):
                candidate = lines[i]
                if candidate.strip() == '':
                    if len(blanks_seen) < HEADER_SCAN_LINES:
                        blanks_seen.append(candidate)
                        i += 1
                        continue
                    else:
                        # Too many blank lines — give up
                        result.extend(blanks_seen)
                        blanks_seen = []
                        break
                # First non-blank line after the marker
                if _is_running_header(candidate):
                    # Drop the header and the blank lines before it
                    removed += 1
                    i += 1
                else:
                    result.extend(blanks_seen)
                    result.append(candidate)
                    i += 1
                break
            continue
        i += 1
    return result, removed


def join_eol_hyphens(lines):
    """Join lines ending with a word-hyphen to the following line.

    The hyphen is preserved. This handles typeset line-break hyphens but
    cannot distinguish them from real compound-word hyphens — review the
    output and remove hyphens manually where the join produces a solid word
    (e.g. 'news-paper' -> 'newspaper').
    """
    STRUCTURAL = re.compile(r'^\s*(#|<!--|---$|>\s|\*\s|-\s|\d+\.)')
    result = []
    joined = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if (re.search(r'\w-\s*$', line)
                and not STRUCTURAL.match(line)
                and i + 1 < len(lines)):
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines) and not STRUCTURAL.match(lines[j]):
                result.append(line.rstrip() + lines[j].lstrip())
                joined += 1
                i = j + 1
                continue
        result.append(line)
        i += 1
    return result, joined


def unescape_markdown(text):
    """Remove unnecessary backslash escapes added by pandoc.

    pandoc escapes \' \" \-- in Markdown output, but these have no special
    meaning in plain prose Markdown and make the text harder to read.
    """
    # Order matters: \-- before \- to avoid partial matches
    text = text.replace("\\'", "'")
    text = text.replace('\\"', '"')
    text = text.replace('\\--', '--')
    return text


def clean(text, do_join_hyphens):
    stats = {}

    n = sum(text.count(c) for c in REMOVE_CHARS)
    for c in REMOVE_CHARS:
        text = text.replace(c, '')
    stats['invisible_chars_removed'] = n

    n = sum(text.count(c) for c in SPACE_CHARS)
    for c in SPACE_CHARS:
        text = text.replace(c, ' ')
    stats['nbsp_normalised'] = n

    n = sum(text.count(k) for k in LIGATURES)
    for k, v in LIGATURES.items():
        text = text.replace(k, v)
    stats['ligatures_expanded'] = n

    n = text.count("\\'") + text.count('\\"') + text.count('\\--')
    text = unescape_markdown(text)
    stats['markdown_escapes_removed'] = n

    lines = text.splitlines()
    stripped = [l.rstrip() for l in lines]
    stats['trailing_whitespace_lines'] = sum(1 for a, b in zip(lines, stripped) if a != b)
    lines = stripped

    lines, stats['running_headers_removed'] = remove_running_headers(lines)

    if do_join_hyphens:
        lines, stats['hyphens_joined'] = join_eol_hyphens(lines)
    else:
        stats['hyphens_joined'] = 0

    text = '\n'.join(lines)
    before_len = len(text)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    stats['excess_blank_lines_collapsed'] = max(0, before_len - len(text))

    return text, stats


def main():
    parser = argparse.ArgumentParser(
        description='Clean common OCR artefacts from assembled OCR Markdown.'
    )
    parser.add_argument('input', help='Path to the OCR Markdown file to clean')
    parser.add_argument('--output', metavar='PATH', help='Output file path')
    parser.add_argument(
        '--join-hyphens',
        action='store_true',
        help='Join lines ending with a hyphen to the following line (hyphen preserved)',
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f'Error: {input_path} not found')

    text = input_path.read_text(encoding='utf-8', errors='replace')
    cleaned, stats = clean(text, args.join_hyphens)

    if args.output:
        output_path = Path(args.output)
    else:
        # Strip any trailing -raw (and optional engine prefix like -tesseract-raw)
        # so the clean file sits alongside the raw file with a parallel name:
        #   tell-me-bella-raw.md          -> tell-me-bella-clean.md
        #   tell-me-bella-tesseract-raw.md -> tell-me-bella-tesseract-clean.md
        stem = re.sub(r'-raw$', '', input_path.stem)
        output_path = input_path.with_name(stem + '-clean' + input_path.suffix)

    output_path.write_text(cleaned, encoding='utf-8')

    total = sum(stats.values())
    print(f'Cleaned {input_path.name} -> {output_path.name}')
    print(f'  {stats["invisible_chars_removed"]:4}  invisible characters removed')
    print(f'  {stats["nbsp_normalised"]:4}  non-breaking spaces normalised')
    print(f'  {stats["ligatures_expanded"]:4}  ligatures expanded')
    print(f'  {stats["markdown_escapes_removed"]:4}  unnecessary Markdown backslash escapes removed')
    print(f'  {stats["trailing_whitespace_lines"]:4}  lines with trailing whitespace stripped')
    print(f'  {stats["running_headers_removed"]:4}  running headers removed')
    if args.join_hyphens:
        print(f'  {stats["hyphens_joined"]:4}  end-of-line hyphens joined')
    print(f'  ----')
    print(f'  {total:4}  total changes')


if __name__ == '__main__':
    main()
