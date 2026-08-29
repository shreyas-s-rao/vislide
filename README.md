# VISlide

A Claude Code skill for building **animated, infographic-rich, single-file HTML
presentation decks**. No PowerPoint, no build step, no framework — one
self-contained `index.html` you can open in any browser.

## What you get

- **One-file decks** authored at 1920x1080, scaled to fit any screen.
- **Step-by-step reveals** — build a slide up click by click.
- **Animated SVG infographics** — pipelines with flowing dots, layered stacks,
  pyramids/hierarchies, hub-and-spoke diagrams, fan-out trees.
- **Synced presenter view** (`?present=1`) with speaker notes, next-slide preview,
  an elapsed timer, a whole-talk countdown, and an optional per-slide countdown.
- **Thumbnail overview** (press `T`) to jump between slides.
- **High-res PDF export** — turn any deck into a shareable PDF, one page per slide or per reveal step, at 2x/3x for crisp 1080p/4K.
- **Keyboard nav + deep-linkable** `#slide/step` hash routing.

## Install

### As a plugin (recommended — installable & updatable)

```
/plugin marketplace add shreyas-s-rao/vislide
/plugin install vislide@vislide
```

If prompted, run `/reload-plugins` to activate. The skill is then available as
`/vislide:vislide`.

### As a personal skill (copy the folder)

```sh
git clone https://github.com/shreyas-s-rao/vislide
cp -r vislide/.claude/skills/vislide ~/.claude/skills/vislide
```

Available in all your sessions; invoke with `/vislide` or let it trigger on
matching requests. For a single project, copy it to `<project>/.claude/skills/`
instead and commit it with the repo.

## What's inside

```
.claude-plugin/
├── plugin.json                 # plugin manifest
└── marketplace.json            # marketplace listing (install via /plugin)
.claude/skills/
├── vislide/                    # build the deck
│   ├── SKILL.md                # the method Claude follows
│   ├── template/
│   │   ├── index.html          # complete, working starter deck (all features)
│   │   └── notes.md            # matching presenter notes
│   └── reference/
│       └── infographics.md     # copyable inline-SVG infographic snippets
└── deck-to-pdf/                # export the deck to PDF
    ├── SKILL.md
    └── scripts/
        └── deck2pdf.py         # headless-Chrome high-res renderer + PDF assembler
```

## Export a deck to PDF

The bundled `deck-to-pdf` skill renders any `#slide/step` HTML deck to a
high-resolution PDF (one page per slide, or per reveal step, at 2x/3x for crisp
1080p/4K output). Ask Claude to "export this deck to PDF", or run the script:

```sh
python3 -m venv /tmp/deck2pdf-venv
/tmp/deck2pdf-venv/bin/pip install websocket-client pillow
cd <deck-dir> && python3 -m http.server 8000 &
/tmp/deck2pdf-venv/bin/python3 .claude/skills/deck-to-pdf/scripts/deck2pdf.py \
  --url http://localhost:8000/index.html --out deck.pdf
# one page per slide (final step). Add --pages all for every step,
# or --slide 10=2,3,5 --slide 27=1-6 to pick specific steps per slide.
```

## Try the template

```sh
# static view
open .claude/skills/vislide/template/index.html

# with presenter notes (needs http)
cd .claude/skills/vislide/template && python3 -m http.server 8000
# then open http://localhost:8000/index.html  (press P for presenter, T for thumbnails)
```

## License

MIT — see [LICENSE](LICENSE).
