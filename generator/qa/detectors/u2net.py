#!/usr/bin/env python3
"""u2net 共享推理器（onnxruntime，零 API，CPU）。

直接加载 ~/.u2net/u2net.onnx，输入 RGB → 输出 0..1 前景掩膜（与原图同尺寸）。
"""
import os
import numpy as np
import onnxruntime as ort
from PIL import Image

U2NET_PATH = os.path.expanduser('~/.u2net/u2net.onnx')
_sess = None


def _get_session():
    global _sess
    if _sess is None:
        if not os.path.exists(U2NET_PATH):
            raise FileNotFoundError(f'u2net 模型缺失: {U2NET_PATH}（rembg 首次运行会自动下载）')
        so = ort.SessionOptions()
        so.intra_op_num_threads = 4
        _sess = ort.InferenceSession(U2NET_PATH, sess_options=so, providers=['CPUExecutionProvider'])
    return _sess


def foreground_mask(img: Image.Image, size=320) -> np.ndarray:
    """返回与原图同尺寸的 0..1 float 掩膜（H, W）。"""
    rgb = img.convert('RGB')
    small = rgb.resize((size, size), Image.BILINEAR)
    arr = np.asarray(small, dtype=np.float32) / 255.0
    # u2net: 1x3xHxW，归一化 0..1（此处直接用，模型内部处理）
    inp = arr.transpose(2, 0, 1)[None, ...]
    sess = _get_session()
    inp_name = sess.get_inputs()[0].name
    out_name = sess.get_outputs()[0].name
    pred = sess.run([out_name], {inp_name: inp})[0]
    pred = pred.squeeze()
    if pred.ndim == 3:
        pred = pred[0]
    mask = np.clip(pred, 0, 1)
    return np.array(Image.fromarray((mask * 255).astype(np.uint8)).resize(
        (img.width, img.height), Image.BILINEAR)).astype(np.float32) / 255.0
