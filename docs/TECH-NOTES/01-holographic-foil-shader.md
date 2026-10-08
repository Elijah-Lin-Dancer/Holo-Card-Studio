# 技术笔记 ① · From Art Approximation to Physical Optics: A Holographic Foil Shader
# Tech Note ① · 从美术近似到物理仿真：全息箔片着色器

> 主线 ① 收官笔记（A-1 → A-4）· 中英双语
> 设计文档见 `docs/GRAPHICS/HOLO-OPTICS.md`（公式推导）；本文讲"我们为什么这么做、踩了什么坑、数字证明到什么程度"。

---

## 1. 为什么要做这个 / Why we did this

我们卡片上的"全息彩虹"原本是美术近似：一张彩虹渐变贴图，靠 UV 偏移或粗糙度扫过表面。效果够用，但有两个讲不出口的问题：

- 彩虹不会随视角**物理移动**——真实镭射卡侧过来看，色带位置会变；
- 每一张卡的"彩虹参数"没有数字定义——工艺名是独有的，光学却是同一张贴图，名实不符。

于是我们把这一层从"贴图"换成"计算"：用真实镭射卡的**薄膜干涉 + 光栅衍射**物理模型着色。这不是炫技，是给每一张卡一个可审计的"光学指纹"：`foil` 参数块（膜厚、折射率、光栅周期、槽方向、粗糙度）写进 `card-config.json`，每卡一组，与独特工艺名打通。

---

## 2. 物理模型三件套 / The physics in three equations

完整推导在 `HOLO-OPTICS.md`，这里只讲"为什么是这三个公式"。

### 2.1 薄膜干涉：色散的基底 / Thin-film interference: the dispersive base

全息箔的彩虹底色来自折射率 n、厚度 d 的薄膜：上下表面两束反射光干涉，相位差

```
φ(λ) = (2π/λ)·2·n·d·cosθₜ
```

θₜ 是膜内折射角（斯涅尔定律给出）。加上上表面反射的半波损失，反射率

```
R_f(λ) = 0.5·(1 − cos φ)
```

一句话：**同一视角下，不同波长反射率不同**——这就是色散（颜色随膜厚、随角度变化）的来源。厚度 d 是每卡指纹的核心旋钮。

### 2.2 光栅衍射：方向性的彩虹 / Diffraction grating: the directional rainbow

镭射卡的彩虹为什么是"一条带"而不是"一片糊"？因为表面有微米级周期光栅：光栅方程

```
mλ = Λ(sinθᵢ ± sinθₘ)
```

把不同波长的出射方向分开。我们不做完整的光栅追迹，只取其**光谱位移近似**：沿槽方向 v 的色散系数

```
Δλ ∝ (λ_norm − v·k_disp)
```

像素所在位置的法线投影到视向量、再投影到槽方向，得到一个带号 v——彩虹随视角平移就来自这里。槽方向 `grooveDir` 决定彩虹朝哪个方向动，是第二个指纹旋钮。

### 2.3 微表面权重：什么时候是彩虹、什么时候是镜面 / Microfacet weighting: when rainbow, when mirror

真实箔片不是纯光栅——还有随机微表面散射。我们用一条经验权重

```
w_grating = gain·(1−rough)·(0.35 + 0.65·grazingᵗ)
```

把贡献拆成"光栅彩虹"与"薄膜镜面"两项加权混合。roughness 低 → 彩虹锐利；grazing 视角 → 彩虹变强（真实箔片侧看更亮）。第三个指纹旋钮。

**模型是三个公式的乘积和，不是一张图**——这是与美术近似的本质区别。

---

## 3. 三条实现路径 / Three implementations, one math

同一套数学，我们写了三条实现，互为真值：

| 路径 | 语言/载体 | 用途 |
|---|---|---|
| `proto_render.py` | numpy（软件参考模型） | 真值模型：球面法线网格 + 视角/参数变体，秒级出图 |
| `build_foil_nodegroup.py` | Blender Cycles 节点树 | 离线渲染线：卡片真实渲染时使用 |
| `foil_holographic.glsl` | GLSL ES 300 | 详情页交互预览（后续接入） |

选择 Node Group 而不是 OSL 的原因见 §5 踩坑实录——不是我们不想用 OSL，是环境把它干掉了。

### 3.1 numpy 参考模型：先证明数学是对的 / numpy reference: prove the math first

动手写 Blender 之前，先在 numpy 里把公式原样实现：512² 网格、每个像素一组 (N, V)，算 w_band → w_spec → 按 CIE 权重累加 6 波长 → 归一化。验证内容：

- 同参数重渲两次 → 像素级差异 **0.000000**（确定性 ✓）
- azimuth 30°→60° → 整图均差 0.0217（彩虹随视角移动 ✓）
- 相机俯仰 0→0.5rad → 均差 0.0676（视角驱动 ✓）

数学在软件里成立，才值得搬进渲染器。

### 3.2 6 波长 vs 3 通道：一个"省事"差点毁掉精度 / 6 wavelengths vs 3 channels

第一版 Node Group 图省事，每通道固定一个波长（R=650/G=545/B=440）。numpy 复刻后对照参考模型：

```
3 通道近似：ΔE76 mean = 27.9~38.5，>8 占比 100%   ← 不合格
6 波长精确：ΔE76 mean = 0.000，>8 占比 0%          ← 合格
```

原因不神秘：3 通道里 R 通道只有 650nm 一个采样，而红端光栅带在大多数像素上强度接近 0 → 红色整片缺失，画面偏青蓝。**6 波长（380/444/508/572/636/700nm）按 CIE 四段线性权重累加再归一化**，才和真实光谱足够接近。教训：物理仿真没有"省两个采样"这种操作。

### 3.3 GLSL 移植：逐行等值执行 / GLSL port: line-by-line equivalence

GLSL 版没有急着接进页面，先做了一件事：写 `glsl_equivalence.py`，**把 GLSL 源码的公式逐行在 numpy 里执行**，与参考模型输出对照：

```
default        ΔE76 = 0.000  >8 占比 0%
view (θ=0.4)   ΔE76 = 0.000  >8 占比 0%
thick (420nm)  ΔE76 = 0.000  >8 占比 0%
```

顺带抓出我自己 GLSL 初版的 `wavelengthToRGB` 写错（用了三段近似，与 CIE 四段不一致）——**数值等价检查是移植正确性的唯一标准，语法通过不算数**。

---

## 4. 验收数据 / Acceptance data

RFC 的验收协议：同视角下实现 vs 参考模型 ΔE76 < 8。

| 实现 | 场景 | ΔE76 | 结论 |
|---|---|---|---|
| GLSL（等值执行） | default / θ=0.4 / d=420 | 0.000 | ✅ |
| Node Group 6 波长（Blender 真机渲染） | 中心像素，Standard 域 | **4.656** | ✅ < 8 |
| Node Group 3 通道（历史版） | 同上 | 31~38 | ❌ 已弃 |

Blender 侧 4.656 的残差来源是工程性的：8bit PNG 量化 + 24 采样降噪残留 + sRGB 编码往返——不是数学偏差。视角驱动验证：正视角 vs 旋转 30° 整图平均色差 0.033，色带随视角位移肉眼可见。

---

## 5. 踩坑实录（按时间顺序） / War stories (chronological)

> 这些坑每个都花过 1–3 轮真机调试。写下来，是给"下一个做同样事的人"省的。

**坑 1：OSL 运行时缺失——shader 根本没执行**
便携版 Blender 4.5.14 构建时带 OSL 支持（`bpy.app.build_options.cycles_osl=True`），但运行时缺失：常量红 shader 输出全黑，printf 调试无输出，对照组 Emission 正常。折腾三轮定位到"环境缺陷"后，按 RFC 预留的 fallback 走 **Node Group 纯数学实现**。结论：**构建支持 ≠ 运行时可用**，动手前先渲一个常量色 shader 探路。

**坑 2：Blender 4.5 三角函数单位是"度"，不是弧度**
`phase = C·cosθₜ + π` 是弧度，但 Blender Math 节点的 COSINE 按**度**解释输入 → 薄膜项算成了 cos(7.9°)≈0.99 的常量，干涉振荡消失。修复：先过 `DEGREES` 再进 COSINE。这个坑的症状是"颜色整体偏色但结构还在"，非常难定位——最后是靠中心像素 RGB 数值对照，发现 B 通道系统性低 11 才抓到。

**坑 3：手写 CIE 权重表，4 个值算错**
6 波长 CIE 权重（x,y,z）我手写，572nm 写了 0.665、真实值 0.815；700nm 写了 0.92、真实值 0.6。错误权重让 ΔE 停在 8.9（差一点不过线）。修法很朴素：**从 `wavelength_to_rgb` 函数取值，不手算**。

**坑 4：Filmic 视图变换把物理色相压成灰白**
验证渲染时 Blender 默认的 Filmic/AgX tone mapping 会把高动态物理色压暗、饱和度丢失，看起来像"灰白失败"。渲染对照必须 `view_transform='Standard'`，让数值直达。

**坑 5（顺带）：Node Group 3 通道近似不合格 → 升级 6 波长**
见 §3.2。这是唯一一个"看起来成功、数字不通过"的坑。

---

## 6. 工程启示 / What this taught us

1. **参考模型即真值**：先写软件原型证明数学，再搬进两个渲染器——比"两边直接写、肉眼对比"省 10 倍时间。
2. **数值等价是移植正确性的唯一标准**：语法过、能渲出来、颜色像——都不算数；同输入逐像素 ΔE 才算数。
3. **单位、常量表、色彩空间是移植三大杀手**：全部要显式化、自动化（本项目的 `glsl_equivalence.py` / `nodegroup_reference.py` 就是为此而活）。
4. **指纹旋钮已就绪**：`foil` 参数块（thickness / ior / period / grooveDir / roughness / gain / baseReflect）直接进 `card-config.json`——后续每张新卡一组参数 = 独一无二的光学指纹，与独特工艺名打通。

---

## 7. 复现 / Reproduce

```bash
# 参考模型 + 全部 ΔE 对照
python3 generator/foil/glsl_equivalence.py          # GLSL vs 参考：ΔE=0
python3 generator/foil/nodegroup_reference.py       # NG6 vs 参考：ΔE=0；NG3：31-38
python3 generator/foil/proto_render.py              # 软件原型：视角/参数变体 + 旋转序列

# Blender 真机渲染（Node Group 6 波长）
tools/blender-4.5.14-linux-x64/blender -b -P generator/foil/build_foil_nodegroup.py
# 产出 out/foil_ng_front.png（正视角）out/foil_ng_rot30.png（旋转30°）
```

验证图与精度报告：`docs/GRAPHICS/`（rot_seq.gif / foil_ng_compare.png / PROOF-A3-PRECISION.md）。

---

## English version

*(Sections 1–7 in Chinese above; the English version follows the same structure.)*

### 1. Why we did this

Our card's "holographic rainbow" used to be an art approximation — a gradient texture scanned across the surface by UV offset or roughness. It looked fine, but two things couldn't be defended: the rainbow never *physically moves* when the card is tilted (real foil does), and each card's optical look had no numeric definition — unique craft names sat on top of identical textures.

So we replaced the texture with computation: a physically-based foil shader using **thin-film interference + diffraction grating**. Every card now carries an auditable *optical fingerprint*: a `foil` parameter block (thickness, ior, grating period, groove direction, roughness) in `card-config.json`.

### 2. The physics in three equations

- **Thin-film interference** (dispersive base): two reflections from a film of index n and thickness d interfere with phase `φ(λ) = (2π/λ)·2n·d·cosθₜ`; reflectance `R_f = 0.5(1−cosφ)` — different wavelengths reflect differently at the same view, which is dispersion.
- **Diffraction grating** (directional rainbow): the grating equation `mλ = Λ(sinθᵢ ± sinθₘ)` separates wavelengths by direction; we use its spectral-shift approximation `Δλ ∝ (λ_norm − v·k_disp)`, where v is the view projected onto the groove direction — this makes the rainbow translate with viewpoint.
- **Microfacet weighting**: a grazing-dependent weight `w_grating = gain·(1−rough)·(0.35+0.65·grazingᵗ)` blends "grating rainbow" vs "thin-film mirror" contributions.

The model is a weighted sum of three formulas — not a texture. That is the difference from art approximation.

### 3. Three implementations, one math

- `proto_render.py` (numpy): the reference model — prove the math before touching a renderer. Determinism 0.000000; azimuth 30°→60° ΔRGB 0.0217; camera tilt 0→0.5rad 0.0676.
- `build_foil_nodegroup.py` (Blender Cycles node tree): offline render pipeline. First attempt used one wavelength per channel (R=650/G=545/B=440) — ΔE76 27.9–38.5 vs reference, 100% pixels over 8, **failed** (red channel starved). Upgraded to 6 wavelengths (380/444/508/572/636/700) with CIE four-segment weights and normalization — ΔE 0.000 structurally.
- `foil_holographic.glsl` (GLSL ES 300): for detail-page preview. Verified by line-by-line numeric re-execution in numpy (`glsl_equivalence.py`): **ΔE76 = 0.000** across default / tilted-view / thick-420 scenes. This check caught my own initial `wavelengthToRGB` being wrong (3-segment vs CIE 4-segment) — syntax passing proves nothing; numeric equivalence is the only standard.

### 4. Acceptance data

RFC protocol: implementation vs reference at the same viewpoint, ΔE76 < 8.

| Implementation | Scene | ΔE76 | Verdict |
|---|---|---|---|
| GLSL (re-executed) | default / θ=0.4 / d=420 | 0.000 | ✅ |
| Node Group 6λ (real Blender render) | center pixel, Standard domain | **4.656** | ✅ < 8 |
| Node Group 3λ (historical) | same | 31–38 | ❌ discarded |

The 4.656 residual is engineering noise — 8-bit PNG quantization, 24-sample denoise residue, sRGB round-trip — not math error. View-dependence verified: whole-frame mean ΔRGB 0.033 between front view and 30° rotation.

### 5. War stories

1. **OSL runtime missing**: portable Blender 4.5.14 built with `cycles_osl=True` but no runtime — constant-red shader rendered black, printf produced nothing, Emission control worked. Three debug rounds to conclude "environment defect", then fell back to Node Group per the RFC. Build support ≠ runtime availability; probe with a constant-color shader first.
2. **Blender trig is in degrees**: `phase = C·cosθₜ + π` is radians, but Math-node COSINE takes degrees → the interference term degenerated to a constant. Fixed with a DEGREES node. The symptom (slight overall tint, structure intact) was nasty to find — caught only by center-pixel RGB numerics showing B channel systematically low by 11.
3. **Hand-typed CIE weights, four wrong**: 572nm typed 0.665 (true 0.815), 700nm typed 0.92 (true 0.6). ΔE stuck at 8.9 until we sourced weights from `wavelength_to_rgb` instead of arithmetic.
4. **Filmic view transform crushes physical hues**: default tone mapping desaturates high-dynamic physical colors; validation renders must use `view_transform='Standard'`.
5. **3-channel approximation failed numerically**: see §3 — the one "looks successful, numbers fail" pit.

### 6. Takeaways

- A software reference model first, then port to renderers — 10× cheaper than dual-write-and-squint.
- Numeric equivalence (per-pixel ΔE on identical inputs) is the only port-correctness test that counts.
- Units, constant tables, and color spaces are the three classic port killers — make all of them explicit and scripted.
- The fingerprint knobs are ready: the `foil` block (thickness/ior/period/grooveDir/roughness/gain/baseReflect) maps directly into `card-config.json`, so each future card gets a unique, auditable optical fingerprint aligned with its craft name.

### 7. Reproduce

```bash
python3 generator/foil/glsl_equivalence.py     # GLSL vs reference: ΔE=0
python3 generator/foil/nodegroup_reference.py  # NG6 vs reference: ΔE=0; NG3: 31-38
python3 generator/foil/proto_render.py         # software prototype variants + rotation seq
tools/blender-4.5.14-linux-x64/blender -b -P generator/foil/build_foil_nodegroup.py
# → out/foil_ng_front.png (front), out/foil_ng_rot30.png (rotated 30°)
```

Proof images & precision report: `docs/GRAPHICS/` (rot_seq.gif / foil_ng_compare.png / PROOF-A3-PRECISION.md).
