#!/usr/bin/env python3
"""本地四层处理：抠图 subject → 提线稿 → 背景归一化。不调任何 API。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image
from ai_generate import make_subject, make_lineart, CANVAS

CARDS = [
    "shang-fu-hao", "shang-wu-ding", "shang-oracle",
    # 殷商纪 Vol.I 余（004-006）
    "shang-pan-geng", "shang-tang", "shang-yi-yin",
    # 殷商纪 Vol.II 重器（007-009）
    "shang-houmuwu-ding", "shang-fuhao-owl-zun", "shang-four-ram-zun",
    # 殷商纪 Vol.III 文明密码（010-014）
    "shang-dark-bird", "shang-divination", "shang-yin-xu",
    "shang-chariot", "shang-taotie",
    # 罪恶都市 Vol.II 场景文化（057-064）
    "vc-ocean-drive", "vc-starfish-island", "vc-little-havana", "vc-little-haiti",
    "vc-vercetti-estate", "vc-fm-radio", "vc-dockyard", "vc-neon-1986",
    # 殷商纪 Vol.IV 殷末三仁与贤相（015-018）
    "shang-bi-gan", "shang-ji-zi", "shang-wei-zi", "shang-fu-yue",
    # 殷商纪 Vol.V 重器续编（019-022）
    "shang-simuxin-ding", "shang-fuhao-yue", "shang-dragon-tiger-zun", "shang-nipple-ding",
    # 殷商纪 Vol.VI 生活与文字（023-027）
    "shang-cowrie", "shang-millet", "shang-fuhao-jade", "shang-ganzhi", "shang-zhen-ren",
]
ROOT = Path(__file__).resolve().parent.parent  # generator/

def main() -> None:
    for slug in CARDS:
        proj = ROOT / "projects" / slug
        assets = proj / "assets"
        work = proj / "work"
        assets.mkdir(exist_ok=True)

        # 1. 抠图 + 归一化到 CANVAS
        make_subject(work / "subject_ai.png", assets / "subject.png", None)
        print(f"[{slug}] subject.png 完成（含透明 alpha）")

        # 2. 线稿（白底黑线，与主体像素级注册）
        make_lineart(assets / "subject.png", assets / "lineart.png")
        print(f"[{slug}] lineart.png 完成")

        # 3. 背景等比铺满到 CANVAS（空镜直接缩放）
        bg = Image.open(work / "background_ai.png").convert("RGB")
        bg = bg.resize(CANVAS, Image.LANCZOS)
        bg.save(assets / "background.png")
        print(f"[{slug}] background.png 完成 {CANVAS}")

        # 校验四层同尺寸
        for name in ["subject.png", "background.png", "lineart.png"]:
            im = Image.open(assets / name)
            assert im.size == CANVAS, f"{name} 尺寸异常 {im.size}"
        print(f"[{slug}] ✅ 四层尺寸一致（缺 text.png，下一步排版）\n")

if __name__ == "__main__":
    main()
