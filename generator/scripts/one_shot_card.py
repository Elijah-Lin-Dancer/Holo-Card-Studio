#!/usr/bin/env python3
"""
one_shot_card.py — 一句话自动出卡（One-Sentence Card Generator）

用户输入一句话，Doubao-Seed-2.1-lite 自动生成 card-config.json，
输出到 generator/projects/<slug>/，随后可接现有流水线出卡：

    python scripts/ai_generate.py projects/<slug> [--model doubao-seedream-5-0-flash-260915]
    python scripts/run_pipeline.py  projects/<slug>
    python scripts/publish_card.py  projects/<slug>

用法：
    python scripts/one_shot_card.py "给中国航天员设计一张全息收藏卡"
选项：
    --outdir <dir>    指定输出目录（默认按模型给出的 slug 自动创建）
    --model <id>      覆盖文字模型（默认 doubao-seed-2-1-lite-260915）
    --skip-fetch      仅校验已有 config，不调用模型（开发调试用）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # generator/
DEFAULT_MODEL = "doubao-seed-2-0-mini-260428"
API_BASE = os.environ.get("ARK_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")

SYSTEM_PROMPT = """你是 HoloLab Studio 的全息收藏卡创意总监。用户会给你一句话，你要把它变成一张收藏卡的完整配置。

输出必须是合法 JSON，字段如下（全部必填）：
- "slug": 英文小写 slug，字母/数字/连字符，如 "taikonaut-odyssey"（用于文件夹与 URL）
- "title": 中文主标题，4-8 个字，像卡面大字
- "subtitle": 中文/英文混合副标题，不超过 20 字，如 "出征 · 星辰大海"
- "technique": 技能名，2-4 个字的意境词，如 "潘帕斯雄鹰"、"月球漫步"
- "tagline": 一句口号，不超过 16 个字
- "collection": 合集名，格式 "HoloLab 典藏 · XXX系列"
- "description": 两句介绍，不超过 60 个字
- "style": 视觉风格，沿用 "日式浮世绘与水墨动漫勾勒的收藏卡插画，矿物颜料质感，笔触清晰" 并可按主题微调（如加"星空、夜景"）
- "prompt": 一句话概括主体画面（给生图模型看，主谓宾清楚）
- "subject_desc": 主体细节描述：主体是谁、姿态、服饰、表情、位置（用于生成透明主体层，需可单独成图）
- "background_desc": 背景细节描述：场景、氛围、光线；必须包含"画面中下部留出安静空间，不出现人物"（用于生成背景层）

质量要求：内容准确、不夸大事实；涉及真实人物时只写客观身份与标志性特征，不编造事件；title 要响亮，technique 要有意境。只输出 JSON，不要任何其他文字。"""


REQUIRED_KEYS = [
    "slug", "title", "subtitle", "technique", "tagline",
    "collection", "description", "style", "prompt", "subject_desc", "background_desc",
]


def call_llm(user_input: str, model: str, api_key: str, max_retries: int = 4) -> str:
    """调用文字模型，返回模型输出的原始文本。

    服务端偶发限流断连（RemoteDisconnected / 5xx / 429），
    采用指数退避重试，最多 max_retries 次。
    """
    import time as _time

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
        "max_tokens": 1500,
    }
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(
            f"{API_BASE}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except Exception as exc:  # 网络断连/超时/5xx/限流均可重试
            last_err = exc
            if attempt < max_retries:
                _time.sleep(2 * attempt)  # 2s, 4s, 6s 退避
    raise RuntimeError(f"文字模型调用失败（{max_retries} 次重试后）：{last_err}") from last_err


def extract_json(text: str) -> dict:
    """从模型输出中提取 JSON（容忍 ```json 围栏与前后杂质）。"""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def validate(cfg: dict) -> list[str]:
    """校验配置，返回问题列表（空列表 = 通过）。"""
    problems = []
    for key in REQUIRED_KEYS:
        val = cfg.get(key)
        if not isinstance(val, str) or not val.strip():
            problems.append(f"缺字段/为空：{key}")
            continue
        if key == "slug" and not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", val):
            problems.append(f"slug 不合法：{val!r}（需小写字母/数字/连字符，3-64 字符）")
        if key == "title" and not (2 <= len(val) <= 12):
            problems.append(f"title 长度异常：{val!r}（建议 4-8 字）")
        if key == "tagline" and len(val) > 24:
            problems.append(f"tagline 过长：{val!r}")
        if key == "description" and len(val) > 120:
            problems.append(f"description 过长：{val!r}")
        if key == "background_desc" and "不出现人物" not in val:
            problems.append(f"background_desc 缺 '不出现人物' 约束：{val!r}")
    return problems


def default_params() -> dict:
    """与现有卡片一致的默认渲染参数。"""
    return {
        "parameters": {
            "subjectScale": 1.25,
            "subjectDepth": 0.4,
            "backgroundDepth": -0.25,
            "foil": 1.0,
        },
        "safeArea": {"scale": 1.12, "offset": [-0.06, -0.085]},
    }


def next_edition() -> str:
    """根据 gallery 现有卡数生成 edition，如 003 / 003。"""
    gallery = ROOT.parent / "gallery" / "cards.json"
    count = 0
    if gallery.exists():
        try:
            count = len(json.loads(gallery.read_text(encoding="utf-8")).get("cards", []))
        except Exception:
            pass
    n = count + 1
    return f"{n:03d} / {n:03d}"


def main() -> int:
    parser = argparse.ArgumentParser(description="一句话自动出卡（One-Sentence Card Generator）")
    parser.add_argument("sentence", help="一句话主题，如：给中国航天员设计一张全息收藏卡")
    parser.add_argument("--outdir", default=None, help="输出目录（默认 projects/<slug>）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"文字模型 ID（默认 {DEFAULT_MODEL}）")
    parser.add_argument("--skip-fetch", action="store_true", help="跳过模型调用，仅校验已有配置")
    args = parser.parse_args()

    api_key = os.environ.get("ARK_API_KEY", "")
    if not args.skip_fetch and not api_key:
        print("错误：环境变量 ARK_API_KEY 未设置（可 source 项目 .env）", file=sys.stderr)
        return 2

    if args.skip_fetch:
        outdir = Path(args.outdir) if args.outdir else None
        if not outdir:
            print("错误：--skip-fetch 需要 --outdir 指向已有配置目录", file=sys.stderr)
            return 2
        cfg = json.loads((outdir / "card-config.json").read_text(encoding="utf-8"))
    else:
        print(f"[1/3] 调用文字模型 {args.model} 生成配置…")
        raw = call_llm(args.sentence, args.model, api_key)
        cfg = extract_json(raw)

    problems = validate(cfg)
    if problems:
        print("校验未通过：", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print(f"模型输出原文（供排查）：\n{json.dumps(cfg, ensure_ascii=False, indent=2)}", file=sys.stderr)
        return 1

    cfg["mode"] = "holographic"
    cfg["edition"] = next_edition()
    cfg.update(default_params())

    slug = cfg["slug"]
    outdir = Path(args.outdir) if args.outdir else (ROOT / "projects" / slug)
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "card-config.json"
    out.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[2/3] 校验通过 → {out}")
    print(f"      主题：{cfg['title']}｜{cfg['subtitle']}｜{cfg['technique']}｜{cfg['collection']}")
    print(f"[3/3] 接下来跑流水线出卡：")
    print(f"  python scripts/ai_generate.py projects/{slug} --model doubao-seedream-5-0-flash-260915")
    print(f"  python scripts/run_pipeline.py projects/{slug}")
    print(f"  python scripts/publish_card.py projects/{slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
