# HOLO-OPTICS: 物理仿真全息光学模型（Physically-Based Holographic Foil Model）

> 状态：RFC 阶段（A-1）· 主线 ① 的单一事实来源
> 用途：Blender（Cycles OSL）与详情页 GLSL **共用同一套光学数学**；参数入 `card-config.json` 的 `foil` 块，每卡一组 = 独有光学指纹。
> 阅读对象：面试官 / 协作者 / 未来维护者。公式可直接复现。

---

## 1. 目标与范围

把"全息效果"从美术近似（彩虹贴图按视角扫过）升级为**真实镭射卡的物理仿真**：

- 彩虹的位置、宽度、方向随视角**按物理公式变化**，而非贴图平移；
- Blender 离线渲染与浏览器实时交互**同一套数学**，观感一致（延续 WHITEPAPER 的 dual-rendering-path 叙事）；
- 每卡一组光学参数 = 可审计的"光学指纹"，与独特工艺名打通。

范围：只做**反射外观**（卡面 foil 层），不做体全息/透射光栅。模型 = 薄膜干涉（色散基底）+ 微表面光栅（方向性彩虹）。

---

## 2. 光学物理基础（推导）

### 2.1 薄膜干涉（Thin-Film Interference）——色散基底

考虑折射率 n 的薄膜（厚度 d），置于折射率 n₀ 的介质（空气）之上。入射光（波长 λ，入射角 θᵢ）在膜上下表面反射，两束反射光的光程差：

```
Δ = 2·n·d·cosθₜ
```

其中 θₜ 由斯涅尔定律给出：`n₀·sinθᵢ = n·sinθₜ`。

两束反射光（上表面：n₀→n，下表面：n→n₀）相位差：

```
φ(λ) = (2π/λ)·2·n·d·cosθₜ
```

考虑上表面反射的半波损失（n > n₀ 时），总相位差：

```
δ(λ) = φ(λ) + π
```

反射率随波长振荡（Airy 近似，忽略多次反射）：

```
R(λ) = [ r₁² + r₂² + 2·r₁·r₂·cos(δ) ] / [ 1 + r₁²·r₂² + 2·r₁·r₂·cos(δ) ]
```

其中 r₁、r₂ 为两界面的菲涅尔振幅反射系数（s/p 偏振各算）。膜厚 d 不同 → 反射峰波长不同 → 卡面不同区域/厚度呈现不同颜色（Newton 环物理）。

**工程简化**：用"膜厚 → 色相"一维查找表（LUT）替代逐波长 Airy 求和（见 §5.2 性能预算）：对给定 d、n，预计算 `θ → R(λₖ)` 光谱（λₖ 为 6 个采样波长），运行时按 θ 插值。

### 2.2 光栅衍射（Grating Diffraction）——方向性彩虹

卡面压印周期光栅（周期 Λ，沟槽方向角 α）。光栅方程（反射式，m 级）：

```
m·λ = Λ·( sinθᵢ + sinθ_m )
```

- m 为衍射级（0、±1…），θ_m 为该级出射角；
- **不同 λ 在同一出射角上的衍射级不同** → 白光被色散成彩虹；
- 彩虹沿**垂直于沟槽方向**展开；沟槽方位 α 决定彩虹在卡面上的方向（旋转卡 → 彩虹旋转）。

**工程简化**：只模拟 m=±1 级的彩虹色散（更高级能量占比小），出射方向由视向量分解到"沟槽坐标系"：

```
视向量在卡面平面投影 → (u,v)
u = 沿沟槽分量（不色散）
v = 垂直沟槽分量（色散，控制彩虹位置）
```

彩虹强度按 v 值偏移采样"波长→颜色"映射（见 §3.3）。

### 2.3 微表面散射（Microfacet）——彩虹锐利度与各向异性

用 GGX（Trowbridge–Reitz）微表面法线分布：

```
D(h) = α² / [ π·( (h·n)²·(α²−1) + 1 )² ]
```

- α（roughness）小 → 彩虹锐利、镜面感强（镭射卡的"金属刮痕"质感）；
- **各向异性**：α_u、α_v 不同（沿沟槽/垂直沟槽粗糙度不同）→ 彩虹在垂直方向拉长/压缩——真实镭射卡的典型观感。

---

## 3. 仿真模型：L1（薄膜）+ L2（微表面光栅）

最终反射颜色（每像素）：

```
C(ωᵢ, ωₒ) = F0 · Sₘf(ωᵢ, ωₒ) · [ T_film(θₜ, d, n) ⊕ R_grating(v, Λ, m) ]
```

分量：
- `F0`：基础反射率（金属卡体底色）
- `Sₘf`：GGX 微表面阴影遮蔽（Smith 项 × D × 可见性）
- `T_film`：薄膜反射光谱（§2.1，θ 驱动 → 油彩渐变基底）
- `R_grating`：光栅衍射色散（§2.2，v 驱动 → 彩虹方向性）

**合成规则**：T_film 提供"任何视角都有的低饱和油彩"，R_grating 提供"特定视角的饱和彩虹"；两者权重按粗糙度 α 融合（α 小 → 光栅主导；α 大 → 薄膜主导）。

### 3.1 输入参数规范（`card-config.json → foil`）

| 参数 | 类型 | 默认 | 物理含义 | 视觉影响 |
|---|---|---|---|---|
| `thickness_nm` | number | 320 | 薄膜厚度（nm） | 油彩基底色相 |
| `ior` | number | 1.5 | 薄膜折射率 | 色散强度 |
| `grating_period_um` | number | 1.8 | 光栅周期（μm） | 彩虹展开宽度 |
| `grating_azimuth_deg` | number | 30 | 沟槽方位角（°） | 彩虹方向 |
| `roughness` | number | 0.18 | 微表面粗糙度 α | 彩虹锐利度 |
| `anisotropy` | number | 0.4 | 各向异性（αu≠αv） | 彩虹拉伸 |
| `wavelength_samples` | int | 6 | 光谱采样数 | 质量/性能权衡 |
| `rainbow_gain` | number | 1.0 | 光栅彩虹强度 | 强弱控制 |

**约束**：同系列卡可共用基底参数（品牌感），每卡至少一项不同（光学指纹）。

---

## 4. 双实现架构

### 4.1 统一数学核心（两个引擎共享的伪代码）

```
// 输入: viewDir(V), normal(N), foil{...}, texcoord(uv)
// 1. 视角几何
H   = normalize(V + L)            // 半程向量（反射）
θᵢ  = acos(dot(N, V))
θₜ  = asin( (n₀/n)·sin(θᵢ) )      // 斯涅尔

// 2. 薄膜光谱（LUT 插值）
spec = thinFilmLUT(θₜ, foil.thickness_nm, foil.ior)   // → 6 波长反射率

// 3. 光栅坐标系
u  = dot(flat(V), tangent(grating_azimuth))            // 沿沟槽
v  = dot(flat(V), bitangent(grating_azimuth))          // 垂直沟槽（色散轴）
rainbow = gratingSpectrum(v, foil.grating_period_um)   // → 波长权重

// 4. 微表面权重
D  = GGX_aniso(H, N, roughness, anisotropy)
G  = Smith(V, L)
w_grating = smoothstep(0.6, 0.9, D/(D+0.05))           // 锐利时光栅主导

// 5. 合成（分波长求和 → RGB）
C = Σ_λ  [ F0·D·G · ( (1-w_grating)·spec[λ] + w_grating·rainbow[λ] ) ] · white[λ]
```

### 4.2 Blender（Cycles OSL）实现

- 单文件 OSL shader `foil_holographic.osl`（同 §4.1 数学逐行移植）；
- Cycles CPU 验证（OSL 不支持 GPU 编译时 fallback 为 Node Group）；
- 输出接 `Emission`/`Diffuse` 混合 → hero 渲染 + GLB 材质（Principled BSDF 的 Sheen/Base 层注入）。

### 4.3 详情页 GLSL 实现

- 替换现有 fragment shader 的 foil 模块（`#ifdef HOLO_FOIL` 分支）；
- 输入：uniform `uFoil[...]`（来自 card-config 编译进 JSON）、`vViewDir`/`vNormal`；
- 输出：`gl_FragColor.rgb` 叠加在现有全息视差之上（保留原视差/发光，只换"彩虹生成"段）。

---

## 5. 性能预算

| 引擎 | 预算 | 手段 |
|---|---|---|
| GLSL | ≤ 2 ms/帧（1080p 卡面） | 光谱 LUT 预计算（256×8 纹理，薄膜+光栅各一）、6 波长 → 3 波长循环 + 2 次插值、避免逐像素 asin（用 cosθ 多项式） |
| Cycles OSL | 无实时约束 | 全 6 波长 + 真实菲涅尔（可开 L3 全衍射对照） |

**LUT 预计算**：`thickness→(θ,λ)` 反射率 2D 纹理（256×256 RGBA16F），运行时一次采样。光栅彩虹用解析式（周期已知）→ 无 LUT 成本。

---

## 6. 验证与验收协议

### 6.1 同视角 ΔE 对照（主验收）

1. 固定相机视角（正视角 + 30° 旋转 × 2），Blender 与 GLSL 各渲一帧；
2. sRGB→Linear→XYZ→Lab（D65）转换，逐像素色差：
   ```
   ΔE = sqrt( (ΔL*)² + (Δa*)² + (Δb*)² )
   ```
3. 验收：卡面主体区域平均 ΔE < 8（可忽略），P95 < 15。

### 6.2 物理正确性测试（证明不是贴图）

| 测试 | 方法 | 预期 |
|---|---|---|
| 彩虹方向 | 旋转 azimuth 30°→60° | 彩虹方向随之旋转（几何关系验证） |
| 彩虹位置 | 改 grating_period_um | 色散宽度按光栅方程变化 |
| 油彩色相 | 改 thickness_nm | 反射峰波长按 2nd 规律移动 |
| 视角扫描 | 录制拖拽旋转 | 彩虹连续、无跳变、有方向性 |

### 6.3 回归

- 现有 78 卡详情页视觉基线截图存档；替换 foil 后抽查 5 卡无断裂/过曝；
- pytest 增加 `test_foil_params_schema`（card-config foil 字段校验）+ `test_foil_lut_bounds`。

---

## 7. 交付物清单

- [ ] `docs/GRAPHICS/HOLO-OPTICS.md`（本文档）
- [ ] `generator/foil/thin_film_lut.py`（LUT 生成，可复现）
- [ ] `generator/foil/foil_holographic.osl`（Blender 实现）
- [ ] 详情页 shader `foil` 模块（GLSL 实现）
- [ ] 对比渲染脚本 `generator/foil/compare_delta_e.py`
- [ ] 技术笔记《From Art Approximation to Physical Optics》（中英双语，A-4）

---

## 8. 参考

- Born & Wolf, *Principles of Optics*（薄膜干涉、光栅）
- Walter et al., *Microfacet Models for Refraction through Rough Surfaces*（GGX）
- CIE ΔE 色差标准（CIELAB）
- 真实镭射卡母版工艺（全息母版、镍版复制、压印）——观感校准对象
