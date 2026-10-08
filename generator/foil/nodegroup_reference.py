#!/usr/bin/env python3
"""nodegroup_reference.py — numpy 模拟 Blender Node Group（3 通道 = 3 波长近似）。

Blender Node Group 因节点树复杂度限制采用每通道一个固定波长（R=650/G=545/B=440），
本文件用 numpy 精确复刻该 3 通道公式，用于报告「Node Group 实现 vs 6 波长参考模型」的 ΔE。
"""
import numpy as np
from proto_render import render_foil, wavelength_to_rgb


def nodegroup_render(size=512, thickness_nm=320.0, ior=1.5, grating_period_um=1.8,
                     grating_azimuth_deg=30.0, roughness=0.18, rainbow_gain=1.0,
                     base_reflect=0.85, cam_theta=0.0, cam_phi=0.0):
    """复刻 Node Group：3 通道各自单一波长，通道值 = w_spec(该波长)，无累加归一化。"""
    H = W = size
    yy, xx = np.mgrid[0:H, 0:W]
    nx = (xx / W * 2 - 1) * 1.2
    ny = (yy / H * 2 - 1) * 1.2
    nz = np.ones_like(nx)
    norm = np.sqrt(nx*nx + ny*ny + nz*nz)
    N = np.stack([nx/norm, ny/norm, nz/norm], axis=-1)

    V0 = np.array([0.0, 0.0, 1.0])
    cy, sy = np.cos(cam_theta), np.sin(cam_theta)
    cz, sz = np.cos(cam_phi), np.sin(cam_phi)
    V = np.array([
        V0[0]*cz + V0[2]*sz,
        V0[1]*cy - V0[2]*sy*cz + V0[0]*sy*sz,
        -V0[1]*sy + V0[2]*cy*cz + V0[0]*cy*sz,
    ])
    V = V / np.linalg.norm(V)

    cosI = np.clip(np.einsum('ijh,h->ij', N, V), 0.0, 1.0)
    sinT = np.minimum(1.0, np.sqrt(np.maximum(1.0 - cosI*cosI, 0.0)) / max(ior, 1.01))
    cosT = np.sqrt(np.maximum(1.0 - sinT*sinT, 0.0))

    az = np.deg2rad(grating_azimuth_deg)
    B = np.array([-np.sin(az), np.cos(az), 0.0])
    flatV = V - N * np.einsum('ijh,h->ij', N, V)[..., None]
    lenF = np.maximum(np.linalg.norm(flatV, axis=-1), 1e-6)
    v = np.einsum('ijh,h->ij', flatV, B) / lenF

    grazing = np.power(np.maximum(1.0 - cosI, 0.0), 0.5)
    wGrating = np.clip(rainbow_gain * (1.0 - roughness) * (0.35 + 0.65 * grazing), 0.0, 1.0)
    dispK = 0.5 * (1.8 / max(grating_period_um, 0.1))

    WL = [650.0, 545.0, 440.0]   # R/G/B 固定波长（Node Group 通道）
    rgb = np.zeros((H, W, 3))
    for ch, lam in enumerate(WL):
        lam_norm = (lam - 380.0) / 320.0
        peak = np.clip(lam_norm - v * dispK, 0.0, 1.0)
        wBand = np.exp(-np.power(peak / 0.22, 2.0)) * (1.0 - roughness * 2.2)
        C = 2.0 * np.pi * ior * thickness_nm / lam
        phase = C * cosT + np.pi
        Rf = 0.5 * (1.0 - np.cos(phase))
        wSpec = 0.95 * wGrating * wBand + 0.5 * (1.0 - wGrating) * Rf * (1.0 - 0.8 * wBand)
        rgb[..., ch] = wSpec
    return rgb * base_reflect


if __name__ == '__main__':
    from glsl_equivalence import deltaE_srgb
    for name, kw in [
        ('default', dict()),
        ('thick 420', dict(thickness_nm=420.0)),
        ('period 3.6', dict(grating_period_um=3.6)),
    ]:
        ref = render_foil(**kw)
        ng = nodegroup_render(**kw)
        dE = deltaE_srgb(ref, ng)
        print(f'[NodeGroup vs 6波长参考 {name}] ΔE76 mean={dE.mean():.3f} max={dE.max():.3f} '
              f'p95={np.percentile(dE,95):.3f} >8占比={(dE>8).mean()*100:.2f}%')
