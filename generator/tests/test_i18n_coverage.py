"""i18n 词条覆盖：cards.json 中全部 style_tags 必须能在 i18n.js 词典中找到翻译。
防止新增卡标签后英文界面露出中文（曾因哈兰德新标签漏翻译复发）。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent   # holo-lab/
GALLERY = ROOT / "gallery"


def load_manifest():
    return json.loads((GALLERY / "cards.json").read_text(encoding="utf-8"))


def load_i18n_keys():
    """解析 i18n.js 词典：匹配形如 '标签': { zh: ..., en: ... } 的 key 集合。"""
    src = (GALLERY / "i18n.js").read_text(encoding="utf-8")
    # 词条 key 为单引号字符串后跟冒号：'足球': 或 '梗卡':
    keys = set(re.findall(r"'([^']+)'\s*:", src))
    return keys


def test_all_style_tags_have_i18n_entries():
    m = load_manifest()
    tags = set()
    for c in m["cards"]:
        for t in (c.get("style_tags") or []):
            tags.add(t)
    assert tags, "cards.json 中没有 style_tags，检查数据源"
    keys = load_i18n_keys()
    missing = sorted(tags - keys)
    assert not missing, (
        "以下 style_tags 缺少 i18n.js 词条，英文模式将显示中文：\n"
        + "\n".join(f"  - {t}" for t in missing)
        + "\n请在 gallery/i18n.js 词典补充 { zh: ..., en: ... } 词条。"
    )


def test_every_style_tag_is_string():
    m = load_manifest()
    for c in m["cards"]:
        for t in (c.get("style_tags") or []):
            assert isinstance(t, str) and t.strip(), f"卡 {c['id']} 存在空 style_tag"
