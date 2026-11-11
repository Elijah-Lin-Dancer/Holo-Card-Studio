#!/usr/bin/env python3
"""
decompose_layers.py — 按深度把单张背景图分解为 K 个带软掩膜的平面层。

每层输出 RGBA PNG：
  - RGB = 原图像素
  - A   = 该层深度窗口的软掩膜（相邻层 alpha 重叠，避免硬接缝）

同时输出一个视差模拟对比图：多平面视差 vs 单层整体平移。

用法：
    python3 decompose_layers.py <background.png> <depth_png> <outdir> [--k 6]
"""
import argparse
from pathlib import Path

import cv2
import numpy as np


def load_depth(path):
    d = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if d is None:
        raise SystemExit(f"读不到深度图: {path}")
    if d.dtype == np.uint16:
        d = d.astype(np.float32) / 65535.0
    else:
        d = d.astype(np.float32)
        if d.max() > 1.0:
            d /= d.max()
    return d


def soft_masks(depth, k, feather=None, eps=1e-4):
    """把深度分解为 K 层。

    纯等面积分位在「大片区域深度值恒为 0」时会退化（多个 bin 塌缩成同一点），
    所以先把 depth<=eps 的远场（天空/极远）单独切出为第 0 层，
    剩下有梯度的像素再按分位数等面积分 K-1 层。
    """
    if feather is None:
        feather = 0.02

    far = depth <= eps
    d_eff = depth[~far & np.isfinite(depth)]

    if d_eff.size < 100:
        raise SystemExit("有效深度像素过少，深度图可能失效")

    # K-1 个区间的 K 个边界
    edges = np.quantile(d_eff, np.linspace(0, 1, k))
    edges[0] = eps          # 远场与近场的分界
    edges[-1] = d_eff.max() + 1e-6

    masks = []
    # 第 0 层：远场（平原，几乎不动）
    m0 = 1.0 / (1.0 + np.exp((depth - edges[0]) / feather))
    m0[far] = 1.0
    masks.append(m0.clip(0, 1).astype(np.float32))

    # 层 1..K-1：有效区间的等面积分段（首尾向外延伸保证全覆盖）
    for i in range(k - 1):
        lo, hi = edges[i], edges[i + 1]
        up = 1.0 / (1.0 + np.exp(-(depth - lo) / feather))
        down = 1.0 / (1.0 + np.exp((depth - hi) / feather))
        m = up * down
        if i == 0:
            m = np.where(depth <= lo, 0.0, m)   # 远场已属第 0 层
        if i == k - 2:
            m = np.where(depth >= hi, 1.0, m)
        masks.append(m.clip(0, 1).astype(np.float32))

    return masks, edges


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bg")
    ap.add_argument("depth")
    ap.add_argument("outdir")
    ap.add_argument("--k", type=int, default=6)
    a = ap.parse_args()

    bg = cv2.imread(a.bg, cv2.IMREAD_COLOR)
    if bg is None:
        raise SystemExit(f"读不到背景图: {a.bg}")
    H, W = bg.shape[:2]
    depth = load_depth(a.depth)
    if depth.shape[:2] != (H, W):
        depth = cv2.resize(depth, (W, H), interpolation=cv2.INTER_CUBIC)

    masks, qs = soft_masks(depth, a.k)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)

    layers = []
    for i, m in enumerate(masks):
        rgba = np.dstack([bg, (m * 255).astype(np.uint8)])
        cv2.imwrite(str(out / f"layer_{i}.png"), rgba)
        cov = float((m > 0.5).mean())
        layers.append(rgba)
        lo = qs[i] if i < len(qs) - 1 else qs[-1]
        hi = qs[i + 1] if i + 1 < len(qs) else qs[-1]
        print(f"  layer {i}: 深度窗 [{lo:.3f},{hi:.3f}] 覆盖 {cov*100:5.1f}%")

    # ---- 视差模拟：用 K 层各自偏移合成 vs 整层单偏移 ----
    def compose(offsets):
        canvas = np.zeros((H, W, 3), dtype=np.float32)
        # 远 -> 近 依次叠加
        for rgba, dx in zip(layers, offsets):
            a = (rgba[:, :, 3:4].astype(np.float32) / 255.0)
            rgb = rgba[:, :, :3].astype(np.float32)
            M = np.float32([[1, 0, dx], [0, 1, 0]])
            shifted = cv2.warpAffine(rgb, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
            sa = cv2.warpAffine(a[:, :, 0], M, (W, H), borderMode=cv2.BORDER_CONSTANT,
                                borderValue=0)[..., None]
            canvas = shifted * sa + canvas * (1 - sa)
        return canvas.clip(0, 255).astype(np.uint8)

    # 单层基线：整张背景同速平移
    def compose_single(dx):
        M = np.float32([[1, 0, dx], [0, 1, 0]])
        return cv2.warpAffine(bg, M, (W, H), borderMode=cv2.BORDER_REPLICATE)

    # 视差强度：最远层动得少，最近层动得多
    base = 42.0  # 模拟最大视角偏移的像素量
    ts = np.linspace(0.0, 1.0, a.k)           # 0=最远 1=最近
    multi_off = [-base * (0.25 + 0.75 * t) for t in ts]
    single_off = [-base * 0.55] * a.k          # 单层用平均速度

    for tag, img in [
        ("parallax_multi", compose(multi_off)),
        ("parallax_single", compose_single(single_off[0])),
    ]:
        cv2.imwrite(str(out / f"{tag}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 93])
        print(f"  写入 {tag}.jpg")

    print(f"\n完成：{a.k} 层 + 2 张对比图 -> {out}")


if __name__ == "__main__":
    main()
