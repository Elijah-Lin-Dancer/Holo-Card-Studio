#!/usr/bin/env python3
"""
estimate_depth.py — 用 Depth Anything V2 (ONNX int8) 对单张图估计相对深度。

输出：与输入同尺寸、归一化到 [0,1] 的深度图（越大 = 越近，Depth Anything 惯例）。
纯 CPU 可跑，无需 GPU / torch。

用法：
    python3 estimate_depth.py <input_image> <output_depth_png> [--size 518]
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image

MODEL = Path(__file__).resolve().parent / "models" / "model_int8.onnx"
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def load_session():
    so = ort.SessionOptions()
    so.intra_op_num_threads = 2          # 只有 2 核
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(
        str(MODEL), sess_options=so, providers=["CPUExecutionProvider"]
    )


def estimate(sess, image_path, size=518):
    """返回 (depth_float32 HxW 归一化到 0..1, 原图 WxH)。"""
    im = Image.open(image_path).convert("RGB")
    W, H = im.size

    # 保持长宽比缩到最长边 = size，并对齐到 14 的倍数
    scale = size / max(W, H)
    nw, nh = max(14, int(W * scale)), max(14, int(H * scale))
    nw = (nw // 14) * 14
    nh = (nh // 14) * 14

    im_r = im.resize((nw, nh), Image.LANCZOS)
    arr = np.asarray(im_r, dtype=np.float32) / 255.0
    arr = (arr - MEAN) / STD
    arr = arr.transpose(2, 0, 1)[None, ...].astype(np.float32)

    out = sess.run(["predicted_depth"], {"pixel_values": arr})[0]
    depth = np.asarray(out, dtype=np.float32).reshape(out.shape[-2], out.shape[-1])

    # 归一化到 0..1（Depth Anything 输出为相对逆深度，越大越近）
    lo, hi = float(depth.min()), float(depth.max())
    depth = (depth - lo) / max(hi - lo, 1e-6)

    depth = cv2.resize(depth, (W, H), interpolation=cv2.INTER_CUBIC)
    return depth, (W, H)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("out")
    ap.add_argument("--size", type=int, default=518)
    a = ap.parse_args()

    if not MODEL.exists():
        sys.exit(f"模型缺失: {MODEL}")

    sess = load_session()
    depth, (W, H) = estimate(sess, a.image, a.size)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    # 存 16 位 PNG 保精度
    cv2.imwrite(a.out, (depth * 65535).astype(np.uint16))

    print(f"[depth] {a.image} -> {a.out}")
    print(f"  原图 {W}x{H}  推理 {a.size}")
    print(f"  depth range(归一化后) {depth.min():.4f} .. {depth.max():.4f}")
    print(f"  分位数 p10/p50/p90 = "
          f"{np.percentile(depth,10):.3f} / {np.percentile(depth,50):.3f} / "
          f"{np.percentile(depth,90):.3f}")


if __name__ == "__main__":
    main()
