"""Per-AOI settings for Scarline. Add a new area here; both scripts read it."""

AOIS = {
    "capeyork": {
        "aoi_lonlat": (142.05, -13.5, 142.5, -13.0),
        "tile": "54LXL",
        "pre": "S2A_54LXL_20220713_0_L2A",
        "post": "S2B_54LXL_20221026_0_L2A",
        "truth_months": [8, 9, 10],
        "ambiguous_months": [7, 11],
    },
    "gulf": {
        # 0.1 deg inside tile 54KWF (141.00-142.04E, 17.18-18.18S) so the AOI never straddles a tile edge
        "aoi_lonlat": (141.10, -18.10, 141.50, -17.70),
        "tile": "54KWF",
        "pre": "S2A_54KWF_20220901_0_L2A",    # 0% cloud; no QLD scars before October
        "post": "S2B_54KWF_20221215_0_L2A",   # 0% cloud; covers most Oct-Nov burning
        "truth_months": [10, 11],
        "ambiguous_months": [9, 12],          # month 12 is ambiguous (post is 15 Dec)
    },
}
