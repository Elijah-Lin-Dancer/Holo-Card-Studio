#!/usr/bin/env python3
"""
infer_occlusion.py — 从深度图自动推断「主体是否应被背景前景物遮挡」。

问题背景：
    现有管线里 subject 永远以固定 depth=+0.4 压在 background 之上，
    不区分背景里是否有比主体更近的前景物（棕榈树、电线杆、岩石、栏杆）。
    结果是主体像是「贴在玻璃上」，而现实里应被前景物挡住一部分。

方法：
    1. 用 subject 的 alpha 得到它在画面上的 footprint；
    2. 在该 footprint 内取 background 深度的中位数 d_s，视为主体的「安装平面」；
    3. 背景里 depth > d_s + margin 的像素，就是比主体更近的前景；
    4. 把前景区域从 subject 的 alpha 里扣掉，并把该区域单独提成一层 foreground；
    5. 若被遮挡面积占主体面积不足 min_frac，判定「无有意义前景」，回退现状。

输出：
    foreground.png      只有前景遮挡物的 RGBA 层（没有则全透明）
    subject_occluded.png 扣掉遮挡区的 subject
    occlusion_meta.json {d_s, margin, fg_cover, occluded_ratio, apply, ...}
    预览图              当前合成 vs 遮挡后合成

用法：
    python3 infer_occlusion.py <project_dir> [--margin 0.15] [--min-frac 0.05]
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from estimate_depth import estimate, load_session


def clean_mask(m, ksize=7):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, k)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    return m.astype(np.float32)


def infer(project, margin=0.15, min_frac=0.05, feather=9):
    proj = Path(project)
    bg_path = proj / "assets" / "background.png"
    sub_path = proj / "assets" / "subject.png"
    for p in (bg_path, sub_path):
        if not p.exists():
            return {"ok": False, "error": f"缺文件 {p.name}"}

    bg = cv2.imread(str(bg_path), cv2.IMREAD_COLOR)
    sub = cv2.imread(str(sub_path), cv2.IMREAD_UNCHANGED)
    if sub is None or sub.shape[2] != 4:
        return {"ok": False, "error": "subject 不是 RGBA"}
    if sub.shape[:2] != bg.shape[:2]:
        return {"ok": False, "error": f"尺寸不一致 {sub.shape[:2]} vs {bg.shape[:2]}"}

    H, W = bg.shape[:2]

    # 1) 深度
    sess = load_session()
    depth, _ = estimate(sess, bg_path)

    # 2) 主体 footprint
    alpha = sub[:, :, 3].astype(np.float32) / 255.0
    footprint = alpha > 0.1
    if footprint.sum() < 1000:
        return {"ok": False, "error": "主体可见区域过小"}

    # 3) 安装平面深度
    d_s = float(np.median(depth[footprint]))

    # 4) 前景 = 比安装平面更近
    raw_fg = depth > (d_s + margin)
    fg = clean_mask(raw_fg, 9)

    fg_cover = float((fg > 0.5).mean())
    occluded_ratio = float(((fg > 0.5) & footprint).sum() / max(footprint.sum(), 1))

    # 5) 判定是否值得应用
    apply = occluded_ratio >= min_frac

    # 层输出
    out = proj / "occlusion"
    out.mkdir(parents=True, exist_ok=True)

    # foreground 层：背景像素 × 前景 mask
    fg_a = (fg * 255).astype(np.uint8)
    fg_rgba = np.dstack([bg, fg_a])
    cv2.imwrite(str(out / "foreground.png"), fg_rgba)

    # subject 被扣掉遮挡区（羽化边界）
    if apply:
        soft = cv2.GaussianBlur(fg, (feather | 1, feather | 1), 0)
        new_alpha = (alpha * (1.0 - soft)).clip(0, 1)
        sub_o = np.dstack([sub[:, :, :3], (new_alpha * 255).astype(np.uint8)])
    else:
        sub_o = sub.copy()
    cv2.imwrite(str(out / "subject_occluded.png"), sub_o)

    # 预览：现状 vs 遮挡后
    def composite(sub_rgba, fg_layer=None):
        base = bg.astype(np.float32).copy()
        a = sub_rgba[:, :, 3:4].astype(np.float32) / 255.0
        base = sub_rgba[:, :, :3].astype(np.float32) * a + base * (1 - a)
        if fg_layer is not None:
            fa = fg_layer[:, :, 3:4].astype(np.float32) / 255.0
            base = fg_layer[:, :, :3].astype(np.float32) * fa + base * (1 - fa)
        return base.clip(0, 255).astype(np.uint8)

    before = composite(sub)
    after = composite(sub_o, fg_rgba if apply else None)
    sc = 0.33
    pw, ph = int(W * sc), int(H * sc)
    b = cv2.resize(before, (pw, ph), interpolation=cv2.INTER_AREA)
    a2 = cv2.resize(after, (pw, ph), interpolation=cv2.INTER_AREA)
    for im, txt in ((b, "BEFORE: subject always front"),
                    (a2, "AFTER: depth-inferred occlusion")):
        cv2.rectangle(im, (0, 0), (im.shape[1], 30), (15, 15, 15), -1)
        cv2.putText(im, txt, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (255, 255, 255), 2, cv2.LINE_AA)
    board = np.hstack([b, a2])
    cv2.imwrite(str(out / "preview.jpg"), board, [cv2.IMWRITE_JPEG_QUALITY, 92])

    # 深度可视化
    vis = cv2.applyColorMap((depth * 255).clip(0, 255).astype(np.uint8), cv2.COLORMAP_TURBO)
    cv2.imwrite(str(out / "depth_vis.jpg"), vis, [cv2.IMWRITE_JPEG_QUALITY, 90])

    meta = {
        "ok": True,
        "project": proj.name,
        "mount_plane_depth": round(d_s, 4),
        "margin": margin,
        "fg_cover_pct": round(fg_cover * 100, 2),
        "subject_occluded_pct": round(occluded_ratio * 100, 2),
        "apply": bool(apply),
        "min_frac": min_frac,
    }
    (out / "occlusion_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projects", nargs="+")
    ap.add_argument("--margin", type=float, default=0.15)
    ap.add_argument("--min-frac", type=float, default=0.05)
    a = ap.parse_args()

    rows = []
    for p in a.projects:
        m = infer(p, margin=a.margin, min_frac=a.min_frac)
        rows.append(m)
        if m.get("ok"):
            flag = "✅应用" if m["apply"] else "⏭ 无前景(回退)"
            print(f"{m['project']:24s} d_s={m['mount_plane_depth']:.3f} "
                  f"前景={m['fg_cover_pct']:5.1f}% "
                  f"主体被遮={m['subject_occluded_pct']:5.1f}%  {flag}")
        else:
            print(f"{m.get('project','?')}: 失败 {m.get('error')}")

    (Path(a.projects[0]).parent / "occlusion_summary.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
