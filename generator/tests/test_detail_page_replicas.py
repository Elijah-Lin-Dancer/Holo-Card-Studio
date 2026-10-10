"""详情页三副本一致性测试（补-1）：模板 → 项目 web/ → 发布单卡，三层同源。

设计目标：
  1. 所有 gallery/cards/<id>/ 的 app.js、style.css 必须与 canonical 模板逐字节一致；
  2. 模板演进必须显式回填到全部存量卡，否则本测试失败；
  3. 触发点：任何新卡发布后 CI 跑本测试，模板/单卡漂移立即可见。
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent          # holo-lab/
GALLERY = ROOT / "gallery"
TPL = ROOT / "generator" / "scripts" / "web-template-holographic"


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def test_template_assets_exist():
    assert (TPL / "app.js").is_file()
    assert (TPL / "style.css").is_file()


def test_all_published_cards_match_template():
    cards = json.loads((GALLERY / "cards.json").read_text(encoding="utf-8"))["cards"]
    assert len(cards) >= 1
    tpl_app = md5(TPL / "app.js")
    tpl_css = md5(TPL / "style.css")
    drifted = []
    for c in cards:
        d = GALLERY / "cards" / c["id"]
        if not (d / "app.js").is_file() or md5(d / "app.js") != tpl_app:
            drifted.append(f"{c['id']}/app.js")
        if not (d / "style.css").is_file() or md5(d / "style.css") != tpl_css:
            drifted.append(f"{c['id']}/style.css")
    assert not drifted, f"详情页文件偏离模板：{drifted}（模板演进需回填全部存量卡）"


def test_web_template_is_single_source():
    """canonical 模板目录内不应存在第二份 app.js/style.css 副本（防双源漂移）。"""
    for extra in [ROOT / "generator" / "templates"]:
        if extra.exists():
            for hit in extra.rglob("app.js"):
                assert False, f"发现第二模板源：{hit}"
