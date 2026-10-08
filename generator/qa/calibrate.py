#!/usr/bin/env python3
"""calibrate.py — B-1 阈值校准：5 张历史卡回放 + 人工基准对照。

人工基准（对已知卡的真实判定）：
  shang-wang-hai      人物·四肢完整 → PASS
  vc-tommy-vercetti   人物·四肢完整 → PASS
  pouch-invader       动物·掩膜连通 → PASS
  eletrico-28-lisboa  物件·掩膜连通 → PASS
  shang-houmuwu-ding  物件·掩膜连通 → PASS
验收：自动 vs 人工一致率 ≥ 90%
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quality_gate import run_gate

BASE = Path('/home/user/.super_doubao/super-doubao-runtime/workspace/holo-lab/generator/projects')
GROUND_TRUTH = {
    'shang-wang-hai': True,
    'vc-tommy-vercetti': True,
    'pouch-invader': True,
    'eletrico-28-lisboa': True,
    'shang-houmuwu-ding': True,
}

if __name__ == '__main__':
    results = []
    for cid, expect in GROUND_TRUTH.items():
        rep = run_gate(BASE / cid)
        match = (rep['pass'] == expect)
        results.append((cid, rep['pass'], expect, match, rep.get('scores', {}),
                        rep['issues'][:2]))
        print(f"{'✅' if match else '❌'} {cid}: auto={rep['pass']} expect={expect} "
              f"scores={rep.get('scores')} issues={rep['issues'][:2]}")
    agree = sum(1 for r in results if r[3]) / len(results)
    print(f'\n一致率 = {agree*100:.0f}% (5 张)  验收线 ≥ 90% → {"✅ PASS" if agree >= 0.9 else "❌ 需调阈值"}')
    sys.exit(0 if agree >= 0.9 else 1)
