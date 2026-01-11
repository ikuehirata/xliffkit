"""Project-wide constants.

Place for small, reusable constants such as language code groups.
"""

# Languages that do not require inter-word spacing (e.g. Japanese, Korean, Chinese)
# Used to decide whether to insert spaces when joining flattened segments.
NO_WORD_SEPARATION_LANGS = (
	'ja', 'jp', 'ja-JP',  # Japanese
	'ko', 'ko-KR',         # Korean
	'zh', 'zh-CN', 'zh-TW', 'zh-Hans', 'zh-Hant',  # Chinese variants
)
