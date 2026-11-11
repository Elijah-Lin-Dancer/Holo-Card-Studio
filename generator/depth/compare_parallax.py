#!/usr/bin/env python3
"""
compare_parallax.py — 两种基于深度的视差方案离线对比。

方案 A（逐像素深度位移 / per-pixel depth displacement）：
    对每个像素按自己的深度值偏移采样坐标，等价于 shader 里
    `uv' = uv + viewOffset * k * (1 - depth)`
    连续、无台阶，但遮挡区域会被拉伸（前向无遮挡信息）。

方案 B（分层 / layered）：
    按深度切 K 层，每层一个位移，远→近依次叠加。
    有遮挡层次，但层数不足时出现台阶条纹。

用法：
    python3 compare_parallax.py <bg> <depth_png> <outdir> [--k 6] [--shift 42]
"""
import argparse
from pathlib import Path

import cv2
import numpy as np

from decompose_layers import load_depth, soft_masks


def layer_compose(bg, depth, k, shift):
    masks, edges = soft_masks(depth, k)
    H, W = bg.shape[:2]
    # 用最远层铺底，避免右侧漏空变黑
    canvas = bg.astype(np.float32).copy()
    ts = np.linspace(0.0, 1.0, k)
    for i, m in enumerate(masks):
        dx = -shift * (0.2 + 0.8 * ts[i])
        a = m[..., None].astype(np.float32)
        rgb = bg.astype(np.float32)
        M = np.float32([[1, 0, dx], [0, 1, 0]])
        rgb_s = cv2.warpAffine(rgb, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
        a_s = cv2.warpAffine(a[..., 0], M, (W, H), borderMode=cv2.BORDER_REPLICATE)
        canvas = rgb_s * a_s[..., None] + canvas * (1 - a_s[..., None])
    return canvas.clip(0, 255).astype(np.uint8)


def per_pixel_displace(bg, depth, shift):
    """逐像素：近处（depth 大）位移多，远处（depth 小）位移少。"""
    H, W = bg.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # 位移量：远处 0.2 倍，近处 1.0 倍
    dx = -shift * (0.2 + 0.8 * depth)
    map_x = (xx - dx).astype(np.float32)
    map_y = yy
    out = cv2.remap(bg, map_x, map_y, interpolation=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REPLICATE)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bg")
    ap.add_argument("depth")
    ap.add_argument("outdir")
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--shift", type=float, default=42.0)
    a = ap.parse_args()

    bg = cv2.imread(a.bg, cv2.IMREAD_COLOR)
    H, W = bg.shape[:2]
    depth = load_depth(a.depth)
    if depth.shape[:2] != (H, W):
        depth = cv2.resize(depth, (W, H), interpolation=cv2.INTER_CUBIC)

    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    # 单层基线（整张同速平移）
    M = np.float32([[1, 0, -a.shift * 0.55], [0, 1, 0]])
    single = cv2.warpAffine(bg, M, (W, H), borderMode=cv2.BORDER_REPLICATE)

    imgs = [
        ("A_perpixel", per_pixel_displace(bg, depth, a.shift)),
        ("B_layered", layer_compose(bg, depth, a.k, a.shift)),
        ("C_single", single),
        ("D_original", bg),
    ]
    for name, im in imgs:
        cv2.imwrite(str(out / f"{name}.jpg"), im, [cv2.IMWRITE_JPEG_QUALITY, 93])
        print(f"  {name}.jpg")

    # 拼成 2x2 对比板（缩到 1/3 便于查看）
    tiles = []
    for name, im in imgs:
        t = cv2.resize(im, (W // 3, H // 3), interpolation=cv2.INTER_AREA)
        cv2.putText(t, name.replace("_", " "), (18, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(t, name.replace("_", " "), (18, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        tiles.append(t)
    top = np.hstack([tiles[0], tiles[1]])
    bot = np.hstack([tiles[2], tiles[3]])
    board = np.vstack([top, bot])
    cv2.imwrite(str(out / "compare_board.jpg"), board, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"\n对比板 -> {out/'compare_board.jpg'}  {board.shape}")


if __name__ == "__main__":
    main()
