"""manifest 一致性：cards.json 与 gallery/cards/ 目录一一对应，无孤儿。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent   # holo-lab/
GALLERY = ROOT / "gallery"


def load_manifest():
    return json.loads((GALLERY / "cards.json").read_text(encoding="utf-8"))


def test_manifest_nonempty():
    assert len(load_manifest()["cards"]) > 0


def test_every_manifest_card_has_dir():
    m = load_manifest()
    for c in m["cards"]:
        d = GALLERY / "cards" / c["id"]
        assert d.is_dir(), f"清单卡 {c['id']} 缺少目录"


def test_every_dir_is_in_manifest():
    m = load_manifest()
    ids = {c["id"] for c in m["cards"]}
    for d in (GALLERY / "cards").iterdir():
        if d.is_dir():
            assert d.name in ids, f"孤儿目录：{d.name} 不在 cards.json"


def test_manifest_ids_unique():
    m = load_manifest()
    ids = [c["id"] for c in m["cards"]]
    assert len(ids) == len(set(ids)), "cards.json 存在重复 id"


def test_manifest_fields():
    m = load_manifest()
    for c in m["cards"]:
        for k in ("id", "title", "edition", "url", "thumb", "style_tags"):
            assert k in c, f"卡 {c.get('id')} 缺少字段 {k}"
