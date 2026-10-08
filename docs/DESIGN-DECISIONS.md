# Design Decisions — HoloLab Studio

> Why the gallery looks the way it does, why submissions require a GitHub account,
> and why we deliberately do **not** expose an open, anonymous "type a sentence →
> get a card" endpoint to every visitor.

---

## 1. The creative loop

HoloLab turns **one sentence** into a **3D holographic collectible card**:

```
sentence → card config → 4 AI-generated layers (subject / background / line-art / typography)
        → Blender scene build → GLB export → Three.js viewer → public gallery
```

Every card in the gallery is a small production run: it costs real AI API calls,
real render minutes, and real curation attention. This document records the
engineering and product decisions behind that loop.

## 2. How community submission works today

- Anyone can **view** the gallery — no account, no install, 100% static pages.
- To **submit** a card, a visitor writes one sentence in the **Create Studio**
  page, previews/edits the generated description, and is handed a **pre-filled
  GitHub issue** (`[Submission]` template).
- The `auto-render.yml` workflow listens for that issue: it generates the four
  layers with the ARK image API, renders the card with Blender, commits and
  pushes it, replies to the author with the live URL, and closes the issue.
- A `[Remove]` issue takes a card back down.
- Rate limits: per-author 24h cap, an open-issue cap, and a blocklist guard
  against spam and abuse.

So the pipeline is **fully automated end-to-end**, but the entry door is a
GitHub issue — which means the submitter needs a GitHub account.

## 3. Why we deliberately keep the anonymous door closed

We explored adding a lightweight backend endpoint (e.g. a serverless worker) so
that any visitor could POST a sentence and get a card with zero sign-up. We
decided **not** to. The reasons:

### 3.1 Cost — the only real bill is the AI API

| Resource | Cost model | Notes |
|---|---|---|
| GitHub Actions (public repo) | **Free, unlimited minutes** | Public repos get unlimited standard-runner minutes. Concurrency is the only soft cap (~20 parallel jobs on a free account) |
| GitHub Pages hosting | **Free** | Public Pages hosting has no charge |
| Blender rendering (cloud runner) | **Free** (Actions) | Render minutes are covered by the free tier above |
| **ARK image API (4 layers per card)** | **Pay-as-you-go** | **This is the only real money line.** One card = 4 image generations; 100 anonymous submissions = 400 calls charged to the repo owner's account |

An open anonymous endpoint turns the repo owner's API account into a public
printing press: anyone can burn quota at zero personal cost, and the bill has no
ceiling. That is not a scaling problem — it is an invitation to abuse.

### 3.2 Abuse & content safety

- Anonymous generation with no identity trail means **no accountability**:
  spam floods, low-effort garbage, and policy-violating content would all land
  in the gallery (or in the repo, since the render writes back).
- The GitHub-issue gate gives every submission a **traceable author**, which is
  what makes rate limits, the blocklist, and takedown workflows meaningful.

### 3.3 Curation quality

Every card in this gallery is intentional: a chosen subject, a deliberate
language, a designed punchline. An open firehose would drown the collection in
noise and destroy the "curated portfolio" character of the project.

### 3.4 Architecture simplicity

The site is 100% static — no backend, no database, no API keys in the browser.
That keeps it free to host, free to scale horizontally, and trivially
reproducible. A serverless endpoint would add a maintained component, a secret,
and a cost surface for a feature we believe is the wrong trade.

## 4. Existing defenses

- **Per-author rate limit**: 1 open submission per 24h per GitHub user.
- **Open-issue cap**: prevents a single author from queueing an infinite pile.
- **Blocklist**: repeat offenders are blocked at the workflow level.
- **[Remove] workflow**: any published card can be taken down via a `[Remove]`
  issue, with an audit trail.

## 5. Future evolution (not built, by design)

If HoloLab ever opens the door wider, the responsible paths are:

- **Quota / approval queue**: anonymous submissions land in a pending pool,
  rendered only after human review — adds moderation cost, keeps the bill sane.
- **Whitelisted community**: open submission to a curated group, not the public.
- **Bring-your-own-key**: submitters provide their own API key for their own
  card, so the owner's account is never exposed.
- **Paid tier**: sponsored/paid cards to cover API costs.

Each of these preserves the core constraint: **the repo owner's API account
must never be an unlimited public resource.**

---

## 6. Card language policy

Every card carries **one deliberate language** across its entire surface — card-face
typography, the back story, **and the technique name** (the technique line is printed
on the card face itself, below the tagline).

- **Default: English.** Most cards are made in pure English — face text, back story,
  technique name alike.
- **Chinese cultural series (殷商纪 / Yin-Shang Chronicles, etc.): Chinese only.**
  When the subject is our own cultural heritage, the full card speaks Chinese —
  title, tagline, back story, and the technique name (e.g. `青铜服牛` for
  Wang Hai, not `Bronze-Ox-Yoke`).
- **Other cultural subjects follow their own language**: Bengali (Satyajit Ray),
  Danish (Friesian horse), Portuguese (Lisbon tram), German (Marco Reus) — the
  language of the subject is the language of the card.

The technique-name language must always match the card's language; a Chinese card
with an English technique line is a defect, not a style choice.

---

*This document is a design decision record, not an apology. The GitHub-issue
gate is a feature: it makes submission safe, attributable, and cheap — and it
happens to look great on a résumé.*
