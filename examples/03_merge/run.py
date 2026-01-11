"""segment merge flow."""

from xliffkit.core.load import load
from xliffkit.core.save import save
from xliffkit.core.serializer.raw_sync import sync_raw_with_tus
from xliffkit.segment.merge import merge_document


def run():
    """Read sample file and output tag-corrected version to output.mqxliff."""
    input_file = 'examples/03_merge/input.mqxliff'
    # タグ修正はここで自動で行われる
    doc = load(input_file)

    merged_doc = merge_document(doc)

    # 最低限の検査: 分割後の TU 数は元の TU 数以下であるべき
    assert len(merged_doc.tus) <= len(doc.tus), \
        'Merged document should have at most as many TUs as the original.'

    # mqxliff用DOM再構築
    sync_raw_with_tus(merged_doc)
    # 書き出し
    out_path = 'examples/03_merge/output.mqxliff'
    save(merged_doc, out_path)


if __name__ == '__main__':
    run()
