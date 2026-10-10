<p align="center">
  <img src="docs/screenshots/hero-banner.png" alt="HoloLab Studio — 一句话 → 一张 3D 全息卡 → 一个在线展厅" width="100%">
</p>

<h1 align="center">🃏 HoloLab Studio</h1>

<p align="center"><b>一句话 → 一张随视线流动光影的 3D 全息收藏卡 → 一个全世界任何人都能打开的在线展厅。</b></p>

<p align="center">
  🌐 <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><b>https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/</b></a>
</p>

<p align="center">
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/%F0%9F%8C%90_%E5%9C%A8%E7%BA%BF%E5%B1%95%E5%8E%85-%E7%AB%8B%E5%8D%B3%E4%BD%93%E9%AA%8C-7fd4ff?style=for-the-badge" alt="在线展厅"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/%F0%9F%93%9C_%E8%AE%B8%E5%8F%AF-MIT-yellow?style=for-the-badge" alt="MIT License"></a>
  <a href="https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio"><img src="https://img.shields.io/badge/%E2%9A%A1_100%25_%E9%9D%99%E6%80%81-%E9%9B%B6%E6%9C%8D%E5%8A%A1%E5%99%A8-b98ae6?style=for-the-badge" alt="100% Static"></a>
  <a href="https://www.blender.org/"><img src="https://img.shields.io/badge/%F0%9F%A7%8A_Blender-4.5-e08ac0?style=for-the-badge" alt="Blender 4.5"></a>
  <a href="https://threejs.org/"><img src="https://img.shields.io/badge/%F0%9F%8C%80_Three.js-0.180-8a7446?style=for-the-badge" alt="Three.js 0.180"></a>
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2FElijah-Lin-Dancer.github.io%2FHolo-Card-Studio%2Fcards.json&query=%24.cards.length&label=%F0%9F%83%8F%20%E5%8D%A1%E7%89%87&color=c9a86a&style=for-the-badge" alt="Cards (auto)"></a>
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2FElijah-Lin-Dancer.github.io%2FHolo-Card-Studio%2Fmeta.json&query=%24.languages&label=%F0%9F%8C%90%20%E8%AF%AD%E8%A8%80&color=7fd4ff&style=for-the-badge" alt="Languages (auto)"></a>
  <a href="https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio/actions"><img src="https://img.shields.io/github/actions/workflow/status/Elijah-Lin-Dancer/Holo-Card-Studio/gallery-check.yml?style=for-the-badge&label=CI%20Passing" alt="CI Passing"></a>
</p>

**中文 · [English](README.md)**

---

## 🚀 在线展厅

> 拖动卡片、翻转、看镭射彩虹随角度流转——无需安装、无需账号、无需服务器。

## ✨ 这是什么？

一条端到端的 **AIGC 管线**，把**一句话**变成一张**可交互的 3D 全息收藏卡**，并发布到零后端的静态展厅：

| 步骤 | 发生了什么 |
|---|---|
| 🧠 **文字模型** | 一句话（自动识别 中文 / English / Deutsch / Español / বাংলা / Dansk / Português / Norsk）→ 结构化卡面配置 |
| 🎨 **AI 分层素材** | 4 个独立图层 — 主体 · 背景 · 线稿 · 文字 — 每层交给最擅长的工具 |
| 🧊 **3D 场景** | Blender 构建视差 / 镭射彩虹场景并导出 **GLB** |
| 🌀 **实时合成** | Three.js + GLSL 在浏览器实时渲染视差、镭射彩虹、星尘与泛光 |
| 🚀 **发布** | 一条命令 → 纯静态 GitHub Pages（零服务器、零数据库、零运行成本） |

*AI × 3D 交叉方向 · 原生 JS 前端 · 零框架*

## 🎴 会动的卡片

| 演示 — 马尔科·罗伊斯「黄黑之魂」（edition 007/009，德语卡面） |
|:--|
| ![罗伊斯全息卡演示](docs/screenshots/demo-reus.gif) |

Blender 管线输出的**真实转台渲染**（96 帧），不是效果图。展厅里悬停播放、详情页实时渲染 WebGL 场景。

| 80 张卡的展厅墙 |
|:--|
| ![展厅墙](docs/screenshots/card-wall.jpg) |

## 🔑 核心亮点

- **四层素材管线** — 一张图无法同时做到视差、独立镭射、可靠文字。主体 / 背景 / 线稿 / 文字分层生成，每层有独立的质检与兜底。
- **双线渲染管线** — 同一份卡配置、两套物理机制完全不同的镭射：标准美术近似线，与**高级光学 Premium Optics**（6 波长薄膜干涉 + 光栅衍射 + CIE 权重配色 的物理仿真）。见 [⚗️ 双线渲染管线](#%E2%9A%97%EF%B8%8F-双线渲染管线--标准线--高级光学)。
- **零后端、全链路可审计** — 静态站点由 JSON 清单驱动；管线、发布脚本、CI 全部入库、逐行可查。API 密钥只存在被 git 忽略的 `.env`。
- **80 张卡 · 8 种语言** — 殷商纪（中文）、哈兰德梗卡系列（中文 / English / Norsk）、罪恶都市之夜（English）、巴萨传承（Español），以及德语 / 孟加拉语 / 丹麦语 / 葡萄牙语等单卡致敬作品。站点 UI 本身双语（中文 / English）。
- **每次推送都有质量门** — 34 个管线单元测试 + 4 个前端纯函数测试 + 80 卡展厅体检 + QA 门禁，全部在部署前的 CI 里执行。

## 🗂 展厅一览

| 系列 | 卡数 | 卡面语言 |
|---|---|---|
| 殷商纪 Yin-Shang Chronicles | 29 | 中文 |
| 哈兰德多元宇宙 · 梗卡系列 | 15 | 中文 / English / Norsk |
| 罪恶都市之夜 · 人物 + 场景 | 15 | English |
| 巴萨传承 FC Barcelona Legacy | 6 | Español |
| HoloLab 典藏 · 传奇系列 | 2 | 中文 |
| 单卡定制与致敬作品 | 13 | de / bn / da / pt / en / 中文 |

> 实时数字来自 [`gallery/cards.json`](gallery/cards.json) 与 [`gallery/meta.json`](gallery/meta.json)——上方徽章永不滞后。

## 🛠 快速开始

```bash
git clone https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio.git
cd Holo-Card-Studio

make setup        # 安装 Python 依赖 + 生成 .env（填入你的 ARK_API_KEY）
make preview      # 本地预览 http://127.0.0.1:4191
```

制作并发布你的第一张卡：

```bash
make card SENTENCE="a snow leopard under the aurora" SLUG=aurora-ridge
# → 4 层 AI 素材 → Blender GLB → 展厅清单
make publish SLUG=aurora-ridge
git add -A && git commit -m "add card aurora-ridge" && git push   # CI 渲染 + 部署
```

完整命令表见 [`Makefile`](Makefile)，逐步复现教程见 [`docs/REPRODUCE.md`](docs/REPRODUCE.md)。

## ⚗️ 双线渲染管线 —— 标准线 / 高级光学

同一份卡配置、两套物理机制完全不同的镭射管线。按卡选择：`--render-mode` 或 `card-config.json` 里的 `render_mode`（默认 `standard`）：

| | **标准线（默认）** | **高级光学 Premium Optics** |
|---|---|---|
| 镭射模型 | 美术近似（条带 + 木纹渐变） | **物理仿真** — 6 波长薄膜干涉（380/444/508/572/636/700 nm）+ 光栅衍射 + CIE 权重配色，ΔE≈4.7 对照验收 |
| 触发方式 | `--render-mode standard`（或省略） | `--render-mode premium` + config 写 `"foil": {...}` 参数块 |
| 光学参数 | — | `thickness_nm` · `ior` · `grating_period_um` · `grating_azimuth_deg` · `roughness` · `rainbow_gain` · `base_reflect`（每卡光学指纹） |
| 展厅角标 | 无 | 自动 **✦ 高级光学** 角标（双语，随站点语言切换） |
| 成本 | 不变 | 同一套 Blender 管线，零额外 API 调用 |

```bash
# 标准线（默认）
python3 generator/scripts/run_pipeline.py --project generator/projects/<slug> --render-mode standard
# 高级线：card-config.json 写 "render_mode": "premium" + "foil": {...}，或显式传参
python3 generator/scripts/run_pipeline.py --project generator/projects/<slug> --render-mode premium
```

首张高级线正式发行：**桑尼·弗雷利 — 「The Forelli Don」**（罪恶都市之夜 · 065/009，工艺 `Pinstripe Prism`，320 nm 膜厚 / 1.5 折射率 / 1.8 µm 光栅 @ 30°）。存量卡保持标准线不动。

## 📁 仓库结构

<details>
<summary>点击展开</summary>

```
Holo-Card-Studio/
├── gallery/                  # 公开站点（GitHub Pages 根目录）
│   ├── index.html            # 展厅
│   ├── create.html           # 一句话 → 卡面描述 创作台
│   ├── cards.json            # 展厅清单（徽章的权威数据源）
│   ├── meta.json             # 自动生成的计数（卡数 / 语言数）
│   ├── curation.json         # 策展时间线
│   ├── cards/<slug>/         # 每张卡一个目录（4 层素材 + GLB + 详情页）
│   └── vendor/               # 固定的 three.js / gsap
├── generator/
│   ├── projects/<slug>/      # 每张卡的工作目录（配置 + 原始素材）
│   ├── scripts/              # one_shot_card / ai_generate / run_pipeline / publish_card ...
│   ├── tests/ + tests-js/    # 34 pytest + 4 node 测试
│   └── qa/                   # 零 API 视觉质检门禁
├── docs/                     # 架构 · 管线 · 部署 · 设计决策 · 白皮书
├── .github/workflows/        # gallery-check · deploy · auto-render · render-card
└── Makefile                  # 一条命令 setup / new / render / publish / test
```
</details>

## 🧰 技术栈

| 层 | 工具 |
|---|---|
| 图像生成 | 豆包 Seedream 5.0（经 ARK API） |
| 抠图 / 线稿 | rembg (u2net) · OpenCV |
| 排版 | fontTools + Pillow |
| 3D 场景与离线渲染 | Blender 4.5（Cycles） |
| 实时查看器 | Three.js 0.180 + GLSL |
| 前端 | 原生 JS · GSAP |
| 托管 | GitHub Pages（纯静态） |
| CI | GitHub Actions — gallery-check（pytest + node + 体检 + QA 门）+ deploy + auto-render |

## ❓ 常见问题

<details>
<summary><b>做一张卡需要 API 密钥吗？</b></summary>
只有 AI 图像层需要。`make setup` 会从 `.env.example` 生成 `.env`——把 ARK_API_KEY 放进去即可。之后的渲染（Blender）与后续一切免费且离线。已发布的展厅本身既不需要密钥也不需要服务器。

</details>

<details>
<summary><b>怎么向公开展厅投稿一张卡？</b></summary>
开一个 issue，用一句话描述卡片（或在 `create.html` 里把它展开成结构化描述）。`auto-render` workflow 会接管，跑完整管线并开 PR。按作者限频以保持展厅策展质量。细节：[`CONTRIBUTING.md`](CONTRIBUTING.md)。

</details>

<details>
<summary><b>可以拿这个做自己的项目吗？</b></summary>
可以——MIT 协议。本仓库是对开源项目 **holo-card-studio**（MIT）的再工程化：上游"镭射与视差随视角响应"的核心思想被完整保留并致谢。核心之外的生成管线、发布、展厅前端与文档均为本仓库自己的成果。

</details>

## 📚 文档

| 文档 | 内容 |
|---|---|
| [白皮书](docs/WHITEPAPER.md) | 端到端叙述：架构、管线、部署、贡献声明 |
| [架构](docs/architecture.md) | 系统设计与四层素材策略 |
| [AI 管线](docs/ai-pipeline.md) | 提示词工程、抠图、轮廓提取、排版 |
| [光学 RFC](docs/GRAPHICS/HOLO-OPTICS.md) | 物理镭射模型：薄膜干涉 + 光栅 + CIE |
| [技术笔记①](docs/TECH-NOTES/01-holographic-foil-shader.md) · [②](docs/TECH-NOTES/02-visual-qa-gate.md) | 着色器数学 · 零 API 视觉质检门 |
| [复现指南](docs/REPRODUCE.md) | 逐步复现教程 |
| [部署](docs/DEPLOYMENT.md) | 静态托管与发布流程 |
| [设计决策](docs/DESIGN-DECISIONS.md) | 关键取舍与原因 |
| [提示词指南](docs/PROMPT-GUIDE.md) · [卡面质量](docs/CARD-QUALITY.md) | 怎么写提示词 · 质量标准 |
| [更新日志](CHANGELOG.md) | 版本历史 |

## 🙏 致谢

对 MIT 协议开源项目 **holo-card-studio** 的再工程化——上游"角度响应镭射与视差卡"的思想被完整保留并致谢。

## 📜 更新日志

见 [CHANGELOG.md](CHANGELOG.md)。
