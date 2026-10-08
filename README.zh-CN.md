<p align="center">
  <img src="docs/screenshots/hero-banner.png" alt="HoloLab Studio — 一句话 → 一张 3D 全息卡 → 一个在线展厅" width="100%">
</p>

<h1 align="center">🃏 HoloLab Studio ✨</h1>

<p align="center"><b>一句话 → 一张随视线流动光影的 3D 全息卡 → 一个全世界任何人都能打开的在线展厅。</b></p>

<p align="center">
  🌐 <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><b>https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/</b></a>
</p>

<p align="center">
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/%F0%9F%8C%90_%E5%9C%A8%E7%BA%BF%E5%B1%95%E5%8E%85-%E7%AB%8B%E5%8D%B3%E4%BD%93%E9%AA%8C-7fd4ff?style=for-the-badge" alt="在线展厅"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/%F0%9F%93%9C_%E8%AE%B8%E5%8F%AF-MIT-yellow?style=for-the-badge" alt="MIT License"></a>
  <a href="https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio"><img src="https://img.shields.io/badge/%E2%9A%A1_100%25_%E9%9D%99%E6%80%81-%E9%9B%B6%E6%9C%8D%E5%8A%A1%E5%99%A8-b98ae6?style=for-the-badge" alt="100% Static"></a>
  <a href="https://www.blender.org/"><img src="https://img.shields.io/badge/%F0%9F%A7%8A_Blender-4.5-e08ac0?style=for-the-badge" alt="Blender 4.5"></a>
  <a href="https://threejs.org/"><img src="https://img.shields.io/badge/%F0%9F%8C%80_Three.js-GLSL-8a7446?style=for-the-badge" alt="Three.js"></a>
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2FElijah-Lin-Dancer.github.io%2FHolo-Card-Studio%2Fcards.json&query=%24.cards.length&label=%F0%9F%83%8F%20%E5%8D%A1%E7%89%87&color=c9a86a&style=for-the-badge" alt="Cards (auto)"></a>
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/%F0%9F%8C%90_8_%E8%AF%AD%E8%A8%80-7fd4ff?style=for-the-badge" alt="8 Languages"></a>
  <a href="https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio/actions"><img src="https://img.shields.io/github/actions/workflow/status/Elijah-Lin-Dancer/Holo-Card-Studio/gallery-check.yml?style=for-the-badge&label=CI%20Passing" alt="CI Passing"></a>
</p>

**中文 · [English](README.md)**

---

## 🚀 在线预览

> ### 🌐 **<https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/>**
> 拖动卡片、翻转、看镭射彩虹随角度流转——无需安装、无需账号、无需服务器。

## ✨ 这是什么？

一条完整的 **AIGC 管线**，把**一句话**变成一张**可交互的 3D 全息收藏卡**：

| 步骤 | 发生了什么 |
|---|---|
| 🧠 **文字模型** | 一句话（自动识别 中文 / Deutsch / English）→ 结构化双语卡面配置 |
| 🎨 **AI 分层素材** | 豆包 Seedream 分层绘制 **4 层** — 主体 · 背景 · 线稿 · 文字层 — 分而治之 |
| 🧊 **3D 场景** | Blender 构建视差 / 镭射彩虹场景，导出 **GLB** |
| 🌀 **实时合成** | Three.js + GLSL 着色器在浏览器实时渲染视差、镭射彩虹、星尘与泛光 |
| 🚀 **发布** | 一条命令 → 纯静态 GitHub Pages（零服务器、零数据库） |

*作品集项目 · AI × 3D 交叉方向 · 原生 JS 前端 · 零框架*

## 🎴 会动的卡片

| 演示 — 马尔科·罗伊斯「黄黑之魂」（edition 007/009，德语卡面） |
|:--|
| ![罗伊斯全息卡演示](docs/screenshots/demo-reus.gif) |

这是 Blender 管线输出的**真实转台渲染**（96 帧），不是效果图。展厅里悬停播放、详情页实时渲染 WebGL 场景。


## 🔬 技术含金量提升（RFC 规划）
> 物理仿真全息 shader · AI 素材质检流水线 → [docs/PLANS/technical-lift-roadmap.md](docs/PLANS/technical-lift-roadmap.md)
