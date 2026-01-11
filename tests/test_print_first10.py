"""サンプルの mqxliff ファイルをパースして最初の10件を表示する。"""
import os

from xliffkit.core.dialects.mqxliff import MQXLIFF
from xliffkit.core.internal import xml_parser
from xliffkit.normalize.flatten import flatten_segment

show_num = 10


def print_first10():
    """サンプルの mqxliff ファイルをパースして最初の10件を表示する。"""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path = os.path.join(repo_root, 'sample1.mqxliff')

    doc = xml_parser.parse_xliff(path, dialect=MQXLIFF())
    tus = doc.tus[6:7]

    out = []
    for tu in tus:
        item = {
            'tu_id': tu.tu_id,
            'order': tu.order,
            'state': tu.state,
            # 'comment': tu.comment,
            'source_text': tu.source.text if tu.source else None,
            'source_inline_tags': [
                {'tag': t.tag, 'tag_id': t.tag_id,
                'xml': t.xml, 'raw': t.raw, 'position': t.position}
                for t in (tu.source.inline_tags or [])
            ],
            # 'target_text': tu.target.text if tu.target else None,
            # 'extra_attrs': tu.extra_attrs,
            # 'context_xml': tu.context_xml,
        }

        # flatten_segment を試す
        segment = tu.source
        try:
            flat_text = flatten_segment(segment)
        except Exception as exc:
            flat_text = str(exc)

        flat_item = {}
        flat_item['flat_text'] = flat_text

        item.update(flat_item)

        out.append(item)

    # pprint(out, width=80, sort_dicts=False)
    # 結果をjson 形式でtmp.json に保存
    import json
    with open('tmp.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f'Saved first {show_num} TUs to tmp.json')

def test_print_first10():
    """サンプルの mqxliff ファイルをパースして最初の10件を表示するテスト。"""
    print_first10()
    assert True
