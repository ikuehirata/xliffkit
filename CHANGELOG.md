# Changelog

## [0.1.5]

### Fixed
- Separated `TU.state` decision making per dialect.
- Converter to `tmx`: Fixed several attribution imports from `mqxliff`.

### Added
- Added a member `TU.locked`.
- Added `x` as a tag in TU (compatible with TMX export).
- Supported segment splitting with `x`.
- When splitting by structural tags, structural tags are attached to the previous chunk. WIP
- Added a default setting so that locked TUs are not split during TU splitting.
- Hotfix for context id extraction.

## [0.1.4]

### Fixed
- Ignored `<mrk>` while parsing (highlight source/target where commented)
- Moved `docs` to root
- Converted package-internal imports to relative imports

### Added
- Added `split_policy` to `split_document()` which enables/disables split per segment.
- When splitting segments, `<ept>` tags will be moved to the previous segment.
- Added a function to convert `xliff` to `tmx`, utilizing `tmxkit`. (example 04)

## [0.1.3]

### Fixed
- Fixed tag regex.
- Optimized merge process.
- Fixed tag sorting by position.
- Fixed where half-width space was not added when merging non-`NO_WORD_SEPARATION_LANGS` languages.

### Added
- Added whilespace normalization to `load()`.
- Enabled `trigger` in `split_tu()` for segment splitting.

## [0.1.2]

### Fixed
- Fixed an error in xlm rendering: Fixed an issue where tag insertion positions were shifted during rendering due to changes in text length caused by escape characters.

### Added
- Exposed context_id renumbering as a callable external utility: `xliffkit.normalize.context_id`.


## [0.1.1]

### Fixed
- Fixed inconsistencies in `__init__.py` files to ensure correct module exports.


## [0.1.0]

### Added
- Initial release of xliffkit.
- Core parsing and serialization for XLIFF/mqXLIFF.
- Segment-level data handling with separation of text and inline tags.
- Normalization and segmentation utilities.
