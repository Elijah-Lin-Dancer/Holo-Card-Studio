"""补-3：渲染冒烟模式 CLI 注册测试。

--smoke 是 build_card.py 的快速低配渲染开关（低采样/小分辨率/少帧），
用于在本地/CI 快速验证"四层素材 → Blender → GLB"链路不崩。
本测试锁住 run_pipeline.py 的 CLI 注册与透传逻辑（build_card 内部是
Blender 环境，无法在 pytest 内 import，靠此 CLI 契约保护）。
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def test_smoke_flag_registered_in_cli():
    out = subprocess.run(
        [sys.executable, str(ROOT / "generator" / "scripts" / "run_pipeline.py"), "--help"],
        capture_output=True, text=True,
    )
    assert out.returncode == 0
    assert "--smoke" in out.stdout, "run_pipeline 应注册 --smoke 冒烟开关"


def test_smoke_forwarded_to_build_card():
    """run_pipeline 应在 Blender 子进程命令中透传 --smoke。"""
    src = (ROOT / "generator" / "scripts" / "run_pipeline.py").read_text(encoding="utf-8")
    assert "a.smoke" in src and "cmd.append('--smoke')" in src


def test_build_card_has_smoke_branch():
    """build_card.py 应存在 --smoke 低配渲染分支（samples/res/frames 下调）。"""
    src = (ROOT / "generator" / "scripts" / "build_card.py").read_text(encoding="utf-8")
    assert "'--smoke' in args" in src
    assert "samples=8" in src and "frame_end=12" in src
