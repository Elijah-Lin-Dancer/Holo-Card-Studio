"""资源齐全性：每张卡的 web 三件套、四层贴图、GLB、thumb、preview 全部存在且非空。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent   # holo-lab/
GALLERY = ROOT / "gallery"

FILES = ["index.html", "app.js", "style.css", "card-config.json",
         "assets/subject.webp", "assets/background.webp",
         "assets/lineart.webp", "assets/text.webp", "assets/card.glb",
         "thumb.jpg"]

GLB_MAGIC = b"glTF"


def manifest_ids():
    m = json.loads((GALLERY / "cards.json").read_text(encoding="utf-8"))
    return [c["id"] for c in m["cards"]]


def test_all_cards_have_all_assets():
    missing = []
    for cid in manifest_ids():
        base = GALLERY / "cards" / cid
        for f in FILES:
            p = base / f
            if not p.exists() or p.stat().st_size == 0:
                missing.append(f"{cid}/{f}")
    assert not missing, f"缺失或空文件: {missing}"


def test_glb_is_valid_gltf():
    bad = []
    for cid in manifest_ids():
        glb = GALLERY / "cards" / cid / "assets" / "card.glb"
        if glb.exists():
            head = glb.read_bytes()[:4]
            if head != GLB_MAGIC:
                bad.append(f"{cid}: GLB 魔数错误 {head!r}")
    assert not bad, bad


def test_thumb_is_jpeg():
    bad = []
    for cid in manifest_ids():
        th = GALLERY / "cards" / cid / "thumb.jpg"
        if th.exists() and th.read_bytes()[:2] != b"\xff\xd8":
            bad.append(cid)
    assert not bad, f"thumb 非 JPEG: {bad}"


def test_vendor_exists():
    for v in ("three/build/three.module.js", "gsap/gsap.min.js"):
        p = GALLERY / "vendor" / v
        assert p.exists(), f"共享 vendor 缺失：{v}"
