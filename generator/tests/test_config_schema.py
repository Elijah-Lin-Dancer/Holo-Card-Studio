"""config 字段完整性：每张已发布卡的 card-config.json 必须满足发布所需的最小字段。
数据源 = gallery/cards/*/card-config.json（projects/ 不入库，线上卡配置以 gallery 为准）。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent   # holo-lab/
GALLERY = ROOT / "gallery"

REQUIRED = ["slug", "title", "subtitle", "tagline", "collection", "edition",
            "description", "stats", "honors", "back_story", "prompt"]


def all_configs():
    cfgs = []
    for d in sorted((GALLERY / "cards").iterdir()):
        f = d / "card-config.json"
        if f.exists():
            cfgs.append((d.name, json.loads(f.read_text(encoding="utf-8-sig"))))
    return cfgs


def test_project_dirs_have_config():
    assert len(all_configs()) > 0, "gallery/cards 下没有任何 card-config.json"


def test_required_fields_present():
    for name, cfg in all_configs():
        missing = [k for k in REQUIRED if not cfg.get(k)]
        assert not missing, f"{name}: 缺少必填字段 {missing}"


def test_slug_matches_dirname():
    for name, cfg in all_configs():
        assert cfg.get("slug") == name, f"{name}: slug 与目录名不一致"


def test_edition_format():
    import re
    # 手工系列 NNN/NNN；公众投稿卡（auto-render）使用 PUB- 编号
    pat = re.compile(r"^(\d{3} / \d{3}|PUB-[\w-]+)$")
    for name, cfg in all_configs():
        ed = cfg.get("edition", "")
        assert pat.match(ed), f"{name}: edition 格式应为 NNN / NNN 或 PUB-xxx，实际 {ed!r}"


def test_honors_is_list():
    for name, cfg in all_configs():
        h = cfg.get("honors")
        assert isinstance(h, list) and len(h) > 0, f"{name}: honors 应为非空列表"
