#!/usr/bin/env python3
"""preflight_card.py — 云端渲染前的本地快速预检（流水线缺口 #3）。

dispatch render-card.yml 之前跑一遍，10 秒内抓出 config 缺字段 / slug 不匹配 /
edition 格式错 / assets 缺失等问题，避免云端 6 分钟渲染完才发现失败（白跑一轮）。

用法：
  python3 generator/scripts/preflight_card.py --project generator/projects/<slug>
  python3 generator/scripts/preflight_card.py --project generator/projects/<slug> --check-assets

退出码：0 = 通过；1 = 有失败项。输出 PASS/FAIL 逐项报告。
"""
import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = ["slug", "title", "subtitle", "tagline", "collection", "edition",
            "description", "stats", "honors", "back_story", "prompt"]
ASSETS = ("subject", "background", "lineart", "text")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", required=True, help="卡片项目目录（含 card-config.json）")
    p.add_argument("--check-assets", action="store_true", help="同时检查 assets/ 四层 PNG 是否存在")
    args = p.parse_args()

    root = Path(args.project).resolve()
    ok = True

    def check(cond: bool, msg: str) -> None:
        nonlocal ok
        status = "✅" if cond else "❌"
        print(f"  {status} {msg}")
        if not cond:
            ok = False

    # 1) config 存在且可解析
    cfg_path = root / "card-config.json"
    check(cfg_path.is_file(), f"card-config.json 存在（{cfg_path}）")
    if not cfg_path.is_file():
        return 1
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
        check(True, "config JSON 可解析")
    except Exception as e:
        print(f"  ❌ config JSON 解析失败：{e}")
        return 1

    # 2) 必填字段
    missing = [k for k in REQUIRED if not cfg.get(k)]
    check(not missing, f"必填字段齐全（缺失：{missing or '无'}）")

    # 3) slug 与目录名一致（云端 Verify project exists 依赖 projects/<slug>）
    check(cfg.get("slug") == root.name, f"slug == 目录名（{cfg.get('slug')} == {root.name}）")

    # 4) edition 格式
    pat = re.compile(r"^(\d{3} / \d{3}|PUB-[\w-]+)$")
    check(bool(pat.match(str(cfg.get("edition", "")))), f"edition 格式合法（{cfg.get('edition')!r}）")

    # 5) honors 非空列表
    h = cfg.get("honors")
    check(isinstance(h, list) and len(h) > 0, "honors 为非空列表")

    # 6) 四层素材（可选）
    if args.check_assets:
        for name in ASSETS:
            f = root / "assets" / f"{name}.png"
            check(f.is_file(), f"assets/{name}.png 存在")

    print(f"\n{'═══ 预检通过 ✅ 可 dispatch ═══' if ok else '═══ 预检未通过 ❌ 修复后再 dispatch ═══'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
