"""xliff ファイルから <trans-unit> を抽出し、実務向けに簡略化した YAML を出力する。

このモジュールは内部パーサー（`xliffkit.core.parser`）を用いて変換を行う。
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from ..core.internal import xml_parser as core_parser
from ..dialects.mqxliff import MQXLIFF
from .stream import iter_tus


def export_yaml(file_path: str, dialect: MQXLIFF) -> str:
    """yaml ファイルとして出力する。

    ファイル名は入力の basename を .yaml にしたものを `txt/mqxliff_yaml/` に出力する。
    """
    input_path = Path(file_path)

    # 拡張子を確認
    if input_path.suffix.lower() not in {'.xliff', '.xlf', '.mqxliff'}:
        raise ValueError('Input file path is not xliff family')

    # ファイル存在確認
    if not input_path.is_file():
        raise FileNotFoundError(f'File not found: {file_path}')

    doc = core_parser.parse_xliff(file_path, dialect)

    data: list[dict] = []
    for d in iter_tus(doc, dialect):
        data.append(d)

    os.makedirs('txt/mqxliff_yaml', exist_ok=True)
    yaml_name = input_path.with_suffix('.yaml').name
    out_path = os.path.join('txt/mqxliff_yaml', yaml_name)

    with open(out_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            width=4096,
            indent=2,
        )

    print(f'exported: {out_path}')
    return out_path
