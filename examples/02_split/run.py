"""segment split flow."""

from xliffkit.core.load import load
from xliffkit.core.save import save
from xliffkit.core.serializer.raw_sync import sync_raw_with_tus
from xliffkit.segment.split import split_document


def run():
    """Read sample file and output split version to output.mqxliff."""
    input_file = 'examples/02_split/input.mqxliff'
    # タグ修正はここで自動で行われる
    doc = load(input_file)

    split_doc = split_document(doc)

    # 最低限の検査: 分割後の TU 数は元の TU 数以上であるべき
    assert len(split_doc.tus) >= len(doc.tus), \
        'Split document should have at least as many TUs as the original.'

    # mqxliff用DOM再構築
    sync_raw_with_tus(split_doc)

    # 書き出し
    out_path = 'examples/02_split/output.mqxliff'
    save(split_doc, out_path)


if __name__ == '__main__':
    run()

