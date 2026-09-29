# 🃏 HoloLab Studio

**One sentence → a 3D holographic card that shimmers with your viewing angle → a globally playable online gallery.**

HoloLab Studio is an end-to-end **AIGC pipeline**: a sentence (or a reference photo)
is layered into four card-art assets by the Doubao Seedream image model, assembled
into a parallax/holo-foil 3D scene in Blender, exported as GLB, and recomposited
in real time in the browser with Three.js — subject pops forward, background recedes,
and a rainbow foil sweeps as you rotate the card. Finished cards are published into
a purely static gallery (GitHub Pages, zero servers, zero databases) with one
command, so anyone can open a link and drag, flip, and tune the lighting.

> Portfolio project · AI × 3D intersection
> Asset layers: Doubao Seedream 5.0 + rembg matting + OpenCV lineart
> 3D pipeline: Blender 4.5 (auto-downloaded portable) → glTF export
> Real-time render: Three.js + GLSL shaders (parallax / foil / stars / bloom)

---

## ✨ Why it matters

This is not "call an image model and print a picture" — it is a production-grade
pipeline that turns a generative model into a playable product:

| Capability | Evidence |
|---|---|
| **AI application** | Seedream API integration; a **divide-and-conquer** 4-layer generation strategy (subject / background / lineart / text); prompt engineering; image-conditioned generation that preserves identity |
| **3D graphics** | Procedural Blender scene (parallax UV, foil material node groups); glTF export; GLSL fragment shader recomposition in Three.js |
| **Systems engineering** | Python pipeline (generate → validate → render → export → publish); static-site generation; idempotent publish script; CI/CD ready |
| **Product design** | Masonry gallery, per-card permanent URLs, style filters, mobile adaptation |

## 🧱 Architecture

```
┌────────────────────────────── Local toolchain ──────────────────────────────┐
│  one sentence / one photo                                                    │
│      │                                                                       │
│      ▼                                                                       │
│  ai_generate.py (Doubao Seedream 5.0)                                        │
│    ├─ subject.png     generate → rembg matting → transparent PNG             │
│    ├─ background.png  same-style environment, quiet lower third for type      │
│    ├─ lineart.png     OpenCV contour extraction from subject (pixel-registered)│
│    └─ text.png        precise font typesetting (never let AI draw text)      │
│      │                                                                       │
│      ▼                                                                       │
│  run_pipeline.py (Blender 4.5 portable, SHA-256 verified)                    │
│    ├─ card.blend          editable 3D scene                                  │
│    ├─ renders/hero.png    Cycles hero render                                 │
│    └─ web/                Three.js viewer + card.glb                         │
│      │                                                                       │
│      ▼                                                                       │
│  publish_card.py (one-command publish)                                       │
└──────────────────────────────┬───────────────────────────────────────────────┘
                              │ git push (pure static, zero backend)
                              ▼
        GitHub Pages online gallery (masonry + filters + per-card URLs)
```

## 🚀 Quick start

Requirements: Python 3.10+ (`pip install pillow opencv-python-headless rembg
onnxruntime`), Node.js 18+, and a Doubao (Volcano Ark) API key in `.env`:

```bash
# .env (git-ignored)
ARK_API_KEY=your-key
```

Blender is downloaded automatically (portable, checksum-verified). For mainland
China networks, drop the same package from a mirror into `tools/` first.

```bash
# 1) configure generator/projects/<id>/card-config.json
# 2) generate the four asset layers
python3 generator/scripts/ai_generate.py --project generator/projects/<id>
# 3) run the Blender pipeline
python3 generator/scripts/run_pipeline.py --project generator/projects/<id>
# 4) preview locally
cd generator/projects/<id>/web && npm install && node server.mjs   # :4173
# 5) publish into the gallery
python3 generator/scripts/publish_card.py --project generator/projects/<id> --id <id> --tags "style,theme"
cd gallery && python3 -m http.server 4174
```

Reference-photo cards (pet / friend / character):

```bash
python3 generator/scripts/ai_generate.py --project generator/projects/<id> --reference photo.jpg
```

Deployment to GitHub Pages: see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## 📁 Layout

```
holo-lab/
├── generator/
│   ├── scripts/
│   │   ├── ai_generate.py         # Seedream layered generation (core addition)
│   │   ├── run_pipeline.py        # pipeline orchestration
│   │   ├── build_card.py          # procedural Blender scene + materials
│   │   ├── export_web.py          # glTF export
│   │   ├── generate_typography.py # text-layer typesetting
│   │   ├── validate_assets.py     # asset QA (real alpha / lineart extrema)
│   │   ├── ensure_blender.py      # portable Blender + SHA-256
│   │   ├── publish_card.py        # one-command gallery publish (core addition)
│   │   └── web-template-holographic/
│   └── projects/<card-id>/
├── gallery/                       # static gallery (GitHub Pages ready)
│   ├── index.html                 # masonry homepage
│   ├── cards.json                 # JSON-driven manifest (no database)
│   ├── vendor/three/              # shared three.js dependency
│   └── cards/<card-id>/
├── docs/                          # architecture / AI pipeline / graphics
└── .github/workflows/deploy.yml   # CI auto-deploy
```

## 📖 Docs

- `docs/architecture.md` — system design and key decisions
- `docs/ai-pipeline.md` — four-layer generation, prompt engineering, matting & lineart
- `docs/graphics.md` — parallax UV, foil material, GLSL shaders
- `docs/DEPLOYMENT.md` — going live on GitHub Pages

## 🎴 Example card

「梅西称王 / King Messi」— Legend · Argentina No.10 · Holographic collectible.

## ⚖️ Open-source notice

Built on [EverettFish/holo-card-studio](https://github.com/EverettFish/holo-card-studio)
(MIT). Personal additions: **automated AI layered generation** (the original relies
on a Codex agent to call image models manually; this project replaces it with a
reproducible Doubao API pipeline), **OpenCV lineart extraction**, **one-command
publish + static gallery system**, and **deployment/docs**. Blender scene-building
scripts follow the original implementation; asset specs stay compatible.

## 📄 License

MIT
