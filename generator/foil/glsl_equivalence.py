#!/usr/bin/env python3
"""glsl_equivalence.py — GLSL 与 numpy 原型的数值等价验证（ΔE 对照）。

按 foil_holographic.glsl 的公式逐行在 numpy 里执行，与 proto_render.render_foil
（6 波长、同 CIE 四段近似、同沟槽坐标系）输出对照。数学一致 → 像素级差异≈0。
"""
import numpy as np
from proto_render import render_foil, wavelength_to_rgb


def wavelength_to_rgb_glsl(lam):
    """严格复刻 GLSL wavelengthToRGB（四段线性）。"""
    lam = np.asarray(lam, dtype=float)
    x = np.zeros_like(lam); y = np.zeros_like(lam); z = np.zeros_like(lam)
    m1 = lam < 450.0
    q = (lam[m1] - 380.0) / 70.0
    x[m1] = 0.55 * q; y[m1] = 0.18 * q; z[m1] = 1.0 - 0.6 * q
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


def glsl_foil(size=512, thickness_nm=320.0, ior=1.5, grating_period_um=1.8,
              grating_azimuth_deg=30.0, roughness=0.18, rainbow_gain=1.0,
              base_reflect=0.85, cam_theta=0.0, cam_phi=0.0):
    """GLSL 等值执行（球面法线网格 + 固定视向量，与 proto_render 同场景）。"""
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

    Nw = 6
    lam = np.array([380.0, 444.0, 508.0, 572.0, 636.0, 700.0])
    acc = np.zeros((H, W, 3)); sumw = np.zeros((H, W))
    for i in range(Nw):
        lam_norm = (lam[i] - 380.0) / 320.0
        peak = np.clip(lam_norm - v * dispK, 0.0, 1.0)
        wBand = np.exp(-np.power(peak / 0.22, 2.0)) * (1.0 - roughness * 2.2)
        C = 2.0 * np.pi * ior * thickness_nm / lam[i]
        phase = C * cosT + np.pi
        Rf = 0.5 * (1.0 - np.cos(phase))
        wSpec = 0.95 * wGrating * wBand + 0.5 * (1.0 - wGrating) * Rf * (1.0 - 0.8 * wBand)
        rgb = wavelength_to_rgb_glsl(lam[i])
        acc += rgb * wSpec[..., None]
        sumw += wSpec
    acc = np.where(sumw[..., None] > 1e-6, acc / np.maximum(sumw[..., None], 1e-6), 0.0)
    return acc * base_reflect


def deltaE_srgb(a, b):
    """sRGB → Lab 简化 ΔE76（同 RFC §6.1 验收协议）。"""
    def rgb_to_lab(im):
        srgb = np.clip(im, 0.0, 1.0)
        lin = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
        m = np.array([[0.4124564, 0.3575761, 0.1804375],
                      [0.2126729, 0.7151522, 0.0721750],
                      [0.0193339, 0.1191920, 0.9503041]])
        XYZ = lin @ m.T   # (H,W,3) @ (3,3)
        X, Y, Z = XYZ[..., 0], XYZ[..., 1], XYZ[..., 2]
        Xn, Yn, Zn = 0.95047, 1.0, 1.08883
        def f(t):
            return np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16.0 / 116.0)
        fx, fy, fz = f(X/Xn), f(Y/Yn), f(Z/Zn)
        return np.stack([116*fy - 16, 500*(fx - fy), 200*(fy - fz)], axis=-1)
    l1, l2 = rgb_to_lab(a), rgb_to_lab(b)
    return np.sqrt(((l1 - l2) ** 2).sum(-1))


if __name__ == '__main__':
    # 3 组对照（默认 / 旋转视角 / 变厚度）
    cases = [
        ('default (θ=0, d=320)', dict()),
        ('view (θ=0.4)', dict(cam_theta=0.4)),
        ('thick (d=420)', dict(thickness_nm=420.0)),
    ]
    for name, kw in cases:
        ref = render_foil(**kw)          # numpy 原型（等价模型）
        gls = glsl_foil(**kw)            # GLSL 公式等值执行
        dE = deltaE_srgb(ref, gls)
        md = np.abs(ref - gls).mean()
        print(f'[{name}] 平均|ΔRGB|={md:.6f}  ΔE76 max={dE.max():.3f}  mean={dE.mean():.3f}  '
              f'p95={np.percentile(dE, 95):.3f}  >8像素占比={(dE>8).mean()*100:.2f}%')
    # 顺带：Node Group（3 通道）相对参考模型的 ΔE（Blender 实现精度报告）
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('ngref', 'nodegroup_reference.py')
        ng = importlib.util.module_from_spec(spec); spec.loader.exec_module(ng)
        ref = render_foil()
        ngout = ng.nodegroup_render()
        dE = deltaE_srgb(ref, ngout)
        print(f'[NodeGroup 3通道 vs 参考6波长] ΔE76 mean={dE.mean():.3f} max={dE.max():.3f} p95={np.percentile(dE,95):.3f}')
    except Exception as e:
        print('NodeGroup 对照跳过:', e)
    print('done')
