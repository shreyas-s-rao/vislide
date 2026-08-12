---
name: vislide
description: Build animated, infographic-rich, single-file HTML presentation decks. Use when the user wants to create a slide deck / presentation / talk as HTML (not PowerPoint), especially one with step-by-step reveals, animated SVG infographics (flows with moving dots, layered stacks, pyramids, hub-and-spoke diagrams), a synced presenter view with speaker notes and countdown timers, and a thumbnail overview. Also use when asked to add slides, infographics, presenter notes, or timers to an existing VISlide deck.
---

# VISlide — build animated HTML presentation decks

VISlide decks are **one self-contained `index.html`** file: no build step, no
framework, no dependencies (a Google Font is loaded with a system fallback).
Open it in any browser. A sibling `notes.md` powers the presenter view.

Everything a user asks for — new slides, new infographics, reveal animations,
presenter notes, per-slide timers — is done by editing `index.html` (and
`notes.md`). This skill teaches the architecture and the authoring patterns.

## Start from the template

The working reference deck is `template/index.html` + `template/notes.md` in this
skill directory. It already demonstrates every feature. To start a new deck, copy
both files to the user's target directory and replace the `slides[]` content and
`inf*()` functions. Never rebuild the engine from scratch — copy the template and
edit its data.

```
cp <skill>/template/index.html  <target>/index.html
cp <skill>/template/notes.md    <target>/notes.md
```

## Architecture (how the one file works)

- **Authored at a fixed 1920x1080.** `#deck` is a 1920x1080 box; JS `fit()` scales
  it to the window with `transform:scale()` and centers it. Author everything as if
  the canvas is exactly 1920x1080 — never worry about the real window size.
- **`slides[]`** is the single source of truth. Each entry:
  `{label:"NN Title", steps:N, html:`...`, center?:true}`.
  - `label` — the leading number is **cosmetic** (footer/thumbnail caption). The
    slide's **array position** is its real index, used by routing, counter,
    presenter, notes, and timers. If you delete/reorder slides, the array position
    is what changes; renumber `label`s for cosmetics only.
  - `steps` — the highest `data-step`/`data-appear` on that slide. `0` = static.
    Getting this wrong means reveals never fire (too low) or dead clicks (too high).
  - `center:true` — vertically/horizontally centered layout (title & divider slides).
- **Reveal engine.** Inside a slide's html, tag any element with:
  - `data-step="N"` or `data-appear="N"` — hidden until the viewer reaches step N.
  - `data-until="M"` — also hides again after step M (for elements that should only
    exist during a step range, e.g. a box that gets replaced on the next click).
  - The engine adds/removes the `.vis` class; CSS fades+slides it in. Baseline is
    step 0 (nothing revealed). A slide with `steps:4` has states 0..4.
- **Navigation & routing.** Arrows/Space/click advance a step, then the slide. The
  URL hash is `#slide/step` (1-indexed slide), so `index.html#5/3` deep-links to
  slide 5 at step 3. `Home`/`End` jump to first/last. `F` fullscreen.
- **`bar(right)`** renders the top brand bar; pass a section/chapter tag or `''`.
  **`chapter(n,title,kick)`** returns a centered divider slide object.

## The infographic method (inline SVG generated from JS)

Infographics are functions returning an SVG **string**, interpolated into a slide's
html: `<div class="svg-wrap">${infFlow()}</div>`. Key rules:

- **One coordinate system per SVG** via `viewBox="0 0 W H"` (commonly `1440 x H`).
  `.svg-wrap svg` scales to the slide width, so design in viewBox units.
- **Stage reveals with `class="s" data-appear="N"`** on `<g>` groups — the same
  step engine drives SVG elements, so a diagram builds up click-by-click.
- **Arrows:** define a `<marker>` in `<defs>` once, reference with `marker-end`.
- **Moving-dot packets** (data flowing along an arrow): give the path an `id`, then
  `<circle><animateMotion><mpath href="#id"/></animateMotion></circle>`.
- **Helper functions** (`box()`, etc.) keep repeated shapes consistent. The template
  ships `box`, `infFlow` (animated pipeline), `infStack` (layered stack),
  `infPyramid` (hierarchy), `infHubSpokes` (central object + orbiting cards).
- A **copyable snippet library** of these building blocks is in
  `reference/infographics.md` — read it when generating a new infographic and adapt
  the closest pattern rather than starting from a blank SVG.

**When the user asks for a NEW infographic**, pick the closest pattern from the
reference, copy it into a new `infXxx()` function, change the data arrays and
labels, wire `data-appear` for the reveal order, set the slide's `steps` to the
highest step used, and verify by screenshot (below).

## Presenter view, notes, and timers

- **`?present=1`** opens a synced presenter window (the deck's `P` key does this).
  It shows current notes, next-slide title, a step counter, an **elapsed** timer, a
  mandatory **overall countdown** (whole-talk remaining), and an optional
  **per-slide countdown**. Both windows sync through `localStorage`, so advancing in
  either moves both.
- **`notes.md`** holds the speaker notes: one `## <n> — <title>` section per slide,
  keyed by array position. `-`/`•` bullets (2-space indent nests), `` `code` ``
  spans, and `[click]` cues render with highlighting. The presenter fetches this, so
  it only works when served over http (e.g. `python3 -m http.server`); over `file://`
  the deck still runs, notes just show a hint.
- **Timers come from `SLIDE_SECONDS`** in `index.html` — a 1-indexed array of seconds
  per slide (`0` = no budget, e.g. title/divider). `TOTAL_SECONDS` (the overall
  countdown) is their sum. The per-slide countdown shows only when a slide's budget
  is non-zero; it runs green → amber (last 25% or 30s) → red and negative past zero.

### Computing per-slide timings from user input

When the user gives timings (in chat or a file), **you** compute `SLIDE_SECONDS`:

1. Parse their input. It may be per-slide (`16 - 3m`) or **grouped** (`13,14 - 3m`,
   meaning a shared 3-minute budget for slides 13 and 14).
2. **Split grouped budgets evenly** across their slides unless told otherwise
   (`13,14 - 3m` → 90s each). Convert all to seconds.
3. Emit the 1-indexed `SLIDE_SECONDS` array (index 0 is a leading `0` placeholder so
   slide N maps to `SLIDE_SECONDS[N]`). Dividers/title/`na` → `0`.
4. Optionally append the budget to each `notes.md` heading (`## 16 — Storage (3m)`)
   for the presenter's eyes — cosmetic only.
5. State the computed total back to the user and confirm it matches their intended
   talk length.

## Thumbnail overview

Press **T** (deck window only) for a full-screen grid of live slide miniatures
(each a scaled clone showing all steps revealed). Click a tile to jump. `Esc`/`T`
closes. No code change needed; it is built once on first open.

## The verify loop (do this after every change)

1. **Parse-check** the script block — a syntax error blanks the whole deck:
   ```
   node -e 'const fs=require("fs");const h=fs.readFileSync("index.html","utf8");
   const m=h.match(/<script>([\s\S]*?)<\/script>/g);
   let s=m.map(x=>x.replace(/<\/?script>/g,"")).join("\n");
   try{new Function(s);console.log("PARSE OK");}catch(e){console.log("FAIL:",e.message);}'
   ```
2. **Screenshot the changed slide at its final step** with headless Chrome and LOOK
   at it (overflow, clipping, alignment). Deep-link via the hash:
   ```
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
     --headless --disable-gpu --hide-scrollbars --window-size=1920,1080 \
     --screenshot=/tmp/s.png "file://<abs>/index.html#<N>/<step>"
   ```
   (In sandboxed environments, headless Chrome may need the Bash tool's
   `dangerouslyDisableSandbox: true`.)
3. For infographics with multiple reveal steps, screenshot **each** step to confirm
   consecutive states differ and nothing overlaps.
4. Presenter view needs http, not file://: `python3 -m http.server`, then capture
   `http://localhost:PORT/index.html?present=1`.

## Common tasks — quick recipes

- **Add a content slide:** copy an existing `slides[]` entry, change `label`, set
  `steps` to the max `data-step` you use, write the html. Add a `## N — Title`
  section to `notes.md` at the matching array position.
- **Add a divider:** `chapter("07","The Solution","Section 3"),` in the array.
- **Delete/reorder slides:** edit the array; then renumber `label` leading numbers,
  the `SLIDE_SECONDS` entries, and the `## N` notes headings to match the new array
  positions. Re-verify the counter and presenter line up.
- **New infographic:** adapt a snippet from `reference/infographics.md`.
- **Change theme:** edit the `:root` CSS custom properties and the JS palette
  constants (`ACC`, `GRN`, ...) together — they mirror each other.

## Style defaults (match the template)

Clean, modern, lots of whitespace. Big bold headings, muted descriptions, mono for
labels/code. Reveal complex slides progressively rather than dumping everything at
once. Prefer a diagram over a bullet list where it clarifies. Keep one idea per
slide.
