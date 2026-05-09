# Scatterpub Toolchain

Scripts and Claude Code skills for digitising physical books from scans and preparing manuscripts for publication in [Vellum](https://vellum.pub).

## New here? Start with the example project

**[scatterpub-toolchain-example](https://github.com/scattercode/scatterpub-toolchain-example)** is a ready-to-run project containing real sample scans and a step-by-step tutorial. Fork it, follow the tutorial, and you will have a complete working pipeline in around 30 minutes — without needing to set up a project from scratch.

---

## What's included

| Component | Purpose |
|---|---|
| `scripts/extract-vellum.py` | Extract a Vellum project to Markdown |
| `scripts/ocr-to-markdown.py` | OCR clean page scans into raw Markdown |
| `scripts/clean-ocr.py` | Clean OCR artefacts, running headers, invisible characters |
| `scripts/clean-vellum.py` | Remove invisible artefacts from a `.vellum` package |
| `scripts/md-to-docx.py` | Convert Markdown to Word for Vellum import |
| `.claude/skills/copyeditor` | Claude Code skill: copy-edit to Hart's Rules, British English |
| `.claude/skills/pdf` | Claude Code skill: general-purpose PDF processing |
| `.claude/skills/skill-creator` | Claude Code skill: create and improve skills |

---

## Using as a submodule

The toolchain is designed to be embedded in a book project repository as a git submodule.

### 1. Add the submodule

```bash
git submodule add https://github.com/scattercode/scatterpub-toolchain.git toolchain
git submodule update --init
```

### 2. Install Python dependencies

```bash
brew install poppler tesseract pandoc  # system tools
cd toolchain && poetry install         # Python deps
```

### 3. Symlink the skills

So that Claude Code can discover the skills via the standard `.claude/skills/` path:

```bash
mkdir -p .claude/skills
ln -s ../../toolchain/.claude/skills/copyeditor .claude/skills/copyeditor
ln -s ../../toolchain/.claude/skills/pdf .claude/skills/pdf
ln -s ../../toolchain/.claude/skills/skill-creator .claude/skills/skill-creator
```

Commit the symlinks — they are tracked by git and wired up automatically for every contributor.

### 4. Create book.md

In each book folder, create a `book.md` with YAML front matter:

```markdown
---
title: "Book Title"
author: Author Name
---
```

The scripts read this automatically and inject it as front matter in every generated Markdown file.

---

## Standalone use

To use the toolchain directly (not as a submodule):

```bash
git clone https://github.com/scattercode/scatterpub-toolchain.git
cd scatterpub-toolchain
brew install poppler tesseract pandoc
poetry install
```

---

## Publishing workflow

### From a Vellum source file

```bash
# Extract to Markdown
python3 toolchain/scripts/extract-vellum.py "publishing/<title>/<title>.vellum"

# Copy-edit
# Load /copyeditor in Claude Code and provide the extracted Markdown path

# Generate Word document for re-import
python3 toolchain/scripts/md-to-docx.py "publishing/<title>/review/<slug>.md"
```

### From physical book scans

```bash
# Step 1: OCR the clean scans
poetry run --directory toolchain python toolchain/scripts/ocr-to-markdown.py \
  "publishing/<title>/ocr/scans/clean"

# Step 2: Clean the raw output
python3 toolchain/scripts/clean-ocr.py "publishing/<title>/ocr/<slug>-raw.md" --join-hyphens

# Step 3: Copy-edit
# Load /copyeditor in Claude Code and provide the cleaned Markdown path
```

---

## Prerequisites

| Tool | Install | Required for |
|---|---|---|
| Python 3.6+ | system / pyenv | all scripts |
| Poetry | `pip install poetry` | Python dep management |
| pandoc | `brew install pandoc` | `.docx` conversion |
| poppler | `brew install poppler` | PDF text extraction |
| tesseract | `brew install tesseract` | `--ocr tesseract` |
| marker-pdf | `poetry install` | `--ocr marker` (default) |

The `.vellum` package format is macOS-specific; `extract-vellum.py` and `clean-vellum.py` require macOS.
