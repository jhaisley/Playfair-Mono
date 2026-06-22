SOURCES=$(shell uv run --no-project python scripts/read-config.py --sources)
FAMILY=$(shell uv run --no-project python scripts/read-config.py --family)
DRAWBOT_SCRIPTS=$(wildcard documentation/*.py)
DRAWBOT_OUTPUT=$(patsubst %.py,%.png,$(DRAWBOT_SCRIPTS))

help:
	@echo "###"
	@echo "# Build targets for $(FAMILY)"
	@echo "###"
	@echo
	@echo "  make build:  Builds the fonts and places them in the fonts/ directory"
	@echo "  make test:   Tests the fonts with fontspector"
	@echo "  make proof:  Creates HTML proof documents in the proof/ directory"
	@echo "  make images: Creates PNG specimen images in the documentation/ directory"
	@echo

build: build.stamp

venv: .venv

.venv: pyproject.toml uv.lock
	uv sync

customize: venv
	uv run python scripts/customize.py

build.stamp: venv sources/config.yaml $(SOURCES)
	rm -rf fonts
	for config in sources/config*.yaml; do uv run gftools builder $$config; done && touch build.stamp

test: build.stamp
	which fontspector || (echo "fontspector not found. Please install it with 'cargo binstall fontspector'." && exit 1)
	TOCHECK=$$(find fonts/variable -type f 2>/dev/null); if [ -z "$$TOCHECK" ]; then TOCHECK=$$(find fonts/ttf -type f 2>/dev/null); fi ; mkdir -p out/ out/fontspector; fontspector --profile googlefonts -l warn --full-lists --succinct --html out/fontspector/fontspector-report.html --ghmarkdown out/fontspector/fontspector-report.md --badges out/badges $$TOCHECK  || echo '::warning file=sources/config.yaml,title=fontspector failures::The fontspector QA check reported errors in your font. Please check the generated report.'

proof: venv build.stamp
	which diff3proof || (echo "diff3proof not found. Please install it with 'cargo binstall diffenator3'." && exit 1)
	TOCHECK=$$(find fonts/variable -type f 2>/dev/null); if [ -z "$$TOCHECK" ]; then TOCHECK=$$(find fonts/ttf -type f 2>/dev/null); fi ; mkdir -p out/ out/proof; uv run diff3proof $$TOCHECK --output out/proof

images: venv $(DRAWBOT_OUTPUT)

%.png: %.py build.stamp
	uv run python $< --output $@

clean:
	rm -rf .venv build.stamp out
	find . -name "*.pyc" -delete

update-project-template:
	npx update-template https://github.com/googlefonts/googlefonts-project-template/

update: venv
	uv lock --upgrade
	git commit -m "Update requirements" uv.lock || true
	git push
