#!/usr/bin/env python3
"""画廊体检：cards.json ↔ 目录一致性 + 每卡资源完整 + vendor 存在。
CI 入口（gallery-check.yml）与本地开发共用。坏卡 → 非零退出。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent   # holo-lab/
GALLERY = ROOT / "gallery"
MANIFEST = GALLERY / "cards.json"

FILES = ["index.html", "app.js", "style.css", "card-config.json",
         "assets/subject.webp", "assets/background.webp",
         "assets/lineart.webp", "assets/text.webp", "assets/card.glb",
         "thumb.jpg"]
OPTIONAL = ["preview.webm"]   # 悬停预览动画：auto-render 投稿卡可能缺失，属增强项
GLB_MAGIC = b"glTF"


def main() -> int:
    errors = []
    if not MANIFEST.exists():
        print("FAIL: 缺少 gallery/cards.json")
        return 1
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cards = data.get("cards", [])
    print(f"[gallery-check] 清单 {len(cards)} 张卡")

    ids = {c["id"] for c in cards}
    if len(ids) != len(cards):
        errors.append("cards.json 存在重复 id")

    # 1) 清单 ↔ 目录一一对应
    dirs = {d.name for d in (GALLERY / "cards").iterdir() if d.is_dir()}
    for cid in ids - dirs:
        errors.append(f"清单卡缺目录: {cid}")
    for cid in dirs - ids:
        errors.append(f"孤儿目录: {cid}")

    # 2) 每卡资源完整
    for c in cards:
        cid = c["id"]
        base = GALLERY / "cards" / cid
        for f in FILES:
            p = base / f
            if not p.exists() or p.stat().st_size == 0:
                errors.append(f"{cid}/{f} 缺失或空")
        for f in OPTIONAL:
            p = base / f
            if not p.exists():
                print(f"  [warn] {cid}/{f} 缺失（可选增强项）")
        glb = base / "assets" / "card.glb"
        if glb.exists() and glb.read_bytes()[:4] != GLB_MAGIC:
            errors.append(f"{cid}/card.glb 魔数错误")
        thumb = base / "thumb.jpg"
        if thumb.exists() and thumb.read_bytes()[:2] != b"\xff\xd8":
            errors.append(f"{cid}/thumb.jpg 非 JPEG")

    # 3) 共享 vendor
    for v in ("three/build/three.module.js", "gsap/gsap.min.js"):
        if not (GALLERY / "vendor" / v).exists():
            errors.append(f"共享 vendor 缺失: {v}")

    if errors:
        print("FAIL:")
        for e in errors:
            print("  -", e)
        return 1
    print("PASS: 清单一致 · 资源完整 · vendor 在位")
    return 0


if __name__ == "__main__":
    sys.exit(main())
