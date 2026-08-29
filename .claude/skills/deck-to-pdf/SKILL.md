---
name: deck-to-pdf
description: Export an existing HTML slide deck to a high-resolution PDF, one PDF page per slide (or per reveal step). Use when the user wants to share, print, or archive an HTML presentation as a PDF, convert a slide deck to PDF, or generate a PDF from a VISlide/reveal-style deck. Renders each slide state via headless Chrome at 2x/3x for crisp output on 1080p/4K, and lets you pick exactly which reveal steps become pages.
---

# deck-to-pdf — HTML slide deck → high-resolution PDF

Turns an HTML deck into a PDF where each page is one rendered slide state. Built for
VISlide decks but works with any deck that navigates via a `#slide/step` URL hash and
(ideally) exposes a global `slides[]` array with a `steps` count per slide.

The heavy lifting is a bundled script, `scripts/deck2pdf.py`. It drives one
persistent headless Chrome over the DevTools/CDP protocol, sets the layout viewport
to the deck's authored size with a device-scale factor (so captures are 2x/3x =
sharp), reads the per-slide step counts live from the page, screenshots each selected
state, and assembles the PNGs into a PDF with Pillow.

## When to use

- "Export/convert this deck to PDF", "share the slides as a PDF", "PDF version of the
  presentation", "print the deck".
- After building or editing a VISlide deck and the user wants a shareable artifact.

## Prerequisites

- Google Chrome installed (the script auto-finds it on macOS/Linux; or set `$CHROME`).
- A Python venv with `websocket-client` and `pillow`:
  ```sh
  python3 -m venv /tmp/deck2pdf-venv
  /tmp/deck2pdf-venv/bin/pip install -q websocket-client pillow
  ```
- **Serve the deck over http** if it fetches anything (e.g. `notes.md`, remote logos):
  ```sh
  cd <deck-dir> && python3 -m http.server 8000
  ```
  A `file://` URL is fine only if the deck loads nothing external. (Presenter notes
  are never included — the PDF renders the plain deck, never `?present=1`.)

## Run it

Default — one page per slide at its final (fully-revealed) step:
```sh
/tmp/deck2pdf-venv/bin/python3 <skill>/scripts/deck2pdf.py \
  --url http://localhost:8000/index.html \
  --out /abs/path/deck.pdf
```

Common variations:
- **Every reveal step as its own page:** `--pages all`
- **Per-slide step selection** (repeatable; steps and/or ranges): include exactly
  those steps for that slide, contiguously, in order:
  ```sh
  --slide 10=2,3,5 --slide 27=1-6
  ```
  (e.g. "for the gang-scheduling slide give me steps 2, 3 and 5; for the network
  fabric slide give me steps 1 through 6".)
- **Higher resolution:** `--scale 3` (3x native → ~5760x3240). Default `--scale 2`.
- **Different authored size:** `--width 1280 --height 720` (default 1920x1080).
- **Decks without a `slides[]` global:** pass the step counts explicitly,
  `--steps "0,4,0,5,2"` (one integer per slide, 0 = static).
- **Smaller/larger file:** `--jpeg-quality 90` (default; pages embed as JPEG inside
  the PDF to bound size while keeping full pixel dimensions). `--jpeg-quality 0`
  keeps lossless PNG (much larger).

The script prints a JSON summary (`out`, `pages`, `px`, `mb`) on success.

## How to choose the page set

- Ask the user what they want. Sensible default: **one page per slide, final step**
  (`--pages final`) — clean and compact, shows each slide fully revealed.
- Use `--pages all` only if they want every intermediate build state (can be many
  pages).
- Use `--slide N=SPEC` for slides where specific reveal states tell a story on their
  own (e.g. a before/after or a step-by-step diagram) — pick the meaningful steps and
  skip empty/intermediate ones (step 0 of an animated diagram is often blank).

## Verify before reporting done

1. Report the page count and confirm it matches the intended selection
   (final mode: one per slide; plus any per-slide overrides change the count).
2. Confirm the page pixel dimensions are `width*scale x height*scale`
   (e.g. 3840x2160 at scale 2, 1920x1080 authored).
3. Re-render a few PDF pages back to images and look: title present and sharp;
   any per-slide-override slides show the intended distinct states; no blank pages;
   no presenter notes; full-bleed with no browser chrome.
4. Report the final PDF path, page count, per-page dimensions, and file size.

## Notes / gotchas

- The script hides the deck's transient on-screen keyboard hint (`.hint`) via injected
  CSS so it never appears in the PDF. It does not modify the deck files.
- Give animated slides a moment to paint: `--settle 1.3` (seconds) is the default;
  raise it for heavy SVG animations.
- If the deck uses a different hash scheme than `#slide/step`, this script won't drive
  it — adapt the `location.hash` line in `capture()`.
- Chrome headless in a sandbox may need elevated permissions; if a plain run is
  blocked, retry with the environment's escape hatch for spawning Chrome.
