#!/usr/bin/env python3
"""
ablate_occlusion.py — 对遮挡序判据做参数消融，检验「误裁」是调参问题还是结构问题。

判据回顾（infer_occlusion.py）：
    d_s = median(depth[footprint])      # 主体「安装平面」深度
    foreground = depth > d_s + margin   # 比安装平面更近 ⇒ 视为主体被遮挡
构造真值：background 与 subject 独立生成后合成，主体被放在最上层
          ⇒ 正确输出恒为「无遮挡」，任何扣减都是假阳性。

消融维度：
    estimator ∈ {median, mean, p25, p75, plane(最小二乘平面残差)}
    margin    ∈ {0.05, 0.10, 0.15, 0.20, 0.25, 0.30}
诊断量：
    spread = p90(depth[footprint]) - p10(depth[footprint])   # 主体足迹下的纵深跨度
用法：
    python3 ablate_occlusion.py --repo <holo-lab> --out <dir>
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ESTIMATORS = ["median", "mean", "p25", "p75", "plane"]
MARGINS = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]


def clean_mask(m, ksize=9):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, k)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    return m.astype(np.float32)


def plane_fit_resid(depth, footprint):
    ys, xs = np.nonzero(footprint)
    if len(xs) < 3:
        return depth
    z = depth[ys, xs]
    A = np.stack([xs.astype(np.float64), ys.astype(np.float64), np.ones_like(xs, dtype=np.float64)], 1)
    coef, *_ = np.linalg.lstsq(A, z.astype(np.float64), rcond=None)
    Y, X = np.mgrid[0:depth.shape[0], 0:depth.shape[1]]
    fitted = coef[0] * X + coef[1] * Y + coef[2]
    return depth - fitted.astype(np.float32)


def run_card(proj, sess, estimate):
    bg_p, sub_p = proj / "assets" / "background.png", proj / "assets" / "subject.png"
    if not bg_p.exists() or not sub_p.exists():
        return None
    bg = cv2.imread(str(bg_p), cv2.IMREAD_COLOR)
    sub = cv2.imread(str(sub_p), cv2.IMREAD_UNCHANGED)
    if bg is None or sub is None or sub.ndim != 3 or sub.shape[2] != 4 or sub.shape[:2] != bg.shape[:2]:
        return None

    depth, _ = estimate(sess, bg_p)
    alpha = sub[:, :, 3].astype(np.float32) / 255.0
    fp = alpha > 0.1
    if fp.sum() < 1000:
        return None

    dz = depth[fp]
    spread = float(np.percentile(dz, 90) - np.percentile(dz, 10))
    iqr = float(np.percentile(dz, 75) - np.percentile(dz, 25))

    out = {"project": proj.name, "spread": round(spread, 4), "iqr": round(iqr, 4),
           "occ": {}, "fg": {}}
    for est in ESTIMATORS:
        if est == "plane":
            resid = plane_fit_resid(depth, fp)
            for m in MARGINS:
                fg = clean_mask(resid > m, 9)
                out["occ"][f"{est}|{m:.2f}"] = round(float(((fg > .5) & fp).sum() / fp.sum()) * 100, 2)
                out["fg"][f"{est}|{m:.2f}"] = round(float((fg > .5).mean()) * 100, 2)
        else:
            d_s = float({"median": np.median(dz), "mean": np.mean(dz),
                         "p25": np.percentile(dz, 25), "p75": np.percentile(dz, 75)}[est])
            for m in MARGINS:
                fg = clean_mask(depth > (d_s + m), 9)
                out["occ"][f"{est}|{m:.2f}"] = round(float(((fg > .5) & fp).sum() / fp.sum()) * 100, 2)
                out["fg"][f"{est}|{m:.2f}"] = round(float((fg > .5).mean()) * 100, 2)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    sys.path.insert(0, str(Path(a.repo) / "generator" / "depth"))
    from estimate_depth import estimate, load_session

    sess = load_session()
    projs = sorted([p for p in (Path(a.repo) / "generator" / "projects").iterdir() if p.is_dir()])
    rows = []
    for i, p in enumerate(projs, 1):
        try:
            r = run_card(p, sess, estimate)
        except Exception as e:                              # noqa: BLE001
            print(f"[{i}] {p.name}: ERR {e}")
            continue
        if r is None:
            continue
        rows.append(r)
        print(f"[{i}/{len(projs)}] {r['project']:26s} spread={r['spread']:.3f} "
              f"occ(median,.15)={r['occ']['median|0.15']:5.1f}%")

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "occlusion_ablation.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n完成 {len(rows)} 张")


if __name__ == "__main__":
    main()
