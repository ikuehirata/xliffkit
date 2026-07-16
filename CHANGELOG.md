# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.6] - 2026-07-16

### Fixed
- Fixed incorrect tag insertion order during flattening.
- Changed the `TU` translation state enumeration to align with XLIFF v1.2, and updated `mqxliff` accordingly.
- Added negative lookbehinds to `_default_trigger()` so that periods after honorifics/abbreviations such as `Dr.` `Ms.` `Mr.` `Mrs.` `Prof.` `Rev.` `Sr.` `Jr.` `St.` `vs.` are excluded from sentence splitting.

## [0.1.5] - 2026-02-12

### Fixed
- Separated `TU.state` decision making per dialect.
- Converter to `tmx`: Fixed several attribution imports from `mqxliff`.

### Added
- Added a member `TU.is_locked`.
- Added `x` as a tag in TU (compatible with TMX export).
- Supported segment splitting with `x`.
- When splitting by structural tags, structural tags are attached to the previous chunk. WIP
- Added a default setting so that locked TUs are not split during TU splitting.
- Hotfix for context id extraction.

## [0.1.4] - 2026-02-01

### Fixed
- Ignored `<mrk>` while parsing (highlight source/target where commented)
- Moved `docs` to root
- Converted package-internal imports to relative imports

### Added
- Added `split_policy` to `split_document()` which enables/disables split per segment.
- When splitting segments, `<ept>` tags will be moved to the previous segment.
- Added a function to convert `xliff` to `tmx`, utilizing `tmxkit`. (example 04)

## [0.1.3] - 2026-01-27

### Fixed
- Fixed tag regex.
- Optimized merge process.
- Fixed tag sorting by position.
- Fixed where half-width space was not added when merging non-`NO_WORD_SEPARATION_LANGS` languages.

### Added
- Added whilespace normalization to `load()`.
- Enabled `trigger` in `split_tu()` for segment splitting.

## [0.1.2] - 2026-01-15

### Fixed
- Fixed an error in xlm rendering: Fixed an issue where tag insertion positions were shifted during rendering due to changes in text length caused by escape characters.

### Added
- Exposed context_id renumbering as a callable external utility: `xliffkit.normalize.context_id`.

## [0.1.1] - 2026-01-12

### Fixed
- Fixed inconsistencies in `__init__.py` files to ensure correct module exports.

## [0.1.0] - 2025-12-28

### Added
- Initial release of xliffkit.
- Core parsing and serialization for XLIFF/mqXLIFF.
- Segment-level data handling with separation of text and inline tags.
- Normalization and segmentation utilities.

[0.1.6]: https://github.com/ikuehirata/xliffkit/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/ikuehirata/xliffkit/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/ikuehirata/xliffkit/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/ikuehirata/xliffkit/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/ikuehirata/xliffkit/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/ikuehirata/xliffkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ikuehirata/xliffkit/releases/tag/v0.1.0
