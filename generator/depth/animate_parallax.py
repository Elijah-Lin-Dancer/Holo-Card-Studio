#!/usr/bin/env python3
"""
animate_parallax.py — 生成三方案并排的视角扫描动画 GIF。

左：单层整体平移（当前项目做法）
中：逐像素深度位移
右：分层（K 层）

用法：
    python3 animate_parallax.py <bg> <depth_png> <out.gif> [--k 6] [--shift 42] [--frames 24]
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from decompose_layers import load_depth, soft_masks


def per_pixel(bg, depth, shift):
    H, W = bg.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = -shift * (0.2 + 0.8 * depth)
    return cv2.remap(bg, (xx - dx).astype(np.float32), yy,
                     interpolation=cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_REPLICATE)


def layered(bg, depth, k, shift):
    masks, _ = soft_masks(depth, k)
    H, W = bg.shape[:2]
    canvas = bg.astype(np.float32).copy()
    ts = np.linspace(0.0, 1.0, k)
    for i, m in enumerate(masks):
        dx = -shift * (0.2 + 0.8 * ts[i])
        M = np.float32([[1, 0, dx], [0, 1, 0]])
        rgb_s = cv2.warpAffine(bg.astype(np.float32), M, (W, H),
                               borderMode=cv2.BORDER_REPLICATE)
        a_s = cv2.warpAffine(m.astype(np.float32), M, (W, H),
                             borderMode=cv2.BORDER_REPLICATE)
        canvas = rgb_s * a_s[..., None] + canvas * (1 - a_s[..., None])
    return canvas.clip(0, 255).astype(np.uint8)


def single(bg, shift):
    H, W = bg.shape[:2]
    M = np.float32([[1, 0, -shift], [0, 1, 0]])
    return cv2.warpAffine(bg, M, (W, H), borderMode=cv2.BORDER_REPLICATE)


def label(img, text):
    im = img.copy()
    cv2.rectangle(im, (0, 0), (im.shape[1], 34), (20, 20, 20), -1)
    cv2.putText(im, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (255, 255, 255), 2, cv2.LINE_AA)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bg")
    ap.add_argument("depth")
    ap.add_argument("out")
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--shift", type=float, default=42.0)
    ap.add_argument("--frames", type=int, default=24)
    a = ap.parse_args()

    bg = cv2.imread(a.bg, cv2.IMREAD_COLOR)
    H, W = bg.shape[:2]
    depth = load_depth(a.depth)
    if depth.shape[:2] != (H, W):
        depth = cv2.resize(depth, (W, H), interpolation=cv2.INTER_CUBIC)

    # 缩到 1/4 减少内存与体积
    sc = 0.25
    small = cv2.resize(bg, (int(W * sc), int(H * sc)), interpolation=cv2.INTER_AREA)
    dsmall = cv2.resize(depth, (int(W * sc), int(H * sc)), interpolation=cv2.INTER_AREA)
    shift_s = a.shift * sc

    frames = []
    # 来回扫描：-1 -> +1 -> -1
    ts = np.concatenate([np.linspace(-1, 1, a.frames // 2),
                         np.linspace(1, -1, a.frames // 2)])
    for t in ts:
        p1 = label(single(small, shift_s * 0.55 * t), "C single (current)")
        p2 = label(per_pixel(small, dsmall, shift_s * t), "A per-pixel depth")
        p3 = label(layered(small, dsmall, a.k, shift_s * t), f"B layered K={a.k}")
        frames.append(np.hstack([p1, p2, p3]))

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    pil = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in frames]
    pil[0].save(str(out), save_all=True, append_images=pil[1:],
                duration=90, loop=0, optimize=True)
    print(f"GIF -> {out}  {len(frames)} 帧  面板 {frames[0].shape}")


if __name__ == "__main__":
    main()
