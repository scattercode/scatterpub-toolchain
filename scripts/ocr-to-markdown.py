#!/usr/bin/env python3
"""
ocr-to-markdown.py

Extracts text from all files in a clean scans folder and assembles them
into a single Markdown file in page-number order.

Supported file types:
  .pdf  — text extracted with pdftotext if a text layer is present;
          falls back to the chosen OCR engine for image-only pages
  .docx — converted with pandoc

Files are sorted by the first integer in their filename, so 7.pdf, 8.docx,
9.pdf, 10-11.pdf, 12-13.pdf, etc. come out in the correct sequence.

Usage:
  python3 scripts/ocr-to-markdown.py <clean_dir> [options]

  python3 scripts/ocr-to-markdown.py "publishing/<title>/ocr/scans/clean"
  python3 scripts/ocr-to-markdown.py "publishing/<title>/ocr/scans/clean" --ocr marker
  python3 scripts/ocr-to-markdown.py "publishing/<title>/ocr/scans/clean" --output out.md

Options:
  --ocr {marker,tesseract}   OCR engine for image-only pages (default: marker)
  --output PATH              Output file path (default: publishing/<title>/ocr/<slug>[-<engine>].md)

When using the default output path, the engine name is appended for non-default
engines, so both versions can coexist for comparison:
  tell-me-bella.md            (marker, default)
  tell-me-bella-tesseract.md  (tesseract)

Prerequisites:
  pdftotext  (brew install poppler)        — always required
  pandoc     (brew install pandoc)         — required for .docx files
  ocrmypdf   (brew install ocrmypdf)       — required for --ocr tesseract
  marker     (pip install marker-pdf)      — required for --ocr marker
  Python 3.6+, standard library only
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SUPPORTED = {'.pdf', '.docx'}
OCR_ENGINES = ('tesseract', 'marker')


def check_tools(files, ocr_engine):
    needed = {'pdftotext'}
    for f in files:
        if f.suffix.lower() == '.pdf':
            needed.add('ocrmypdf' if ocr_engine == 'tesseract' else 'marker_single')
        elif f.suffix.lower() == '.docx':
            needed.add('pandoc')

    install = {
        'pdftotext':   'brew install poppler',
        'ocrmypdf':    'brew install ocrmypdf',
        'marker_single': 'pip install marker-pdf',
        'pandoc':      'brew install pandoc',
    }
    missing = [t for t in needed if not shutil.which(t)]
    if missing:
        lines = '\n'.join(f'  {t:15} {install.get(t, "")}' for t in missing)
        sys.exit(f'Error: missing required tools:\n{lines}')


def sort_key(path):
    """Sort by the first integer in the stem — handles 7, 9, 10-11, 12-13…"""
    m = re.search(r'\d+', path.stem)
    return (int(m.group()) if m else 0, path.stem)


def extract_pdf(pdf_path, ocr_engine):
    """Extract text from a PDF.

    Tries pdftotext first (instant for PDFs with an embedded text layer).
    Falls back to the chosen OCR engine for image-only pages.
    """
    result = subprocess.run(
        ['pdftotext', '-layout', str(pdf_path), '-'],
        capture_output=True, text=True,
    )
    text = result.stdout.strip()
    if text:
        return text

    if ocr_engine == 'tesseract':
        return _ocr_tesseract(pdf_path)
    else:
        return _ocr_marker(pdf_path)


def _ocr_tesseract(pdf_path):
    """OCR via ocrmypdf/Tesseract, returning text from the --sidecar file."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as sf:
        sidecar = Path(sf.name)
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as of:
        out_pdf = Path(of.name)

    try:
        result = subprocess.run(
            [
                'ocrmypdf',
                '--sidecar', str(sidecar),
                '--language', 'eng',
                '--optimize', '0',  # skip PDF optimisation — we only want the text
                '--quiet',
                str(pdf_path),
                str(out_pdf),
            ],
            capture_output=True, text=True,
        )
        if result.returncode not in (0, 6):
            print(
                f'    warning: ocrmypdf returned {result.returncode}: '
                f'{result.stderr.strip()[:120]}',
                file=sys.stderr,
            )
        return sidecar.read_text(encoding='utf-8', errors='replace') if sidecar.exists() else ''
    finally:
        sidecar.unlink(missing_ok=True)
        out_pdf.unlink(missing_ok=True)


def _ocr_marker(pdf_path):
    """OCR via marker (ML-based), returning Markdown text."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        result = subprocess.run(
            [
                'marker_single',
                '--output_dir', tmp_dir,
                '--output_format', 'markdown',
                str(pdf_path),
            ],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(
                f'    warning: marker returned {result.returncode}: '
                f'{result.stderr.strip()[:120]}',
                file=sys.stderr,
            )
        md_files = list(Path(tmp_dir).rglob('*.md'))
        if not md_files:
            return ''
        return md_files[0].read_text(encoding='utf-8', errors='replace')


def extract_docx(docx_path):
    """Convert a .docx to Markdown via pandoc and return the text."""
    result = subprocess.run(
        ['pandoc', str(docx_path), '-t', 'markdown', '--wrap=none'],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(
            f'    warning: pandoc failed: {result.stderr.strip()[:120]}',
            file=sys.stderr,
        )
        return ''
    return result.stdout


def slugify(text):
    return re.sub(r'[^\w]+', '-', text.strip().lower()).strip('-')


def main():
    parser = argparse.ArgumentParser(
        description='Extract text from clean scans and assemble into Markdown.'
    )
    parser.add_argument('clean_dir', help='Path to the clean scans folder')
    parser.add_argument(
        '--ocr',
        choices=OCR_ENGINES,
        default='marker',
        help='OCR engine for image-only pages (default: marker)',
    )
    parser.add_argument('--output', metavar='PATH', help='Output file path')
    args = parser.parse_args()

    clean_dir = Path(args.clean_dir).resolve()
    if not clean_dir.is_dir():
        sys.exit(f'Error: {clean_dir} is not a directory')

    files = sorted(
        [f for f in clean_dir.iterdir() if f.suffix.lower() in SUPPORTED],
        key=sort_key,
    )
    if not files:
        sys.exit(f'Error: no .pdf or .docx files found in {clean_dir}')

    check_tools(files, args.ocr)

    engine_label = '' if args.ocr == 'tesseract' else f' [{args.ocr}]'
    print(f'Processing {len(files)} files from {clean_dir.name}/{engine_label}')

    sections = []
    for f in files:
        print(f'  {f.name} ...', end=' ', flush=True)
        if f.suffix.lower() == '.pdf':
            text = extract_pdf(f, args.ocr)
        else:
            text = extract_docx(f)
        text = text.strip()
        if text:
            sections.append(f'<!-- {f.stem} -->\n\n{text}')
            print('done')
        else:
            print('empty — skipped')

    if not sections:
        sys.exit('Error: no text was extracted from any file')

    # publishing/<title>/ocr/scans/clean → publishing/<title>
    book_dir = clean_dir.parent.parent.parent
    book_md = book_dir / 'book.md'
    frontmatter = book_md.read_text(encoding='utf-8').strip() if book_md.exists() else ''

    assembled = '\n\n---\n\n'.join(sections)
    output = (frontmatter + '\n\n' + assembled) if frontmatter else assembled

    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = book_dir / 'ocr'
        output_dir.mkdir(parents=True, exist_ok=True)
        slug = slugify(book_dir.name)
        engine = f'-{args.ocr}' if args.ocr != 'marker' else ''
        output_path = output_dir / f'{slug}{engine}-raw.md'

    output_path.write_text(output, encoding='utf-8')
    print(f'\nAssembled {len(sections)} pages → {output_path}')


if __name__ == '__main__':
    main()
