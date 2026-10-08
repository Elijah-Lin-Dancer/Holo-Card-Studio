# HoloLab Studio — one-command reproducibility
#
# Targets:
#   make setup     install Python deps + create .env template (Blender auto-downloads on first render)
#   make preview   serve the gallery locally at http://127.0.0.1:4191
#   make new       turn ONE sentence into a card config (prints the generated slug)
#   make render    AI-generate the four layers + run the Blender pipeline for a project
#   make publish   publish an existing project to the gallery manifest
#   make test      run the full CI test suite locally (same as gallery-check)
#   make check     preflight checks only (config fields, assets, caches)
#   make docs      show this help
#
# Usage examples:
#   make new SENTENCE="a snow leopard under the aurora"
#   make render SLUG=aurora-ridge
#   make publish SLUG=aurora-ridge
#   make card SENTENCE="..." SLUG=...   # shorthand: new + render in one call
#
# Full guide: docs/REPRODUCE.md

PY      ?= python3
PIP     ?= pip3
SERVER_PORT ?= 4191

# ---- bootstrap --------------------------------------------------------------

.PHONY: setup preview new render publish card test check docs

setup:
	$(PIP) install -r generator/requirements.txt
	@if [ ! -f .env ]; then cp .env.example .env && echo "created .env — add your ARK_API_KEY"; fi
	@echo "setup done. Next: make preview (browse) or make new (create)."

preview:
	cd gallery && $(PY) -m http.server $(SERVER_PORT)

# ---- one-sentence card ------------------------------------------------------

new:
	@test -n "$(SENTENCE)" || (echo "usage: make new SENTENCE=\"...\"" && exit 1)
	$(PY) generator/scripts/one_shot_card.py "$(SENTENCE)"

render:
	@test -n "$(SLUG)" || (echo "usage: make render SLUG=<slug>" && exit 1)
	$(PY) generator/scripts/ai_generate.py --project generator/projects/$(SLUG)
	$(PY) generator/scripts/run_pipeline.py --project generator/projects/$(SLUG)

card:
	@test -n "$(SENTENCE)" || (echo "usage: make card SENTENCE=\"...\" SLUG=<slug>" && exit 1)
	@test -n "$(SLUG)" || (echo "usage: make card SENTENCE=\"...\" SLUG=<slug>" && exit 1)
	$(PY) generator/scripts/one_shot_card.py "$(SENTENCE)" --outdir generator/projects/$(SLUG)
	$(PY) generator/scripts/ai_generate.py --project generator/projects/$(SLUG)
	$(PY) generator/scripts/run_pipeline.py --project generator/projects/$(SLUG)

# ---- quality & tests --------------------------------------------------------

test:
	$(PY) -m pytest generator/tests -q

check:
	$(PY) generator/scripts/preflight_card.py --all

# ---- publish an existing project -------------------------------------------

publish:
	@test -n "$(SLUG)" || (echo "usage: make publish SLUG=<slug>" && exit 1)
	$(PY) generator/scripts/publish_card.py --project generator/projects/$(SLUG)
	@echo "card published. commit + push to deploy: git add -A && git commit -m \"add card $(SLUG)\" && git push"

docs:
	@echo "HoloLab Studio quick reference — full guide in docs/REPRODUCE.md"
	@grep -E "^[a-z-]+:" Makefile | head -20
