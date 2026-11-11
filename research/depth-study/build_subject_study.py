#!/usr/bin/env python3
"""
build_subject_study.py — 为「大气合成是否被人感知」构造 2AFC 主观实验的全套材料。

产物：
    stimuli/pair_XX_A.jpg / _B.jpg        成对刺激（左/右随机分配前/后版本）
    stimuli/pair_mapping.json             随机化映射（评分用，不展示给被试）
    stimuli/selection.json                入选卡片的客观指标
    主观实验-2AFC.html                    单文件自包含问卷（图片 base64 内嵌，可直接发人）
    analyze_subjective.py                 评分脚本

设计：
    强改善组 8 张（ΔSR 最大） + 近乎无效组 8 张（ΔSR 最小，含倒挂卡）
    ⇒ 若被试真能感知，强改善组的「选后版」比例应显著高于弱改善组；
      若两组都接近 50%，说明 SR 这个客观指标与感知脱钩——这正是要检验的。
"""
import base64
import json
import random
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent        # research/depth-study
REPO = HERE.parents[1]                        # 仓库根目录
OUT = HERE / "subject-study"
DATA = HERE / "data"
sys.path.insert(0, str(REPO / "generator" / "depth"))

N_PER_GROUP = 8
MAX_W = 760
SEED = 20261110


def compose(bg, sub, far, smax, haze_color, use_atm):
    """返回合成图（before: use_atm=False；after: True）。"""
    a = (sub[:, :, 3].astype(np.float32) / 255.0)[..., None]
    if not use_atm:
        base = bg.astype(np.float32)
        out = sub[:, :, :3].astype(np.float32) * a + base * (1 - a)
        return out.clip(0, 255).astype(np.uint8)
    from atmosphere import depth_blur
    sig = np.array([0, 3, 6, 9, 12, 15], dtype=np.float32)
    bg_dof = depth_blur(bg, far * smax, sig)
    h = (far * 0.10)[..., None]
    bg_atm = bg_dof * (1 - h) + haze_color * h
    bg_atm = bg_atm * (1.0 - 0.08 * far[..., None])
    out = sub[:, :, :3].astype(np.float32) * a + bg_atm * (1 - a)
    return out.clip(0, 255).astype(np.uint8)


def main():
    rows = json.loads((DATA / "atmosphere_batch.json").read_text())
    rows = [r for r in rows if r["sigma"]["12"]["SR"] > 0]
    for r in rows:
        r["dSR"] = r["sigma"]["12"]["SR"] - r["SR_before"]
    rows.sort(key=lambda r: -r["dSR"])
    strong = rows[:N_PER_GROUP]
    weak = sorted(rows, key=lambda r: r["dSR"])[:N_PER_GROUP]

    from estimate_depth import estimate, load_session
    sess = load_session()

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "stimuli").mkdir(exist_ok=True)
    mapping, selection = [], []

    # 组内左右平衡：每组恰好 4 个「后版在左」、4 个在右，避免位置与组别混淆
    LEFT_PLAN = {}
    for group, cards in (("strong", strong), ("weak", weak)):
        flags = [True, True, True, True, False, False, False, False]
        random.Random(SEED + (0 if group == "strong" else 97)).shuffle(flags)
        LEFT_PLAN[group] = flags

    for group, cards in (("strong", strong), ("weak", weak)):
        for k, r in enumerate(cards):
            proj = REPO / "generator" / "projects" / r["project"]
            bg = cv2.imread(str(proj / "assets" / "background.png"), cv2.IMREAD_COLOR)
            sub = cv2.imread(str(proj / "assets" / "subject.png"), cv2.IMREAD_UNCHANGED)
            if bg is None or sub is None or sub.shape[:2] != bg.shape[:2]:
                continue
            depth, _ = estimate(sess, proj / "assets" / "background.png")
            alpha = sub[:, :, 3].astype(np.float32) / 255.0
            d_focus = min(float(np.median(depth[alpha > 0.1])) + 0.06, 0.98)
            far = np.clip((d_focus - depth) / max(d_focus, 1e-3), 0, 1)
            far = np.clip(cv2.GaussianBlur(far.astype(np.float32), (0, 0), 6), 0, 1)
            far_px = depth <= np.percentile(depth, 25)
            haze = (np.median(bg[far_px].reshape(-1, 3), axis=0).astype(np.float32)
                    if far_px.sum() > 1000 else np.array([196, 210, 224], np.float32))

            before = compose(bg, sub, far, 12.0, haze, use_atm=False)
            after = compose(bg, sub, far, 12.0, haze, use_atm=True)

            # 可见变化量：背景区的平均像素差（衡量「改动看不看得见」，与 ΔSR 不是一回事）
            bg_m = alpha < 0.05
            pixel_delta = float(np.abs(after.astype(np.float32) - before.astype(np.float32))[bg_m].mean())

            sc = MAX_W / before.shape[1]
            nh = int(before.shape[0] * sc)
            before = cv2.resize(before, (MAX_W, nh), interpolation=cv2.INTER_AREA)
            after = cv2.resize(after, (MAX_W, nh), interpolation=cv2.INTER_AREA)

            pid = f"pair_{len(mapping)+1:02d}"
            after_on_left = LEFT_PLAN[group][k]
            left, right = (after, before) if after_on_left else (before, after)
            cv2.imwrite(str(OUT / "stimuli" / f"{pid}_A.jpg"), left, [cv2.IMWRITE_JPEG_QUALITY, 88])
            cv2.imwrite(str(OUT / "stimuli" / f"{pid}_B.jpg"), right, [cv2.IMWRITE_JPEG_QUALITY, 88])

            mapping.append({"pair_id": pid, "group": group, "project": r["project"],
                            "after_on_left": after_on_left})
            selection.append({"pair_id": pid, "group": group, "project": r["project"],
                              "SR_before": r["SR_before"], "SR_after": r["sigma"]["12"]["SR"],
                              "dSR": round(r["dSR"], 3), "far_mean": r["far_mean"],
                              "S_bg_before": r["S_bg_before"],
                              "pixel_delta": round(pixel_delta, 2)})
            print(f"{pid} [{group:6s}] {r['project']:24s} ΔSR={r['dSR']:+6.2f} far={r['far_mean']:.3f}")

    (OUT / "stimuli" / "pair_mapping.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "stimuli" / "selection.json").write_text(json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------- 生成自包含 HTML ----------
    def b64(p):
        return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()

    items = []
    for m in mapping:
        items.append({"id": m["pair_id"],
                      "a": b64(OUT / "stimuli" / f"{m['pair_id']}_A.jpg"),
                      "b": b64(OUT / "stimuli" / f"{m['pair_id']}_B.jpg")})

    html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>卡片层次感知测试</title>
<style>
:root{--ink:#1c1c1e;--muted:#8a8a8e;--line:#e5e5ea;--accent:#2f5d8a;--bg:#fafaf7}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:960px;margin:0 auto;padding:24px 18px 64px}
h1{font-size:19px;margin:0 0 6px}
.sub{color:var(--muted);font-size:13px;margin-bottom:20px}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:18px}
.q{font-size:14px;font-weight:600;margin:0 0 10px}
.pair{display:flex;gap:10px}
.opt{flex:1;cursor:pointer;border:2px solid transparent;border-radius:10px;padding:6px;text-align:center;transition:.15s}
.opt:hover{border-color:#cfd8e3}
.opt.sel{border-color:var(--accent);background:#eef3f9}
.opt img{width:100%;border-radius:6px;display:block}
.opt span{display:inline-block;margin-top:6px;font-size:13px;font-weight:600;color:var(--accent)}
.nodiff{display:block;width:100%;margin-top:10px;padding:9px;border:1px solid var(--line);background:#fff;border-radius:9px;font-size:13px;cursor:pointer}
.nodiff.sel{border-color:var(--accent);background:#eef3f9}
.prog{position:sticky;top:0;background:var(--bg);padding:10px 0;font-size:13px;color:var(--muted);z-index:9}
button.go{width:100%;padding:14px;border:0;border-radius:12px;background:var(--accent);color:#fff;font-size:16px;font-weight:600;cursor:pointer}
button.go:disabled{opacity:.45;cursor:not-allowed}
.hide{display:none}
@media(max-width:700px){.pair{flex-direction:column}}
</style></head><body><div class="wrap">
<h1>卡片层次感知测试</h1>
<div class="sub">每次给你一组两张卡（A / B），问哪一张的<b>主体更清楚地浮在背景之前</b>。约 3 分钟，16 组。没有正确答案，凭第一感觉即可。</div>
<div class="card" id="intro">
  <div class="q">先填一个匿名编号（随便写，比如你的首字母+数字，用于去重）</div>
  <input id="pid" placeholder="例：ZL07" style="width:100%;padding:11px;border:1px solid var(--line);border-radius:9px;font-size:15px">
  <div class="q" style="margin-top:16px">你的观感经验（可多选，不影响结果）</div>
  <label style="display:block;font-size:14px"><input type="checkbox" class="exp" value="design"> 做设计 / 摄影相关</label>
  <label style="display:block;font-size:14px"><input type="checkbox" class="exp" value="3d"> 接触过 3D / 全息 / 立体显示</label>
  <label style="display:block;font-size:14px"><input type="checkbox" class="exp" value="none"> 都没有</label>
  <button class="go" style="margin-top:16px" onclick="start()">开始</button>
</div>
<div id="stage" class="hide"></div>
</div>
<script>
const ITEMS = __ITEMS__;
let idx=0, answers=[], t0=0, pid="", exp=[];
function start(){
  pid=document.getElementById('pid').value.trim()||("anon"+Math.random().toString(36).slice(2,7));
  exp=[...document.querySelectorAll('.exp:checked')].map(e=>e.value);
  document.getElementById('intro').classList.add('hide');
  document.getElementById('stage').classList.remove('hide');
  render();
}
function render(){
  const it=ITEMS[idx]; t0=performance.now();
  const html=`<div class="prog">第 ${idx+1} / ${ITEMS.length} 组</div>
  <div class="card">
    <div class="q">哪一张的主体更清楚地浮在背景之前（更有层次感）？</div>
    <div class="pair">
      <div class="opt" data-c="A" onclick="pick('A')"><img src="${it.a}"><span>A</span></div>
      <div class="opt" data-c="B" onclick="pick('B')"><img src="${it.b}"><span>B</span></div>
    </div>
    <button class="nodiff" data-c="same" onclick="pick('same')">看不出区别 / 都一样</button>
  </div>`;
  document.getElementById('stage').innerHTML=html;
}
function pick(c){
  document.querySelectorAll('.opt,.nodiff').forEach(e=>e.classList.remove('sel'));
  document.querySelector(`[data-c="${c}"]`).classList.add('sel');
  answers[idx]={id:ITEMS[idx].id, choice:c, rt_ms:Math.round(performance.now()-t0)};
  setTimeout(()=>{
    idx++;
    if(idx<ITEMS.length){render();}else{finish();}
  },260);
}
function finish(){
  localStorage.setItem('holo_2afc_'+pid, JSON.stringify({pid, exp, answers}));
  document.getElementById('stage').innerHTML=`<div class="card">
    <div class="q">已完成，谢谢！</div>
    <div class="sub">把下面这段结果复制发回给发起人即可（无需截图）。</div>
    <textarea style="width:100%;height:150px;font:12px/1.5 monospace;padding:10px;border:1px solid var(--line);border-radius:9px" onclick="this.select()">${JSON.stringify({pid, exp, answers})}</textarea>
    <button class="go" style="margin-top:12px" onclick="dl()">下载 CSV</button>
  </div>`;
  window.__RESULT={pid, exp, answers};
}
function dl(){
  const r=window.__RESULT;
  const lines=["pid,exp,pair_id,choice,rt_ms"].concat(r.answers.map(a=>[r.pid,'"'+r.exp.join(';')+'"',a.id,a.choice,a.rt_ms].join(',')));
  const blob=new Blob([lines.join('\\n')],{type:'text/csv;charset=utf-8'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='2afc_'+r.pid+'.csv';a.click();
}
</script></body></html>"""
    html = html.replace("__ITEMS__", json.dumps(items, ensure_ascii=False))
    (OUT / "主观实验-2AFC.html").write_text(html, encoding="utf-8")
    print(f"\nHTML 生成完成：{OUT/'主观实验-2AFC.html'}  ({len(items)} 组, {len(html)/1e6:.1f}MB)")


if __name__ == "__main__":
    main()
