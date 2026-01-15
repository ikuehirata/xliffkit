# Changelog

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
