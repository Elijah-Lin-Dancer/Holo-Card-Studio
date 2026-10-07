# Changelog

All notable changes to HoloLab Studio are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project is pre-1.0.

## [Unreleased]

### Added
- Pipeline smoke tests: prompt building, asset validation, preflight gating
  (no API / Blender required)
- `CONTRIBUTING.md` — submission guide and local development docs

## [2026-10-07]

### Added
- **Yin-Shang Chronicles · 殷商纪** Vol.I–III complete — **14 cards total**:
  Vol.I 人物志 (妇好 · 武丁 · 盘庚 · 商汤 · 伊尹), Vol.II 重器典藏 (后母戊鼎 ·
  妇好鸮尊 · 四羊方尊), Vol.III 文明密码 (甲骨文 · 玄鸟 · 占卜 · 殷墟 · 战车 ·
  饕餮); earliest verifiable dynasty (oracle-bone evidence, c. 1600–1046 BCE),
  all 中文 card faces, each card carries a unique technique name
- New style tags i18n entries (迁都 · 开国 · 贤相 · 元圣 · 重器 · 鸮尊 · 羊尊 ·
  神话 · 占卜 · 都城 · 战车 · 饕餮)
- Streaming-style two-level category filters — gallery top row now shows
  `全部 · ⚽ Football · 🤣 Memes · 🎮 Games · 🏺 Civilization · 🎨 Art & Culture · 🌍 Travel`
  (45 cards mapped to 6 categories, `category` field in cards.json); picking a
  category reveals a second row of fine-grained sub-tags with More/Less collapse.
  Raw style_tags no longer flood the top filter bar (73 chips → 7).

## [2026-10-06]

### Added
- **Vice City Nights · Characters Vol.I** — 6 cards (Tommy Vercetti,
  Lance Vance, Ken Rosenberg, Ricardo Diaz, General Cortez, Auntie Poulet),
  GTA Vice City tribute, English card faces

## [2026-10-01]

### Added
- **Haaland Multiverse** — 15 meme cards (Majin Buu · goal machine ·
  meditation · disco anthem · Viking · scallion-man · Chongqing monorail ·
  goalie-water thief · shark grin · Tom cat · raccoon · Wanglaoji · bun ·
  "eat the kid" · physics), EN/ZH/NO card faces
- **Pouch Invader** — community submission from Lay ("The Laytenant")
- Curated timeline view (C1) — bilingual creation notes for every card

## [2026-09-30]

### Added
- **FC Barcelona Legacy** — 6 cards (Messi ×4 eras, Cruyff, Guardiola),
  Spanish card faces
- **Satyajit Ray** — Bengali card face
- **Neeltje** — Friesian mare, Danish card face, first **password-locked**
  card (SHA-256 hash in registry)
- **Kenji Kishimoto** — Shatter Me fan-favourite, English card face
- **Elétrico 28** — Lisbon yellow tram, Portuguese card face
- **Luminous Blue Whale** — first community-submitted card via the
  auto-render pipeline (Issue → render → deploy)
- Password-locked cards: locked card stays hidden until unlocked in-hall

## [2026-09-29]

### Added
- Initial gallery: Messi, King (梅西称王) · King of Pop (流行之王) ·
  Stellar Expedition (星辰远征) · Great Sage (齐天大圣) · Aurora Ridge snow
  leopard · Frida Kahlo
- **The Reus Trilogy** — 3 cards (BVB · DFB · LA Galaxy), German card faces
- Four-layer AI pipeline: subject / background / line-art / typography
  (Seedream → rembg → OpenCV → font rendering)
- Blender parallax + rainbow-foil scene → GLB export
- Three.js real-time viewer (parallax · foil · stardust · glow)
- One-sentence → card pipeline with language auto-detection
  (zh · en · de · es · bn · da · pt · no)
- Structured card backs (career stats · honors · quote, in the card's own
  language)
- GitHub Pages deployment, zero backend, zero database

### Changed
- Pipeline hardening: push-retry ×3 + auto-deploy dispatch for concurrent
  renders
- Repository slimming: git gc 996M → 124M
