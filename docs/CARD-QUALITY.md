# Card Quality Gate — 卡片质量门禁（制作必读）

> Every card shipped to the gallery must pass the gates below.
> These rules are **mandatory** for anyone producing cards with this repository —
> whether you run the full AI pipeline, bring your own subject/background artwork,
> or use the Create studio workflow. Skipping a gate means the card ships with a defect.

## 0. 为什么要有这套门禁（背景）

Real user feedback on shipped batches surfaced two recurring defects:

- **缺胳膊少腿 / 肢体残缺** — figure cards occasionally lost an arm or a leg
  (weak generation on complex poses + background-like limbs matted away by rembg).
- **透明化 / 隐形主体** — object & vehicle cards could look "transparent": you
  couldn't see the car at front view, it only appeared after rotation created parallax
  (subject blended into a same-color background + semi-transparent cut-out edges).

Neither is a holographic-card feature. The real features of a holographic card are
**multi-layer parallax (subject / background / text at different depths), light
folding, and rotation** — a card must always read clearly at front view first.

## 1. 五道质量门禁（Five Gates）

### Gate 1 · Prompt locks（生成环节锁死）
- 人物卡 prompt 显式包含：`四肢完整、全身可见、无残缺、无遮挡切割`。
- 器物/车辆卡 prompt 显式包含：`主体与背景强对比，亮色主体配深色背景，
  主体完全不透明、轮廓清晰`。
- 参考 `docs/PROMPT-GUIDE.md` 的通用 prompt 规则；本门禁为硬性追加。

### Gate 2 · Background contrast（背景对比度）
- 背景空镜色调**不得与主体同色系**，避免主体"融入"背景。
- 背景空镜终极配方（最可靠）：
  `极简单色背景：<色A>到<色B>的平滑渐变，没有任何<具象名词>，只有干净的渐变色块`
- 背景 prompt 中**禁止出现任何具象名词**（陶器/烛台/篝火/展柜……），
  名词即召唤意象；文字必须显式写 `没有任何文字` 封锁。

### Gate 3 · Matting self-check（抠图后自检）
- 生成 `subject.png`（rembg 抠图）后检查透明通道：
  肢体/轮廓边缘是否有大面积误抠（孔洞、半透明边缘、整块肢体缺失）。
- 有疑点 → **立即重新生成原图**，不得进入排版与渲染。
- 快速检查示例（Python，需 Pillow）：
  ```python
  from PIL import Image
  im = Image.open("generator/projects/<id>/assets/subject.png").convert("RGBA")
  a = im.getchannel("A").getextrema()          # alpha 范围
  # 半透明像素占比（alpha 介于 1..254）
  half = sum(1 for p in im.getdata() if 0 < p[3] < 255)
  print("alpha range:", a, "| semi-transparent px:", half)
  ```
  人物卡若半透明像素异常偏高或 alpha 存在大片"内部空洞"，视为抠图缺陷。

### Gate 4 · Front-view check（正视角抽检）
- 渲染完成后，**正视角（不旋转）必须能清晰辨认主体**。
- 仅靠旋转视差才显形的卡 = 缺陷，重做主体（回到 Gate 1-2）。
- 检查方式：查看 `generator/projects/<id>/renders/hero.png`
  或发布后的 `gallery/cards/<id>/thumb.jpg` 正面观感。

### Gate 5 · No batch-speed waiver（批量不豁免）
- 批量制作时**不得以"赶批量/提速"为由跳过 Gate 3-4**。
- 单批 5-6 张原图之间预留自检；发现问题当场重生成，拒绝带病入库。

## 2. 特色 vs 缺陷 判定表

| 现象 | 判定 | 说明 |
|---|---|---|
| 旋转/拖动时前景后景分层移动 | ✅ 特色 | 多层视差 parallax |
| 光随角度流动、镭射折光 | ✅ 特色 | light folding / foil |
| 正看人、侧看另一图案 | ✅ 特色 | lenticular dual-image（规划中的扩展） |
| 人物缺胳膊少腿 | ❌ 缺陷 | 生成/抠图问题，重做 |
| 正视角看不见主体（"透明车"） | ❌ 缺陷 | 对比度+抠图问题，重做 |

## 3. 落地位置
- 本规范已接入 `CONTRIBUTING.md`（出卡章节引用）。
- 若使用 CI 渲染流程（`.github/workflows/render-card.yml`），发布前请人工执行
  Gate 3-4；automated matting checks can be added as a future CI job.
