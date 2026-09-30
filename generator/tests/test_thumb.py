"""缩略图生成回归：make_thumb 输出非空、尺寸正确、JPEG 格式（A 类 bug 防护）。"""
import tempfile
from pathlib import Path
from PIL import Image

import publish_card

ROOT = Path(__file__).resolve().parent.parent.parent   # holo-lab/


def _fixture_project():
    """从 gallery 任意一张卡复制 hero.png 构造最小渲染目录（不动真实 projects）。"""
    cards = ROOT / "gallery" / "cards"
    hero_src = None
    for d in cards.iterdir():
        cand = d / "assets" / "subject.webp"
        if cand.exists():
            hero_src = cand
            break
    assert hero_src, "找不到测试用素材"

    tmp = Path(tempfile.mkdtemp(prefix="hololab-thumb-test-"))
    renders = tmp / "renders"
    renders.mkdir(parents=True)
    img = Image.open(hero_src)
    img = img.convert("RGB").resize((1080, 1500), Image.LANCZOS)
    img.save(renders / "hero.png")
    return tmp


def test_make_thumb_outputs_valid_jpeg():
    proj = _fixture_project()
    dest = proj / "out"
    dest.mkdir()
    thumb = publish_card.make_thumb(proj, dest)
    assert thumb.exists()
    assert thumb.stat().st_size > 1000, "缩略图过小，疑似空白"
    im = Image.open(thumb)
    assert im.format == "JPEG"
    assert im.size[0] <= 420, f"缩略图宽应 ≤420，实际 {im.size}"


def test_make_thumb_missing_hero_raises():
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="hololab-thumb-missing-"))
    dest = tmp / "out"
    dest.mkdir()
    try:
        publish_card.make_thumb(tmp, dest)
        assert False, "缺少 hero.png 时应抛 FileNotFoundError"
    except FileNotFoundError:
        pass
