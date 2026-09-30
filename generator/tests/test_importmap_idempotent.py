"""importmap 幂等性：rewrite_importmap 对已改写的 index.html 再跑 → 无 diff（防回归）。"""
import copy
from pathlib import Path

import publish_card

GALLERY = Path(__file__).resolve().parent.parent.parent / "gallery"


def test_rewrite_importmap_idempotent():
    """对 gallery 所有卡详情页 index.html 重跑 rewrite_importmap，内容必须不变。"""
    changed = []
    for d in (GALLERY / "cards").iterdir():
        f = d / "index.html"
        if not f.exists():
            continue
        before = f.read_text(encoding="utf-8")
        publish_card.rewrite_importmap(f)
        after = f.read_text(encoding="utf-8")
        if before != after:
            changed.append(d.name)
        f.write_text(before, encoding="utf-8")   # 还原，测试只读
    assert not changed, f"rewrite_importmap 非幂等，产生了 diff: {changed}"


def test_importmap_points_to_shared_vendor():
    f = GALLERY / "cards.json"
    m = f.parent / "cards"
    if not m.exists():
        return
    first = next(m.iterdir(), None)
    if not first or not (first / "index.html").exists():
        return
    text = (first / "index.html").read_text(encoding="utf-8")
    assert "vendor/three" in text, "详情页 importmap 未指向共享 vendor"
