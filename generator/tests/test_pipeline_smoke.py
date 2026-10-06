"""Pipeline smoke tests：在不调用 API / 不跑 Blender 的前提下，验证核心生成链路的关键纯逻辑。

覆盖：
- build_prompts（提示词构造：风格前缀共享、构图约束、背景留白约束）
- validate_assets（四层素材校验：尺寸一致、真实 alpha、线稿明暗）
- preflight_card（config 必填字段门禁，subprocess 真跑）
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from ai_generate import build_prompts
from validate_assets import validate

ROOT = Path(__file__).resolve().parent.parent.parent  # holo-lab/


def _make_layer(path: Path, mode: str, color, *, alpha_shape: bool = False):
    """生成一张测试层 PNG。alpha_shape=True 时画一个不透明矩形，其余透明。"""
    img = Image.new(mode, (256, 256), color)
    if alpha_shape:
        import random
        px = img.load()
        for x in range(64, 192):
            for y in range(64, 192):
                px[x, y] = (200, 120, 60, 255)  # 不透明主体区域
    img.save(path)


@pytest.fixture
def fake_project(tmp_path: Path):
    """构造一个通过校验的最小假项目：assets/ 下四层同尺寸 PNG。"""
    assets = tmp_path / "assets"
    assets.mkdir()
    _make_layer(assets / "subject.png", "RGBA", (0, 0, 0, 0), alpha_shape=True)
    _make_layer(assets / "background.png", "RGB", (30, 60, 90))
    # 白底黑线：中心画一条黑线保证极值 (0, 255)
    line = Image.new("RGB", (256, 256), (255, 255, 255))
    d = line.load()
    for x in range(120, 136):
        for y in range(100, 156):
            d[x, y] = (10, 10, 10)
    line.save(assets / "lineart.png")
    _make_layer(assets / "text.png", "RGBA", (0, 0, 0, 0), alpha_shape=True)
    return tmp_path


class TestBuildPrompts:
    def test_returns_two_prompts_with_shared_style(self):
        cfg = {
            "style": "测试风格前缀",
            "prompt": "一只凤凰",
            "subject_desc": "金红相间的凤凰，居中",
        }
        subject, background = build_prompts(cfg, reference=None)
        assert isinstance(subject, str) and isinstance(background, str)
        # 风格前缀必须共享，保证两次生成同风格
        assert subject.startswith("测试风格前缀")
        assert background.startswith("测试风格前缀")
        # 主体 prompt 含构图约束（占画布比例）
        assert "65%" in subject
        # 背景 prompt 明确要求不出现主体/人物
        assert "不出现" in background

    def test_falls_back_to_title_when_prompt_missing(self):
        cfg = {"title": "Messi, King"}
        subject, _ = build_prompts(cfg, reference=None)
        assert "Messi, King" in subject


class TestValidateAssets:
    def test_accepts_valid_project(self, fake_project):
        report = validate(fake_project)
        assert set(report.keys()) == {"subject", "background", "lineart", "text"}
        # 校验产物写回（发布链路依赖此文件）
        assert (fake_project / "asset-validation.json").is_file()

    def test_rejects_subject_without_real_alpha(self, fake_project):
        # 破坏 subject 的 alpha：改成无透明通道的 RGB
        img = Image.new("RGB", (256, 256), (200, 120, 60))
        img.save(fake_project / "assets" / "subject.png")
        with pytest.raises(ValueError, match="alpha"):
            validate(fake_project)

    def test_rejects_lineart_without_dark_contours(self, fake_project):
        # 线稿全灰（无黑线）→ 极值不满足 lo<=80 / hi>=230
        Image.new("RGB", (256, 256), (180, 180, 180)).save(
            fake_project / "assets" / "lineart.png"
        )
        with pytest.raises(ValueError, match="contours|Line art"):
            validate(fake_project)


class TestPreflight:
    def test_rejects_config_missing_honors(self, tmp_path):
        """缺 honors 的 config 必须让 preflight 以非 0 退出（subprocess 真跑）。"""
        proj = tmp_path / "fake-card"
        proj.mkdir()
        cfg = {
            "title": "Test",
            "slug": proj.name,
            "edition": "001 / 001",
            # 故意缺 honors
        }
        (proj / "card-config.json").write_text(
            json.dumps(cfg, ensure_ascii=False), encoding="utf-8"
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / "generator/scripts/preflight_card.py"),
             "--project", str(proj)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0
        assert "honors" in result.stdout

    def test_accepts_full_config(self, tmp_path):
        proj = tmp_path / "ok-card"
        proj.mkdir()
        cfg = {
            "title": "Test",
            "subtitle": "Sub",
            "tagline": "Tag",
            "collection": "Test Series",
            "slug": proj.name,
            "edition": "001 / 001",
            "description": "A test card",
            "stats": ["2026"],
            "honors": ["Test honor"],
            "back_story": "Back story",
            "prompt": "a test prompt",
        }
        (proj / "card-config.json").write_text(
            json.dumps(cfg, ensure_ascii=False), encoding="utf-8"
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / "generator/scripts/preflight_card.py"),
             "--project", str(proj)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
