#!/usr/bin/env python3
"""proto_render.py — foil_holographic 光学模型的 numpy 软件渲染验证（与 OSL/GLSL 同一套数学）。

用途：在接入 Blender 之前快速验证物理正确性：
  1) 彩虹随 grating_azimuth 旋转
  2) 油彩色相随 thickness_nm 变化
  3) 彩虹宽度随 grating_period 变化
输出：out/<name>.png（PIL 保存）
"""
import numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'out'
OUT.mkdir(exist_ok=True)


def wavelength_to_rgb(lam):
    """简化 CIE 波长→sRGB（与 OSL 同一段三段近似，工程级）。"""
    lam = np.asarray(lam, dtype=float)
    x = np.zeros_like(lam); y = np.zeros_like(lam); z = np.zeros_like(lam)
    m1 = lam < 450.0
    q = (lam[m1] - 380.0) / 70.0
    x[m1] = 0.55 * q; z[m1] = 1.0 - 0.6 * q; y[m1] = 0.18 * q
    m2 = (lam >= 450.0) & (lam < 510.0)
    q = (lam[m2] - 450.0) / 60.0
    x[m2] = 0.55 - 0.2 * q; y[m2] = 0.18 + 0.82 * q; z[m2] = 0.4 - 0.4 * q
    m3 = (lam >= 510.0) & (lam < 590.0)
    q = (lam[m3] - 510.0) / 80.0
    x[m3] = 0.35 + 0.6 * q; y[m3] = 1.0 - 0.15 * q
    m4 = lam >= 590.0
    q = (lam[m4] - 590.0) / 110.0
    x[m4] = 0.95 - 0.35 * q; y[m4] = 0.85 - 0.6 * q
    return np.stack([x, y, z], axis=-1)


def render_foil(size=512, thickness_nm=320.0, ior=1.5, grating_period_um=1.8,
                grating_azimuth_deg=30.0, roughness=0.18, anisotropy=0.4,
                rainbow_gain=1.0, wavelength_samples=6, base_reflect=0.85,
                cam_theta=0.0, cam_phi=0.0):
    """软件渲染一张卡面（球面法线网格），相机俯仰/偏航可调，返回 HxWx3 线性 RGB。"""
    H = W = size
    yy, xx = np.mgrid[0:H, 0:W]
    # 归一化到 [-1, 1]，球面凸起：N = normalize(x, y, 1)
    nx = (xx / W * 2 - 1) * 1.2
    ny = (yy / H * 2 - 1) * 1.2
    nz = np.ones_like(nx)
    norm = np.sqrt(nx*nx + ny*ny + nz*nz)
    N = np.stack([nx/norm, ny/norm, nz/norm], axis=-1)

    # 相机视向量（绕 Y 俯仰、绕 Z 偏航）
    V0 = np.array([0.0, 0.0, 1.0])
    cy, sy = np.cos(cam_theta), np.sin(cam_theta)
    cz, sz = np.cos(cam_phi), np.sin(cam_phi)
    V = np.array([
        V0[0]*cz + V0[2]*sz,
        V0[1]*cy - V0[2]*sy*cz + V0[0]*sy*sz,
        -V0[1]*sy + V0[2]*cy*cz + V0[0]*cy*sz,
    ])
    V = V / np.linalg.norm(V)

    cos_theta_i = np.clip(np.einsum('ijh,h->ij', N, V), 0.0, 1.0)
    theta_i = np.arccos(cos_theta_i)
    n0 = 1.0
    sin_theta_t = np.clip((n0 / max(ior, 1.01)) * np.sin(theta_i), 0.0, 1.0)
    theta_t = np.arcsin(sin_theta_t)

    # 沟槽坐标系
    az = np.deg2rad(grating_azimuth_deg)
    T = np.array([np.cos(az), np.sin(az), 0.0])
    B = np.array([-np.sin(az), np.cos(az), 0.0])

    dotVN = np.einsum('ijh,h->ij', N, V)
    flatV = V - N * dotVN[..., None]
    len_flat = np.linalg.norm(flatV, axis=-1)
    len_flat_safe = np.maximum(len_flat, 1e-6)
    u = np.einsum('ijh,h->ij', flatV, T) / len_flat_safe
    v = np.einsum('ijh,h->ij', flatV, B) / len_flat_safe

    # 微表面权重
    grazing = np.power(1.0 - cos_theta_i, 0.5)
    w_grating = np.clip(rainbow_gain * (1.0 - roughness) * (0.35 + 0.65 * grazing), 0.0, 1.0)

    # 光谱合成
    Nw = max(wavelength_samples, 3)
    acc = np.zeros((H, W, 3))
    sumw = np.zeros((H, W))
    for k in range(Nw):
        t = k / (Nw - 1)
        lam = 380.0 + t * (700.0 - 380.0)

        phase = 2.0 * np.pi * ior * thickness_nm * np.cos(theta_t) / lam + np.pi
        Rf = 0.5 * (1.0 - np.cos(phase))

        lam_norm = (lam - 380.0) / 320.0
        disp_k = 0.5 * (1.8 / max(grating_period_um, 0.1))
        peak = np.clip(lam_norm - v * disp_k, 0.0, 1.0)
        w_band = np.exp(-np.power(peak / 0.22, 2.0)) * (1.0 - roughness * 2.2)

        rgb = wavelength_to_rgb(lam)
        w_spec = (0.95 * w_grating * w_band) + ((1.0 - w_grating) * Rf * 0.5 * (1.0 - w_band * 0.8))
        acc += rgb * w_spec[..., None]
        sumw += w_spec

    acc = np.where(sumw[..., None] > 1e-6, acc / np.maximum(sumw[..., None], 1e-6), 0.0)
    return acc * base_reflect


def save(acc, name):
    """线性 RGB → sRGB 简单伽马 → 保存 PNG。"""
    srgb = np.clip(acc, 0.0, 1.0) ** (1.0 / 2.2)
    img = (srgb * 255).astype(np.uint8)
    from PIL import Image
    Image.fromarray(img, 'RGB').save(OUT / f'{name}.png')
    print(f'✓ out/{name}.png  ({img.shape[1]}x{img.shape[0]})')


if __name__ == '__main__':
    # 1) 默认参数：油彩基底 + 彩虹
    save(render_foil(grating_azimuth_deg=30.0), 'az30')
    # 2) azimuth 30° → 60°：彩虹方向应旋转
    save(render_foil(grating_azimuth_deg=60.0), 'az60')
    # 3) thickness 320 → 420 nm：油彩色相应移动
    save(render_foil(thickness_nm=420.0), 'thick420')
    # 4) grating_period 1.8 → 3.6 μm：彩虹应更窄（色散减弱）
    save(render_foil(grating_period_um=3.6), 'period36')
    # 5) 相机倾斜 25°：整体彩虹分布应偏移（视角驱动证据）
    save(render_foil(cam_theta=0.4), 'cam_tilt')
    print('done')
