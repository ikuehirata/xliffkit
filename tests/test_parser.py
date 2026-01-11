"""サンプルの mqxliff ファイルをパースして期待されるフィールドが取得できることを検証する。"""
import json

from xliffkit.core.load import load


def test_parse_sample1(path: str):
    """sample1.mqxliff をパースして期待されるフィールドを検証する。

    - 最初の TU の `id`, `order`, `source.text`, `target.text` を検証する。
    """
    print(path)
    doc = load(path)

    # 基本検証
    assert len(doc.tus) > 0

    first = doc.tus[0]
    assert first.tu_id == '1'
    assert first.order == 0

    # 各tu.source の inline_tags を tu_id ごとに dict 化して tmp.json に保存
    data = {tu.tu_id: [tag.__dict__ for tag in tu.source.inline_tags] for tu in doc.tus}
    with open('tmp.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    test_parse_sample1(path='samples/tag_test.txt_jpn.mqxliff')
