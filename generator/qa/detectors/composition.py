#!/usr/bin/env python3
"""G4/G5 构图与视角：u2net 显著性掩膜 bbox → 主体占比 / 居中偏差；质心对称预警。"""
import numpy as np
from PIL import Image
from scipy import ndimage

from .u2net import foreground_mask


def run(subject_path, thr):
    img = Image.open(subject_path).convert('RGBA')
    mask = foreground_mask(img)
    bw = (mask > 0.5).astype(np.uint8)

    H, W = bw.shape
    if bw.sum() == 0:
        return {'pass': False, 'score': 0.0, 'issues': ['未检测到主体'],
                'detail': {'ratio': 0.0}}

    ys, xs = np.nonzero(bw)
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    ratio = float((y1 - y0 + 1) * (x1 - x0 + 1)) / (H * W)

    cx, cy = (x0 + x1) / 2 / W, (y0 + y1) / 2 / H
    center_off = float(np.hypot(cx - 0.5, cy - 0.5))

    # G5 预警：掩膜质心 vs bbox 质心（强烈偏移 → 遮挡/截断嫌疑）
    cy_mass, cx_mass = ndimage.center_of_mass(bw)
    mass_off = float(np.hypot(cx_mass / W - cx, cy_mass / H - cy))

    rmin, rmax = thr.get('g4_subject_ratio', [0.30, 0.80])
    off_max = thr.get('g4_center_offset_max', 0.15)

    issues = []
    if not (rmin <= ratio <= rmax):
        issues.append(f'主体占比异常（{ratio:.2f}，要求 {rmin}-{rmax}）')
    if center_off > off_max:
        issues.append(f'主体偏离中心（偏移 {center_off:.2f} > {off_max}）')
    warnings = []
    if mass_off > 0.25:
        warnings.append(f'掩膜质心偏移 {mass_off:.2f}，疑似遮挡/截断')

    return {'pass': not issues, 'score': min(1.0, max(0.0,
            1.0 - abs(ratio - (rmin + rmax) / 2) * 3 - center_off * 2)),
            'issues': issues, 'warnings': warnings,
            'detail': {'ratio': round(ratio, 3), 'center_offset': round(center_off, 3),
                       'mass_offset': round(mass_off, 3)}}
