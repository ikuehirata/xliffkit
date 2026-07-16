# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**xliffkit** is a Python library for safely handling XLIFF files produced by memoQ (`mqXLIFF` dialect) in translation workflows. It is a pure library — no CLI, no application logic. The scope is intentionally limited to the mqXLIFF dialect.

## Commands

```bash
# Install (editable)
pip install -e .

# Lint
ruff check xliffkit
ruff format xliffkit
ruff check --fix xliffkit

# Tests — the project uses example scripts, not a formal test suite
python examples/01_fix_ph_to_bpt_ept/run.py
python examples/02_split/run.py
python examples/03_merge/run.py
python examples/04_convert_to_tmx/run.py

# Run with pytest
pytest examples/
```

Ruff config: line length 100, Python 3.13 target, single quotes for normal strings, double for docstrings.

## Architecture

### Processing Flow

```
XLIFF file
  → core.load(path)
      → detect.detect_dialect()
      → xml_parser.parse_xliff()
      → normalize_all_tags()       # ph → bpt/ept fixup
      → flatten_all_segments()     # tags extracted, plaintext kept
      → normalize_whitespace()
  → XliffDocument (internal model)
  → core.save(doc, path)          # dialect-aware serialization
```

**Always use `core.load()` / `core.save()`** — they handle dialect detection and normalization. Calling serializers directly bypasses these checks.

### Core Data Model

```
XliffDocument
  ├─ tus: list[TU]
  ├─ dialect: Dialect
  └─ raw_root: etree.Element      # original XML preserved for roundtrip

TU
  ├─ source / target: Segment
  ├─ state: State
  ├─ locked: bool
  └─ [memoQ-specific attrs]

Segment
  ├─ text: str                    # plaintext, tags removed
  └─ tags: list[InlineTag]

InlineTag
  ├─ tag: str                     # ph, bpt, ept, g, it, x
  ├─ tag_id: str
  └─ position: int                # approximate
```

### Key Modules

| Module | Purpose |
|---|---|
| `xliffkit.core.load` | Entry point: `load(path)` |
| `xliffkit.core.save` | Entry point: `save(doc, path)` |
| `xliffkit.core.models` | `XliffDocument`, `TU`, `Segment`, `InlineTag` |
| `xliffkit.dialects` | Dialect abstraction + auto-detect |
| `xliffkit.normalize.tags` | Tag normalization (`ph` → `bpt`/`ept`) |
| `xliffkit.normalize.flatten` | Extract tags from XML, keep plaintext |
| `xliffkit.segment.split` | Rule-based segment splitting |
| `xliffkit.segment.merge` | Strategy-driven segment merging |
| `xliffkit.io.yaml_export/import` | TU ↔ YAML |
| `xliffkit.io.tmx_export` | TU → TMX |

### Dialect Pattern

Dialects are subclasses of `xliffkit.dialects.base.Dialect`. The primary dialect is `mqxliff.MQXLIFF`, with flags such as:
- `PH_CONTAINS_ESCAPED_XML` — memoQ `<ph>` often contains escaped XML
- `INLINE_TAG_POSITION_IS_APPROXIMATE` — tag positions may be imprecise
- `roundtrip_safe = False` — mqXLIFF is not roundtrip-safe

New dialects go in `xliffkit/dialects/`.

## Key Constraints

- **Stateless**: All processing is deterministic; no shared mutable state across calls.
- **Splitting and merging are separate operations** — split first, merge later; never combine in a single pass.
- **Known issue**: When merging segments with differing tag counts, target tags are flattened.
- The only production dependency is `lxml`.
