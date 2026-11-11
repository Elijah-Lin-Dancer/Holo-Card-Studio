#!/usr/bin/env python3
"""
probe_depth_failure.py — 在真实生产卡片上量化「单目深度在生成式背景上的失效」。

研究问题：
    单目深度模型在真实照片上训练，生成式背景（尤其平铺装饰纹理）是分布外输入。
    它会否在光度上平坦、但纹理密集的区域「脑补」出并不存在的地形起伏？
    这种伪起伏是否直接导致下游遮挡序推断把主体误裁？

关键设计：真值来自构造，不来自标注。
    每张卡的 background 与 subject 是分别生成后合成的，主体在合成时被放在最上层。
    ⇒ 「主体应当完整可见」是构造已知的真值。
    ⇒ 遮挡推断扣掉主体任何一部分，都是可证伪的假阳性。

指标（全部无需真值即可计算）：
    FRDG  平坦-纹理区（flat∧textured）内的平均深度梯度，按全图均值归一
    FRDGc 对照区（flat∧smooth）同上 —— 光度平坦区的「本底」伪起伏
    TRD   FRDG / FRDGc —— 纹理诱导的伪起伏倍率（本研究的主指标）
    DSP   flat∧textured 区内 depth 的标准差 / 全图 depth 标准差
后果指标：
    OCC   主体被遮挡推断扣掉的像素占比（%）（构造成立时应为 0）

用法：
    python3 probe_depth_failure.py --repo <holo-lab> --out <dir>
"""
import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def clean_mask(m, ksize=9):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, k)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    return m.astype(np.float32)


def grad_mag(a):
    gx = cv2.Sobel(a, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(a, cv2.CV_32F, 0, 1, ksize=3)
    return np.sqrt(gx * gx + gy * gy)


def compute(proj, sess, estimate):
    bg_p = proj / "assets" / "background.png"
    sub_p = proj / "assets" / "subject.png"
    if not bg_p.exists() or not sub_p.exists():
        return None

    bg = cv2.imread(str(bg_p), cv2.IMREAD_COLOR)
    sub = cv2.imread(str(sub_p), cv2.IMREAD_UNCHANGED)
    if bg is None or sub is None or sub.ndim != 3 or sub.shape[2] != 4:
        return None
    if sub.shape[:2] != bg.shape[:2]:
        return None

    depth, _ = estimate(sess, bg_p)

    # ---------- 图像侧统计 ----------
    L = (0.299 * bg[:, :, 2] + 0.587 * bg[:, :, 1] + 0.114 * bg[:, :, 0]).astype(np.float32) / 255.0
    L_lp = cv2.GaussianBlur(L, (0, 0), 15)
    g_lp = grad_mag(L_lp)                                   # 低频结构（光照/地势）
    L_hp = L - cv2.GaussianBlur(L, (0, 0), 2)
    hf = cv2.GaussianBlur(np.abs(L_hp), (0, 0), 7)          # 局部纹理能量

    p40 = np.percentile(g_lp, 40)
    p60 = np.percentile(hf, 60)
    p25 = np.percentile(hf, 25)
    flat = g_lp <= p40
    textured = hf >= p60
    smooth = hf <= p25
    R = flat & textured          # 主区：光度平坦 + 纹理密集（生成式装饰背景的典型形态）
    Rc = flat & smooth           # 对照区：光度平坦 + 无纹理

    # ---------- 深度侧统计 ----------
    dg = grad_mag(depth)
    dg_mean = float(dg.mean()) + 1e-6
    FRDG = float(dg[R].mean()) / dg_mean if R.sum() > 500 else np.nan
    FRDGc = float(dg[Rc].mean()) / dg_mean if Rc.sum() > 500 else np.nan
    TRD = float(FRDG / (FRDGc + 1e-6)) if np.isfinite(FRDG) and np.isfinite(FRDGc) else np.nan
    dstd = float(depth.std()) + 1e-6
    DSP = float(depth[R].std() / dstd) if R.sum() > 500 else np.nan

    # ---------- 下游后果（构造真值：主体应在最上层）----------
    alpha = sub[:, :, 3].astype(np.float32) / 255.0
    footprint = alpha > 0.1
    if footprint.sum() < 1000:
        return None
    d_s = float(np.median(depth[footprint]))
    raw_fg = depth > (d_s + 0.15)
    fg = clean_mask(raw_fg, 9)
    occ = float(((fg > 0.5) & footprint).sum() / footprint.sum()) * 100.0

    # 主体 vs 背景锐度（此前发现的「锐度倒挂」）
    lap = cv2.Laplacian(cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY), cv2.CV_32F, ksize=3)
    bg_sharp = float(lap.std())
    sub_gray = cv2.cvtColor(sub[:, :, :3], cv2.COLOR_BGR2GRAY)
    sub_sharp = float(cv2.Laplacian(sub_gray, cv2.CV_32F, ksize=3)[footprint].std())

    return {
        "project": proj.name,
        "FRDG": round(FRDG, 4),
        "FRDGc": round(FRDGc, 4),
        "TRD": round(TRD, 3),
        "DSP": round(DSP, 4),
        "texture_density": round(float(hf.mean()), 4),
        "flat_frac": round(float(flat.mean()), 3),
        "region_frac": round(float(R.mean()), 3),
        "d_s": round(d_s, 4),
        "OCC": round(occ, 2),
        "bg_sharp": round(bg_sharp, 2),
        "sub_sharp": round(sub_sharp, 2),
        "sharp_ratio": round(bg_sharp / (sub_sharp + 1e-6), 3),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--out", default=".")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    sys.path.insert(0, str(Path(a.repo) / "generator" / "depth"))
    from estimate_depth import estimate, load_session

    sess = load_session()
    projs = sorted([p for p in (Path(a.repo) / "generator" / "projects").iterdir() if p.is_dir()])
    if a.limit:
        projs = projs[: a.limit]

    rows, t0 = [], time.time()
    for i, p in enumerate(projs, 1):
        try:
            r = compute(p, sess, estimate)
        except Exception as e:                              # noqa: BLE001
            print(f"[{i}/{len(projs)}] {p.name}: ERR {e}")
            continue
        if r is None:
            print(f"[{i}/{len(projs)}] {p.name}: 跳过（素材不全）")
            continue
        rows.append(r)
        print(f"[{i}/{len(projs)}] {p.name:26s} TRD={r['TRD']:5.2f} OCC={r['OCC']:5.1f}% "
              f"锐度比={r['sharp_ratio']:5.2f}")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "depth_failure_probe.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    # CSV
    if rows:
        keys = list(rows[0].keys())
        with open(out / "depth_failure_probe.csv", "w", encoding="utf-8") as f:
            f.write(",".join(keys) + "\n")
            for r in rows:
                f.write(",".join(str(r[k]) for k in keys) + "\n")

    print(f"\n完成 {len(rows)} 张，用时 {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
