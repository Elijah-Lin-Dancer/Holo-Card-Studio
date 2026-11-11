#!/usr/bin/env python3
"""
atmosphere.py — 深度驱动的大气合成（景深 + 空气透视）。

设计原则：
    只改「外观」（模糊量、雾气混色、亮度衰减），绝不动轮廓，
    因此结构上不可能像遮挡推断那样把主体切坏。

  · 景深（DOF）：以主体安装平面为对焦面，背景按「比主体远多少」渐进模糊
  · 空气透视：越远越去饱和、越偏冷、越淡（大气散射的常用近似）
  · 深度光衰减：越远越暗（可选，本脚本默认 0.25 强度）

用法：
    python3 atmosphere.py <project_dir> [--outdir ...] [--sigma 12] [--haze 0.22]
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from estimate_depth import estimate, load_session

HAZE_COLOR = np.array([196, 210, 224], dtype=np.float32)   # 冷调淡青，BGR


def blur_stack(img, sigmas):
    return [cv2.GaussianBlur(img, (0, 0), s) if s > 0 else img.copy() for s in sigmas]


def depth_blur(img, target_sigma, sigmas):
    """按每像素目标 sigma，在预模糊层之间线性插值。"""
    stack = blur_stack(img, sigmas)
    pos = np.interp(target_sigma, sigmas, np.arange(len(sigmas)))
    lo = np.floor(pos).astype(np.int32)
    hi = np.minimum(lo + 1, len(sigmas) - 1)
    frac = (pos - lo)[..., None]
    lo_img = np.take_along_axis(
        np.stack(stack, 0), lo[None, ..., None], axis=0)[0]
    hi_img = np.take_along_axis(
        np.stack(stack, 0), hi[None, ..., None], axis=0)[0]
    return (lo_img.astype(np.float32) * (1 - frac)
            + hi_img.astype(np.float32) * frac)


def process(project, sigma_max=12.0, haze_max=0.10, light_falloff=0.08,
            adaptive_haze=True, save=True):
    proj = Path(project)
    bg_p = proj / "assets" / "background.png"
    sub_p = proj / "assets" / "subject.png"
    if not bg_p.exists() or not sub_p.exists():
        return {"ok": False, "error": "缺 background/subject"}

    bg = cv2.imread(str(bg_p), cv2.IMREAD_COLOR)
    sub = cv2.imread(str(sub_p), cv2.IMREAD_UNCHANGED)
    if sub.shape[:2] != bg.shape[:2]:
        return {"ok": False, "error": "尺寸不一致"}

    H, W = bg.shape[:2]
    sess = load_session()
    depth, _ = estimate(sess, bg_p)

    # 对焦面 = 主体安装平面（取主体足迹下的背景深度中位数）+ 微前移
    alpha = sub[:, :, 3].astype(np.float32) / 255.0
    footprint = alpha > 0.1
    d_focus = float(np.median(depth[footprint])) if footprint.sum() > 1000 else 0.5
    d_focus = min(d_focus + 0.06, 0.98)

    # 「比对焦面远多少」→ 0..1
    far = np.clip((d_focus - depth) / max(d_focus, 1e-3), 0.0, 1.0)

    # 温和化：避免深度噪声导致斑块
    far = cv2.GaussianBlur(far.astype(np.float32), (0, 0), 6)
    far = np.clip(far, 0, 1)

    sigmas = np.array([0, 3, 6, 9, 12, 15], dtype=np.float32)
    target = far * sigma_max
    bg_dof = depth_blur(bg, target, sigmas)

    # 空气透视：雾色优先取背景自身远景区，避免把金色/暖调材质洗成灰蓝
    if adaptive_haze:
        far_px = depth <= np.percentile(depth, 25)
        if far_px.sum() > 1000:
            haze_color = np.median(bg[far_px].reshape(-1, 3), axis=0).astype(np.float32)
        else:
            haze_color = HAZE_COLOR
    else:
        haze_color = HAZE_COLOR

    h = (far * haze_max)[..., None]
    bg_atm = bg_dof * (1 - h) + haze_color * h
    bg_atm = bg_atm * (1.0 - light_falloff * far[..., None])

    # 主体保持完全锐利（在焦平面上）
    out = bg_atm.copy()
    a = alpha[..., None]
    out = sub[:, :, :3].astype(np.float32) * a + out * (1 - a)
    out = out.clip(0, 255).astype(np.uint8)

    if save:
        odir = proj / "atmosphere"
        odir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(odir / "result.jpg"), out, [cv2.IMWRITE_JPEG_QUALITY, 93])

        # 三版对比板
        base = bg.astype(np.float32).copy()
        base = sub[:, :, :3].astype(np.float32) * a + base * (1 - a)
        base = base.clip(0, 255).astype(np.uint8)

        bg_dof_only = bg_dof.clip(0, 255).astype(np.uint8)
        dof_only = bg_dof_only.astype(np.float32).copy()
        dof_only = sub[:, :, :3].astype(np.float32) * a + dof_only * (1 - a)
        dof_only = dof_only.clip(0, 255).astype(np.uint8)

        sc = 0.33
        pw, ph = int(W * sc), int(H * sc)
        tiles = []
        for im, txt in ((base, "A current (flat)"),
                        (dof_only, "B + depth of field"),
                        (out, "C + DOF + adaptive haze")):
            t = cv2.resize(im, (pw, ph), interpolation=cv2.INTER_AREA)
            cv2.rectangle(t, (0, 0), (t.shape[1], 28), (15, 15, 15), -1)
            cv2.putText(t, txt, (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                        (255, 255, 255), 2, cv2.LINE_AA)
            tiles.append(t)
        board = np.hstack(tiles)
        cv2.imwrite(str(odir / "board.jpg"), board, [cv2.IMWRITE_JPEG_QUALITY, 92])
        # 同时保留一版纯景深，便于单独评估
        cv2.imwrite(str(odir / "result_dof_only.jpg"), dof_only,
                    [cv2.IMWRITE_JPEG_QUALITY, 93])

    meta = {
        "ok": True,
        "project": proj.name,
        "focus_depth": round(d_focus, 4),
        "sigma_max": sigma_max,
        "haze_max": haze_max,
        "far_pixels_pct": round(float((far > 0.5).mean()) * 100, 2),
    }
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projects", nargs="+")
    ap.add_argument("--sigma", type=float, default=12.0)
    ap.add_argument("--haze", type=float, default=0.10)
    ap.add_argument("--no-adaptive-haze", action="store_true")
    a = ap.parse_args()

    for p in a.projects:
        m = process(p, sigma_max=a.sigma, haze_max=a.haze,
                    adaptive_haze=not a.no_adaptive_haze)
        if m.get("ok"):
            print(f"{m['project']:24s} 对焦面={m['focus_depth']:.3f} "
                  f"远景区={m['far_pixels_pct']:5.1f}%")
        else:
            print(f"{Path(p).name}: {m.get('error')}")


if __name__ == "__main__":
    main()
