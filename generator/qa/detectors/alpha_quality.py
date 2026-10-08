#!/usr/bin/env python3
"""G3 透明通道质量：残边占比 / 半透明噪点 / 边缘硬度。

- 残边：alpha 完全透明(0)但与不透明(≈255)邻接的像素占比（抠图残留硬边）
- 半透明噪点：alpha ∈ (8, 248) 的内部像素占比（雾状/半透明脏点）
- 边缘硬度：边缘像素的 alpha 梯度均值（越高越锐利）
"""
import numpy as np
from PIL import Image
from scipy import ndimage


def run(subject_path, thr):
    img = Image.open(subject_path).convert('RGBA')
    a = np.asarray(img)[..., 3].astype(np.float32) / 255.0

    opaque = a > 0.98
    clear = a < 0.02
    n_pix = a.size

    # 半透明噪点（内部灰度区）
    transl = ((a > 0.03) & (a < 0.97))
    transl_ratio = float(transl.mean())

    # 残边：透明像素的邻域有不透明像素
    trans_mask = (a < 0.5).astype(np.uint8)
    opaque_mask = opaque.astype(np.uint8)
    nbr = ndimage.binary_dilation(opaque_mask, iterations=2)
    leftover = float(((trans_mask == 1) & nbr).mean())

    # 边缘硬度：alpha 梯度在边缘带的均值
    edge = ndimage.laplace(a)
    hardness = float(np.abs(edge[~opaque & ~clear]).mean()) if np.any(~opaque & ~clear) else 0.0

    issues = []
    if leftover > thr.get('g3_edge_leftover_max', 0.02):
        issues.append(f'残边占比偏高（{leftover:.3f}）')
    if transl_ratio > thr.get('g3_translucent_noise_max', 0.05):
        issues.append(f'半透明噪点偏多（{transl_ratio:.3f}）')

    score = 1.0 - min(1.0, leftover * 20 + transl_ratio * 5)
    return {'pass': not issues, 'score': score, 'issues': issues,
            'detail': {'leftover_ratio': round(leftover, 4),
                       'translucent_ratio': round(transl_ratio, 4),
                       'edge_hardness': round(hardness, 3)}}
