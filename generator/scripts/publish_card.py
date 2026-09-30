#!/usr/bin/env python3
"""
HoloLab Studio · publish_card.py
把一张生成好的卡一键发布进展厅（gallery/）。

步骤：
  1. 校验项目 web/ 产物完整（card.glb + 四层图 + card-config.json）
  2. 用 renders/hero.png 生成瀑布流缩略图 thumb.jpg
  3. 复制 web/ → gallery/cards/<id>/（剔除 node_modules / server / package）
  4. 压缩四层贴图 PNG → WebP（保留透明通道，前端零改动；幂等）
  5. 渲染预览动画 preview.webm（96 帧 → ffmpeg 合成 → 更新清单；幂等，--skip-preview 可跳过）
  6. 改写 index.html 的 importmap 指向展厅共享 vendor（避免每卡重复打包 three）
  7. 从 card-config.json 更新 gallery/cards.json 清单
首次发布自动初始化 gallery/vendor/three（共享 three.js 依赖）。

用法：
  python3 scripts/publish_card.py --project generator/projects/messi-demo [--id messi-demo] [--tags 足球,传奇]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]          # holo-lab/
GALLERY = ROOT / "gallery"
VENDOR_THREE = GALLERY / "vendor" / "three"
EXCLUDE = {"node_modules", "server.mjs", "package.json", "package-lock.json", "README.md"}
PREVIEW_FRAMES = 96          # 预览动画帧数（与 card.blend 时间线一致）
PREVIEW_FPS = 24
PREVIEW_CRF = 42


def find_blender(override: str | None = None) -> str | None:
    """定位 Blender 可执行文件：--blender 参数 > 系统 PATH > 仓库顶层便携版。"""
    if override and Path(override).is_file():
        return str(Path(override).resolve())
    system = shutil.which("blender")
    if system:
        return system
    for cand in (ROOT / "tools").glob("blender-*/blender"):
        if cand.is_file():
            return str(cand.resolve())
    return None


def ensure_vendor() -> None:
    """首次发布时，从已有项目的 node_modules 初始化共享 three vendor 目录。"""
    if (VENDOR_THREE / "three.module.js").exists():
        return
    src_three = None
    for web in (ROOT / "gallery" / "cards").glob("*/node_modules/three"):
        src_three = web
        break
    if src_three is None:
        # 兜底：从流水线模板（若有 node_modules）找
        for cand in (ROOT / "generator").rglob("node_modules/three/build/three.module.js"):
            src_three = cand.parents[1]
            break
    if src_three is None:
        raise RuntimeError(
            "找不到 three 依赖来源：请先在本机任意卡片 web/ 目录执行 npm install，"
            "或手动把 three 包放入 gallery/vendor/three/。"
        )
    shutil.copytree(src_three, VENDOR_THREE, dirs_exist_ok=True)
    _trim_vendor()
    print(f"  [vendor] three 依赖初始化 → {VENDOR_THREE.relative_to(ROOT)}")


def _trim_vendor() -> None:
    """精简 three 包：删除 src 源码与示例页，只保留运行所需的 build/jsm。"""
    # src 源码目录（three.module.js 已打包，运行不需要）
    shutil.rmtree(VENDOR_THREE / "src", ignore_errors=True)
    # build 只保留运行必需的打包文件（jsm addons 会相对引用 three.core.js 等）
    build = VENDOR_THREE / "build"
    if build.exists():
        keep = {"three.module.js", "three.core.js", "three.webgpu.js"}
        for f in build.iterdir():
            if f.name not in keep:
                shutil.rmtree(f, ignore_errors=True) if f.is_dir() else f.unlink(missing_ok=True)
    # examples 只保留 jsm（addons）
    examples = VENDOR_THREE / "examples"
    if examples.exists():
        for item in examples.iterdir():
            if item.name != "jsm":
                shutil.rmtree(item, ignore_errors=True) if item.is_dir() else item.unlink(missing_ok=True)
    # 顶层只保留必要项
    for item in VENDOR_THREE.iterdir():
        if item.name not in ("build", "examples", "LICENSE", "package.json", "README.md"):
            shutil.rmtree(item, ignore_errors=True) if item.is_dir() else item.unlink(missing_ok=True)


def make_thumb(project: Path, dest_dir: Path) -> Path:
    hero = project / "renders" / "hero.png"
    if not hero.exists():
        raise FileNotFoundError(f"缺少渲染图：{hero}（请先跑完整流水线，不要 --skip-render）")
    im = Image.open(hero)
    im.thumbnail((420, 600), Image.LANCZOS)
    thumb = dest_dir / "thumb.jpg"
    im.convert("RGB").save(thumb, quality=88)
    return thumb


# 四层贴图压缩：WebP（保留 alpha），quality 按图层信息量分层
TEXTURE_COMPRESS = {
    "background": 78,  # 大面积渐变，低损即可
    "subject": 82,     # 主体细节 + 透明通道
    "text": 88,        # 文字清晰度优先
    "lineart": 80,     # 黑白线条
}


def compress_assets(card_dir: Path) -> None:
    """把归档卡的四层 PNG 贴图转 WebP，改写 config.assets 映射并删除 PNG。

    幂等：assets/ 下已存在同名 .webp 时跳过，可重复发布。
    前端 app.js 通过 config.assets[name] 动态加载贴图，无需改页面。
    """
    assets_dir = card_dir / "assets"
    if not assets_dir.is_dir():
        return
    cfg_path = card_dir / "card-config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
    assets = cfg.get("assets", {})
    changed = False
    for name, quality in TEXTURE_COMPRESS.items():
        png = assets_dir / f"{name}.png"
        webp = assets_dir / f"{name}.webp"
        if not png.is_file() or webp.exists():
            continue  # 无 PNG 或已压缩
        im = Image.open(png)
        # RGBA/L 模式保存 WebP 时自动保留 alpha；RGB/L 直接编码
        im.save(webp, "WEBP", quality=quality, method=4)
        png.unlink()
        assets[name] = f"./assets/{name}.webp"
        changed = True
    if changed:
        cfg["assets"] = assets
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  [compress] 四层贴图已转 WebP：{', '.join(str(p) for p in assets_dir.glob('*.webp'))}")


def render_preview(project: Path, card_dir: Path, blender: str | None = None) -> bool:
    """渲染卡片预览动画（96 帧 → preview.webm）并更新清单 preview 字段。

    幂等：preview.webm 已存在则跳过，可重复发布。渲染自动分段
    （每段 40 帧），避免长任务中断导致全部重来；已渲染帧保留复用。
    返回是否执行了渲染。
    """
    webm = card_dir / "preview.webm"
    if webm.exists():
        return False
    blender_exe = find_blender(blender)
    if not blender_exe:
        print("  [preview] 跳过：未找到 Blender（可用 --blender 指定）")
        return False
    if not shutil.which("ffmpeg"):
        print("  [preview] 跳过：未找到 ffmpeg（预览动画需要）")
        return False
    frames_dir = project / "work" / "preview-frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve().parent / "render_preview.py"
    BATCH = 40
    for start in range(1, PREVIEW_FRAMES + 1, BATCH):
        end = min(start + BATCH - 1, PREVIEW_FRAMES)
        missing = [f for f in range(start, end + 1)
                   if not (frames_dir / f"frame_{f:04d}.png").exists()]
        if not missing:
            continue  # 该段已渲染（中断续跑）
        cmd = [blender_exe, "--background", "--python", str(script), "--",
               str(project.resolve()), str(frames_dir.resolve()),
               str(missing[0]), str(missing[-1])]
        subprocess.run(cmd, check=True, timeout=900)
    ffmpeg = ["ffmpeg", "-y", "-framerate", str(PREVIEW_FPS), "-i",
              str(frames_dir / "frame_%04d.png"),
              "-c:v", "libvpx-vp9", "-crf", str(PREVIEW_CRF), "-b:v", "0",
              "-an", "-pix_fmt", "yuv420p", str(webm)]
    subprocess.run(ffmpeg, check=True, timeout=300)
    shutil.rmtree(frames_dir)
    # 更新清单 preview 字段
    manifest = GALLERY / "cards.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    for card in data["cards"]:
        if card["id"] == card_dir.name:
            card["preview"] = f"cards/{card_dir.name}/preview.webm"
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    size_kb = webm.stat().st_size // 1024
    print(f"  [preview] preview.webm 生成（{size_kb}KB），cards.json 已更新")
    return True


def rewrite_importmap(index_html: Path) -> None:
    """把本地 node_modules importmap 改成展厅共享 vendor 的相对路径。"""
    text = index_html.read_text(encoding="utf-8")
    if 'vendor/three' in text:
        return
    import re
    pattern = re.compile(
        r'<script type="importmap">(.*?)</script>', re.S
    )
    new_map = (
        '{"imports":{"three":"../../vendor/three/build/three.module.js",'
        '"three/addons/":"../../vendor/three/examples/jsm/"}}'
    )
    text, n = pattern.subn(f'<script type="importmap">{new_map}</script>', text, count=1)
    if n == 0:
        raise RuntimeError(f"index.html 中未找到 importmap：{index_html}")
    index_html.write_text(text, encoding="utf-8")


def load_card_meta(cfg: dict, tags: list[str]) -> dict:
    """从 card-config.json 抽取展厅清单字段。"""
    meta = {
        "id": cfg.get("_card_id", ""),
        "title": cfg.get("title", ""),
        "subtitle": cfg.get("subtitle", ""),
        "technique": cfg.get("technique", ""),
        "tagline": cfg.get("tagline", ""),
        "edition": cfg.get("edition", ""),
        "collection": cfg.get("collection", ""),
        "description": cfg.get("description", ""),
        "author": cfg.get("author") or "HoloLab Studio",
        "style_tags": tags,
    }
    # 隐藏解锁：locked=true 时透传锁定标记与密码哈希（前端 SHA-256 比对，不存明文）
    if cfg.get("locked"):
        meta["locked"] = True
        if cfg.get("lockHash"):
            meta["lockHash"] = cfg["lockHash"]
    return meta


def update_cards_json(meta: dict, thumb: Path, card_url: str, date: str) -> None:
    manifest = GALLERY / "cards.json"
    data = {"cards": []}
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
    old = next((c for c in data.get("cards", []) if c.get("id") == meta["id"]), {})
    data["cards"] = [c for c in data.get("cards", []) if c.get("id") != meta["id"]]
    entry = {
        **meta,
        "url": card_url,
        "thumb": str(thumb),
        "date": date,
    }
    # 保留已有的 preview 字段（预览动画独立于配置生成）
    if old.get("preview"):
        entry["preview"] = old["preview"]
    # 新发布的排前面
    data["cards"] = [entry] + data["cards"]
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [manifest] cards.json 已更新（共 {len(data['cards'])} 张）")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", required=True, help="卡片项目目录")
    p.add_argument("--id", help="展厅卡片 ID（默认取项目目录名）")
    p.add_argument("--tags", default="", help="逗号分隔的风格标签，如：足球,传奇")
    p.add_argument("--date", help="发布日期，默认今天")
    p.add_argument("--blender", help="Blender 可执行文件路径（默认自动查找）")
    p.add_argument("--skip-preview", action="store_true", help="跳过预览动画渲染（preview.webm）")
    args = p.parse_args(argv)

    project = Path(args.project).resolve()
    card_id = args.id or project.name
    web = project / "web"
    for need in ["assets/card.glb", "card-config.json", "index.html"]:
        if not (web / need).exists():
            raise FileNotFoundError(f"缺少 web/{need}：请先跑完整流水线")

    import datetime
    date = args.date or datetime.date.today().isoformat()
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    dest = GALLERY / "cards" / card_id
    dest.mkdir(parents=True, exist_ok=True)

    print(f"[1/5] 初始化共享 vendor…")
    ensure_vendor()

    print(f"[2/5] 复制 web/ → gallery/cards/{card_id}/（剔除依赖与运行文件）…")
    # 保留已渲染的 preview.webm（避免重跑 publish 时重复渲染 96 帧）
    preserved_webm = None
    if (dest / "preview.webm").exists():
        preserved_webm = GALLERY / f".preview-{card_id}.tmp"
        (dest / "preview.webm").replace(preserved_webm)
    # 先清空旧归档，防止残留被排除的文件（必须在生成缩略图之前）
    for old in dest.iterdir():
        if old.is_dir():
            shutil.rmtree(old)
        else:
            old.unlink()
    for item in web.iterdir():
        if item.name in EXCLUDE:
            continue
        target = dest / item.name
        if target.exists():
            shutil.rmtree(target) if target.is_dir() else target.unlink()
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    if preserved_webm is not None and preserved_webm.exists():
        preserved_webm.replace(dest / "preview.webm")

    print(f"[3/6] 生成缩略图 thumb.jpg（复用 renders/hero.png）…")
    make_thumb(project, dest)

    print(f"[4/7] 压缩四层贴图 PNG → WebP（保留透明通道）…")
    compress_assets(dest)

    if args.skip_preview:
        print(f"[5/7] 跳过预览动画渲染（--skip-preview）…")
    else:
        print(f"[5/7] 渲染预览动画 96 帧 → preview.webm…")
        render_preview(project, dest, args.blender)

    print(f"[6/7] 改写 importmap → 共享 vendor…")
    rewrite_importmap(dest / "index.html")

    cfg = json.loads((web / "card-config.json").read_text(encoding="utf-8-sig"))
    cfg["_card_id"] = card_id
    cfg.setdefault("author", "HoloLab Studio")
    # 把 _card_id 写回归档副本，保持清单与归档一致
    dest_cfg = dest / "card-config.json"
    saved = json.loads(dest_cfg.read_text(encoding="utf-8-sig"))
    saved["_card_id"] = card_id
    saved.setdefault("author", "HoloLab Studio")
    dest_cfg.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
    meta = load_card_meta(cfg, tags)
    print(f"[7/7] 更新 cards.json…")
    update_cards_json(meta, Path(f"cards/{card_id}/thumb.jpg"), f"cards/{card_id}/", date)

    print(f"\n发布完成：{dest.relative_to(ROOT)}")
    print(f"展厅入口：gallery/index.html（本地预览：python3 -m http.server 4174）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
