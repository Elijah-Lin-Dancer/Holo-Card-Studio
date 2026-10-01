#!/usr/bin/env python3
"""sync_i18n.py — 新 style_tags 自动补 i18n.js 词条（流水线 A#1 钩子）。

用法：
  python3 generator/scripts/sync_i18n.py            # 扫描并自动补全缺失词条（写回 i18n.js）
  python3 generator/scripts/sync_i18n.py --check    # 只检查不写回；有缺失时退出码 1（供 CI）

原则：
  - 中文显示一律用 tag 原词（与筛选器展示一致，保证 UI 不裂）
  - 英文显示优先取 KNOWN_EN 映射表；未收录的中文 tag 回退原词，并打印"待人工精修"清单
  - 幂等：已存在词条绝不动，可重复运行

与 test_i18n_coverage.py 使用同一解析口径（'key': 正则），保证"补完必过测试"。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent   # holo-lab/
GALLERY = ROOT / "gallery"
I18N = GALLERY / "i18n.js"
MANIFEST = GALLERY / "cards.json"

# 已知英文映射：新增标签在此补充；未收录的中文标签会回退原文并提示人工精修
KNOWN_EN = {
    "梗卡": "Meme Card",
    "足球": "Football",
    "大葱塑": "Scallion Stan",
    "重庆轻轨": "Chongqing Monorail",
    "轻轨": "Monorail",
    "偷喝门将水": "Goalie-Water Thief",
    "鲨鱼笑": "Shark Grin",
    "Tom猫": "Tom Cat",
    "沙特联赛": "Saudi League",
    "多特蒙德": "Borussia Dortmund",
    "德国队": "Germany NT",
    "世界杯": "World Cup",
    "巴萨传承": "Barça Legacy",
}


def load_tags() -> set[str]:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    tags = set()
    for c in m["cards"]:
        for t in (c.get("style_tags") or []):
            tags.add(t)
    return tags


def load_existing_keys() -> set[str]:
    src = I18N.read_text(encoding="utf-8")
    return set(re.findall(r"'([^']+)'\s*:", src))


def pick_en(tag: str) -> str:
    """英文词条：映射表优先；纯 ASCII 原样；中文回退原文（供人工精修）。"""
    if tag in KNOWN_EN:
        return KNOWN_EN[tag]
    if tag.isascii() or re.fullmatch(r"[\w .&'-]+", tag):
        return tag
    return tag


def sync(write: bool) -> list[tuple[str, str]]:
    tags = load_tags()
    existing = load_existing_keys()
    missing = sorted(tags - existing)
    if not missing:
        print("✅ i18n 词条已完整覆盖（无缺失标签）")
        return []

    print(f"🔎 发现 {len(missing)} 个缺失词条：{', '.join(missing)}")
    if not write:
        print("⚠️ --check 模式：以下词条缺失（CI 将失败）")
        for t in missing:
            print(f"   - {t} → en: {pick_en(t)}")
        return [(t, pick_en(t)) for t in missing]

    # 生成词条块
    block = "".join(
        f"    '{t}': {{ zh: '{t}', en: '{pick_en(t)}' }},\n" for t in missing
    )
    src = I18N.read_text(encoding="utf-8")
    marker = "    // 卡面占位"
    if marker in src:
        src = src.replace(marker, block + marker, 1)
    else:
        # 兜底：找不到占位注释就在 dict 收尾前插入
        src = src.replace("  };", block + "  };", 1)
    I18N.write_text(src, encoding="utf-8")
    print(f"✍️  已补 {len(missing)} 条词条 → {I18N.relative_to(ROOT)}")

    # 人工精修提示（英文用了原文的中文标签）
    needs = [t for t in missing if not pick_en(t).isascii()]
    if needs:
        print("⚠️  以下标签英文回退为原文，请在 i18n.js 精修：")
        for t in needs:
            print(f"   - {t}（当前 en: {t}）")
    return [(t, pick_en(t)) for t in missing]


if __name__ == "__main__":
    write = "--check" not in sys.argv
    added = sync(write=write)
    sys.exit(1 if (added and not write and "--check" in sys.argv) else 0)
