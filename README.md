<p align="center">
  <img src="docs/screenshots/hero-banner.png" alt="HoloLab Studio — one sentence → a 3D holographic card → a live gallery" width="100%">
</p>

<h1 align="center">🃏 HoloLab Studio ✨</h1>

<p align="center"><b>One sentence → a 3D holographic card → a live gallery playable by anyone on Earth.</b></p>

<p align="center">
  🌐 <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><b>https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/</b></a>
</p>

<p align="center">
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/%F0%9F%8C%90_Live_Gallery-Online-7fd4ff?style=for-the-badge" alt="Live Gallery"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/%F0%9F%93%9C_License-MIT-yellow?style=for-the-badge" alt="MIT License"></a>
  <a href="https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio"><img src="https://img.shields.io/badge/%E2%9A%A1_100%25_Static-Zero_Server-b98ae6?style=for-the-badge" alt="100% Static"></a>
  <a href="https://www.blender.org/"><img src="https://img.shields.io/badge/%F0%9F%A7%8A_Blender-4.5-e08ac0?style=for-the-badge" alt="Blender 4.5"></a>
  <a href="https://threejs.org/"><img src="https://img.shields.io/badge/%F0%9F%8C%80_Three.js-GLSL-8a7446?style=for-the-badge" alt="Three.js"></a>
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2FElijah-Lin-Dancer.github.io%2FHolo-Card-Studio%2Fcards.json&query=%24.cards.length&label=%F0%9F%83%8F%20Cards&color=c9a86a&style=for-the-badge" alt="Cards (auto)"></a>
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/%F0%9F%8C%90_8_Languages-7fd4ff?style=for-the-badge" alt="8 Languages"></a>
  <a href="https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio/actions"><img src="https://img.shields.io/github/actions/workflow/status/Elijah-Lin-Dancer/Holo-Card-Studio/gallery-check.yml?style=for-the-badge&label=CI%20Passing" alt="CI Passing"></a>
</p>

**English · [中文版](README.zh-CN.md)**

---

## 🚀 Live preview

> ### 🌐 **<https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/>**
> Drag the cards, flip them, watch the rainbow foil shift with the angle — no install, no account, no server.

## ✨ What is this?

A complete **AIGC pipeline** that turns **one sentence** into an **interactive 3D holographic collectible card**:

| Step | What happens |
|---|---|
| 🧠 **Text model** | One sentence (auto-detects 中文 / Deutsch / English) → structured bilingual card config |
| 🎨 **AI layered art** | Doubao Seedream draws **4 layers** — subject · background · line-art · typography — divide & conquer |
| 🧊 **3D scene** | Blender builds the parallax / rainbow-foil scene, exports **GLB** |
| 🌀 **Live composite** | Three.js + GLSL shader renders parallax, rainbow foil, stardust & glow in the browser |
| 🚀 **Publish** | One command → pure-static GitHub Pages (zero server, zero database) |

*Portfolio project · AI × 3D intersection · vanilla JS front-end · zero frameworks*

## 🎴 See it move

| Demo — Marco Reus, "Gelbwand" (edition 007/009, German card face) |
|:--|
| ![Reus holographic card demo](docs/screenshots/demo-reus.gif) |

That's a **real turntable render** from the Blender pipeline (96 frames), not a mockup. The gallery plays it on hover; the detail page renders the live WebGL scene.


## 🔬 Technical Value Lift (RFC)
> Physically-based holographic foil shader · automated visual QA gate → [docs/PLANS/technical-lift-roadmap.md](docs/PLANS/technical-lift-roadmap.md)
> ✅ A-1→A-4 已交付：光学模型 + Node Group/GLSL 双实现 + ΔE 验收 → [Tech Note ①](docs/TECH-NOTES/01-holographic-foil-shader.md) · [光学 RFC](docs/GRAPHICS/HOLO-OPTICS.md)
> ✅ B-1→B-3 已交付：零 API 视觉质检门禁（G1-G4）+ 校准/破坏样本验收 + CI 轻量门 → [Tech Note ②](docs/TECH-NOTES/02-visual-qa-gate.md)

### ⚗️ Dual Render Pipeline — Standard / Premium Optics

One card config, two physically distinct foil pipelines. Pick per card via `--render-mode` or `render_mode` in `card-config.json` (default `standard`):

| | **Standard** (default) | **Premium Optics** |
|---|---|---|
| Foil model | Artistic approximation (stripes + woodgrain ramp) | **Physically simulated** — 6-wavelength thin-film interference (380/444/508/572/636/700 nm) + grating diffraction + CIE-weighted color, ΔE≈4.7 vs reference |
| Trigger | `--render-mode standard` (or omit) | `--render-mode premium` + `"foil": {...}` params block in config |
| Foil params | — | `thickness_nm` · `ior` · `grating_period_um` · `grating_azimuth_deg` · `roughness` · `rainbow_gain` · `base_reflect` (per-card optical fingerprint) |
| Gallery badge | none | automatic **✦ Premium Optics** badge (bilingual, follows site language) |
| Cost | unchanged | same Blender pipeline, zero extra API calls |

```bash
# standard（默认）
python3 generator/scripts/run_pipeline.py --project generator/projects/<slug> --render-mode standard
# premium：在 card-config.json 写入 "render_mode": "premium" + "foil": {...}，或显式传参
python3 generator/scripts/run_pipeline.py --project generator/projects/<slug> --render-mode premium
```

First premium release: **Sonny Forelli — "The Forelli Don"** (Vice City Nights · 065/009, technique `Pinstripe Prism`, 320 nm film / 1.5 ior / 1.8 µm grating @ 30°). Existing 78 cards stay on the standard line untouched.
