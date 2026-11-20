# Scarline: free data sources

Scope: $0 only. Items below are free to download or use, unless marked otherwise. Paid and unavailable items are listed under Excluded. Licences come from search snippets and conflict in places. **Verify each licence on the source page before publishing.**

Status key: **Core** = needed for v1. **Check** = second source or validation, use if licence confirmed. **Context** = optional features. **Skip** = not needed for v1.

---

## 1. Imagery

### 1.1 Sentinel-2 Level-2A (Earth Search, AWS) — Core
- URL: https://earth-search.aws.element84.com/v1/ (STAC API); bucket `sentinel-cogs` (no-sign-request)
- What: Surface reflectance (atmospherically corrected) optical imagery, 10–20 m, about every 5 days. Includes SCL scene classification band for cloud and shadow masks.
- Why: Pre/post fire scenes. Burn index (NBR/dNBR) needs SWIR and NIR bands. Free, no account; AWS sponsors storage.
- Licence: Copernicus open terms (free, full, open). Attribution: "Contains modified Copernicus Sentinel data [year]". Confirmed live: STAC metadata says `proprietary` and links the Sentinel Data Legal Notice. The Legal Notice is the free, open Copernicus licence, but the label is misleading. Cite the Legal Notice.
- Collections (confirmed on the live endpoint): `sentinel-2-c1-l2a` (Collection 1, from 2015, gaps in 2022) and `sentinel-2-l2a` (legacy, full 2022 coverage) both exist. Use `sentinel-2-l2a` for 2022. `sentinel-2-pre-c1-l2a` covers baseline < 05.00. **Correction (tested):** `sentinel-2-c1-l2a` has no scenes for Sept–Nov 2022 over the Gulf AOI (0 features, while 2021 returns 76). Use legacy `sentinel-2-l2a` for 2022 scenes. It has full coverage for Aug–Dec 2022.

### 1.2 Sentinel-2 via Copernicus Data Space Ecosystem — Core (fallback)
- URL: https://dataspace.copernicus.eu (free registration for downloads)
- What: Official ESA portal, same Sentinel-2 archive, plus S3 access.
- Why: Fallback if Earth Search is slow or changes. Also source for Sentinel-1 (1.6).
- Licence: Copernicus open terms. CDSE terms: https://dataspace.copernicus.eu/node/10

### 1.3 Copernicus Australasia Regional Data Hub — Check
- URL: https://copernicus.gov.au/ (user guide: https://copernicus.gov.au/user-guide)
- What: Australian-hosted Sentinel-1/2/3 copies, run with Geoscience Australia. Listed as free and open.
- Why: Faster local downloads for AU. Backup source.
- Licence: Listed as "Not Specified" on data.gov.au. Confirm on the hub.

### 1.4 DEA Analysis Ready Data (Sentinel-2 and Landsat) — Check
- URL: https://www.ga.gov.au/scientific-topics/dea/learning-hub/ways-to-access-dea-data ; public bucket `dea-public-data` (data.dea.ga.gov.au)
- What: Geoscience Australia analysis-ready imagery in Open Data Cube format. Includes Sentinel-2 surface reflectance and Landsat.
- Why: Australian-calibrated, consistent product for cross-checking.
- Licence: DEA says free. Check the specific product licence (CC BY 4.0 is the usual DEA default; confirm).
- Note: Sentinel-2 Collection 3 migration in progress. Check the product page before pinning paths.

### 1.5 Landsat Collection 2 (USGS, AWS) — Skip
- URL: https://www.usgs.gov/landsat-missions/landsat-data-access
- What: 30 m, 1972–present. Level-2 surface reflectance on AWS and EarthExplorer.
- Why: Longer history for pre-2017 comparison. Not needed for v1 (Sentinel-2 covers 2017 onward).
- Licence: USGS public domain. The Landsat burned-area product (Level-3) is documented for the US only; no AU coverage confirmed.

### 1.6 Sentinel-1 SAR — Context
- URL: https://dataspace.copernicus.eu (Sentinel-1); also https://copernicus.gov.au/
- What: C-band radar, unaffected by cloud or smoke.
- Why: Cloud-free burn detection if optical scenes are cloudy. Also useful for flood extent. Adds complexity; add only if cloud masking fails.
- Licence: Copernicus open terms.

---

## 2. Labels and reference burn extents

### 2.1 Queensland Sentinel-2 Fire Scars (QLD DES algorithm) — Core
- URL: https://www.data.qld.gov.au/dataset/sentinel-2-queensland-fire-scars-series ; TERN record: https://geonetwork.tern.org.au/geonetwork/srv/api/records/7b6d2b84-cbf3-46e8-aa8c-c49352f9ffd5 ; methodology: https://www.qld.gov.au/environment/land/management/mapping/statewide-monitoring/firescar/firescar-methodology
- What: Statewide burnt area from Sentinel-2, annual and monthly GeoTIFF composites, from 2017 onward.
- Why: Main ground-truth labels for the burn scar demo.
- Licence: **Confirmed CC BY 4.0** on the data.qld.gov.au dataset page ("Creative Commons Attribution 4.0", Open Definition) and in the TERN record's use constraints. data.gov.au mirrors say "Not Specified" and are not the source of truth.
- Available years (open portal): annual GeoTIFFs for 2017, 2019, 2020, 2021, 2022. **2024 is not on the open portal.** Only an ArcGIS layer (FireScarMapping MapServer, layer 38) is listed, marked "Offline Data".
- Validation (TERN, self-reported): F1 0.91, commission 13%, omission 8%. Omission excludes cloud-missed burns. Not independent of Sentinel-2 imagery; the method uses Sentinel-2 fractional cover. Expect the dNBR baseline to look good against these labels.
- Caveat: Fire scars under 2 ha may be omitted. Cloud, smoke and haze can hide scars. Labels are a product, not hand-checked truth. Use at scales no finer than 1:100,000.
- Grid: **Confirmed mismatch.** Labels are Australian Albers Equal Area (TERN AusCover naming, `a2`). Sentinel-2 is UTM. Reproject labels to the Sentinel-2 grid (nearest neighbour for masks) before scoring.

### 2.2 DEA Burnt Area Characteristic Layers / Vectors (Sentinel-2 NRT, provisional) — Check
- URL: https://knowledge.dea.ga.gov.au/data/product/dea-burnt-area-characteristic-layers-sentinel-2-near-real-time/ ; data.gov.au: https://data.gov.au/data/en/dataset/8a51fa0e-ddef-4d15-86e8-effdfad25b4b
- Note: The vectors page linked on DEA is v1.0.0 (old version). Check for a newer version before use.
- What: Burn polygons from Sentinel-2 near real-time, national. Characteristic layers listed for 1 Jul 2021 – 29 Aug 2023. Status of later coverage unclear.
- Why: Second independent label source, outside Queensland.
- Limit: Coverage **1 Jul 2021 to 29 Aug 2023**, status "No further updates". Confirmed on the DEA product page. Cannot validate a 2024 event. Only usable for 2021–2023 events.
- Licence: **Confirmed CC BY 4.0** on the DEA product page. Provisional, not quality-controlled yet.
- Caveat: DEA says use with other sources to rule out non-fire change.

### 2.3 NAFI fire scars and fire histories (northern savanna) — Check
- URL: https://firenorth.org.au/nafi3/views/data/Download.html ; about: https://firenorth.org.au/nafi3/views/help/about.html
- What: 250 m annual fire scars back to 2000, plus fire history datasets. 2025 burnt area mapping published. Shapefile and image downloads.
- Why: Best free source for northern Australian savanna burns, where most AU burning happens.
- Licence: NAFI's About page says downloads are under terms similar to CC BY 4.0, with attribution to NAFI. Some TERN mirrors use TERN BY-SA or require consent before publishing; data.gov.au says "Not Specified". Take the licence from NAFI's own page. Do not use the mirrors as the source.

### 2.4 Geoscience Australia Bushfire Historical Extents (v3.0) — Check
- URL: https://digital.atlas.gov.au/datasets/524e2962bd8b4968b8df9f9774345926 (FGDB, ~847 MB); data.gov.au record: https://data.gov.au/data/dataset/468af92d-88c0-49ba-8738-7efd7df06727 ; GA eCat: https://ecat.ga.gov.au/geonetwork/srv/api/records/eb1209b4-99cf-4265-965c-ad9ca1a702c7
- What: National compilation of state and territory fire history, from 1899. Pin v3.0.
- Why: Cross-state historical labels for validation across regions.
- Licence: GA eCat record says CC BY 4.0; data.gov.au says "Not Specified". Cite eCat.
- Caveat: Duplicate features possible. Coverage differs by jurisdiction. Not all NT data is in v3.0.

### 2.5 NSW fire history (RFS and NPWS) — Check
- URL: https://data.nsw.gov.au/data/dataset/fa2fe6c7-2530-4b5a-87dc-5afdb290141a (NSW Fire History); https://data.nsw.gov.au/data/dataset/3ccf63aa-d17d-4094-9c6a-343a323dd4a5 (NPWS Wildfires and Prescribed Burns, shapefile, 1920–2025)
- What: Fire extents and prescribed burns. NPWS is a shapefile package, updated over time.
- Why: Labels for an NSW test region (eastern forests, different vegetation from QLD).
- Licence: Some listings CC BY, others "Not Specified". Confirm on data.nsw.gov.au.
- Caveat: Fire extents accurate to 10–100 m.

### 2.6 NSW Fire Extent and Severity Mapping (FESM) — Context
- URL: Historical: https://data.gov.au/data/dataset/4f9433ed-0148-43a0-a986-f8569402d92d . Statewide current product (from 2016/17, Sentinel-2): no verified URL yet. Find it on data.nsw.gov.au.
- What: Burn extent plus severity classes, not only boundaries.
- Why: Severity as a second target or feature. Useful for "how bad", not only "burnt or not".
- Licence: Check per record on data.nsw.gov.au.

### 2.7 Victoria fire history (fire scars and severity) — Check
- URL: https://discover.data.vic.gov.au/dataset/fire-history-records-of-fires-across-victoria-showing-the-fire-scars ; https://discover.data.vic.gov.au/dataset/fire-history-records-of-fires-across-victoria
- What: Fire extents back to 1903, including CFA data on private land from 2009. Separate severity layer from 1998 onward (aggregated).
- Why: Victorian test region (temperate forest and grassland).
- Licence: Mixed. CC BY 4.0 on some records, CC BY 3.0 AU on others. Confirm per record.

---

## 3. Context layers

### 3.1 Copernicus DEM GLO-30 — Context
- URL: https://registry.opendata.aws/copernicus-dem/ ; Copernicus DS: https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM
- What: 30 m global elevation.
- Why: Slope and aspect. Terrain affects burn severity and spread. Hillshade for the map.
- Licence: Appears free with an attribution notice (Copernicus WorldDEM-30 licence). No AU-specific restriction found. AWS notes a small restricted subset of tiles, not known to include AU. Confirm before use.

### 3.2 NVIS Version 7.0 (Extant Vegetation) — Context
- URL: https://data.gov.au/data/dataset/b0ea7fe2-dfff-420f-8a7d-08813b551c5a (extant vectors); rasters: https://data.gov.au/data/en/dataset/3723f4ce-6a95-4500-a25b-a3815058ed30 ; DCCEEW: https://www.dcceew.gov.au/environment/environment-information-australia/discover-datasets
- What: National map of present native vegetation groups and subgroups.
- Why: Stratify results by vegetation type. Report scores per class, not one average.
- Licence: Version 7.0 shows "Not Specified"; Version 5.1 is CC BY 4.0. Confirm 7.0.
- Caveat: Version differences change class names. Pin a version.

### 3.3 OpenStreetMap roads and tracks — Context
- URL: Australia extract: https://download.geofabrik.de/australia-oceania/australia.html
- What: Roads, tracks, power lines, buildings. Community-mapped.
- Why: Access and proximity features. Map base layer (see 4.1).
- Licence: ODbL 1.0. Attribution "© OpenStreetMap contributors"; share-alike on derived databases. Several government re-publications of OSM say "Not Specified"; use Geofabrik or OSM directly.

### 3.4 Geoscience Australia National Electricity Infrastructure — Skip
- URL: https://data.gov.au/data/dataset/national-electricity-infrastructure
- What: Transmission and substation locations.
- Why: Not needed for burn scars. Keep for the power-line idea later.
- Licence: Check listing.

---

## 4. Basemaps and tooling

### 4.1 OSM tile basemap — Context
- Why: Map background for the static site.
- Caveat: OSM tile server has a usage policy (no heavy bulk use). Read it, attribute, and cache sparingly. Esri and Stadia were dropped: they need an account and key, and Stadia's free tier is non-commercial only.

### 4.2 Open-source libraries — Core
- Python: `pystac-client`, `odc-stac` or `rasterio`, `geopandas`, `numpy`, `scikit-learn` or `lightgbm`. Leaflet for the map (CDN).
- Not data, but needed. All MIT, BSD or Apache licences (confirm per package).

---

## 5. Weather (optional, pre-fire context)

### 5.1 NSW RFS Fire Weather Viewer — Context
- URL: https://fireweather.aig.apps.rfs.nsw.gov.au/
- What: Hourly forecast download for a lat/long, up to four days (temperature, humidity, wind, Drought Factor, Forest Fire Danger Index). NSW only.
- Why: Fire danger context for a scene. Viewer, not an API. Manual download only.
- Licence: Not stated. Check before use.

### 5.2 BoM free feeds — Context
- URL: https://www.bom.gov.au/catalogue/data-feeds.shtml
- What: Real-time observations and some general forecast and warning products, free via web and FTP.
- Why: Weather observations at the time of the fire. Free feeds exclude the official fire danger grids.
- Licence: BoM Data Licence Agreement. Confirm per product.

### 5.3 Open-Meteo BOM endpoint — Dead, do not use
- URL: https://open-meteo.com/en/docs/bom-api
- Status: Docs say the last ACCESS-G run is from 2025-06-26, so no current forecasts. Commercial use requires a paid licence.

---

## Excluded

- **BoM fire weather grids** (AFDRS / ADFD, NetCDF4): annual fee. Heatwave grids are priced at $2,092 per the BoM charges page: https://www.bom.gov.au/other/charges.shtml
- **Geofabrik "power export"** (detailed power network): quoted, fee-based. Standard OSM extract is free and enough.
- **Google Earth Engine**: free for research and non-commercial use, but needs an account. The GEE MCP server is currently down. Not used for v1; revisit if needed.
- **Open-Meteo BOM endpoint**: no current data (see 5.3).

Not excluded but unresolved: NAFI and some state licences. Included only as Check until confirmed.

---

## Recommended v1 set

Core (all $0):
1. Sentinel-2 L2A from Earth Search (1.1), with Copernicus Data Space as fallback (1.2).
2. QLD Sentinel-2 Fire Scars as primary labels (2.1).
3. Copernicus DEM GLO-30 for slope (3.1), once AU tile access is confirmed.
4. OSM tiles for the map background (4.1).

Optional for v1 (add if licence confirmed):
5. DEA Burnt Area as cross-check (2.2). Only for events 2021–2023.
6. NVIS 7.0 for vegetation strata (3.2).

Second region, later: NSW (2.5) or Victoria (2.7). Savanna test: NAFI (2.3).

---

## Open items before v1

- Confirm licence on: QLD fire scars (2.1), DEA burnt area (2.2), NAFI (2.3), Bushfire Historical Extents (2.4), NSW (2.5), Victoria (2.7), FESM (2.6), NVIS 7.0 (3.2), Copernicus DEM AU tiles (3.1), OSM Geofabrik (3.3), Copernicus AU hub (1.3), DEA product (1.4), BoM per-product terms (5.2), RFS viewer terms (5.1).
- Find a verified URL for the statewide NSW FESM product (2.6).
- Confirm Earth Search collection ID (`sentinel-2-l2a` vs `sentinel-2-c1-l2a`).
- Check whether DEA burnt area still updates after Aug 2023 (2.2).
- Check CRS and grid of QLD fire scars vs Sentinel-2 (2.1).
- Choose AOI: an event with QLD scar labels and clear pre/post Sentinel-2 scenes.
