"""convert to tmx

This operation reads `tmxkit`, which is distributed at
https://github.com/ikuehirata/tmxkit
"""

from pathlib import Path

from xliffkit.core.load import load
from xliffkit.io.tmx_export import convert_xliffdoc_to_tmx


def run():
    """Read a sample file and convert it to output.tmx."""
    input_file = 'examples/04_convert_to_tmx/input.mqxliff'
    # タグ修正はここで自動で行われる
    doc = load(input_file)

    out_path = 'examples/04_convert_to_tmx/output.tmx'
    convert_xliffdoc_to_tmx(doc, out_path=Path(out_path))


if __name__ == '__main__':
    run()
