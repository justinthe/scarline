# Scarline: PRD

Status: draft v1. Owner: Justin. Last updated: 2026-11-20.

## 1. Summary

Scarline is a static, public web demo of burn scar change detection over Cape York, Queensland. It shows a pre-fire and a post-fire Sentinel-2 scene, the burn index change (dNBR) computed from them, Queensland's 2022 fire-scar labels, and the scores from the baseline tests. Its main message is honest: a simple dNBR threshold does not beat a trivial "everything burnt" guess on this area, and the page explains why.

## 2. Problem and goal

Free satellite data makes burn mapping possible for anyone, but published accuracy claims are often unclear about labels, baselines and limits. Scarline shows the full chain on one area, with the baselines included, so readers can judge the result themselves.

Goals:
- G1. Let a reader see the pre-fire, post-fire, dNBR and label layers for one area, with a pre/post slider.
- G2. Show the scores against the trivial baselines, and state the result plainly.
- G3. Show where every number and every licence comes from.
- G4. Run with no backend and no paid service ($0).

Non-goals:
- Not a national or operational burn product.
- Not a new model. No learned classifier in v1.
- Not an alerting or live-monitoring tool.
- Not a Gulf or multi-area product. Gulf is out of scope (see section 9).

## 3. Users

- Remote-sensing learners and practitioners who want a worked, honest example.
- Journalists and policy readers who need to know what a simple method can and cannot do.
- Justin, as a portfolio item and a reference for the pipeline.

## 4. Scope (v1)

One area: Cape York, tile 54LXL. One scene pair: pre 2022-07-13 (0.08% cloud), post 2022-10-26 (0.71% cloud). Labels: QLD 2022 fire scars, months 8–10 counted as burnt.

## 5. Features

Home page (`docs/index.html`), written for ages 13 to 15, sentences under 20 words, no third-party requests:
- F1. Title, the honesty line and a "Negative result" label with a "What does this mean?" note.
- F2. Before and after plates (July, October) side by side on wide screens, one flip button (aria-pressed) on phones, with scale bar and north arrow. Plate 3 shows change (orange) with the official scar outlines in white, built by `pipeline/build_web.py` as `home_change.png`.
- F3. Numbered sections: the place, what happened, how a satellite sees a burn, what we found (two score bars, 75 and 81 out of 100), why it failed here, what it means for you.
- F4. Sources and licences, links to the specialists page and the repository.

Specialists page (`docs/specialists.html`), local Leaflet only:
- F5. 2D map with scene buttons, layer toggles, threshold slider, opacity and click-to-inspect (no basemap).
- F6. Results table (F1, IoU, true and false positives, misses) and six-block chart with pooled scores.
- F7. Method details, limits and a one-line Gulf note (investigated, not scored; scars mostly in December).
- F8. Glossary: NBR, dNBR, NIR, SWIR2, F1, IoU, leave-one-block-out, false colour, tile, threshold, scene.

Removed: the 3D terrain view and the OpenStreetMap basemap.

## 6. Data

| Asset | Source | Licence | Format in app |
|---|---|---|---|
| Pre and post Sentinel-2 bands (red, NIR, SWIR2, SCL) | Earth Search (Element 84), tile 54LXL | Copernicus Legal Notice (free, full, open) | Single JPG overlays (`map_pre.jpg`, `map_post.jpg`) on a 1024-wide EPSG:3857 grid, pre-rendered |
| dNBR raster | Derived in `pipeline/baseline.py` | Derived; attribute to sources | `map_k.png` (single PNG on the same 3857 grid, for painting) and `inspect.bin` (per-cell raw values and flags, read by Range request) |
| QLD 2022 fire scars | QLD FireScarMapping, layer 36 | CC BY 4.0 | `scars.json` (GeoJSON, simplified to about 50 m) |
| Home plate 3 | Built from the post-fire composite, dNBR at 0.21 and the Aug-Oct scars | Derived; attribute to sources | `home_change.png`, same size as `map_post.jpg` |
| Metrics | `data/capeyork/processed/` | Derived | JSON (`map_meta.json` for the grid and record layout, plus the metrics files) |

All assets are pre-built by the pipeline. The app reads static files only.

## 7. Technical requirements

- Static site in `docs/`, hosted on GitHub Pages. No server, no database, no API keys.
- Map library: Leaflet 1.9.4, local copy in `docs/vendor/leaflet/`, specialists page only. No basemap.
- Raster rendering: pre-rendered PNG tiles or a single image overlay for the AOI. No in-browser GeoTIFF decoding in v1.
- Page loads in under 5 s on a typical broadband connection with the default view.
- Works on desktop and phone widths (16 px side gutter, no horizontal scroll).
- Accessible: colour scales have labels, and red/green is not the only cue for burnt vs unburnt.
- No personal data collected. No analytics in v1.
- Privacy: the home page makes no third-party requests; the specialists page requests only local files.

## 8. Honesty requirements

These are part of the product, not footnotes. They must be visible on the main page, not only in the methods panel.

- Banner: "Negative result: a dNBR threshold does not beat 'everything burnt' on this area."
- Labels are agency-derived from Sentinel-2, the same sensor as the input. Scores measure agreement with that product, not ground truth.
- The pre and post scenes are about three and a half months apart. Seasonal change can look like burn.
- One area, one fire season, one scene pair.
- Blocks in the cross-validation are adjacent and not fully independent.
- Gulf is not part of this result.

## 9. Out of scope and deferred

- Gulf (54KWF). Scars are mostly December, outside the label window, and the east half has no scar pixels. Needs a January 2023 post scene and December labels to be scored. Not in v1.
- A learned classifier. Deferred. Would need a re-test with the stronger design: 5 km blocks, 1 km buffers, whole scene.
- Other fire seasons or regions.
- Sentinel-1 radar, DEM and any 3D terrain view.

## 10. Acceptance criteria

- AC1. Specialists map buttons switch pre and post scenes and the view updates in under 300 ms.
- AC2. Threshold slider updates the predicted-burnt layer and the TP/FP/FN counts consistently with `baseline.py` at the same threshold (checked for 0.21 and 0.27).
- AC3. Results panel values match `baseline_metrics.json` and `block_cv.json` exactly.
- AC4. Undefined metrics are shown as "n/a", never as 0.
- AC5. Every dataset has its licence and attribution visible on the Sources panel.
- AC6. Banner and limits are visible without opening any panel.
- AC7. Page works with JavaScript on and off for the static text sections.
- AC8. The home page makes no third-party requests. The specialists page loads only local files (Leaflet from `docs/vendor/leaflet/`).
- AC9. Inspect values equal an independent Python recomputation from the source tifs (`pipeline/check_web.py`).
- AC10. The inspect panel states the ~49 m display-cell limit and shows n/a for unscored cells.
- AC11. Map above-threshold cells equal dnbr > t at 0.21 and 0.27.
- AC12. Default view loads in under 5 s; map assets are lazy-loaded.

## 11. Metrics

- Product: visits, time on page, and use of the threshold slider. Only if privacy-safe, and not in v1 (no analytics).
- Quality: all acceptance criteria pass. Metrics values reproduce from the pipeline.

## 12. Risks

- **Misreading as a product claim.** Mitigation: banner and limits in section 8, visible on the main page.
- **Label licence confusion.** Mitigation: Sources panel and licences file. Confirm before publishing.
- **Range requests.** If GitHub Pages does not honour Range requests, `inspect.bin` downloads in full (21 MB) on first click. Fallback: split it into row strips.
- **Raster size.** The full AOI at 10 m is about 5600×5000 px. Mitigation: pre-render tiles at zoom levels, or downsample for the overview.

## 13. Open questions

1. Repo owner and public name: `scarline` under the personal GitHub account?
2. Include the Gulf analysis as a separate, clearly labelled note, or leave it out?
3. Keep the negative-result banner as the headline, or write a companion article first?
4. ~~Pre-render raster tiles with a tool such as GDAL or rio-tiler?~~ Closed: not needed now; single image overlays are used.
5. Hosting: GitHub Pages is assumed. Confirm.
