#!/usr/bin/env python3
"""
submit_card.py — 公共投稿管线入口（GitHub Actions 调用）

从 Issue 的结构化 body 解析用户投稿 → 自动审核 → 生成 4 层图 →
Blender 构建 3D 卡 → 压缩素材 + 渲染 preview.webm → 更新 cards.json。

用法（Actions 内）：
    python scripts/submit_card.py \
        --body  /tmp/issue-body.txt \
        --idea  "一句话创意" \
        --lang  zh|en|de \
        --author "GitHub 用户名" \
        --repo  Elijah-Lin-Dancer/Holo-Card-Studio \
        --outdir generator/projects

成功：stdout 输出 JSON {"ok": true, "card_id": ..., "url": ...}
失败：stdout 输出 JSON {"ok": false, "error": "人类可读原因"}（exit 1）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
GALLERY = ROOT / "gallery"

# --------------------------------------------------------------------------
# 审核：黑名单（保守类别：暴力/色情/毒品/违禁品制造/极端主义）
# 只做第一道闸，豆包图片 API 自带内容审核为第二道闸。
# --------------------------------------------------------------------------
BLOCKED = [
    # 暴力 / 血腥
    "爆炸物制作", "自制炸弹", "暗杀", "人体炸弹", "blood", "gore",
    # 色情 / 露骨
    "色情", "裸露生殖器", "性行为", "porn", "nudity", "explicit sex",
    # 毒品 / 违禁品
    "冰毒", "海洛因", "可卡因", "制毒", "meth", "heroin", "cocaine",
    # 武器制造 / 攻击手段
    "枪支改造", "3d打印枪", "gun printing", "weapon blueprint",
    # 极端主义 / 煽动
    "极端组织招募", "恐怖袭击教程", "jihad manual", "terror instructions",
]

MAX_IDEA = 200      # 一句话 ≤ 200 字符
MAX_DESIGN = 4000   # 详细描述 ≤ 4000 字符
ALLOWED_LANGS = {"zh", "en", "de"}


def parse_body(body: str) -> dict:
    """解析前端 issue 模板的结构化 body：
    ## IDEA / ## LANG / ## DESIGN（兼容大小写与中英前缀）。"""
    out = {"idea": "", "lang": "", "design": ""}
    m = re.search(r"^##\s*IDEA\s*[:：]?\s*(.+)$", body, re.M | re.I)
    if m: out["idea"] = m.group(1).strip()
    m = re.search(r"^##\s*LANG\s*[:：]?\s*(\w+)", body, re.M | re.I)
    if m: out["lang"] = m.group(1).strip().lower()
    m = re.search(r"^##\s*DESIGN\s*[:：]?\s*(.+)$", body, re.M | re.I | re.S)
    if m: out["design"] = m.group(1).strip()
    return out


def slugify(text: str, fallback: str) -> str:
    """生成 ASCII slug：保留字母数字，其余转 '-'; 中文转拼音不可行 → 用 fallback 兜底。"""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    s = re.sub(r"-+", "-", s)
    if len(s) < 3:
        s = fallback
    return s[:40]


def audit(idea: str, design: str, lang: str) -> list[str]:
    """返回违规原因列表；空列表 = 通过。"""
    issues = []
    if not idea.strip():
        issues.append("一句话创意为空")
    if len(idea) > MAX_IDEA:
        issues.append(f"一句话创意超过 {MAX_IDEA} 字符")
    if not design.strip():
        issues.append("详细描述为空")
    if len(design) > MAX_DESIGN:
        issues.append(f"详细描述超过 {MAX_DESIGN} 字符")
    if lang not in ALLOWED_LANGS:
        issues.append(f"语言不受支持（{lang}），仅支持中文/英文/德文")
    text = (idea + "\n" + design).lower()
    for word in BLOCKED:
        if word in text:
            issues.append(f"包含受限内容（匹配敏感词）")
            break
    return issues


def extract_section(design: str, keys: list[str]) -> str:
    """从结构化描述中提取某段（支持中英两种前缀，冒号或空格分隔均可）。"""
    for k in keys:
        m = re.search(re.escape(k) + r"\s*[:：]?\s*([^\n]+)", design)
        if m:
            return m.group(1).strip()
    return ""


def build_config(idea: str, design: str, lang: str, author: str, slug: str) -> dict:
    """把用户 detail 映射为管线 card-config.json（字段契约见 ai_generate.build_prompts）。"""
    identity = extract_section(design, ["【身份锚点】", "[IDENTITY]"])
    subject = extract_section(design, ["主体层", "Subject layer"]) or identity or idea
    background = extract_section(design, ["背景层", "Background layer"]) or "深邃星夜，纵深感拉开，下方 40% 留白"
    palette = extract_section(design, ["色调", "Palette"]) or "鎏金暖调镭射渐变"
    lineart = extract_section(design, ["线稿层", "Line art layer"]) or "沿主体轮廓发光描边，线宽均匀"
    typography = extract_section(design, ["文字层", "Typography layer"]) or ""

    title = (identity.split("·")[0].strip() or idea)[:32].strip()
    style = f"{palette}；{lineart}。收藏卡插画，金色描边排版，适合全息镭射卡面。"
    edition_no = "PUB-" + time.strftime("%Y%m%d") + "-" + slug[:6].upper()

    return {
        "slug": slug,
        "title": title,
        "subtitle": "Public Submission · 公众投稿",
        "technique": "AI Holographic Card · 一句话出卡",
        "tagline": "Community Gallery · 社区画廊",
        "collection": "HoloLab 公众系列 · Public Series",
        "description": (design[:1200] + ("…" if len(design) > 1200 else "")),
        "style": style,
        "prompt": subject,
        "subject_desc": subject,
        "background_desc": background,
        "mode": "public",
        "edition": edition_no,
        "author": author,
        "parameters": {"subjectScale": 1.25, "subjectDepth": 0.4, "backgroundDepth": -0.25, "foil": 1.0},
        "safeArea": {"left": 0.04, "right": 0.04, "top": 0.06, "bottom": 0.06},
    }


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 1800) -> tuple[int, str]:
    print("  $", " ".join(str(c) for c in cmd)[:160])
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if p.stdout:
        tail = "\n".join(p.stdout.strip().splitlines()[-4:])
        print("    out:", tail[:300])
    if p.returncode != 0 and p.stderr:
        print("    err:", p.stderr.strip()[-400:])
    return p.returncode, p.stdout


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--body", required=True, help="Issue body 文件路径")
    p.add_argument("--idea", default="", help="一句话创意（覆盖 body 解析）")
    p.add_argument("--lang", default="", help="语言：zh/en/de（覆盖 body 解析）")
    p.add_argument("--author", required=True, help="提交者 GitHub 用户名")
    p.add_argument("--outdir", default=str(ROOT / "generator" / "projects"), help="项目输出目录")
    p.add_argument("--skip-ai", action="store_true", help="跳过 AI 生成（仅测试管线，用占位图）")
    args = p.parse_args(argv)

    out = {"ok": False, "error": ""}
    try:
        raw = Path(args.body).read_text(encoding="utf-8")
        parsed = parse_body(raw)
        idea = args.idea or parsed["idea"]
        lang = args.lang or parsed["lang"]
        design = parsed["design"] or raw  # 无结构化模板时退化为全文

        # ① 审核
        problems = audit(idea, design, lang)
        if problems:
            out["error"] = "审核未通过：\n- " + "\n- ".join(problems)
            print(json.dumps(out, ensure_ascii=False))
            return 1

        # ② 构造项目
        slug = slugify(args.idea, "card-" + args.author.replace("@", "")[:12].lower() or "card")
        project = Path(args.outdir) / slug
        if project.exists():
            shutil.rmtree(project)
        (project / "assets").mkdir(parents=True)
        cfg = build_config(args.idea, design, args.lang, args.author, slug)
        (project / "card-config.json").write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[1/5] 项目 {slug} 已创建，审核通过")

        # ③ Blender（自动下载便携版到 gitignored 的 <ROOT>/tools/，Actions runner 可自给自足）
        blender = ""
        rc, out = run([sys.executable, str(HERE / "ensure_blender.py"), str(ROOT)])
        if rc == 0 and out:
            lines = [l.strip() for l in out.splitlines() if l.strip() and not l.startswith("  $")]
            if lines and Path(lines[-1]).is_file():
                blender = lines[-1]
        if blender:
            print(f"[2/5] Blender: {blender}")
        else:
            print("[2/5] Blender 不可用，跳过 3D 渲染（将只产出平面卡）")

        # ④ AI 生成 4 层图
        ai_cmd = [sys.executable, str(HERE / "ai_generate.py"), "--project", str(project)]
        if not args.skip_ai:
            rc, _ = run(ai_cmd)
            if rc != 0:
                out["error"] = "AI 图片生成失败（可能是内容审核拒绝或额度问题），请检查 Issue 内日志或稍后重试。"
                print(json.dumps(out, ensure_ascii=False))
                return 1
        else:
            print("[3/5] --skip-ai：跳过图片生成（测试模式）")
        print("[3/5] 4 层图就绪")

        # ⑤ 3D 管线 + 发布（压缩、preview.webm、更新 cards.json）
        if blender:
            rc, _ = run([sys.executable, str(HERE / "run_pipeline.py"),
                         "--project", str(project), "--blender", blender])
            if rc != 0:
                out["error"] = "3D 渲染管线失败，请查看 Actions 日志。"
                print(json.dumps(out, ensure_ascii=False))
                return 1
        rc, _ = run([sys.executable, str(HERE / "publish_card.py"),
                     "--project", str(project),
                     "--blender", blender] if blender else
                    [sys.executable, str(HERE / "publish_card.py"),
                     "--project", str(project), "--skip-preview"])
        if rc != 0:
            out["error"] = "发布管线失败（素材压缩/清单更新），请查看 Actions 日志。"
            print(json.dumps(out, ensure_ascii=False))
            return 1

        # ⑥ 输出结果
        manifest = json.loads((GALLERY / "cards.json").read_text(encoding="utf-8"))
        card = next((c for c in manifest["cards"] if c.get("id") == slug), None)
        out = {
            "ok": True,
            "card_id": slug,
            "url": f"https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/cards/{slug}/",
            "title": cfg["title"],
            "collection": cfg["collection"],
            "edition": cfg["edition"],
            "author": args.author,
        }
        print(json.dumps(out, ensure_ascii=False))
        return 0
    except subprocess.TimeoutExpired:
        out["error"] = "管线超时（>30 分钟），请稍后重试。"
    except Exception as e:  # noqa: BLE001
        out["error"] = f"内部错误：{e}"
    print(json.dumps(out, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    sys.exit(main())
