# Infographic snippet library

Copyable inline-SVG building blocks for VISlide decks. Each is a JS function that
returns an SVG string, meant to be dropped into `index.html` and interpolated into a
slide: `<div class="svg-wrap">${infXxx()}</div>`.

All snippets assume the palette constants defined near the top of the deck's
`<script>`: `INK, MUT, PAPER, BORD, ACC, ACC2, GRN, CORAL, AMBER, VIO`.

## Core technique

- **Design in viewBox units.** `viewBox="0 0 1440 H"`; the SVG scales to slide width.
- **Reveal per step** by putting `class="s" data-appear="N"` on a `<g>`. The deck's
  step engine toggles a `.vis` class exactly as it does for HTML elements. Set the
  slide's `steps` to the highest N used.
- **Arrows:** one `<marker>` in `<defs>`, referenced by `marker-end`.
- **Moving dots:** an `id`'d path + `<animateMotion><mpath href="#id"/>`.
- **Static diagram:** wrap everything in one `data-appear="0"` group (shows at once).

When screenshotting to verify, capture each reveal step (`#N/1`, `#N/2`, ...) so you
catch overlaps that only appear mid-build.

---

## 1. Rounded box helper

```js
function box(x,y,w,h,label,sub,stroke,fill){
  stroke=stroke||MUT; fill=fill||PAPER;
  return `<g>
    <rect x="${x}" y="${y}" width="${w}" height="${h}" rx="14" fill="${fill}" stroke="${stroke}" stroke-width="2.4"/>
    <text x="${x+w/2}" y="${y+h/2+(sub?-4:6)}" font-size="22" text-anchor="middle" fill="${INK}" font-weight="800">${label}</text>
    ${sub?`<text x="${x+w/2}" y="${y+h/2+20}" font-size="14" text-anchor="middle" fill="${MUT}">${sub}</text>`:''}
  </g>`;
}
```

## 2. Animated flow with moving-dot packets

A left-to-right pipeline; each stage reveals on its own step and the connecting arrow
animates a dot. Great for "data moves through these stages".

```js
function infFlow(){
  const stage=(x,label,sub,c)=>box(x,180,230,110,label,sub,c,`${c}14`);
  const arrow=(id,x1,x2,c)=>`
    <path id="${id}" d="M${x1} 235 H ${x2}" fill="none" stroke="${c}" stroke-width="3" marker-end="url(#fArrow)"/>
    <circle r="6" fill="${c}"><animateMotion dur="2.2s" repeatCount="indefinite" rotate="auto"><mpath href="#${id}"/></animateMotion></circle>`;
  return `<svg viewBox="0 0 1440 460" width="1440">
    <defs><marker id="fArrow" markerUnits="userSpaceOnUse" markerWidth="13" markerHeight="13" refX="11" refY="6" orient="auto"><path d="M0 0L12 6L0 12Z" fill="${MUT}"/></marker></defs>
    <g class="s" data-appear="1">${stage(70,'Ingest','raw input',ACC)}</g>
    <g class="s" data-appear="2">${arrow('fa1',300,388,ACC2)}${stage(390,'Transform','normalize',VIO)}</g>
    <g class="s" data-appear="3">${arrow('fa2',620,708,VIO)}${stage(710,'Process','the work',CORAL)}</g>
    <g class="s" data-appear="4">${arrow('fa3',940,1028,CORAL)}${stage(1030,'Serve','result out',GRN)}</g>
  </svg>`;
}
```
Tips: to make a step *replace* a box instead of adding one, give the old box
`data-until="K"` and the new box `data-appear="K+1"` at the same coordinates.

## 3. Layered stack (bottom-to-top)

Labelled bands with a spine label; one layer per step. Use for reference-stack /
"turtles all the way down" diagrams.

```js
function infStack(){
  const layers=[
    ['Presentation','UI · API surface',ACC],
    ['Application','business logic',VIO],
    ['Platform','runtime · orchestration',GRN],
    ['Infrastructure','compute · storage · network',AMBER],
  ];
  const W=900,x=(1440-W)/2,hL=88,gap=12,baseY=40;
  return `<svg viewBox="0 0 1440 470" width="1440">
    ${layers.map(([t,s,c],i)=>{const y=baseY+(layers.length-1-i)*(hL+gap);return `
      <g class="s" data-appear="${i+1}">
        <rect x="${x}" y="${y}" width="${W}" height="${hL}" rx="12" fill="${c}18" stroke="${c}" stroke-width="2.4"/>
        <text x="${x+28}" y="${y+38}" font-size="22" fill="${INK}" font-weight="800">${t}</text>
        <text x="${x+28}" y="${y+64}" font-size="15" fill="${MUT}">${s}</text>
      </g>`;}).join('')}
  </svg>`;
}
```

## 4. Pyramid / hierarchy (widening bands)

Static tiers that widen top-to-bottom; for storage/memory hierarchies, maturity
levels, funnels.

```js
function infPyramid(){
  const tiers=[['Hot','tiny · fastest',GRN,0],['Warm','fast · medium',ACC,1],
    ['Cool','large · slower',VIO,2],['Cold','vast · slowest',MUT,3]];
  const H=70,gap=8,topW=360,step=150,cx=720,y0=40;
  return `<svg viewBox="0 0 1440 380" width="1440"><g class="s" data-appear="0">
    ${tiers.map(([t,s,c,i])=>{const w=topW+i*step,x=cx-w/2,y=y0+i*(H+gap);return `
      <rect x="${x}" y="${y}" width="${w}" height="${H}" rx="8" fill="${c}22" stroke="${c}" stroke-width="2"/>
      <text x="${cx}" y="${y+30}" font-size="18" text-anchor="middle" fill="${INK}" font-weight="800">${t}</text>
      <text x="${cx}" y="${y+52}" font-size="13" text-anchor="middle" fill="${MUT}">${s}</text>`;}).join('')}
  </g></svg>`;
}
```

## 5. Central object with orbiting cards (hub & spokes)

A core concept with satellite cards in two columns and elbow connectors. Reveal the
core first, then cards one per step. Robust two-column layout (avoids the overlap
problems of radial placement).

```js
function infHubSpokes(){
  const cx=720,cy=260,cr=90;
  const left=[['Speed','low latency'],['Simplicity','one API'],['Cost','per unit']];
  const right=[['Scale','horizontal'],['Safety','isolation'],['Observability','metrics']];
  const bw=210,bh=64,gapY=26, colY=[80,80+bh+gapY,80+2*(bh+gapY)];
  const lx=250, rx=1440-250-bw;
  const card=(x,y,t,s,step)=>`<g class="s" data-appear="${step}">
    <rect x="${x}" y="${y}" width="${bw}" height="${bh}" rx="12" fill="${PAPER}" stroke="${VIO}" stroke-width="2"/>
    <text x="${x+bw/2}" y="${y+27}" font-size="17" text-anchor="middle" fill="${INK}" font-weight="800">${t}</text>
    <text x="${x+bw/2}" y="${y+47}" font-size="13" text-anchor="middle" fill="${MUT}">${s}</text></g>`;
  const elbow=(x,y,side,step)=>{const sx=side==='l'?x+bw:x,sy=y+bh/2,tx=side==='l'?cx-cr:cx+cr,ty=cy,mx=(sx+tx)/2;
    return `<g class="s" data-appear="${step}"><path d="M${sx} ${sy} H ${mx} V ${ty} H ${tx}" fill="none" stroke="${BORD}" stroke-width="2" marker-end="url(#hubA)"/></g>`;};
  return `<svg viewBox="0 0 1440 520" width="1440">
    <defs><marker id="hubA" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" refX="9" refY="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="${BORD}"/></marker></defs>
    <g class="s" data-appear="1"><circle cx="${cx}" cy="${cy}" r="${cr}" fill="rgba(37,99,235,.10)" stroke="${ACC}" stroke-width="3"/>
      <text x="${cx}" y="${cy-4}" font-size="24" text-anchor="middle" fill="${ACC}" font-weight="900">Core</text>
      <text x="${cx}" y="${cy+22}" font-size="14" text-anchor="middle" fill="${MUT}">the thing</text></g>
    ${left.map(([t,s],i)=>elbow(lx,colY[i],'l',i+2)+card(lx,colY[i],t,s,i+2)).join('')}
    ${right.map(([t,s],i)=>elbow(rx,colY[i],'r',i+5)+card(rx,colY[i],t,s,i+5)).join('')}
  </svg>`;
}
```

## 6. Fan-out / tree (leaf-spine, org chart, Clos network)

A tiered tree: a root fanning to a middle tier fanning to leaves. Adapt counts.

```js
function infFanout(){
  const node=(x,y,label,c)=>`<g><rect x="${x-46}" y="${y-24}" width="92" height="48" rx="10" fill="${c}18" stroke="${c}" stroke-width="2.2"/>
    <text x="${x}" y="${y+5}" font-size="15" text-anchor="middle" fill="${INK}" font-weight="800">${label}</text></g>`;
  const link=(x1,y1,x2,y2)=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${BORD}" stroke-width="1.6"/>`;
  const spine=[720], agg=[420,720,1020], leaf=[240,420,600,840,1020,1200];
  let s='';
  agg.forEach(ax=>{ s+=link(720,124,ax,236); });
  leaf.forEach(lx=>{ const nearest=agg.reduce((p,c)=>Math.abs(c-lx)<Math.abs(p-lx)?c:p); s+=link(nearest,284,lx,396); });
  return `<svg viewBox="0 0 1440 460" width="1440"><g class="s" data-appear="0">
    ${spine.map(x=>node(x,100,'Spine',ACC)).join('')}
    ${s}
    ${agg.map(x=>node(x,260,'Agg',VIO)).join('')}
    ${leaf.map(x=>node(x,420,'Leaf',GRN)).join('')}
  </g></svg>`;
}
```

## 7. Numbered requirement cards (HTML, not SVG)

For lists that don't need a diagram — reveal one per step. Put directly in slide html.

```js
`<div class="flex col gap-4">
  ${[['01','First','short description'],
     ['02','Second','short description'],
     ['03','Third','short description']].map(([n,t,d],i)=>`
    <div class="card rowitem" data-step="${i+1}"><span class="num">${n}</span>
      <div><div class="h3">${t}</div><div class="desc mt-1">${d}</div></div></div>`).join('')}
</div>`
```

## Colour-with-alpha trick

`` `${c}18` `` appends a hex-alpha byte to a 6-digit hex colour (e.g. `#2563EB` +
`18` → `#2563EB18`, ~9% opacity) for soft fills. Works for any `18`/`22`/`14` suffix.
For rgba you can also write `rgba(37,99,235,.10)` directly.

## Sizing & overflow

- Keep the tallest element within the viewBox height; `.svg-wrap svg` has
  `max-height:760px`. If content clips, either grow the viewBox height (everything
  scales down to fit the slide) or tighten spacing.
- Center text with `text-anchor="middle"` at the shape's center x.
- Long labels: shorten, reduce font-size, or widen the box — verify by screenshot.
