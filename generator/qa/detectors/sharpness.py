#!/usr/bin/env python3
"""G2 清晰度/对比度：Laplacian 方差（模糊）+ 灰度直方图 5/95 跨度（对比度）。"""
import numpy as np
import cv2
from PIL import Image


def run(subject_path, thr):
    img = Image.open(subject_path).convert('RGB')
    arr = np.asarray(img)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(edges.mean())   # 边缘像素占比（%）：真模糊≈0，平滑材质≥0.5
    p5, p95 = np.percentile(gray, (5, 95))
    span = float(p95 - p5)

    issues = []
    warnings = []
    # 真模糊 = 无边缘结构（高斯/运动模糊会把边缘抹平）；平滑材质（贝币/玉石/夜景）有清晰轮廓
    if edge_density < thr.get('g2_edge_density_min', 0.5):
        issues.append(f'模糊/无边缘结构（edge_density={edge_density:.3f}）')
    if lap_var < thr.get('g2_laplacian_var_min', 5.0):
        warnings.append(f'纹理偏平滑（Laplacian var={lap_var:.1f}）')
    if span < thr.get('g2_histogram_span_min', 20.0):
        issues.append(f'对比度过低（直方图跨度={span:.0f}）')

    score = min(1.0, max(0.0,
               0.5 * lap_var / thr.get('g2_laplacian_var_min', 5.0)
               + 0.5 * span / thr.get('g2_histogram_span_min', 20.0)))
    return {'pass': not issues, 'score': score, 'issues': issues,
            'warnings': warnings,
            'detail': {'laplacian_var': round(lap_var, 2), 'histogram_span': round(span, 2),
                       'edge_density': round(edge_density, 4)}}
