#!/usr/bin/env python3
"""quality_gate.py — AI 素材质检门禁主入口（主线② B-1）。

输入：card 项目目录（assets/{background,subject,lineart,text}.png）
输出：{pass, scores, issues, warnings, gates} JSON，写 qa_reports/<card_id>.json。

用法：
    python3 generator/qa/quality_gate.py <card_dir> [--force] [--series meme]
门禁：
    G1 主体完整性  G2 清晰度/对比度  G3 透明通道  G4 构图  G5 视角预警(warning)
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# 轻依赖常驻（G2/G3 与 ci_gate 共用）；G1/G4 的重依赖（mediapipe/u2net）在 run_gate 内延迟导入，
# 保证 CI 轻量门不拖入未安装的重型包。
from detectors import sharpness, alpha_quality  # noqa: E402

CONFIG = Path(__file__).resolve().parent / 'config' / 'qa_thresholds.json'
GATES = ['G1 主体完整性', 'G2 清晰度', 'G3 透明通道', 'G4 构图']


def load_thresholds(series='default'):
    with open(CONFIG) as f:
        cfg = json.load(f)
    return cfg.get(series, cfg['default'])


def run_gate(card_dir, series='default'):
    card_dir = Path(card_dir)
    subj = card_dir / 'assets' / 'subject.png'
    if not subj.exists():
        return {'pass': False, 'scores': {}, 'issues': ['缺少 assets/subject.png'],
                'gates': [], 'warnings': [], 'elapsed_s': 0.0}

    thr = load_thresholds(series)
    t0 = time.time()
    from detectors import completeness, composition  # 延迟导入（重依赖）
    g1 = completeness.run(str(subj), thr)
    g2 = sharpness.run(str(subj), thr)
    g3 = alpha_quality.run(str(subj), thr)
    g4 = composition.run(str(subj), thr)
    elapsed = round(time.time() - t0, 2)

    gates = [g1, g2, g3, g4]
    issues = []
    warnings = []
    for name, g in zip(GATES, gates):
        if not g['pass']:
            issues.extend(g.get('issues', []))
        warnings.extend(g.get('warnings', []))

    ok = not issues
    scores = {GATES[i].split()[0]: round(gates[i]['score'], 3) for i in range(4)}
    report = {
        'card_id': card_dir.name,
        'pass': ok,
        'scores': scores,
        'issues': issues,
        'warnings': warnings,
        'gates': gates,
        'elapsed_s': elapsed,
    }
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('card_dir')
    ap.add_argument('--force', action='store_true', help='忽略门禁结果（手动放行）')
    ap.add_argument('--series', default='default', help='阈值组：default / meme')
    ap.add_argument('--report-dir', default=None, help='报告输出目录（默认 qa_reports/）')
    args = ap.parse_args()

    report = run_gate(args.card_dir, args.series)
    out_dir = Path(args.report_dir or Path(args.card_dir) / 'qa_reports')
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f'{Path(args.card_dir).name}.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if (report['pass'] or args.force) else 1)


if __name__ == '__main__':
    main()
