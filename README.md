# HoloLab Studio

**English · [中文](README.zh-CN.md)**

> One sentence → a 3D holographic card whose light shifts with your gaze → a live online gallery, playable by anyone on Earth.

**▶ [Live Gallery](https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/)**

A complete **AIGC pipeline** that turns one sentence into an interactive 3D holographic collectible card: Doubao Seedream draws the layered art, Blender builds the parallax / rainbow-foil 3D scene, Three.js composites it live in the browser — drag the card, push the subject forward, ease the background back, watch the rainbow foil shift with the angle. Cards are published to a pure-static gallery (GitHub Pages, zero server, zero database) with one command.

*Portfolio project · AI × 3D intersection · 100% static front-end*

| | |
|---|---|
| **Layered art** | Doubao Seedream 5.0 (Flash) + rembg cutout + OpenCV line-art extraction |
| **3D pipeline** | Blender 4.5 (portable, auto-download) → glTF export |
| **Real-time render** | Three.js + GLSL shaders (parallax / rainbow foil / stardust / glow) |

---

## Screenshots

Light theme · full page:

![HoloLab gallery — light theme](docs/screenshots/gallery-light.jpg)

Dark theme · hero (card removed, centered narrative):

![HoloLab hero — dark theme](docs/screenshots/gallery-dark-hero.png)

Dark theme · card wall:

![HoloLab card wall — dark theme](docs/screenshots/gallery-dark.png)

---

## Why it's worth your time

This is not "tune an image model and output a picture" — it is a complete engineering chain that turns generative models into a playable product:

| Capability | Evidence in this repo |
|---|---|
| **AI application** | Doubao Seedream API integration; **divide-and-conquer** layered generation (subject / background / line-art / typography); prompt engineering; image-to-image subject retention |
| **3D graphics** | Blender procedural scenes (parallax UV, rainbow-foil material node group); glTF export; Three.js GLSL fragment shader that rebuilds the material in real time |
| **Systems engineering** | Python pipeline (generate → validate → render → export → publish); static site generation; one-command publish; CI-ready layout |
| **Product design** | Masonry gallery, per-card permanent URLs, style filters, mobile adaptation, share-and-play |

**Front-end showcase (v2):** dual themes (dark stage / light cabinet), bilingual UI (EN / 中文), stardust particles, aurora, cursor glow, per-letter title reveal, staggered card entrance with tilt, glassmorphism chips — all vanilla JS, zero frameworks, zero backend.

---

## System architecture

```
┌─────────────────────── Local toolchain ───────────────────────┐
│  One sentence / one photo                                     │
│     │                                                         │
│     ▼                                                         │
│  ai_generate.py (Doubao Seedream 5.0)                         │
│     ├─ subject.png   generate → rembg cutout → transparent PNG│
│     ├─ background.png same-style empty scene (lower space kept)│
│     ├─ lineart.png   OpenCV contour extraction (pixel-registered)│
│     └─ text.png      typography layer (precise font layout)   │
│     │                                                         │
│     ▼                                                         │
│  run_pipeline.py (Blender 4.5, headless, auto-download + SHA-256)│
│     ├─ card.blend       editable 3D scene                     │
│     ├─ renders/hero.png Cycles front render                   │
│     └─ web/             Three.js viewer + card.glb            │
│     │                                                         │
│     ▼                                                         │
│  publish_card.py (one-command publish: WebP compress + preview│
│                   animation + manifest update, idempotent)    │
└───────────────────────┬───────────────────────────────────────┘
                        │ git push (pure static, zero backend)
                        ▼
        GitHub Pages live gallery (masonry + filters + per-card URL)
```

---

## Features

- **One-sentence card creation** — type an idea; the local expander engine turns it into a structured detailed description (subject / background / palette / line-art / typography) that you can edit before generating.
- **Language follows your input** — card text is produced in the language you typed (CJK → 中文, otherwise English fallback), in both the front-end expander and the local `one_shot_card.py` pipeline.
- **Gallery** — masonry card wall with style filters (all / football / legend / night-scene), per-card permalinks, drag-to-tilt parallax.
- **Create studio** — dual input boxes (one-sentence idea → generated detailed description → editable), local preview, zero API usage in the browser (the API key never enters the front-end).
- **Dual themes + bilingual UI** — dark / light, EN / 中文, shareable `?lang=` URL switch.

---

## Quick start

### Browse the gallery (no setup needed)

Open **[https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/](https://Elijah-Lin-Dancer.github.io/Holo-Card-Studio/)** — it is fully static.

### Run the gallery locally

```bash
cd gallery && python3 -m http.server 8000   # open http://127.0.0.1:8000
```

### Make a card with one sentence (local pipeline)

```bash
# 1. Requirements
pip install pillow opencv-python-headless rembg onnxruntime
# .env (gitignored — never commit it)
ARK_API_KEY=your_key

# 2. Generate the card config from one sentence
python3 generator/scripts/one_shot_card.py "给中国航天员设计一张全息收藏卡"

# 3. Generate layered art → run the Blender pipeline → publish to gallery
python3 generator/scripts/ai_generate.py --project generator/projects/<id>
python3 generator/scripts/run_pipeline.py  --project generator/projects/<id>
python3 generator/scripts/publish_card.py  --project generator/projects/<id> --id <id> --tags "风格,题材"
```

The publish step is fully automatic: WebP compression (PNG→WebP, −81%), 96-frame preview animation (Blender turntable → `preview.webm`), and `cards.json` update — no manual compression or rendering. Re-runs are idempotent (`--skip-preview` skips the animation).

Blender needs **no manual install** — the pipeline auto-downloads the official portable build to `<repo>/tools/` with SHA-256 verification.

**Reference-photo card** (pet, friend, character):

```bash
python3 generator/scripts/ai_generate.py --project generator/projects/<id> --reference photo.jpg
```

Seedream keeps the subject's pose and composition, re-drawing it in card style.

**Model defaults (locked):** image `doubao-seedream-5-0-flash-260915` · text `doubao-seed-2-0-mini-260428` · video `doubao-seedance-2-0-fast` (account not yet enabled).

---

## Repository layout

```
holo-lab/
├── gallery/                      # pure-static front-end (index/create/theme/i18n/cards.json)
│   ├── index.html                # masonry gallery home
│   ├── create.html               # create studio (dual input boxes)
│   ├── cards.json                # card manifest (JSON-driven, no database)
│   └── cards/<card-id>/          # per-card assets: thumb.jpg · card.jpg · scene.glb
├── generator/
│   ├── scripts/
│   │   ├── one_shot_card.py      # one-sentence → card-config.json (language-aware)
│   │   ├── ai_generate.py        # Seedream layered drawing (core increment)
│   │   ├── run_pipeline.py       # Blender build/render/export orchestration
│   │   ├── build_card.py         # procedural 3D scene + material nodes
│   │   ├── export_web.py         # glTF/GLB export
│   │   ├── generate_typography.py# precise text-layer layout
│   │   ├── validate_assets.py    # 4-layer asset health check
│   │   ├── ensure_blender.py     # Blender auto-download + SHA-256
│   │   ├── render_preview.py     # turntable frames (360×500 / 96 frames)
│   │   ├── publish_card.py       # one-command publish (core increment)
│   │   └── web-template-holographic/  # Three.js viewer template
│   └── projects/<card-id>/       # per-card working dir
├── docs/                         # architecture · AI pipeline · graphics · whitepaper
└── .github/workflows/deploy.yml  # CI deploy
```

---

## Example cards

- **Messi, King** (梅西称王) — Argentina No.10 · Holographic Archive series
- **King of Pop** (流行之王) — Michael Jackson · Legend series
- **Stellar Expedition** (星辰远征) — taikonaut · generated by one-sentence pipeline
- **Great Sage** (齐天大圣) — Sun Wukong · Journey to the West series · generated by one-sentence pipeline

---

## Roadmap

- [x] Seedream layered generation + cutout + line-art extraction
- [x] Blender holographic pipeline + Three.js viewer
- [x] Static gallery + one-command publish + CI-ready
- [x] Asset compression (PNG→WebP, −81%, in publish pipeline)
- [x] Animated preview (Blender turntable → preview.webm + hover play)
- [x] One-sentence auto card (text model → config → full auto loop)
- [x] Language-following card text (CJK / English fallback)
- [ ] Lenticular dual-image raster mode
- [ ] Auto gallery categorization (person / style / rarity)

---

## Docs

- [Architecture & system design](docs/architecture.md)
- [AI layered pipeline](docs/ai-pipeline.md)
- [3D rendering & shaders](docs/graphics.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Whitepaper](docs/whitepaper/deliverables/final.md)
- [Toolkit roadmap](docs/TOOLKIT-ROADMAP.md)

---

## Acknowledgement

Built on the MIT-licensed upstream [`holo-card-studio`](https://github.com/EverettFish/holo-card-studio) by EverettFish — original concept; all derivative work retains upstream attribution. Individual increments include: **AI layered-drawing automation** (upstream relied on manual Codex calls; this repo is a reproducible Doubao API pipeline), **OpenCV line-art extraction**, **one-command publish & static gallery**, and the **deployment & documentation system**. Card art generated with Doubao Seedream; 3D scenes rendered with Blender.

## License

[MIT](LICENSE) © 2026 HoloLab Studio · Elijah Lin
