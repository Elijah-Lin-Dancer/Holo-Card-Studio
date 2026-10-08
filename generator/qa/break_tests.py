#!/usr/bin/env python3
"""break_tests.py — B-2 破坏样本验证：故意破坏必须被门禁拦截。

构造 4 类破坏（基于王亥素材，写入 /tmp/qa_break/）：
  g1-break:  人物右臂区域移除（姿态缺肢）
  g2-break:  高斯模糊 σ=15（清晰度）
  g3-break:  alpha 半透明雾 + 残边（透明通道）
  g4-break:  主体缩小至 ~10% 贴角（构图）
验收：拦截率 = 100%
"""
import json
import sys
from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quality_gate import run_gate

SRC = Path(__file__).resolve().parents[2] / 'generator' / 'projects' / 'shang-wang-hai' / 'assets' / 'subject.png'
OUT = Path('/tmp/qa_break')


def make_break_samples():
    OUT.mkdir(exist_ok=True)
    img = Image.open(SRC).convert('RGBA')
    W, H = img.size

    def save_as(n, im):
        d = OUT / n / 'assets'
        d.mkdir(parents=True, exist_ok=True)
        im.save(d / 'subject.png')

    # g1：裁掉右 40%（右臂/右下肢关键点消失）
    save_as('g1-break', ImageOps.crop(img, (int(W * 0.4), 0, 0, 0)))
    # g2：高斯模糊 σ=15
    save_as('g2-break', img.filter(ImageFilter.GaussianBlur(15)))
    # g3：alpha 整体降到 60% + 四周 2px 残边
    a = np.asarray(img).copy()
    a[..., 3] = (a[..., 3] * 0.6).astype(np.uint8)
    save_as('g3-break', ImageOps.expand(Image.fromarray(a, 'RGBA'),
                                        border=2, fill=(0, 0, 0, 255)))
    # g4：主体缩到 10% 贴左上角
    small = img.resize((int(W * 0.1), int(H * 0.1)), Image.BILINEAR)
    g4 = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g4.paste(small, (0, 0))
    save_as('g4-break', g4)
    return ['g1-break', 'g2-break', 'g3-break', 'g4-break']


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--lite', action='store_true',
                    help='CI 模式：只测 G2/G3 破坏样本（直连检测器，无需 MediaPipe/u2net）')
    args = ap.parse_args()
    names = make_break_samples()
    if args.lite:
        names = [n for n in names if n.startswith(('g2', 'g3'))]
    ok = True
    for n in names:
        if args.lite:
            # 直连 G2/G3（零重依赖）：避免 run_gate 全量拖入 mediapipe/onnxruntime
            from quality_gate import load_thresholds
            from detectors import sharpness, alpha_quality
            thr = load_thresholds('default')
            subj = OUT / n / 'assets' / 'subject.png'
            g2 = sharpness.run(str(subj), thr)
            g3 = alpha_quality.run(str(subj), thr)
            issues = g2['issues'] + g3['issues']
            blocked = bool(issues)
            failed_gates = [issues] if issues else []
        else:
            rep = run_gate(OUT / n)
            blocked = not rep['pass']
            failed_gates = [g['issues'] for g in rep['gates'] if not g['pass']]
        print(f"{'✅' if blocked and failed_gates else '❌'} {n}: blocked={blocked} "
              f"failed_issues={failed_gates}")
        if not (blocked and failed_gates):
            ok = False
    print(f'\n拦截率 = {"100%" if ok else "<100%"}  验收线 100% → '
          f'{"✅ PASS" if ok else "❌ 检测器需加强"}')
    sys.exit(0 if ok else 1)
