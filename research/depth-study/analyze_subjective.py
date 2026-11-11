#!/usr/bin/env python3
"""
analyze_subjective.py — 2AFC 主观实验的评分与统计。

输入：
    subject-study/stimuli/pair_mapping.json   每个 pair 的「后版在左还是在右」
    subject-study/stimuli/selection.json      每个 pair 的客观指标（ΔSR 等）
    被试结果（任选其一）：
        --data <目录>     目录下所有 CSV（问卷页「下载 CSV」产出）
        --paste <文件>    粘贴回来的 JSON 文本（问卷页 textarea 产出）

输出：
    每个 pair 的「选后版」比例
    强改善组 vs 弱改善组的二项检验（H0: p = 0.5）
    ΔSR 与「选后版」比例的 Spearman 相关
    「看不出区别」的比例

用法：
    python3 analyze_subjective.py --data results/
"""
import argparse
import csv
import json
from pathlib import Path

from scipy.stats import binomtest, spearmanr

STUDY = Path(__file__).resolve().parent / "subject-study"


def load_mapping():
    m = json.loads((STUDY / "stimuli" / "pair_mapping.json").read_text(encoding="utf-8"))
    sel = json.loads((STUDY / "stimuli" / "selection.json").read_text(encoding="utf-8"))
    return {r["pair_id"]: r for r in m}, {r["pair_id"]: r for r in sel}


def parse_csv(path):
    out = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            out.append({"pid": row["pid"], "pair_id": row["pair_id"],
                        "choice": row["choice"], "rt_ms": int(row.get("rt_ms") or 0)})
    return out


def parse_paste(path):
    raw = Path(path).read_text(encoding="utf-8").strip()
    data = json.loads(raw)
    if "answers" not in data:
        raise ValueError("粘贴内容里没有 answers 字段")
    return [{"pid": data.get("pid", "?"), "pair_id": a["id"],
             "choice": a["choice"], "rt_ms": int(a.get("rt_ms") or 0)}
            for a in data["answers"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", help="存放 CSV 的目录")
    ap.add_argument("--paste", help="粘贴回来的 JSON 文件")
    ap.add_argument("--min-rt", type=int, default=300, help="低于此反应时的作答视为无效")
    a = ap.parse_args()

    mapping, sel = load_mapping()

    recs = []
    if a.data:
        for p in sorted(Path(a.data).glob("*.csv")):
            recs += parse_csv(p)
    if a.paste:
        recs += parse_paste(a.paste)
    if not recs:
        raise SystemExit("没有读到任何作答。先让被试把 CSV 或 JSON 发回来，放进 results/ 目录。")

    # 反应时过滤
    n_raw = len(recs)
    recs = [r for r in recs if r["rt_ms"] >= a.min_rt]
    print(f"作答 {n_raw} 条，剔除过快（<{a.min_rt}ms）后剩 {len(recs)} 条\n")

    pids = sorted({r["pid"] for r in recs})
    print(f"被试数：{len(pids)}")

    # 配对 → 是否选中「后版」
    by_pair = {}
    same_cnt = {"strong": 0, "weak": 0}
    for r in recs:
        mp = mapping[r["pair_id"]]
        grp = mp["group"]
        if r["choice"] == "same":
            same_cnt[grp] += 1
            continue
        picked_after = (r["choice"] == "A") == mp["after_on_left"]
        by_pair.setdefault(r["pair_id"], {"strong": [], "weak": []})
        by_pair[r["pair_id"]][grp].append(1 if picked_after else 0)

    print(f"\n{'pair':<9}{'组':<8}{'项目':<24}{'n':>4}{'选后版':>9}{'ΔSR':>8}")
    print("-" * 68)
    rows = []
    for pid, v in sorted(by_pair.items()):
        grp = mapping[pid]["group"]
        arr = v[grp]
        if not arr:
            continue
        p_after = sum(arr) / len(arr)
        rows.append({"pair_id": pid, "group": grp, "project": mapping[pid]["project"],
                     "n": len(arr), "p_after": p_after, "dSR": sel[pid]["dSR"],
                     "pixel_delta": sel[pid]["pixel_delta"]})
        print(f"{pid:<9}{grp:<8}{mapping[pid]['project']:<24}{len(arr):>4}{p_after:>8.1%}{sel[pid]['dSR']:>+8.2f}")

    # 分组检验
    print("\n== 分组二项检验（H0: 选后版比例 = 0.5）==")
    for grp in ("strong", "weak"):
        arr = [x for r in rows if r["group"] == grp for x in by_pair[r["pair_id"]][grp]]
        if not arr:
            continue
        k, n = sum(arr), len(arr)
        p = binomtest(k, n, 0.5).pvalue
        print(f"  {grp:7s} 选后版 {k}/{n} = {k/n:.1%}   p = {p:.4f}   "
              f"{'显著' if p < 0.05 else '不显著'}")

    # 与 ΔSR / 像素变化量的相关（核心问题：感知由谁预测）
    if len(rows) >= 5:
        y = [r["p_after"] for r in rows]
        rho_s, p_s = spearmanr([r["dSR"] for r in rows], y)
        rho_p, p_p = spearmanr([r["pixel_delta"] for r in rows], y)
        print("\n== 感知由什么预测（主分析）==")
        print(f"  Spearman(ΔSR, 选后版比例)        = {rho_s:+.3f}   p = {p_s:.4f}")
        print(f"  Spearman(像素变化量, 选后版比例) = {rho_p:+.3f}   p = {p_p:.4f}")
        if max(abs(rho_s), abs(rho_p)) < 0.3:
            print("  → 两个客观指标都没能预测感知，需重新设计量度（建议改用 JND 阈值法或直接主观评分）")
        elif abs(rho_p) > abs(rho_s) + 0.15:
            print("  → 感知主要由改动幅度驱动，SR 只是统计量、不代表可见性；论文不应再用 SR 作效果证据")
        elif abs(rho_s) > abs(rho_p) + 0.15:
            print("  → 感知确实跟随锐度分离（SR 可用），即使像素变化量不大")
        else:
            print("  → 两者接近，需更大样本或更极端刺激才能区分")

    # 「看不出区别」
    total = len(recs)
    s_rate = (same_cnt['strong'] + same_cnt['weak']) / total if total else 0
    print(f"\n== 「看不出区别」占比 {s_rate:.1%}"
          f"（强改善组 {same_cnt['strong']} 次 / 弱改善组 {same_cnt['weak']} 次）==")
    if s_rate > 0.4:
        print("  → 差异对被试不可辨，说明当前参数下效果过弱，需加强或换刺激。")


if __name__ == "__main__":
    main()
