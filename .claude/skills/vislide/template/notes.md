# Speaker Notes — VISlide template

Loaded at runtime by `index.html` and shown in the presenter view (press **P**).
Format: one `## <n> — <title>` section per slide, where `<n>` is the slide's
ARRAY POSITION (1-indexed), not the cosmetic label number. The leading number is
all that matters for matching; the title text after the em-dash is for your eyes.

The optional `(budget)` you can append to a heading is cosmetic in these notes;
the real per-slide countdown is driven by `SLIDE_SECONDS` in `index.html`.

Write each paragraph as one line; use `- ` for bullets (2-space indent = nesting)
and `[click]` cues to mark reveals.

---

## 1 — Title

- open here — one line on what the deck is, then move
- no budget on this slide (it's a title)

## 2 — Cards (1m)

- a grid of cards, revealed one per click
- [click] first card — the reveal pattern
- [click] second — reused component
- [click] third — readable hierarchy

## 3 — Hub & spokes (1m30s)

- [click] the Core appears first — the thing everything hangs off
- then each requirement card clicks in around it
- point: show a central concept with its satellite concerns

## 4 — Infographics

- divider — one line, then advance

## 5 — Animated flow (2m)

- walk the pipeline left to right, one stage per click
- [click] Ingest [click] Transform [click] Process [click] Serve
- the moving dots show data flowing along each arrow
- [click] the summary bar — each stage scales independently

## 6 — Layered stack (1m30s)

- build bottom to top, one layer per click
- [click] Presentation [click] Application [click] Platform [click] Infrastructure
- point: the same model repeats at every layer

## 7 — Pyramid (1m)

- static hierarchy — talk over it top to bottom
- hot/small at the top, cold/large at the bottom

## 8 — Code block (1m)

- [click] the terminal — what running it looks like
- [click] the punchline — one file, zero build

## 9 — Thank you

- close — point people at the slides[] array and inf*() helpers
