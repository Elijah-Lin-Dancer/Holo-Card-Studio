#!/usr/bin/env python3
"""
batch_atmosphere.py — 把「深度驱动大气合成」从 2 张个案扩到全库，量化其有效边界。

度量（全部在合成图上算，主体区 vs 背景区）：
    S_sub  = Laplacian 标准差（主体区，alpha>0.5 腐蚀后）
    S_bg   = Laplacian 标准差（背景区，alpha<0.05 腐蚀后）
    SR     = S_sub / S_bg        分离比（越大 = 主体越「浮」在背景上）
    BVR    = S_bg(处理后) / S_bg(处理前)   背景被虚化/压平的程度
同时诊断：
    far_mean / far_p95 = 「比对焦面远多少」在背景区的均值/95 分位
    ⇒ 若 far≈0，说明背景没有纵深结构，景深根本不会作用（任何 sigma 都救不了）
用法：
    python3 batch_atmosphere.py --repo <holo-lab> --out <dir>
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

SIGMAS = [12.0, 30.0]


def lap_std(gray):
    return float(cv2.Laplacian(gray, cv2.CV_32F, ksize=3).std())


def erode(m, k=9):
    return cv2.erode(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0


def run(proj, sess, estimate, depth_blur):
    bg_p, sub_p = proj / "assets" / "background.png", proj / "assets" / "subject.png"
    if not bg_p.exists() or not sub_p.exists():
        return None
    bg = cv2.imread(str(bg_p), cv2.IMREAD_COLOR)
    sub = cv2.imread(str(sub_p), cv2.IMREAD_UNCHANGED)
    if bg is None or sub is None or sub.ndim != 3 or sub.shape[2] != 4 or sub.shape[:2] != bg.shape[:2]:
        return None

    depth, _ = estimate(sess, bg_p)
    alpha = sub[:, :, 3].astype(np.float32) / 255.0
    fp = alpha > 0.5
    if fp.sum() < 800:
        return None

    d_focus = min(float(np.median(depth[alpha > 0.1])) + 0.06, 0.98)
    far = np.clip((d_focus - depth) / max(d_focus, 1e-3), 0.0, 1.0)
    far = np.clip(cv2.GaussianBlur(far.astype(np.float32), (0, 0), 6), 0, 1)

    sub_m = erode(fp, 9)
    bg_m = erode(alpha < 0.05, 9)
    if sub_m.sum() < 500 or bg_m.sum() < 5000:
        return None

    # 处理前
    base = bg.astype(np.float32).copy()
    a = alpha[..., None]
    base_out = sub[:, :, :3].astype(np.float32) * a + base * (1 - a)
    base_g = cv2.cvtColor(base_out.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    s_sub = lap_std(base_g[sub_m])
    s_bg0 = lap_std(base_g[bg_m])

    # 雾色：远景取样
    far_px = depth <= np.percentile(depth, 25)
    haze_color = (np.median(bg[far_px].reshape(-1, 3), axis=0).astype(np.float32)
                  if far_px.sum() > 1000 else np.array([196, 210, 224], np.float32))

    rec = {"project": proj.name,
           "far_mean": round(float(far[bg_m].mean()), 4),
           "far_p95": round(float(np.percentile(far[bg_m], 95)), 4),
           "S_sub": round(s_sub, 2),
           "S_bg_before": round(s_bg0, 2),
           "SR_before": round(s_sub / (s_bg0 + 1e-6), 2),
           "sigma": {}}

    sig_arr = np.array([0, 3, 6, 9, 12, 15], dtype=np.float32)
    for smax in SIGMAS:
        bg_dof = depth_blur(bg, far * smax, sig_arr)
        h = (far * 0.10)[..., None]
        bg_atm = bg_dof * (1 - h) + haze_color * h
        bg_atm = bg_atm * (1.0 - 0.08 * far[..., None])
        out = bg_atm.copy()
        out = sub[:, :, :3].astype(np.float32) * a + out * (1 - a)
        g = cv2.cvtColor(out.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        s_bg = lap_std(g[bg_m])
        rec["sigma"][f"{smax:.0f}"] = {
            "S_bg": round(s_bg, 2),
            "SR": round(s_sub / (s_bg + 1e-6), 2),
            "BVR": round(s_bg / (s_bg0 + 1e-6), 3),
        }
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    d = Path(a.repo) / "generator" / "depth"
    sys.path.insert(0, str(d))
    from estimate_depth import estimate, load_session
    from atmosphere import depth_blur

    sess = load_session()
    projs = sorted([p for p in (Path(a.repo) / "generator" / "projects").iterdir() if p.is_dir()])
    rows = []
    for i, p in enumerate(projs, 1):
        try:
            r = run(p, sess, estimate, depth_blur)
        except Exception as e:                              # noqa: BLE001
            print(f"[{i}] {p.name}: ERR {e}")
            continue
        if r is None:
            continue
        rows.append(r)
        print(f"[{i}/{len(projs)}] {r['project']:26s} far={r['far_mean']:.3f} "
              f"SR {r['SR_before']:6.2f} → {r['sigma']['12']['SR']:6.2f} (σ12) "
              f"→ {r['sigma']['30']['SR']:6.2f} (σ30)")

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "atmosphere_batch.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n完成 {len(rows)} 张")


if __name__ == "__main__":
    main()
