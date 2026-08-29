#!/usr/bin/env python3
"""
deck2pdf — render an HTML slide deck to a high-resolution PDF, one PDF page per
(slide, step) state you select.

Designed for VISlide-style decks (a `slides=[]` array with a `steps` count per
slide and `#N/S` hash routing), but works with ANY deck that:
  - exposes a global `slides` array where each entry has a numeric `steps`
    (or where you pass --steps to override), AND
  - navigates to slide N (1-indexed) step S when `location.hash = "#N/S"`.

Method: drive one persistent headless Chrome over the DevTools/CDP protocol.
Set the layout viewport to the deck's authored size with a deviceScaleFactor,
so screenshots come out at (size * scale) — crisp on 1080p/4K. Read the per-slide
step counts live from the page. Assemble the PNGs into a PDF with Pillow.

Requires: Google Chrome, Python packages `websocket-client` and `pillow`
(the SKILL.md sets up a venv). Serve the deck over http first if it fetches
notes.md or other files; a plain file:// URL works if it doesn't.

Usage:
  python3 deck2pdf.py --url http://localhost:8000/index.html --out deck.pdf
  python3 deck2pdf.py --url file:///abs/index.html --out deck.pdf --pages final
  python3 deck2pdf.py --url ... --out ... --pages all
  python3 deck2pdf.py --url ... --out ... --pages final \
      --slide 10=2,3,5 --slide 27=1-6            # per-slide overrides
  python3 deck2pdf.py --url ... --out ... --scale 3 --width 1920 --height 1080

--pages modes:
  final  (default) one page per slide at its FINAL step (step == slides[i].steps)
  all              one page per step 0..steps for every slide
Per-slide --slide N=SPEC overrides the mode for that slide. SPEC is a comma list
of steps and/or ranges: "2,3,5" or "1-6" or "0,2-4". Use N=SPEC to include exactly
those steps for slide N (1-indexed), in the given order, contiguously at N's place.
"""
import argparse, json, subprocess, time, os, sys, base64, tempfile, shutil, urllib.request

def log(*a): print(*a, file=sys.stderr, flush=True)

def find_chrome():
    for p in [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
        os.environ.get("CHROME", ""),
    ]:
        if p and os.path.exists(p):
            return p
    raise SystemExit("Chrome not found. Set $CHROME to the binary path.")

def parse_slidespec(spec):
    """'2,3,5' or '1-6' -> [2,3,5] / [1,2,3,4,5,6]"""
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out += list(range(int(a), int(b) + 1))
        elif part != "":
            out.append(int(part))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="deck URL (http://... or file:///abs/index.html)")
    ap.add_argument("--out", required=True, help="output PDF path")
    ap.add_argument("--pages", default="final", choices=["final", "all"], help="default page-selection mode")
    ap.add_argument("--slide", action="append", default=[], metavar="N=SPEC",
                    help="per-slide override, e.g. --slide 10=2,3,5 --slide 27=1-6 (repeatable)")
    ap.add_argument("--steps", default="", help="comma list overriding per-slide step counts if the page has no slides[] (e.g. '0,4,0,5')")
    ap.add_argument("--scale", type=int, default=2, help="deviceScaleFactor (2 = 2x native; 3 for 4K-ish)")
    ap.add_argument("--width", type=int, default=1920, help="deck authored width (CSS px)")
    ap.add_argument("--height", type=int, default=1080, help="deck authored height (CSS px)")
    ap.add_argument("--settle", type=float, default=1.3, help="seconds to wait after navigating before capture")
    ap.add_argument("--port", type=int, default=9333, help="Chrome remote-debugging port")
    ap.add_argument("--jpeg-quality", type=int, default=90, help="JPEG-in-PDF quality (1-95); 0 = keep PNG (huge)")
    ap.add_argument("--keep-pngs", action="store_true", help="do not delete the intermediate PNG dir")
    args = ap.parse_args()

    overrides = {}
    for ov in args.slide:
        n, spec = ov.split("=", 1)
        overrides[int(n)] = parse_slidespec(spec)

    chrome = find_chrome()
    out_dir = tempfile.mkdtemp(prefix="deck2pdf-pngs-")
    profile = tempfile.mkdtemp(prefix="deck2pdf-chrome-")

    proc = subprocess.Popen([
        chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--remote-debugging-port={args.port}", "--remote-allow-origins=*",
        f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check",
        f"--window-size={args.width},{args.height}", "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def get_ws():
        for _ in range(80):
            try:
                data = urllib.request.urlopen(f"http://localhost:{args.port}/json").read()
                for t in json.loads(data):
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                        return t["webSocketDebuggerUrl"]
            except Exception:
                pass
            time.sleep(0.25)
        raise RuntimeError("Chrome DevTools endpoint not reachable")

    import websocket  # websocket-client
    ws = websocket.create_connection(get_ws(), max_size=None)
    _id = [0]
    def cmd(method, params=None, timeout=60):
        _id[0] += 1; mid = _id[0]
        ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            msg = json.loads(ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})
        raise RuntimeError(f"timeout waiting for {method}")

    try:
        cmd("Page.enable"); cmd("Runtime.enable"); cmd("DOM.enable")
        cmd("Emulation.setDeviceMetricsOverride", {
            "width": args.width, "height": args.height,
            "deviceScaleFactor": args.scale, "mobile": False,
            "screenWidth": args.width, "screenHeight": args.height,
        })
        cmd("Page.navigate", {"url": args.url})
        time.sleep(2.0)

        # Determine per-slide step counts.
        if args.steps.strip():
            steps_arr = [int(x) for x in args.steps.split(",")]
        else:
            res = cmd("Runtime.evaluate", {
                "expression": "typeof slides!=='undefined' ? JSON.stringify(slides.map(s=>s.steps||0)) : 'null'",
                "returnByValue": True})
            val = res.get("result", {}).get("value")
            if not val or val == "null":
                raise SystemExit("No global slides[] found. Pass --steps '0,4,0,...' to specify step counts per slide.")
            steps_arr = json.loads(val)
        log(f"slides: {len(steps_arr)}")

        # Build the (slide, step) page list, slide-major, honoring overrides.
        pages = []
        for i, st in enumerate(steps_arr):
            slide = i + 1
            if slide in overrides:
                for s in overrides[slide]:
                    pages.append((slide, s))
            elif args.pages == "all":
                for s in range(0, st + 1):
                    pages.append((slide, s))
            else:  # final
                pages.append((slide, st))
        log(f"pages: {len(pages)}")

        HIDE = ".hint{display:none!important}"
        def capture(slide, step, idx):
            cmd("Runtime.evaluate", {"expression": "location.hash='';"})
            time.sleep(0.05)
            cmd("Runtime.evaluate", {"expression": f"location.hash='#{slide}/{step}';"})
            cmd("Runtime.evaluate", {"expression":
                "(function(){var id='__hidehint';if(!document.getElementById(id)){var s=document.createElement('style');"
                f"s.id=id;s.textContent={json.dumps(HIDE)};document.head.appendChild(s);}}"
                "if(typeof fit==='function')fit();})();"})
            time.sleep(args.settle)
            shot = cmd("Page.captureScreenshot", {
                "format": "png",
                "clip": {"x": 0, "y": 0, "width": args.width, "height": args.height, "scale": 1},
                "captureBeyondViewport": True}, timeout=90)
            path = os.path.join(out_dir, f"page_{idx:03d}_s{slide:02d}_st{step}.png")
            with open(path, "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            return path

        png_paths = []
        for idx, (slide, step) in enumerate(pages):
            png_paths.append(capture(slide, step, idx))
            log(f"  page {idx+1}/{len(pages)}: slide {slide} step {step}")
    finally:
        try: ws.close()
        except Exception: pass
        proc.terminate()
        try: proc.wait(timeout=10)
        except Exception: proc.kill()
        shutil.rmtree(profile, ignore_errors=True)

    # Assemble PDF with Pillow.
    from PIL import Image
    imgs = []
    for p in png_paths:
        im = Image.open(p).convert("RGB")
        imgs.append(im)
    if not imgs:
        raise SystemExit("no pages captured")
    save_kw = {}
    if args.jpeg_quality and 0 < args.jpeg_quality <= 95:
        # embed pages as JPEG inside the PDF to bound size, keeping pixel dims
        save_kw = {"quality": args.jpeg_quality}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    imgs[0].save(args.out, "PDF", save_all=True, append_images=imgs[1:], **save_kw)
    w, h = imgs[0].size
    size_mb = os.path.getsize(args.out) / 1e6
    log(f"DONE  {args.out}  pages={len(imgs)}  {w}x{h}px  {size_mb:.1f} MB")
    print(json.dumps({"out": args.out, "pages": len(imgs), "px": [w, h], "mb": round(size_mb, 2)}))

    if not args.keep_pngs:
        shutil.rmtree(out_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
