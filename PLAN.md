# Scarline: plan

Goal: one public, Australia-relevant spatial AI demo. Burn scar change detection from Sentinel-2 pre/post imagery, scored against real agency burnt-area polygons. $0 stack. Hosted static map, no backend.

## Decisions (defaults, change if you disagree)

- Use case: burn scar change detection. Free labels exist (see Data).
- Labels: Queensland Sentinel-2 Fire Scars (CC BY 4.0, TERN/QLD DES). Secondary check: DEA Burnt Area Vectors (CC BY 4.0, provisional).
- Imagery: Sentinel-2 L2A via Element 84 Earth Search (AWS, free, no key). Fallback: DEA.
- Baseline first, model second. Simplest method that works, then a small classifier to beat it.
- Output: `docs/` static site (Leaflet), same pattern as SiteTwin. GitHub Pages.
- Language: Python 3.11+.

## Data

| Source | Use | Licence (per search, verify) |
|---|---|---|
| Sentinel-2 L2A (Earth Search) | pre/post imagery | Copernicus open terms |
| QLD Sentinel-2 Fire Scars | ground truth polygons/rasters | CC BY 4.0 |
| DEA Burnt Area Vectors S2 NRT | cross-check, second label source | CC BY 4.0, provisional |

Gaps: NAFI (northern savanna) not found. Labels are agency products, not hand-verified. State this in the demo.

## Phases

1. **AOI and event pick.** One fire event with labels, a region with clear pre/post cloud-free scenes. Pick one before coding.
2. **Pull.** Script fetches pre and post Sentinel-2 scenes for the AOI. Cache to `data/` (gitignored). Save licence and source URLs to `data/licences.json`.
3. **Align.** Reproject labels to imagery grid. Mask clouds with SCL band.
4. **Baseline.** dNBR = NBR_pre - NBR_post. Threshold swept on a held-out tile. This is the number to beat.
5. **Model.** Small pixel classifier (e.g. gradient boosting) on pre/post bands + indices. Train tiles A, test tile B. No random pixel split.
6. **Score.** IoU and F1 vs labels, baseline and model. Report both, including where the model loses.
7. **Map.** Export tiles/GeoJSON to `docs/`. Leaflet slider: pre, post, change overlay, label overlay.
8. **Publish.** README with results, limits, licences. Make repo public.

## Done when

- Baseline and model scores in `docs/data/metrics.json`.
- Static map loads with no backend.
- Every data source has a licence and attribution line.
- README states what is not validated.

## Open questions for you

- Which fire event / AOI? (Suggest a QLD event with good labels and few cloud days.)
- Keep DEA Burnt Area as second label source, or drop it to keep scope small?
- Repo name stays `scarline`? Public repo under `justinthe`?
