# 3D 渲染与实时着色器 · docs/graphics.md

> 一张全息卡怎么"闪"起来：Blender 离线构建 + Three.js 实时重建。

## 1. 两条渲染路径的分工

| 路径 | 用途 | 特点 |
|---|---|---|
| **Blender Cycles**（离线） | `renders/hero.png` 宣传图、缩略图 | 路径追踪，光照精确，耗时（~分钟/张） |
| **Three.js + GLSL**（实时） | 网页查看器 | WebGL 逐帧渲染，随视角即时更新 |

网页端无法复刻 Cycles 的离线光照，因此查看器用**同一套 UV/视差公式**重建四层
合成与镭射效果，视觉相近但会有细节差异（原项目已声明，代码注释也注明）。

## 2. 视差（Parallax）原理

```
UV' = (UV - 0.5) × scale + 0.5 + viewOffset × depth

viewOffset = 视线方向（物体局部系）投影到卡面平面
depth 正负 → 主体前凸 / 背景后缩
scale → 主体的安全缩放，避免边缘露出
```

- 主体：scale 1.25 / depth +0.4（前凸）
- 背景：depth −0.25（后缩）
- 文字：depth 0（贴在表面）
- 掠射角保护：视线与法向夹角过小时限制 UV 偏移量，防止"UV 爆开"。

Blender 侧用自定义节点组 `视差 · 通用 UV / Parallax` 实现，Three.js 侧在
fragment shader 的 `parallax()` 函数里按同一公式实现——两侧共享同一套数学，
保证离线渲染与网页预览的视差表现一致。

## 3. 镭射（Foil）材质

镭射色带 = 粉 → 黄 → 蓝 → 白 的渐变，相位由 `UV + 视角偏移` 驱动：

```
w = sin((uv.x·0.848 − uv.y·0.530)·2π·0.55 + 7·noise(uv·1.5))
color = spectrum(w + 视角相位)
```

- Blender：`ShaderNodeTexWave` 条带 + 木版颗粒纹理 + 颜色渐变（ValToRGB）；
- Three.js：shader 内 `spectrum()` + `wave()` 函数重建；
- 叠加方式：`OVERLAY` 混合到主体/背景，强度由用户滑块 `uFoil` 控制；
- 扫光：`sin` 高次幂做窄带扫光，让镭射"流动"。

## 4. 星光与辉光

- **Voronoi 星光**：`DISTANCE_TO_EDGE` 特征做细闪点阈值 + 四维噪声驱动闪烁
  （Blender 与 WebGL 都有对应实现）；
- **UnrealBloomPass**：Three.js 端用 bloom 后处理让镭射高光溢出；Blender 端用
  compositor 辉光节点等效实现；
- 饱和度保护：`pow(color, 2.2)` + 色调映射保证印刷感不被高光冲淡。

## 5. 导出链路

`build_card.py` 构建场景 → `export_web.py` 打开 card.blend，把材质槽替换为
`web_front / web_edge / web_back / web_gold` 占位材质 → 导出 GLB（含 UV 与
节点层级）→ 前端 app.js 按材质名挂上实时 ShaderMaterial：

| GLB 材质槽 | 前端着色器 |
|---|---|
| `web_front` | 四层合成 + 视差 + 镭射 |
| `web_back` | 背面靛蓝 + 纹饰 + 背面图 |
| `web_edge` | 卡边镭射 |
| `web_gold` | 古金压边 |

## 6. 性能

- 纹理：四张 1920×2880 PNG（当前为原始体积，后续压缩）；
- WebGL：正交相机 + 单次 fullscreen 合成，UnrealBloom 720×1000 降采样；
- `prefers-reduced-motion` 用户禁用自动旋转动画。
