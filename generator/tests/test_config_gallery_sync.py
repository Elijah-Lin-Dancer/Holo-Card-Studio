"""config 与 gallery 副本一致性（流水线 A#2）。

真源 = generator/projects/<id>/card-config.json（完整字段）。
已发布的卡若真源存在，其 title/subtitle/collection/edition 必须与
gallery/cards.json 一致——防止手工改 config 后忘记重新发布导致副本过期
（历史教训：电车卡那次改了 4 个文件）。

说明：style_tags 不存 config（发布时由 workflow 参数注入），因此不参与比对。
老卡（真源目录已清理/不存在的）跳过比对，只约束"真源还活着"的卡。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent   # holo-lab/
GALLERY = ROOT / "gallery"
PROJECTS = ROOT / "generator" / "projects"

KEY_FIELDS = ("title", "subtitle", "collection", "edition")


def load_manifest():
    return json.loads((GALLERY / "cards.json").read_text(encoding="utf-8"))


def load_config(card_id: str) -> dict | None:
    p = PROJECTS / card_id / "card-config.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8-sig"))


def test_config_source_matches_manifest():
    m = load_manifest()
    checked = 0
    problems = []
    for card in m["cards"]:
        cfg = load_config(card["id"])
        if cfg is None:
            continue  # 老卡：真源目录已清理，无法比对
        checked += 1
        for k in KEY_FIELDS:
            if cfg.get(k) != card.get(k):
                problems.append(f"{card['id']}: {k} 不一致（gallery={card.get(k)!r} vs config={cfg.get(k)!r}）")
    assert not problems, (
        "以下卡片 config（真源）与 cards.json 不一致，请重新运行 publish 同步：\n"
        + "\n".join(f"  - {p}" for p in problems)
    )
    # 至少检查到一部分卡，避免测试退化成空转
    assert checked >= 5, f"可比对的卡过少（{checked}），检查 ROOT 路径或真源目录"
