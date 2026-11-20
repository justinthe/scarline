# Product

## Platform

web

## Stack

Static site in `docs/`, GitHub Pages: a home page (`index.html`) and a specialists page (`specialists.html`), sharing `site.css`. Plain HTML, CSS and a little JavaScript. Leaflet 1.9.4 is a local copy in `docs/vendor/leaflet/`, used only on the specialists page for the 2D map with click-to-inspect. The home page makes no third-party requests (no fonts, CDN, basemap or analytics); the specialists page loads only local files. System font stacks only. No backend, no build step for viewing. Data as pre-built JSON and PNG/GeoJSON files.

## Users

General public first (reading level about age 13 to 15): people who want to know what a simple burn-mapping method can and cannot do. Specialists second: remote-sensing peers, technical leads and hiring managers who want the map, scores and method details on the specialists page.

## Product Purpose

Scarline is a portfolio demo of burn-scar change detection over Cape York, Queensland, built from public Sentinel-2 imagery and the Queensland 2022 fire-scar product. It shows the full chain: pre-fire and post-fire scenes, the dNBR burn index, the labels, and the scores. The point is the candidate's judgement: the page states a negative result plainly and explains it.

## Positioning

A plain-language, honest worked example of remote-sensing analysis for a general reader, with the full detail one click away for specialists. Not a product, not a national burn map.

## Operating Context

Visitors arrive from a link, usually on desktop, sometimes on a phone. Expect a 60–120 second visit. Many will look only at the first screen and the results, so the first viewport must carry the thesis.

## Capabilities and Constraints

- Static only: no server, no database, no API keys, no analytics.
- Raster data is pre-rendered PNG tiles or a single overlay; no in-browser GeoTIFF decoding.
- Page loads in under 5 seconds on broadband.
- Works at 390 px wide and 1280–1600 px desktop.
- Map overlays use square display cells of about 49 m (EPSG:3857, 1024 wide); each shows the single 10 m pixel at its centre.
- Single area: Cape York, tile 54LXL. Single scene pair: pre 2022-07-13, post 2022-10-26.

## Brand Commitments

- The negative result is stated on the first screen, same visual weight as the title. Not a footnote.
- Scores are labelled with their limits: labels are agency-derived from Sentinel-2, the same sensor as the input; scene pair five months apart; one area, one season.
- Gulf is not part of the result and is not shown as if it were.
- Every dataset has its licence and attribution visible (Copernicus Legal Notice; CC BY 4.0 for the Queensland labels).

## Evidence on Hand

- `data/capeyork/processed/baseline_metrics.json`: full-scene east/west split. Model F1 0.75, IoU 0.60; all-burnt F1 0.815, IoU 0.69.
- `data/capeyork/processed/block_cv.json`: six 10 km blocks, leave-one-block-out. Pooled model F1 0.563; all-burnt 0.539; fixed 0.27 threshold 0.563. Model beats all-burnt on 4 of 6 blocks, not significant.
- Rasters: dNBR, valid mask and truth in `data/capeyork/processed/` (.npy); clipped bands in `data/capeyork/raw/`.
- Full PRD at `PRD.md`; methods and limits in `README.md`.

## Product Principles

1. Honesty over impact: the result shown is the result measured.
2. The data is the star: the plates, scars and scores carry the page, not decorative chrome.
3. Show the mechanism, not a claim: each number can be traced to a layer on the page.
4. Plain words first: a 13 to 15 year old can follow the home page; terms are defined or put in a "What does this mean?" note.

## Accessibility & Inclusion

- WCAG AA contrast for all text; one signal colour (rust) with labels carrying meaning.
- Keyboard operable controls: flip button, slider, toggles. Motion is limited to a 150 ms fade, off under reduced motion.
- Body text 18px or larger, WCAG AA. Native details/summary notes need no JavaScript.
- Glossary on the specialists page defines every technical term.
