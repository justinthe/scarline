# Scarline

Burn scar change detection on public Sentinel-2 imagery, scored against Queensland's 2022 fire-scar product. Scope: one area, Cape York (Queensland, Australia).

**Result (negative):** a single dNBR threshold does not beat a trivial "everything burnt" guess on Cape York. A fixed threshold of 0.27 is no better than a threshold tuned on other blocks.

## Result

Scene pair: pre-fire 2022-07-13 (Sentinel-2A, 0.08% cloud), post-fire 2022-10-26 (Sentinel-2B, 0.71% cloud), tile 54LXL. Burn index dNBR = NBR(pre) − NBR(post), where NBR = (NIR − SWIR2) / (NIR + SWIR2). Labels: QLD 2022 fire scars, months 8–10 counted as burnt. Months 7 and 11 are excluded because they could fall outside the scene dates.

| Test | Model | Comparison |
|---|---|---|
| Full scene, east half (threshold chosen on west half, 0.21) | F1 0.75, IoU 0.60 | All-burnt: F1 0.815, IoU 0.69 |
| Six 10 km blocks, leave-one-block-out (pooled) | F1 0.563 | All-burnt 0.539; fixed 0.27 threshold 0.563 |

On the six blocks, the model beats all-burnt on 4 of 6, but the gain is not significant (sign test p ≈ 0.56–0.69). One block drives most of the pooled gain. The tuned threshold ties the fixed 0.27 threshold.

## Why it doesn't work here

- **Label density.** 40–69% of the scene is scar. An all-burnt guess scores well on any such scene.
- **Seasonal gap.** The pre-fire scene is about three and a half months before the post-fire scene, so ordinary dry-season change can look like burn.
- **Label source.** The QLD product is built from Sentinel-2, the same sensor as the input. The score measures agreement with that product, not with ground truth.
- **Neighbouring blocks** share borders, so held-out blocks are not fully independent.

## Limits

- One area, one fire season, one scene pair.
- Labels are agency-derived, not hand-verified.
- Cloud masking uses the Sentinel-2 scene classification layer only.
- Gulf (54KWF) was investigated but not scored: its scars are mostly December, outside the label window, and its east half contains no scar pixels. It is not part of this result.

## Data and licences

| Source | Use | Licence |
|---|---|---|
| Sentinel-2 L2A, Earth Search (Element 84), tile 54LXL | imagery | Copernicus Sentinel Data Legal Notice (free, full, open) |
| Queensland Sentinel-2 Fire Scars 2022, ArcGIS layer 36 | labels | CC BY 4.0 (data.qld.gov.au and TERN records) |

Attribution: Contains modified Copernicus Sentinel data 2022. State of Queensland (Department of Environment and Science) 2022; produced by JRSRP using Sentinel-2 data.

Per-file records are in `data/licences.json`.

## Reproduce

Run from the project root:

    python3 pipeline/fetch_aoi.py capeyork   # clip scenes and scars to data/capeyork/raw/
    python3 pipeline/baseline.py capeyork    # dNBR threshold, full-scene east/west split
    python3 pipeline/block_cv.py             # leave-one-block-out on mid-density blocks
    python3 pipeline/build_web.py            # web assets into docs/data/ (map, inspect table, scars, home_change.png)
    python3 pipeline/check_web.py            # asserts the web assets against the source tifs

Outputs: `data/capeyork/processed/baseline_metrics.json` and `block_cv.json`. `data/` is git-ignored except for the licence record.

## Pages

- `docs/index.html`: home page for a general audience (ages 13 to 15). Before/after plates, the negative result and why.
- `docs/specialists.html`: interactive map with click-to-inspect, threshold slider, scores, method, glossary. Leaflet 1.9.4 is served locally from `docs/vendor/leaflet/`.

View locally: `cd docs && python3 -m http.server`.

## Layout

    pipeline/
      aoi_config.py   # per-area settings (scenes, label months, extent)
      fetch_aoi.py    # STAC metadata, band clipping, scar download
      baseline.py     # dNBR, threshold sweep, scoring
      block_cv.py     # block cross-validation
      build_web.py    # docs/data/ assets: 2D map, inspect table, home_change.png
      check_web.py    # checks web assets against source rasters and baseline metrics
    docs/
      index.html        # home page: plain-language, no third-party requests
      specialists.html  # map, scores, methods, glossary; local Leaflet only
      site.css, vendor/leaflet/, data/
    data/             # git-ignored outputs
    PLAN.md           # original plan (now superseded by this result)
