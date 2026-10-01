#!/usr/bin/env python3
"""
HoloLab Studio · ai_generate.py
豆包 Seedream 分层画图：把一句描述（或一张参考图）变成一张全息卡需要的四层素材。

分层策略（作品集亮点）：
  1. subject.png    主体层  —— Seedream 生成主体构图 → rembg 抠图出真实透明 alpha
  2. background.png 背景层  —— Seedream 独立生成环境空镜（同风格，中下部安静留白）
  3. lineart.png    线稿层  —— OpenCV 从主体 alpha+彩色边缘程序化提取，保证像素级注册
  4. text.png       文字层  —— 精确字体排版（generate_typography.py），不让 AI 画字

构图一致性缓解：主体图与背景图共享同一风格描述前缀，背景在主体区域刻意留空；
视差效果本身会弱化轻微错位（背景为远景层）。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import threading
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

try:
    import cv2
except ImportError:
    cv2 = None

# ---------- 常量 ----------
API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
DEFAULT_MODEL = "doubao-seedream-5-0-flash-260915"
CANVAS = (1728, 2592)  # 2:3 竖版卡面（flash 模型面积上限 4,624,220 px）


def find_env_file(project: Path) -> Path | None:
    """从项目目录向上找 .env"""
    for p in [project, project.parent, project.parents[1], project.parents[2]]:
        env = p / ".env"
        if env.is_file():
            return env
    return None


def load_env(project: Path) -> str:
    key = os.environ.get("ARK_API_KEY", "")
    if not key:
        env = find_env_file(project)
        if env:
            for line in env.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("ARK_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        raise RuntimeError(
            "未找到 ARK_API_KEY：请把密钥写入项目根目录 .env（见 .env.example），或设置环境变量。"
        )
    return key


def generate_image(
    prompt: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
    reference: str | None = None,
    size: tuple[int, int] = CANVAS,
    out_path: Path | None = None,
    retries: int = 2,
) -> Path:
    """调用豆包 Seedream 生成一张图，返回本地路径。reference 传入公网图 URL 时走以图生图。"""
    payload: dict = {
        "model": model,
        "prompt": prompt,
        "size": f"{size[0]}x{size[1]}",
        "response_format": "url",
        "watermark": False,
    }

    if reference is not None:
        # 该模型 image 字段仅接受公网 URL（base64 会报 InvalidParameter）
        payload["image"] = reference

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            url = data["data"][0]["url"]
            if out_path is None:
                out_path = Path("work") / f"gen_{int(time.time()*1000)}_{attempt}.png"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(url, timeout=180) as img_resp, out_path.open("wb") as f:
                shutil.copyfileobj(img_resp, f)
            return out_path
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"豆包图像生成失败（重试 {retries} 次）：{last_err}")


_SESSION = None


def _rembg_remove(img: Image.Image) -> Image.Image:
    """惰性加载 rembg u2net 会话（轻量模型，首次运行自动下载）。"""
    global _SESSION
    if _SESSION is None:
        from rembg import new_session  # 延迟导入

        _SESSION = new_session("u2net")
    from rembg import remove

    return remove(img, session=_SESSION)


def make_subject(src: Path, out: Path, model_cache: Path) -> Path:
    """抠出透明底主体。先降采样推理（省内存），再放大回原尺寸。失败时退化兜底。"""
    img = Image.open(src).convert("RGB")
    w, h = img.size
    small = img.resize((w // 2, h // 2), Image.LANCZOS)
    try:
        result = _rembg_remove(small)
        result = result.resize((w, h), Image.LANCZOS)
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] rembg 不可用（{e}），退回简易中心抠图")
        result = _fallback_crop_center(img)
    result = result.convert("RGBA")
    result = _normalize_size(result)
    result.save(out)
    return out


def _fallback_crop_center(img: Image.Image) -> Image.Image:
    """兜底：中心 72% 区域保留，四周淡化为透明（至少满足流水线 alpha 校验）。"""
    w, h = img.size
    rgba = img.convert("RGBA")
    alpha = Image.new("L", (w, h), 0)
    from PIL import ImageDraw

    d = ImageDraw.Draw(alpha)
    cx, cy = w / 2, h / 2
    rw, rh = w * 0.72, h * 0.72
    d.ellipse((cx - rw / 2, cy - rh / 2, cx + rw / 2, cy + rh / 2), fill=255)
    alpha = alpha.filter(ImageFilter.GaussianBlur(radius=max(w, h) * 0.01))
    rgba.putalpha(alpha)
    return rgba


def _normalize_size(img: Image.Image) -> Image.Image:
    """统一到 CANVAS：等比缩放后居中贴到透明画布（不拉伸变形）。"""
    w, h = img.size
    scale = min(CANVAS[0] / w, CANVAS[1] / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    resized = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    canvas.paste(resized, ((CANVAS[0] - nw) // 2, (CANVAS[1] - nh) // 2), resized)
    return canvas


def make_lineart(subject_png: Path, out: Path) -> Path:
    """从透明底主体生成白底黑线线稿：主体 alpha 轮廓 + 内部 Canny 边缘。"""
    if cv2 is None:
        raise RuntimeError("生成线稿需要 opencv-python-headless，请先安装。")
    img = Image.open(subject_png).convert("RGBA")
    rgb = np.array(img.convert("RGB"))
    alpha = np.array(img.getchannel("A"))

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    inner = cv2.Canny(gray, 55, 150)  # 内部细节边缘

    amask = (alpha > 128).astype(np.uint8) * 255
    contour = cv2.Canny(amask, 60, 180)  # 主体轮廓线

    inside = (alpha > 128).astype(np.uint8)
    lines = np.where(inner > 0, 1, 0) * inside  # 只保留主体内部的细节线
    lines = np.maximum(lines, contour // 255)  # 加上主体轮廓

    lineart = np.full((alpha.shape[0], alpha.shape[1]), 255, np.uint8)
    lineart[lines > 0] = 0
    # 轻微加粗黑线（对黑色线条做腐蚀 = 取局部最小值，使黑线变粗）
    kernel = np.ones((3, 3), np.uint8)
    lineart = cv2.erode(lineart, kernel, iterations=1)

    result = Image.fromarray(lineart).convert("L")
    result.save(out)
    return out


def build_prompts(cfg: dict, reference: Path | None) -> tuple[str, str]:
    """构造主体图与背景图的提示词，共享风格前缀以保持一致性。"""
    style = cfg.get("style", "日式浮世绘与水墨动漫勾勒的收藏卡插画，矿物颜料质感，笔触清晰")
    subject = cfg.get("prompt") or cfg.get("title", "")
    subject_desc = cfg.get("subject_desc") or f"{subject} 主体形象"
    base = (
        f"{style}。画面内容：{subject_desc}。"
        "构图要求：主体位于画面中央，占据画布约 65%，全身或半身清晰可见，"
        "四周留有呼吸空间；光线戏剧化，适合收藏卡牌。"
    )
    background_desc = cfg.get("background_desc") or (
        f"与「{subject}」同风格的完整环境空镜："
        "竞技场/舞台氛围、背景元素丰富，但画面中部与下部 40% 区域保持安静留白"
        "（供排版叠字），画面中不出现任何人物或主体。"
    )
    return base, f"{style}。{background_desc}"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", required=True, help="卡片项目目录（含 card-config.json）")
    p.add_argument("--prompt", help="覆盖描述主体的一句话（可选）")
    p.add_argument("--reference", help="参考图路径：保留照片主体与构图，AI 重绘为卡牌风格")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--skip-ai", action="store_true", help="跳过 AI 生成，仅从 work/ 已有图抠图/线稿")
    p.add_argument("--force-ai", action="store_true", help="即使已有生成结果也重新调用 AI")
    p.add_argument("--layer", choices=("all", "subject", "background"), default="all",
                   help="只处理指定层：subject（主体生成+抠图+线稿）或 background（背景生成+后处理）；"
                        "失败恢复时用，其余层自动复用已有结果")
    args = p.parse_args(argv)

    root = Path(args.project).resolve()
    assets = root / "assets"
    work = root / "work"
    assets.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)

    cfg_path = root / "card-config.json"
    cfg = {}
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
    if args.prompt:
        cfg["prompt"] = args.prompt

    # 仅当某层"将要实际调用 AI 生成"时才需要 API key：
    # 该层在本次范围内 且（--force-ai 或原图缺失）→ 会生成 → 需要 key；
    # --skip-ai + 原图齐全 = 纯本地复用，无需 key（无 key 环境也能跑抠图/线稿）。
    def will_call_ai(layer: str) -> bool:
        target = work / f"{layer}_ai.png"
        in_scope = args.layer in ("all", layer)
        return in_scope and (args.force_ai or not target.exists())

    needs_ai = will_call_ai("subject") or will_call_ai("background")
    api_key = load_env(root) if needs_ai else ""
    ref = args.reference if args.reference else None
    if ref and not (ref.startswith("http://") or ref.startswith("https://")):
        raise ValueError("--reference 需为公网图片 URL（该模型 image 字段仅接受 URL，不支持本地文件）")

    subject_prompt, background_prompt = build_prompts(cfg, ref)

    # 1) 主体层 + 背景层并行生成（Seedream API 调用并行，省 ~15-30 秒）
    subject_ai = work / "subject_ai.png"
    bg_ai = work / "background_ai.png"

    errors: dict[str, Exception] = {}

    def gen_subject():
        if args.layer not in ("all", "subject"):
            return
        try:
            if subject_ai.exists() and not args.force_ai:
                print("[1/4] 复用已有主体图（--force-ai 可重新生成）")
            else:
                print("[1/4] 生成主体图（豆包 Seedream）…")
                print("      prompt:", subject_prompt[:90], "…")
                gen = generate_image(subject_prompt, api_key, args.model, reference=ref, out_path=subject_ai)
                print("      →", gen)
        except Exception as e:  # noqa: BLE001 — 线程内捕获，join 后统一报错
            errors["subject"] = e

    def gen_background():
        if args.layer not in ("all", "background"):
            return
        try:
            if bg_ai.exists() and not args.force_ai:
                print("[3/4] 复用已有背景图（--force-ai 可重新生成）")
            else:
                print("[3/4] 生成背景环境空镜（并行）…")
                print("      prompt:", background_prompt[:90], "…")
                gen = generate_image(background_prompt, api_key, args.model, out_path=bg_ai)
                print("      →", gen)
        except Exception as e:  # noqa: BLE001
            errors["background"] = e

    t_subject = threading.Thread(target=gen_subject, name="ai-subject")
    t_background = threading.Thread(target=gen_background, name="ai-background")
    t_subject.start()
    t_background.start()
    t_subject.join()
    t_background.join()

    if errors:
        raise RuntimeError(
            "AI 生成失败（用 --layer subject|background 只重跑失败层，成功层自动复用，无需整卡重跑）:\n"
            + "\n".join(f"  - {k}: {v}" for k, v in errors.items())
        )

    if args.layer in ("all", "subject"):
        if not subject_ai.exists():
            raise RuntimeError(
                f"缺少主体层原图 {subject_ai.relative_to(root)}：请先生成主体图"
                "（运行 ai_generate.py --project ... --layer subject），或检查 work/ 是否被清理"
            )
        # 2) 抠图（依赖主体图生成完成）
        print("[2/4] 抠出透明主体…")
        make_subject(subject_ai, assets / "subject.png", work)
        # 3) 线稿层（从透明主体程序化提取，保证注册）
        print("[4/4] 生成线稿层（OpenCV 轮廓提取）…")
        make_lineart(assets / "subject.png", assets / "lineart.png")

    if args.layer in ("all", "background"):
        if not bg_ai.exists():
            raise RuntimeError(
                f"缺少背景层原图 {bg_ai.relative_to(root)}：请先生成背景图"
                "（运行 ai_generate.py --project ... --layer background），或检查 work/ 是否被清理"
            )
        # 背景后处理（依赖背景图生成完成）
        bg = Image.open(bg_ai).convert("RGB")
        bg = _normalize_size(bg.convert("RGBA")).convert("RGB")
        bg.save(assets / "background.png")

    # 4) 文字层（精确字体排版）
    text_script = Path(__file__).resolve().parent / "generate_typography.py"
    if text_script.exists() and not (assets / "text.png").exists():
        import subprocess

        subprocess.run([sys.executable, str(text_script), str(root)], check=True)

    print("\n四层素材就绪：")
    for name in ["subject", "background", "lineart", "text"]:
        f = assets / f"{name}.png"
        if f.exists():
            with Image.open(f) as im:
                print(f"  {name}.png  {im.size}  {im.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
