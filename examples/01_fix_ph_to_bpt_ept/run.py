"""test tag fixing flow."""

from xliffkit.core.load import load
from xliffkit.core.save import save
from xliffkit.core.serializer.raw_sync import sync_raw_with_tus


def run():
    """Read sample file and output tag-corrected version to output.mqxliff."""
    input_file = 'examples/01_fix_ph_to_bpt_ept/input.mqxliff'
    # タグ修正はここで自動で行われる
    doc = load(input_file)
    # どのタグにも ph が残っていないことを確認する
    for tu in doc.tus:
        for seg in [tu.source] + ([tu.target] if tu.target else []):
            for tag in seg.inline_tags:
                assert tag.tag != 'ph', f'Found ph tag in TU {tu.tu_id}'

    # mqxliff用DOM再構築
    sync_raw_with_tus(doc)

    # 書き出し
    out_path = 'examples/01_fix_ph_to_bpt_ept/output.mqxliff'
    save(doc, out_path)


if __name__ == '__main__':
    run()
