#!/usr/bin/env python3
"""ci_gate.py — CI 轻量质检门（G2 清晰度 / G3 透明通道）。

设计取舍：CI 只跑零重型依赖的门（numpy/cv2/scipy），G1 姿态(MediaPipe)与
G1 掩膜/G4 构图(u2net) 全量门在本地 run_pipeline / submit_card 时执行。
对 generator/projects/ 全部素材跑轻量门，输出不通过清单并 exit 1。

用法：
    python3 generator/qa/ci_gate.py [--only-changed]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path('/home/user/.super_doubao/super-doubao-runtime/workspace/holo-lab')
PROJECTS = ROOT / 'generator' / 'projects'

sys.path.insert(0, str(Path(__file__).resolve().parent))
from detectors import sharpness, alpha_quality  # noqa: E402
from quality_gate import load_thresholds  # noqa: E402


def changed_dirs():
    """git diff HEAD~1 中新增/修改的 projects 目录名。"""
    try:
        out = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1', '--', 'generator/projects/'],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None
    return {Path(l).parts[3] for l in out.splitlines()
            if len(Path(l).parts) > 3 and Path(l).parts[3]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only-changed', action='store_true',
                    help='只检最近一次提交变更的项目')
    args = ap.parse_args()

    if args.only_changed:
        changed = changed_dirs()
        if changed is None:  # 单提交历史等场景 → 全量
            targets = [d for d in PROJECTS.iterdir() if d.is_dir()]
        else:
            targets = [PROJECTS / c for c in sorted(changed)
                       if (PROJECTS / c).exists()]
    else:
        targets = [d for d in PROJECTS.iterdir() if d.is_dir()]

    thr = load_thresholds('default')
    failures = []
    for d in targets:
        subj = d / 'assets' / 'subject.png'
        if not subj.exists():
            continue
        # per-card 豁免（qa_overrides）：设计性"缺陷"放行（如极简对比度）
        overrides = []
        cfg = d / 'card-config.json'
        if cfg.exists():
            try:
                overrides = json.loads(cfg.read_text(encoding='utf-8-sig')).get('qa_overrides', [])
            except (json.JSONDecodeError, UnicodeDecodeError):
                overrides = []
        g2 = sharpness.run(str(subj), thr)
        g3 = alpha_quality.run(str(subj), thr)
        issues = [i for i in g2['issues'] + g3['issues']
                  if not any(ov in i for ov in overrides)]
        if issues:
            failures.append((d.name, issues))
            print(f'✗ {d.name}: {issues}')
    if failures:
        print(f'\nCI 轻量门未通过 {len(failures)} 张: '
              f'{", ".join(n for n, _ in failures)}')
        sys.exit(1)
    print(f'✅ CI 轻量门全通过（{len(targets)} 个素材目录）')
    sys.exit(0)


if __name__ == '__main__':
    main()
