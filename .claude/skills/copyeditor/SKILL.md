---
name: copyeditor
description: Copy-edit book manuscripts for the Armenian Institute. Use when the user asks you to copy-edit, proofread, or review a book, chapter, or extracted Markdown file. Produces a self-contained HTML annotation report with colour-coded issue cards (TYPO, PUNCT, STYLE, CONSISTENCY, QUERY), applying Hart's Rules and British English as the style baseline. Trigger on any request to review writing quality, flag errors, or produce a copy-edit review — including when the user simply loads the skill and provides a file path.
license: Proprietary. LICENSE.txt has complete terms
---

# Copy Editor Skill — Armenian Institute

Copy-edit book manuscripts and produce an HTML annotation report. Style baseline: **Hart's Rules** (*New Hart's Rules: The Oxford Guide for Writers and Editors*, 2005), British English.

## Workflow

The Markdown source may come from either of two routes. Both produce a file that begins with YAML front matter (`title`, `author`) followed by `##` chapter headings — extract the title and author from that front matter for the HTML report header.

**Route A — Vellum (work-in-progress book):**
```
python3 scripts/extract-vellum.py "publishing/<title>/<title>.vellum"
# → publishing/<title>/review/<book-slug>.md
```

**Route B — OCR scans (physical book scans):**
```
# Step 1: extract
poetry run python scripts/ocr-to-markdown.py "publishing/<title>/ocr/scans/clean"
# → publishing/<title>/ocr/<book-slug>-raw.md

# Step 2: clean
python3 scripts/clean-ocr.py "publishing/<title>/ocr/<book-slug>-raw.md" --join-hyphens
# → publishing/<title>/ocr/<book-slug>-clean.md
```

Once the Markdown file exists:

1. Read it in full before annotating anything.
2. Work chapter by chapter. For each chapter, identify all issues.
3. Write the completed HTML review to `publishing/<title>/review/<book-slug>-review.html` using the Write tool.

---

## Hart's Rules — Key Guidelines for British English Book Publishing

### 1. Quotation marks

- **Primary quotations use single marks**: 'like this'
- **Quotations within quotations use double marks**: 'He said "I don't know" and left.'
- **Logical punctuation** (Oxford/Hart's rule): closing punctuation goes *inside* the quotation mark only if it belongs to the quoted matter.
  - Correct: She said, 'I am ready.' *(the full stop belongs to the quoted sentence)*
  - Correct: She described herself as 'ready'. *(the full stop belongs to the surrounding sentence)*
  - Correct: Did she say 'I am ready'? *(question mark belongs to the surrounding sentence)*
- Commas and full stops that follow a closing quote in narrative prose go **outside** the mark unless the punctuation is part of what is being quoted.
- Flag any use of double quotes as primary quotation marks — this is American style.
- Flag any inconsistency in quote style (mixing single and double as primaries).

### 2. Ellipsis

- Hart's uses **three unspaced dots** followed by a normal word space: `word... word`
- Or a single Unicode ellipsis character (…) is acceptable: `word… word`
- Do **not** use spaced dots (`. . .`) — this is an older typographic convention not recommended in the 2005 edition.
- When an ellipsis follows a complete sentence, a full stop precedes it: `word.... Next sentence` or `word…. Next sentence`
- Flag any inconsistency in ellipsis style throughout the book.

### 3. Dashes

- **Parenthetical asides**: use a **spaced en dash** — like this — not an em dash (em dash is American style).
  - Correct: `word – aside – word`
  - Incorrect: `word—aside—word` (em dash, no spaces)
- **Ranges**: use an **unspaced en dash**: `1939–45`, `pp. 10–15`, `Monday–Friday`
- **Compound adjectives where one element is already hyphenated** or is a proper noun: use en dash: `pre–First World War`
- Flag any use of an em dash (—) — suggest replacing with spaced en dash ( – ).
- Flag any hyphen used where an en dash is needed for ranges.

### 4. Hyphens and compound words

- **Compound adjectives before a noun**: hyphenate — `well-known author`, `eighteenth-century novel`, `long-term plan`
- **Compound adjectives after a verb**: open — `the author is well known`, `a plan for the long term`
- **Numbers twenty-one to ninety-nine**: hyphenated
- **Prefixes**: generally closed — `prewar`, `postwar`, `midcentury` — unless a doubled vowel or consonant would cause confusion (`pre-eminent`, `co-operate` are acceptable variants)
- Flag inconsistent hyphenation of the same compound across the text.

### 5. Capitalisation

- **Sentence case for headings** — only the first word and proper nouns capitalised
- **Seasons**: lowercase — `spring`, `autumn`, `winter`, `summer`
- **Compass directions**: lowercase unless part of a place name — `go south`, but `the Middle East`
- **Job titles**: lowercase except when used as a direct form of address or immediately before a name — `the president spoke`, but `President Lincoln spoke`
- **Historical periods and events**: capitalised when used as proper names — `the First World War`, `the Armenian Genocide`, `the Renaissance`
- Flag inconsistent capitalisation of the same word or phrase.

### 6. Numbers and dates

- **Spell out** one to ninety-nine in running prose; use numerals for 100 and above
- **Spell out** round numbers in prose: `two hundred`, `five thousand`
- **Exceptions** (use numerals): measurements, percentages, dates, page references, scores
- **Dates**: `15 March 2024` (day–month–year, no ordinals) or `March 2024`; not `March 15th, 2024`
- **Centuries**: lowercase and spelled out — `the nineteenth century` (noun), `a nineteenth-century novel` (compound adjective)

### 7. Spelling (British English, Oxford style)

Oxford house style (used in Hart's Rules) employs **-ize** endings, not -ise, for the main verb class — this surprises many writers but is correct for this style:

| Use | Avoid |
|---|---|
| realize, organize, recognize | realise, organise, recognise |
| But: advertise, comprise, disguise, exercise, supervise, surprise | These **always** take -ise — they are not from the Greek -izo suffix |

Other British spellings to enforce:

| Use | Avoid |
|---|---|
| colour, honour, favour, neighbour | color, honor, favor, neighbor |
| centre, theatre, metre | center, theater, meter |
| travelling, fulfilling, labelling | traveling, fulfilling, labeling |
| catalogue, dialogue, analogue | catalog, dialog, analog |
| programme (but: computer program) | program (non-computing) |
| judgement (general use) | judgment (legal contexts only) |
| ageing, likeable | aging, likable |

### 8. Oxford comma

Use the **Oxford comma** (serial comma) before the final item in a list of three or more: `red, white, and blue` — not `red, white and blue`.

### 9. Punctuation spacing

- **One space** after a full stop, not two.
- No space before a colon, semicolon, full stop, comma, or closing bracket.
- Brackets close without a space: `(like this)`, not `( like this )`.

---

## Issue Categories

| Code | Label | Colour | Use for |
|---|---|---|---|
| `typo` | TYPO | red | Spelling errors, wrong words, missing or doubled words |
| `punctuation` | PUNCT | orange | Quote marks, dashes, ellipsis, comma, semicolon errors |
| `style` | STYLE | yellow | British English, capitalisation, numbers, hyphenation |
| `consistency` | CONSISTENCY | blue | Same word/name formatted differently across the book |
| `query` | QUERY | purple | Ambiguous phrasing, possible translator's idiom — flag for author/editor decision, do not correct |

---

## Notes on Translated Texts

When reviewing a translation (e.g. Mischa Kudian's translations of Vahan Totovents):

- Some unusual or archaic phrasings may be **deliberate stylistic choices** of the translator. Do not correct these — raise them as `QUERY` with a note such as *"Possible translator's idiom — confirm with editor."*
- Place names and personal names in transliterated Armenian may use unconventional spellings that are intentional. Flag only if there is clear inconsistency *within* the text.
- Register shifts (very formal to colloquial) within the same chapter may reflect the original — flag as `QUERY`, not `STYLE`.

---

## HTML Output Format

Write a single self-contained HTML file. The template is in `assets/review-template.html` — use it as the structure and CSS exactly. Replace `BOOK_TITLE` and `AUTHOR` in the header, fill in the summary counts, and add one `<section class="chapter">` per chapter.

**Rules for the context snippet:**
- Include 6–10 words either side of the issue for searchability.
- Use `<mark>` around only the specific word(s) in question.
- Use `…` (the ellipsis character) to show truncation.
- Keep the snippet to one sentence where possible.

**Rules for the suggestion:**
- For TYPO: give the corrected spelling.
- For PUNCT: state the rule and give the corrected form.
- For STYLE: state the Hart's rule and give the corrected form.
- For CONSISTENCY: quote the other occurrence(s) and their location (chapter name).
- For QUERY: explain the ambiguity and ask a specific question for the editor.
