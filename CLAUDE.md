# CLAUDE.md

## Project at a glance

This is the **Ebook Toolchain** — scripts and Claude Code skills for digitising physical books from scans and preparing manuscripts for publication in Vellum.

The toolchain is designed to be used as a git submodule inside a book project repository. See the README for setup instructions.

## Language

All content, comments, and documentation should use **British English** (e.g. 'colour' not 'color', 'organise' not 'organize', 'travelling' not 'traveling'). Use the Oxford comma in lists.

## Repository structure

```
scripts/
  extract-vellum.py     Extracts text from a .vellum ebook project to Markdown
  ocr-to-markdown.py    OCRs clean page scans and assembles into raw Markdown
  clean-ocr.py          Cleans raw OCR output (artefacts, headers, hyphens)
  clean-vellum.py       Removes invisible artefacts from a .vellum package
  md-to-docx.py         Converts Markdown to Word (.docx) for Vellum import

.claude/skills/
  copyeditor/           Copy-editor skill (Hart's Rules, British English)
  pdf/                  PDF processing skill
  skill-creator/        Skill creation and improvement skill

pyproject.toml          Python dependency definition (Poetry)
poetry.lock             Pinned dependency versions
```

## Book metadata

Each book project should contain a `book.md` file at the root of the book folder with YAML front matter declaring the title and author:

```markdown
---
title: "Book Title"
author: Author Name
---
```

The scripts read this file automatically and inject the front matter at the top of every generated Markdown file. If `book.md` is absent, `extract-vellum.py` falls back to metadata stored inside the Vellum project.

## Python environment

Dependencies are managed with Poetry. Run once after cloning (or after initialising the submodule):

```bash
brew install poppler tesseract pandoc  # system tools (not pip-installable)
poetry install                         # creates .venv/ and installs Python deps
```

Run scripts via `poetry run`:

```bash
poetry run python scripts/ocr-to-markdown.py "<path-to-clean-scans>"
```

## Scripts

### `scripts/extract-vellum.py`

Decodes the NSKeyedArchiver binary plist inside a `.vellum` macOS package and emits Markdown with YAML front matter followed by one `##` section per chapter.

```bash
python3 scripts/extract-vellum.py "publishing/<title>/<title>.vellum"
# → publishing/<title>/review/<slug>.md
```

- Reads `book.md` from the same folder as the `.vellum` file; falls back to Vellum project metadata if absent.
- Python 3.6+, standard library only; macOS required.

### `scripts/ocr-to-markdown.py`

Extracts text from all files in a clean scans folder and assembles them into a single Markdown file in page-number order. Supports `.pdf` (text-layer via pdftotext, image-only via OCR) and `.docx` (via pandoc).

```bash
poetry run python scripts/ocr-to-markdown.py "publishing/<title>/ocr/scans/clean"
# → publishing/<title>/ocr/<slug>-raw.md  (marker, default)

poetry run python scripts/ocr-to-markdown.py "publishing/<title>/ocr/scans/clean" --ocr tesseract
# → publishing/<title>/ocr/<slug>-tesseract-raw.md
```

- Reads `book.md` from the book folder and prepends its front matter to the output.
- `--ocr {marker,tesseract}` — OCR engine for image-only pages (default: `marker`)
- `--output PATH` — explicit output path

### `scripts/clean-ocr.py`

Post-processes raw OCR Markdown to remove common artefacts. YAML front matter is preserved unchanged.

```bash
python3 scripts/clean-ocr.py "publishing/<title>/ocr/<slug>-raw.md"
# → publishing/<title>/ocr/<slug>-clean.md

python3 scripts/clean-ocr.py "publishing/<title>/ocr/<slug>-raw.md" --join-hyphens --reflow
```

Always removes: soft hyphens and other invisible characters, bold markers (`**`), unnecessary Markdown backslash escapes, running headers (including common OCR misreads such as `IO` for page 10), trailing whitespace, multiple consecutive spaces, excessive blank lines.

- `--join-hyphens` — join lines ending with a hyphen to the following line (hyphen preserved)
- `--reflow` — join soft line-breaks within paragraphs into single long lines; typeset paragraph indents (2+ leading spaces) are used to detect and preserve paragraph boundaries

### `scripts/clean-vellum.py`

Removes invisible text artefacts (soft hyphens, zero-width spaces, Unicode ligatures, etc.) directly from the binary plist inside a `.vellum` package. Writes a cleaned copy; the original is not modified.

```bash
python3 scripts/clean-vellum.py "publishing/<title>/<title>.vellum"
# → publishing/<title>/<title>-clean.vellum
```

- Python 3.6+, standard library only; macOS required.

### `scripts/md-to-docx.py`

Converts a Markdown file to Word (`.docx`) for import into Vellum. YAML front matter `title` and `author` fields map to Word Title/Author styles; `##` chapter headings are promoted to Word Heading 1 so Vellum splits on each one as a chapter break.

```bash
python3 scripts/md-to-docx.py "publishing/<title>/review/<slug>.md"
# → publishing/<title>/review/<slug>.docx
```

- Requires `pandoc` (`brew install pandoc`).

## Skills

### `/copyeditor`

Located at `.claude/skills/copyeditor/`. Produces an HTML copy-edit review of an extracted Markdown file.

- Style baseline: Hart's Rules (*New Hart's Rules: The Oxford Guide for Writers and Editors*, 2005), British English.
- Output: a self-contained HTML file, open in any browser.
- Issue categories: TYPO, PUNCT, STYLE, CONSISTENCY, QUERY.
- Special handling for translated texts: unusual phrasings are raised as QUERY rather than corrected.

### `/pdf`

Located at `.claude/skills/pdf/`. General-purpose PDF processing: extracting text and tables, merging, splitting, rotating, creating, watermarking, encrypting, OCR, and filling forms.

### `/skill-creator`

Located at `.claude/skills/skill-creator/`. Creates new skills, improves existing ones, runs evaluations, and benchmarks performance.

## Using this toolchain in a project

The intended use is as a git submodule:

```bash
git submodule add https://github.com/scattercode/ebook-toolchain.git toolchain
git submodule update --init
```

Then symlink the skills into the project's `.claude/skills/` so Claude Code can discover them:

```bash
mkdir -p .claude/skills
ln -s ../../toolchain/.claude/skills/copyeditor .claude/skills/copyeditor
ln -s ../../toolchain/.claude/skills/pdf .claude/skills/pdf
ln -s ../../toolchain/.claude/skills/skill-creator .claude/skills/skill-creator
```

Run scripts from the project root:

```bash
python3 toolchain/scripts/extract-vellum.py "publishing/<title>/<title>.vellum"
toolchain/.venv/bin/python toolchain/scripts/ocr-to-markdown.py "..."
```
