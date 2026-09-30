#!/usr/bin/env python3
"""详情页 OG 元信息全量注入（C3）。

对 gallery/cards/*/index.html 的 <head> 注入 Open Graph 块：
  - og:type / og:title / og:description / og:image / og:url
  - og:image = 线上绝对 URL（GitHub Pages 基址，硬编码防改域名）
幂等：已存在 og:image 的页面跳过；不触碰 preview/卡资源。
用法：python3 inject_og.py [--all]     # --all 强制覆盖已注入页面
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent   # holo-lab/
GALLERY = ROOT / "gallery"
BASE = "https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio"   # 硬编码线上基址

OG_TEMPLATE = """<meta property="og:type" content="article">
<meta property="og:site_name" content="HoloLab Studio">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{image}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">"""


def load_card(id_: str) -> dict:
    f = GALLERY / "cards" / id_ / "card-config.json"
    if not f.exists():
        return {}
    return json.loads(f.read_text(encoding="utf-8-sig"))


def inject(index_html: Path, force: bool = False) -> bool:
    text = index_html.read_text(encoding="utf-8")
    if "og:image" in text and not force:
        return False   # 幂等：已注入跳过
    cid = index_html.parent.name
    cfg = load_card(cid)
    title = cfg.get("title", cid)
    desc = (cfg.get("description") or cfg.get("subtitle") or title or "")[:150]
    og = OG_TEMPLATE.format(
        title=title.replace('"', "&quot;"),
        desc=desc.replace('"', "&quot;").replace("\n", " "),
        image=f"{BASE}/cards/{cid}/thumb.jpg",
        url=f"{BASE}/cards/{cid}/",
    )
    if "<meta property=\"og:image\"" in text:
        # 覆盖式更新：替换已有 og 块（--all 场景）
        text = re.sub(
            r'<meta property="og:(?:type|site_name|title|description|image|url)"[^>]*>\n?'
            r'|<meta name="twitter:card"[^>]*>\n?', "", text)
    head_end = text.find("</head>")
    if head_end == -1:
        raise RuntimeError(f"未找到 </head>：{index_html}")
    text = text[:head_end] + og + "\n" + text[head_end:]
    index_html.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="覆盖已注入页面")
    args = ap.parse_args()

    cards_dir = GALLERY / "cards"
    if not cards_dir.is_dir():
        print("FAIL: 缺少 gallery/cards/")
        return 1
    changed, skipped = [], []
    for d in sorted(cards_dir.iterdir()):
        f = d / "index.html"
        if not f.exists():
            skipped.append(f"{d.name}/index.html 缺失")
            continue
        try:
            if inject(f, force=args.all):
                changed.append(d.name)
            else:
                skipped.append(d.name)
        except Exception as e:  # noqa: BLE001
            print(f"  [err] {d.name}: {e}")
            return 1
    print(f"注入 {len(changed)} 张：{', '.join(changed) or '无'}")
    print(f"跳过（已注入/无变更）{len(skipped)}：{', '.join(skipped[:6]) or '无'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
