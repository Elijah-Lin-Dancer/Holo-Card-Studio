# Contributing to HoloLab Studio

Thanks for wanting to help! This project is a portfolio piece and an open
gallery: anyone can turn **one sentence into a permanent 3D holographic card**
in the public exhibition hall. There are two ways to contribute — submit a
card, or improve the code.

---

## 📮 Submit a card (no coding needed)

The gallery is built for this: type a sentence, get a card, share it forever.

### Via the Create studio (recommended)

1. Open the **Live Gallery** → **Create**.
2. Type **one sentence** (your idea), then generate a detailed design.
   Tweak the design text if you like.
3. Tap **Save to my cards** (private, stays in your browser), then
   **Request publish**.
4. A prefilled GitHub Issue opens — add your name and submit it.

### Via a direct Issue

Open an Issue with the title prefix `[Submission]` and include:

```
**Idea:** <one sentence, ≤ 200 chars>
**Language:** zh | en | de
**Design:** <detailed description, ≤ 4000 chars>
**Author:** <your name / handle>
```

### Review rules (enforced by the pipeline)

| Rule | Limit |
|---|---|
| Idea length | ≤ 200 characters |
| Design length | ≤ 4000 characters |
| Card-face language | Chinese · English · German (other languages are hand-made by the maintainer) |
| Same author | ≤ 3 cards per 24h, and ≤ 1 pending `[Submission]` issue at a time |
| Content | blocked-category scan runs on every submission (minors-related sexual content is a hard rejection) |

Approved cards are rendered (4-layer AI art → Blender 3D → preview video),
committed, deployed to the gallery, and the Issue is closed with the live link.
Your card stays in the hall **forever**, credited to you.

> 🛡️ **Card quality gate — read before shipping any card:** every card (submitted
> via Issue, made locally, or by the maintainer) must pass the **five gates** in
> [`docs/CARD-QUALITY.md`](docs/CARD-QUALITY.md): prompt locks (complete limbs,
> strong subject/background contrast) → background never same-toned as the subject
> → matting self-check on the transparent channel → front-view readability
> (a card must read at rest, not only when rotated) → no batch-speed waivers.
> Missing limbs or "invisible" (transparent) subjects are **defects, not features**.

---

## 🧑‍💻 Local development

### Environment

- Python 3.10+
- Node.js 18+ (for the card `web/` template)
- Blender 4.5 — the pipeline auto-downloads a portable build, or you can drop
  one into `tools/` (see below)

### Run the gallery locally

```bash
cd gallery
python3 -m http.server 4191
# open http://127.0.0.1:4191
```

### Make a card locally (one sentence)

```bash
pip install -r generator/requirements.txt
cp .env.example .env   # add your ARK_API_KEY for the AI art step
python3 generator/scripts/one_shot_card.py "your one sentence"
python3 generator/scripts/ai_generate.py --project generator/projects/<slug>
python3 generator/scripts/run_pipeline.py --project generator/projects/<slug>
python3 generator/scripts/publish_card.py --project generator/projects/<slug>
git add -A && git commit -m "add card <slug>" && git push
```

GitHub Actions deploys the gallery automatically.

> **Reference-photo cards** (a pet, a friend, a character): drop the photo at
> `generator/projects/<slug>/ref.png` — the pipeline generates from it.

### Blender portable build

```bash
# auto-download (SHA-256 verified) — or pre-place from a mirror:
mkdir -p tools && cp /path/to/blender-4.5.0-linux-x64.tar.xz tools/
```

---

## 🧪 Tests & quality gates

Every push runs `gallery-check` (GitHub Actions):

- **21+ pipeline tests** — config schema, manifest consistency, i18n coverage,
  importmap idempotency, thumbnails, asset validation, prompt building,
  preflight gating
- **Gallery health check** — every card's assets present, GLB valid,
  vendor in place

Run locally:

```bash
python3 -m pytest generator/tests -q
```

New card labels (`style_tags`) **must** have an entry in `gallery/i18n.js`
(dictionary `zh`/`en`), or the CI i18n test fails.

---

## 🌱 Code style

- Python: type hints on public functions, docstring explaining *why*, not just
  what.
- Keep the pipeline **idempotent**: re-running a step must not corrupt state.
- Front-end: vanilla JS, no frameworks. Static assets vendored locally — no CDN
  dependency at runtime.
- Commit messages describe **what changed** (e.g. `add card <slug>`,
  `fix: handle null input`), not the process behind it.

---

## 🙏 Credits

HoloLab Studio is built on top of the MIT-licensed
[holo-card-studio](https://github.com/EverettFish/holo-card-studio) upstream.
All card art is generated with the Doubao Seedream pipeline; 3D scenes are
built in Blender and composited live with Three.js.
