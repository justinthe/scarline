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

F1. **Map view.** Leaflet map over the AOI, OpenStreetMap basemap on by default (toggleable, attribution shown; the scene composite and overlays sit on top), with a scale bar and click-to-inspect.
F2. **Pre/post buttons.** Buttons switch the displayed scene between pre and post (false colour only: SWIR2, NIR, red; no blue or green bands are fetched).
F3. **dNBR layer.** Colour-scaled dNBR over the AOI, with a legend and the chosen threshold marked. Pixels excluded by the cloud or scene-classification mask are shown hatched.
F4. **Label layer.** QLD scar polygons for months 8–10 as an overlay, toggleable. Months 7 and 11 shown as a separate, ambiguous style.
F5. **Threshold control.** A slider from 0.05 to 0.85 that re-colours the predicted burnt area and shows live counts. Default is the chosen threshold (0.21).
F6. **Results panel.** A table with three rows: model (threshold 0.21, full scene east half), all-burnt guess, and fixed 0.27 threshold. Columns: F1, IoU, TP, FP, FN. Also the block test results (pooled and per block).
F7. **Method panel.** Plain-language steps: scenes, cloud mask, dNBR, labels, split, scores. Lists the limits (section 8).
F8. **Sources and licences panel (deferred, not in v1).** Each dataset with URL, licence and attribution, pulled from `data/licences.json`.
F9. **Download (deferred, not in v1).** Links to the processed dNBR GeoTIFF and metrics JSON, with licence notes.

## 6. Data

| Asset | Source | Licence | Format in app |
|---|---|---|---|
| Pre and post Sentinel-2 bands (red, NIR, SWIR2, SCL) | Earth Search (Element 84), tile 54LXL | Copernicus Legal Notice (free, full, open) | Single JPG overlays (`map_pre.jpg`, `map_post.jpg`) on a 1024-wide EPSG:3857 grid, pre-rendered |
| dNBR raster | Derived in `pipeline/baseline.py` | Derived; attribute to sources | `map_k.png` (single PNG on the same 3857 grid, for painting) and `inspect.bin` (per-cell raw values and flags, read by Range request) |
| 3D and DEM assets (`pre.jpg`, `post.jpg`, `dnbr_raw.png`, `dem.json`) | Copernicus DEM GLO-30 (plus the Sentinel-2 imagery above) | Copernicus DEM licence (see `data/licences.json`) | Textures and heightmap for the 3D terrain view |
| QLD 2022 fire scars | QLD FireScarMapping, layer 36 | CC BY 4.0 | `scars.json` (GeoJSON, simplified to about 50 m) |
| Metrics | `data/capeyork/processed/` | Derived | JSON (`map_meta.json` for the grid and record layout, plus the metrics files) |

All assets are pre-built by the pipeline. The app reads static files only.

## 7. Technical requirements

- Static site in `docs/`, hosted on GitHub Pages. No server, no database, no API keys.
- Map library: Leaflet 1.9.4 from a CDN with SRI. Basemap: OpenStreetMap raster tiles from tile.openstreetmap.org, on by default, toggleable, attribution shown, no API key.
- Raster rendering: pre-rendered PNG tiles or a single image overlay for the AOI. No in-browser GeoTIFF decoding in v1.
- Page loads in under 5 s on a typical broadband connection with the default view.
- Works on desktop and phone widths (16 px side gutter, no horizontal scroll).
- Accessible: colour scales have labels, and red/green is not the only cue for burnt vs unburnt.
- No personal data collected. No analytics in v1.
- Privacy: basemap requests send visitor IP addresses and the site origin (as Referer) to OSM.

## 8. Honesty requirements

These are part of the product, not footnotes. They must be visible on the main page, not only in the methods panel.

- Banner: "Negative result: a dNBR threshold does not beat 'everything burnt' on this area."
- Labels are agency-derived from Sentinel-2, the same sensor as the input. Scores measure agreement with that product, not ground truth.
- The pre and post scenes are five months apart. Seasonal change can look like burn.
- One area, one fire season, one scene pair.
- Blocks in the cross-validation are adjacent and not fully independent.
- Gulf is not part of this result.

## 9. Out of scope and deferred

- Gulf (54KWF). Scars are mostly December, outside the label window, and the east half has no scar pixels. Needs a January 2023 post scene and December labels to be scored. Not in v1.
- A learned classifier. Deferred. Would need a re-test with the stronger design: 5 km blocks, 1 km buffers, whole scene.
- Other fire seasons or regions.
- Sentinel-1 radar and DEM as a map layer (the DEM drives the 3D terrain only).

## 10. Acceptance criteria

- AC1. Buttons switch pre and post scenes and the view updates in under 300 ms.
- AC2. Threshold slider updates the predicted-burnt layer and the TP/FP/FN counts consistently with `baseline.py` at the same threshold (checked for 0.21 and 0.27).
- AC3. Results panel values match `baseline_metrics.json` and `block_cv.json` exactly.
- AC4. Undefined metrics are shown as "n/a", never as 0.
- AC5. Every dataset has its licence and attribution visible on the Sources panel.
- AC6. Banner and limits are visible without opening any panel.
- AC7. Page works with JavaScript on and off for the static text sections.
- AC8. The only third-party requests are to cdn.jsdelivr.net, Google Fonts and tile.openstreetmap.org (the last only for the basemap).
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
- **OSM tile usage.** The basemap loads tiles from tile.openstreetmap.org, which has a usage policy and no SLA, and visitor IPs reach OSM. Mitigation: attribution shown, zoom capped at 13 for tiles, toggle to turn it off, page works without tiles.
- **Raster size.** The full AOI at 10 m is about 5600×5000 px. Mitigation: pre-render tiles at zoom levels, or downsample for the overview.

## 13. Open questions

1. Repo owner and public name: `scarline` under the personal GitHub account?
2. Include the Gulf analysis as a separate, clearly labelled note, or leave it out?
3. Keep the negative-result banner as the headline, or write a companion article first?
4. ~~Pre-render raster tiles with a tool such as GDAL or rio-tiler?~~ Closed: not needed now; single image overlays are used.
5. Hosting: GitHub Pages is assumed. Confirm.
