<p align="center">
  <img src="docs/screenshots/hero-banner.png" alt="HoloLab Studio — one sentence → a 3D holographic card → a live gallery" width="100%">
</p>

<h1 align="center">🃏 HoloLab Studio</h1>

<p align="center"><b>One sentence → an interactive 3D holographic trading card → a live gallery anyone on Earth can open.</b></p>

<p align="center">
  🌐 <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><b>https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/</b></a>
</p>

<p align="center">
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/%F0%9F%8C%90_Live_Gallery-Online-7fd4ff?style=for-the-badge" alt="Live Gallery"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/%F0%9F%93%9C_License-MIT-yellow?style=for-the-badge" alt="MIT License"></a>
  <a href="https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio"><img src="https://img.shields.io/badge/%E2%9A%A1_100%25_Static-Zero_Server-b98ae6?style=for-the-badge" alt="100% Static"></a>
  <a href="https://www.blender.org/"><img src="https://img.shields.io/badge/%F0%9F%A7%8A_Blender-4.5-e08ac0?style=for-the-badge" alt="Blender 4.5"></a>
  <a href="https://threejs.org/"><img src="https://img.shields.io/badge/%F0%9F%8C%80_Three.js-0.180-8a7446?style=for-the-badge" alt="Three.js 0.180"></a>
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2FElijah-Lin-Dancer.github.io%2FHolo-Card-Studio%2Fcards.json&query=%24.cards.length&label=%F0%9F%83%8F%20Cards&color=c9a86a&style=for-the-badge" alt="Cards (auto)"></a>
  <a href="https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2FElijah-Lin-Dancer.github.io%2FHolo-Card-Studio%2Fmeta.json&query=%24.languages&label=%F0%9F%8C%90%20Languages&color=7fd4ff&style=for-the-badge" alt="Languages (auto)"></a>
  <a href="https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio/actions"><img src="https://img.shields.io/github/actions/workflow/status/Elijah-Lin-Dancer/Holo-Card-Studio/gallery-check.yml?style=for-the-badge&label=CI%20Passing" alt="CI Passing"></a>
</p>

**English · [中文版](README.zh-CN.md)**

---

## 🚀 Live gallery

> Drag the cards, flip them, watch the rainbow foil shift with the angle — no install, no account, no server.

## ✨ What it is

An end-to-end **AIGC pipeline** that turns **one sentence** into an **interactive 3D holographic collectible card**, then publishes it to a zero-backend static gallery:

| Step | What happens |
|---|---|
| 🧠 **Text model** | One sentence (auto-detects zh / en / de / es / bn / da / pt / no) → structured card config |
| 🎨 **AI layered art** | 4 independent layers — subject · background · line-art · typography — each drawn by the tool best at it |
| 🧊 **3D scene** | Blender builds the parallax / rainbow-foil scene and exports a **GLB** |
| 🌀 **Live composite** | Three.js + GLSL renders parallax, rainbow foil, stardust & glow in the browser |
| 🚀 **Publish** | One command → pure-static GitHub Pages (zero server, zero database, zero running cost) |

*AIGC × 3D intersection · vanilla JS front-end · zero frameworks*

## 🎴 See it move

| Demo — Marco Reus, "Gelbwand" (edition 007/009, German card face) |
|:--|
| ![Reus holographic card demo](docs/screenshots/demo-reus.gif) |

A **real turntable render** from the Blender pipeline (96 frames), not a mockup. The gallery plays it on hover; the detail page renders the live WebGL scene.

| The 80-card gallery wall |
|:--|
| ![Gallery wall](docs/screenshots/card-wall.jpg) |

## 🔑 Highlights

- **Four-layer asset pipeline** — a single generated image cannot parallax, carry a separate foil, or render reliable text. Subject / background / line-art / typography are separated so each layer is done by the tool best at it, with per-layer validation and fallback.
- **Dual render pipeline** — one card config, two physically distinct foil systems: the standard artistic approximation and **Premium Optics**, a physically simulated holographic foil (6-wavelength thin-film interference + grating diffraction + CIE-weighted color). See [⚗️ Dual render pipeline](#%E2%9A%97%EF%B8%8F-dual-render-pipeline--standard--premium-optics).
- **Zero backend, fully auditable** — static site driven by a JSON manifest; the pipeline, publishing script, and CI all live in the repo, inspectable line by line. API keys stay in a git-ignored `.env`.
- **80 cards · 8 languages** — Yin-Shang Chronicles · 殷商纪 (zh), Haaland Meme Series (zh/en/no), Vice City Nights (en), FC Barcelona Legacy (es), and individual tributes in de / bn / da / pt. The site UI itself is bilingual (EN / 中文).
- **Quality gates on every push** — 34 pipeline unit tests + 4 front-end pure-function tests + an 80-card gallery health check + a QA gate, run by CI before every deploy.

## 🗂 Gallery at a glance

| Series | Cards | Card-face language |
|---|---|---|
| Yin-Shang Chronicles · 殷商纪 | 29 | 中文 |
| Haaland Multiverse · Meme Series | 15 | 中文 / English / Norsk |
| Vice City Nights · Characters + Places | 15 | English |
| HoloLab Archive · FC Barcelona Legacy | 6 | Español |
| HoloLab 典藏 · 传奇系列 | 2 | 中文 |
| Individual commissions & tributes | 13 | de / bn / da / pt / en / 中文 |

> Live counts come from [`gallery/cards.json`](gallery/cards.json) and [`gallery/meta.json`](gallery/meta.json) — the badges above never go stale.

## 🛠 Quick start

```bash
git clone https://github.com/Elijah-Lin-Dancer/Holo-Card-Studio.git
cd Holo-Card-Studio

make setup        # install Python deps + create .env (add your ARK_API_KEY)
make preview      # serve the gallery locally at http://127.0.0.1:4191
```

Create and publish your first card:

```bash
make card SENTENCE="a snow leopard under the aurora" SLUG=aurora-ridge
# → 4 AI layers → Blender GLB → gallery manifest
make publish SLUG=aurora-ridge
git add -A && git commit -m "add card aurora-ridge" && git push   # CI renders + deploys
```

See [`Makefile`](Makefile) for the full command table and [`docs/REPRODUCE.md`](docs/REPRODUCE.md) for the complete walkthrough.

## ⚗️ Dual render pipeline — Standard / Premium Optics

One card config, two physically distinct foil pipelines. Pick per card via `--render-mode` or `render_mode` in `card-config.json` (default `standard`):

| | **Standard** (default) | **Premium Optics** |
|---|---|---|
| Foil model | Artistic approximation (stripes + woodgrain ramp) | **Physically simulated** — 6-wavelength thin-film interference (380/444/508/572/636/700 nm) + grating diffraction + CIE-weighted color, ΔE≈4.7 vs reference |
| Trigger | `--render-mode standard` (or omit) | `--render-mode premium` + `"foil": {...}` params block in config |
| Foil params | — | `thickness_nm` · `ior` · `grating_period_um` · `grating_azimuth_deg` · `roughness` · `rainbow_gain` · `base_reflect` (per-card optical fingerprint) |
| Gallery badge | none | automatic **✦ Premium Optics** badge (bilingual, follows site language) |
| Cost | unchanged | same Blender pipeline, zero extra API calls |

```bash
# standard (default)
python3 generator/scripts/run_pipeline.py --project generator/projects/<slug> --render-mode standard
# premium: write "render_mode": "premium" + "foil": {...} into card-config.json, or pass explicitly
python3 generator/scripts/run_pipeline.py --project generator/projects/<slug> --render-mode premium
```

First premium release: **Sonny Forelli — "The Forelli Don"** (Vice City Nights · 065/009, technique `Pinstripe Prism`, 320 nm film / 1.5 ior / 1.8 µm grating @ 30°). Existing cards stay on the standard line untouched.

## 📁 Repo layout

<details>
<summary>Click to expand</summary>

```
Holo-Card-Studio/
├── gallery/                  # the public site (GitHub Pages root)
│   ├── index.html            # exhibition hall
│   ├── create.html           # one-sentence → card description studio
│   ├── cards.json            # gallery manifest (source of truth for badges)
│   ├── meta.json             # auto-generated counts (cards / languages)
│   ├── curation.json         # exhibition timeline
│   ├── cards/<slug>/         # one directory per card (4 layers + GLB + detail page)
│   └── vendor/               # pinned three.js / gsap
├── generator/
│   ├── projects/<slug>/      # working directory per card (config + raw assets)
│   ├── scripts/              # one_shot_card / ai_generate / run_pipeline / publish_card ...
│   ├── tests/ + tests-js/    # 34 pytest + 4 node tests
│   └── qa/                   # visual quality gate (zero-API)
├── docs/                     # architecture · pipeline · deployment · design decisions · white paper
├── .github/workflows/        # gallery-check · deploy · auto-render · render-card
└── Makefile                  # one-command setup / new / render / publish / test
```
</details>

## 🧰 Tech stack

| Layer | Tool |
|---|---|
| Image generation | Doubao Seedream 5.0 (via ARK API) |
| Matting / line-art | rembg (u2net) · OpenCV |
| Typography | fontTools + Pillow |
| 3D scene & offline render | Blender 4.5 (Cycles) |
| Real-time viewer | Three.js 0.180 + GLSL |
| Front-end | Vanilla JS · GSAP |
| Hosting | GitHub Pages (pure static) |
| CI | GitHub Actions — gallery-check (pytest + node + health + QA gate) · deploy · auto-render |

## ❓ FAQ

<details>
<summary><b>Do I need an API key to build a card?</b></summary>
Only for the AI image layer. `make setup` creates a `.env` from `.env.example` — put your ARK_API_KEY there. Rendering (Blender) and everything after is free and offline. The published gallery itself needs no key and no server.

</details>

<details>
<summary><b>How do I submit a card to the public gallery?</b></summary>
Open an issue with one sentence describing the card (or use `create.html` to expand it into a structured description). The `auto-render` workflow picks it up, runs the pipeline, and opens a PR. Rate-limited per author to keep the hall curated. Details: [`CONTRIBUTING.md`](CONTRIBUTING.md).

</details>

<details>
<summary><b>Can I use this for my own project?</b></summary>
Yes — MIT licensed. This repo is a re-engineering of the open-source project **holo-card-studio** (MIT), whose core idea — a card whose foil and parallax respond to the viewing angle — is preserved and credited. Everything here beyond the upstream core (generation pipeline, publishing, gallery front-end, docs) is our own work.

</details>

## 📚 Docs

| Doc | What's inside |
|---|---|
| [White paper](docs/WHITEPAPER.md) | End-to-end account: architecture, pipeline, deployment, contribution statement |
| [Architecture](docs/architecture.md) | System design & the four-layer asset strategy |
| [AI pipeline](docs/ai-pipeline.md) | Prompt engineering, matting, contour extraction, typography |
| [Graphics / Optics RFC](docs/GRAPHICS/HOLO-OPTICS.md) | Physical foil model: thin-film interference + grating + CIE |
| [Tech Note ①](docs/TECH-NOTES/01-holographic-foil-shader.md) · [②](docs/TECH-NOTES/02-visual-qa-gate.md) | Shader math · zero-API visual QA gate |
| [Reproduce](docs/REPRODUCE.md) | Step-by-step reproduction walkthrough |
| [Deployment](docs/DEPLOYMENT.md) | Static hosting & the publish flow |
| [Design decisions](docs/DESIGN-DECISIONS.md) | Key tradeoffs and why they were made |
| [Prompt guide](docs/PROMPT-GUIDE.md) · [Card quality](docs/CARD-QUALITY.md) | Writing prompts · quality standards |
| [Changelog](CHANGELOG.md) | Version history |

## 🙏 Built on

Re-engineered from the MIT-licensed **holo-card-studio** — the upstream idea of an angle-reactive foil and parallax card is fully preserved and credited.

## 📜 Changelog

See [CHANGELOG.md](CHANGELOG.md).
