#!/usr/bin/env python3
"""
bake_atmosphere.py — 把深度驱动的大气合成烘焙成一张背景图，供渲染管线直接使用。

为什么是「烘焙」而不是「在 Blender 里跑推理」：
    build_card.py 运行在 Blender 的 Python 里，装不了 onnxruntime。
    因此把 AI 这一步拆到渲染之前，产出 assets/background_atm.png，
    Blender 只负责读图。这样：
      · AI 真的进了产品链路（渲染出来的卡就是带景深的）
      · 不污染 Blender 环境
      · 删掉这张图、或渲染时加 --skip-ai，就立刻回到旧管线

用法：
    python3 generator/depth/bake_atmosphere.py --repo . generator/projects/<name>
    python3 generator/depth/bake_atmosphere.py --repo . --all      # 全部项目

产物：
    <project>/assets/background_atm.png   （无损 PNG，尺寸与原背景一致）
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

SIGMAS = np.array([0, 3, 6, 9, 12, 15], dtype=np.float32)


def bake(proj, sigma_max=12.0, haze_max=0.10, light_falloff=0.08, overwrite=False):
    from atmosphere import depth_blur
    from estimate_depth import estimate, load_session

    proj = Path(proj)
    bg_p = proj / "assets" / "background.png"
    sub_p = proj / "assets" / "subject.png"
    out_p = proj / "assets" / "background_atm.png"
    if not bg_p.exists():
        return {"ok": False, "error": "缺 background.png"}
    if out_p.exists() and not overwrite:
        return {"ok": True, "project": proj.name, "skipped": True}

    bg = cv2.imread(str(bg_p), cv2.IMREAD_COLOR)
    if bg is None:
        return {"ok": False, "error": "background 读取失败"}

    # 无主体时退化为「以画面下三分之一为焦平面」，仍能出景深
    if sub_p.exists():
        sub = cv2.imread(str(sub_p), cv2.IMREAD_UNCHANGED)
        if sub is not None and sub.shape[:2] == bg.shape[:2] and sub.ndim == 3 and sub.shape[2] == 4:
            footprint = (sub[:, :, 3].astype(np.float32) / 255.0) > 0.1
        else:
            footprint = None
    else:
        footprint = None

    sess = load_session()
    depth, _ = estimate(sess, bg_p)

    if footprint is not None and footprint.sum() > 1000:
        d_focus = float(np.median(depth[footprint]))
    else:
        d_focus = float(np.median(depth))
    d_focus = min(d_focus + 0.06, 0.98)

    far = np.clip((d_focus - depth) / max(d_focus, 1e-3), 0.0, 1.0)
    far = np.clip(cv2.GaussianBlur(far.astype(np.float32), (0, 0), 6), 0, 1)

    bg_dof = depth_blur(bg, far * sigma_max, SIGMAS)

    far_px = depth <= np.percentile(depth, 25)
    haze_color = (np.median(bg[far_px].reshape(-1, 3), axis=0).astype(np.float32)
                  if far_px.sum() > 1000 else np.array([196, 210, 224], np.float32))

    h = (far * haze_max)[..., None]
    bg_atm = bg_dof * (1 - h) + haze_color * h
    bg_atm = bg_atm * (1.0 - light_falloff * far[..., None])

    # 与 batch_atmosphere 口径一致：far 均值只统计背景区（主体覆盖区不参与观感）
    bg_mask = (footprint == False) if footprint is not None else np.ones(far.shape, bool)
    if bg_mask.sum() < 1000:
        bg_mask = np.ones(far.shape, bool)
    cv2.imwrite(str(out_p), bg_atm.clip(0, 255).astype(np.uint8))
    return {"ok": True, "project": proj.name, "skipped": False,
            "focus": round(d_focus, 4),
            "far_mean": round(float(far[bg_mask].mean()), 4),
            "far_pixels_pct": round(float((far > 0.5).mean()) * 100, 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projects", nargs="*")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--sigma", type=float, default=12.0)
    ap.add_argument("--haze", type=float, default=0.10)
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()

    targets = [Path(p) for p in a.projects]
    if a.all:
        root = Path(a.repo) / "generator" / "projects"
        targets = [d for d in sorted(root.iterdir())
                   if (d / "assets" / "background.png").exists()]

    ok = skipped = fail = 0
    for p in targets:
        m = bake(p, sigma_max=a.sigma, haze_max=a.haze, overwrite=a.overwrite)
        if not m.get("ok"):
            print(f"  失败 {Path(p).name}: {m.get('error')}")
            fail += 1
        elif m.get("skipped"):
            skipped += 1
        else:
            print(f"  {m['project']:24s} 对焦面 {m['focus']:.3f}  far {m['far_mean']:.3f}")
            ok += 1
    print(f"\n完成：烘焙 {ok} / 跳过 {skipped} / 失败 {fail}")


if __name__ == "__main__":
    main()
