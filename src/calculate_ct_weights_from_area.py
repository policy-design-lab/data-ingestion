"""
Calculate allocation weights from old CT counties (8) to new CT planning regions (9)
using TOTAL AREA (GIS polygon intersection) as the weighting factor.

weight(county -> region) = Area(county ∩ region) / Area(county)

Key fixes:
  - make_valid() on both layers
  - extract polygon parts from GeometryCollections returned by overlay
  - compute denominator as TRUE old county area (not sum of intersections)
  - coverage checks + debug

Projection for area:
  - EPSG:5070 (equal-area)
"""

import logging
from typing import Dict, Optional, Tuple

import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union
from shapely.validation import make_valid

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
MERGE_GREATER_BRIDGEPORT_INTO_WESTERN_CT = True

TIGER_OLD_YEAR = 2021
TIGER_NEW_YEAR = 2024
TIGER_COUNTY_URL = "https://www2.census.gov/geo/tiger/TIGER{year}/COUNTY/tl_{year}_us_county.zip"

AREA_CRS = "EPSG:5070"

OLD_COUNTY_FIPS: Dict[str, str] = {
    "Fairfield": "09001",
    "Hartford": "09003",
    "Litchfield": "09005",
    "Middlesex": "09007",
    "New Haven": "09009",
    "New London": "09011",
    "Tolland": "09013",
    "Windham": "09015",
}

NEW_REGION_FIPS: Dict[str, str] = {
    "Capitol": "09901",
    "Lower CT River Valley": "09903",
    "Naugatuck Valley": "09904",
    "Northeastern CT": "09905",
    "Northwest Hills": "09906",
    "South Central CT": "09907",
    "Southeastern CT": "09908",
    "Western CT": "09909",
}

TIGER_GEOID_TO_INTERNAL_REGION: Dict[str, str] = {
    "09110": "Capitol",
    "09130": "Lower CT River Valley",
    "09140": "Naugatuck Valley",
    "09150": "Northeastern CT",
    "09160": "Northwest Hills",
    "09170": "South Central CT",
    "09180": "Southeastern CT",
    "09190": "Western CT",
    "09120": "Western CT" if MERGE_GREATER_BRIDGEPORT_INTO_WESTERN_CT else "Greater Bridgeport",
}

EXPECTED_OLD = set(OLD_COUNTY_FIPS.values())
EXPECTED_NEW = set(TIGER_GEOID_TO_INTERNAL_REGION.keys())


# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------
def _zfill_series(s: pd.Series, width: int) -> pd.Series:
    return (
        s.astype(str)
         .str.replace(r"\.0$", "", regex=True)
         .str.strip()
         .str.zfill(width)
    )


def standardize_tiger_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    if "GEOID" in gdf.columns:
        gdf["GEOID"] = _zfill_series(gdf["GEOID"], 5)
    if "STATEFP" in gdf.columns:
        gdf["STATEFP"] = _zfill_series(gdf["STATEFP"], 2)
    if "COUNTYFP" in gdf.columns:
        gdf["COUNTYFP"] = _zfill_series(gdf["COUNTYFP"], 3)
    return gdf


def polygonal_only(geom):
    """
    Keep polygonal area only.
    - Polygon/MultiPolygon -> keep
    - GeometryCollection -> union polygonal parts
    - Others -> None
    """
    if geom is None or geom.is_empty:
        return None

    gt = geom.geom_type
    if gt in ("Polygon", "MultiPolygon"):
        return geom

    if gt == "GeometryCollection":
        polys = []
        for part in geom.geoms:
            if part is None or part.is_empty:
                continue
            if part.geom_type in ("Polygon", "MultiPolygon"):
                polys.append(part)
        if not polys:
            return None
        return unary_union(polys)

    return None


def make_valid_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["geometry"] = gdf["geometry"].apply(lambda g: make_valid(g) if g is not None else None)
    gdf = gdf[~gdf["geometry"].isna() & ~gdf["geometry"].is_empty].copy()
    return gdf


# -----------------------------------------------------------------------------
# TIGER IO
# -----------------------------------------------------------------------------
def read_tiger_county_layer(year: int) -> gpd.GeoDataFrame:
    url = TIGER_COUNTY_URL.format(year=year)
    logger.info(f"Reading TIGER/Line COUNTY {year}: {url}")
    gdf = gpd.read_file(url)
    gdf = standardize_tiger_columns(gdf)
    logger.info(f"Loaded {len(gdf)} features from TIGER {year}")
    logger.info(f"Original CRS (TIGER {year}): {gdf.crs}")
    return gdf


def extract_old_ct_counties(tiger_old: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    ct = tiger_old[tiger_old["STATEFP"] == "09"].copy()
    out = ct[ct["GEOID"].isin(EXPECTED_OLD)].copy()
    if len(out) != 8:
        logger.error("CT rows preview:\n" + ct[["GEOID", "NAME"]].head(40).to_string(index=False))
        raise ValueError(f"Expected 8 old CT counties, found {len(out)}.")
    logger.info("Old CT counties kept: " + ", ".join(out.sort_values("GEOID")["NAME"].tolist()))
    return out


def extract_new_ct_planning_regions(tiger_new: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    ct = tiger_new[tiger_new["STATEFP"] == "09"].copy()

    # robust: filter by expected GEOIDs (09110..09190)
    out = ct[ct["GEOID"].isin(EXPECTED_NEW)].copy()
    if out.empty:
        cols = [c for c in ["GEOID", "NAME", "NAMELSAD", "COUNTYFP", "LSAD"] if c in ct.columns]
        logger.error("CT rows preview:\n" + ct[cols].head(80).to_string(index=False))
        raise ValueError("No CT planning regions found via expected GEOIDs.")

    logger.info(f"CT planning regions kept: {len(out)}")
    cols = [c for c in ["GEOID", "NAME", "NAMELSAD", "COUNTYFP", "LSAD"] if c in out.columns]
    logger.info("\nSelected planning regions table:\n" + out[cols].sort_values("GEOID").to_string(index=False))
    return out


# -----------------------------------------------------------------------------
# Core: area-weight calculation
# -----------------------------------------------------------------------------
def calculate_total_area_weights_from_gis(old_ct: gpd.GeoDataFrame, new_ct: gpd.GeoDataFrame) -> pd.DataFrame:
    logger.info("\nCalculating TOTAL-AREA allocation weights via GIS intersection...")

    if old_ct.crs is None or new_ct.crs is None:
        raise ValueError("CRS missing on one or both TIGER layers.")

    # Reproject to equal-area
    old_p = old_ct.to_crs(AREA_CRS).copy()
    new_p = new_ct.to_crs(AREA_CRS).copy()
    logger.info(f"Reprojected to {AREA_CRS}.")

    # Make valid (important before overlay)
    old_p = make_valid_gdf(old_p)
    new_p = make_valid_gdf(new_p)

    old_p = old_p[["GEOID", "NAME", "geometry"]].rename(columns={"GEOID": "old_geoid", "NAME": "old_name"})
    new_p = new_p[["GEOID", "geometry"]].rename(columns={"GEOID": "new_geoid"})

    # TRUE denominator: old county total area
    old_p["old_area_m2"] = old_p.geometry.area

    logger.info("Computing overlay intersection...")
    inter = gpd.overlay(old_p, new_p, how="intersection", keep_geom_type=False)

    if inter.empty:
        raise ValueError("Overlay produced 0 rows. Something is wrong with inputs.")

    # Extract polygonal area from GeometryCollections etc.
    inter["geometry"] = inter["geometry"].apply(polygonal_only)
    inter = inter.dropna(subset=["geometry"]).set_geometry("geometry")
    inter = inter[~inter.geometry.is_empty].copy()

    if inter.empty:
        raise ValueError("After extracting polygonal parts, no geometries remain.")

    inter["inter_area_m2"] = inter.geometry.area

    # Coverage check BEFORE mapping (pure geometry)
    pre = inter.groupby(["old_geoid", "old_name"], as_index=False).agg(
        covered_area_m2=("inter_area_m2", "sum"),
        old_area_m2=("old_area_m2", "first"),
    )
    pre["coverage_ratio"] = pre["covered_area_m2"] / pre["old_area_m2"]

    bad_pre = pre[pre["coverage_ratio"] < 0.99].sort_values("coverage_ratio")
    if not bad_pre.empty:
        logger.error("Overlay coverage is low BEFORE mapping (geometry mismatch/loss):\n" +
                     bad_pre[["old_geoid", "old_name", "coverage_ratio"]].to_string(index=False))
        # extra debug: show which new_geoid are present for the worst county
        worst = bad_pre.iloc[0]["old_geoid"]
        dbg = (inter[inter["old_geoid"] == worst]
               .groupby("new_geoid", as_index=False)["inter_area_m2"]
               .sum()
               .sort_values("inter_area_m2", ascending=False))
        logger.error(f"Top intersecting new_geoid for {worst}:\n" + dbg.head(20).to_string(index=False))
        raise ValueError("Overlay did not cover full old county area (coverage < 0.99).")

    # Map GEOID -> internal region name
    inter["new_region_name"] = inter["new_geoid"].map(TIGER_GEOID_TO_INTERNAL_REGION)
    unmapped = inter[inter["new_region_name"].isna()]["new_geoid"].value_counts()
    if not unmapped.empty:
        logger.error("Unmapped new_geoid values:\n" + unmapped.to_string())
    inter = inter.dropna(subset=["new_region_name"])
    if inter.empty:
        raise ValueError("After GEOID mapping, no intersections remain.")

    # Aggregate area per (old county, region)
    by_pair = inter.groupby(["old_geoid", "old_name", "new_region_name"], as_index=False).agg(
        allocated_area_m2=("inter_area_m2", "sum"),
        old_area_m2=("old_area_m2", "first"),
    )

    # Coverage check AFTER mapping (should be ~1 too)
    post = by_pair.groupby(["old_geoid", "old_name"], as_index=False).agg(
        covered_area_m2=("allocated_area_m2", "sum"),
        old_area_m2=("old_area_m2", "first"),
    )
    post["coverage_ratio"] = post["covered_area_m2"] / post["old_area_m2"]

    bad_post = post[post["coverage_ratio"] < 0.99].sort_values("coverage_ratio")
    if not bad_post.empty:
        logger.error("Coverage is low AFTER mapping (mapping drop):\n" +
                     bad_post[["old_geoid", "old_name", "coverage_ratio"]].to_string(index=False))
        raise ValueError("Mapping dropped area (coverage < 0.99). Check GEOID mapping dict.")

    # Weights
    by_pair["allocation_weight"] = by_pair["allocated_area_m2"] / by_pair["old_area_m2"]

    # Output
    rows = []
    for _, r in by_pair.iterrows():
        region = r["new_region_name"]
        if region not in NEW_REGION_FIPS:
            logger.warning(f"Region '{region}' not in NEW_REGION_FIPS; skipping.")
            continue
        rows.append({
            "old_fips_code": r["old_geoid"],
            "old_county_name": r["old_name"],
            "new_fips_code": NEW_REGION_FIPS[region],
            "new_region_name": region,
            "allocation_weight": round(float(r["allocation_weight"]), 6),
            "old_county_total_area_m2": round(float(r["old_area_m2"]), 2),
            "allocated_area_m2": round(float(r["allocated_area_m2"]), 2),
            "notes": (
                f"GIS area intersection (TIGER {TIGER_OLD_YEAR} counties × TIGER {TIGER_NEW_YEAR} planning regions), "
                f"projected {AREA_CRS}"
                + (", Bridgeport merged into Western CT" if MERGE_GREATER_BRIDGEPORT_INTO_WESTERN_CT else "")
            )
        })

    weights_df = pd.DataFrame(rows).sort_values(["old_fips_code", "new_fips_code"])

    logger.info("\nWeight sums by old county:\n" +
                weights_df.groupby("old_fips_code")["allocation_weight"].sum().to_string())
    logger.info("\n#regions per old county:\n" +
                weights_df.groupby("old_fips_code")["new_region_name"].nunique().to_string())

    logger.info("\n" + "=" * 80)
    logger.info("TOTAL-AREA ALLOCATION WEIGHTS")
    logger.info("=" * 80)
    logger.info(weights_df.to_string(index=False))

    return weights_df


def save_weights(weights_df: pd.DataFrame, output_path: str) -> None:
    weights_df.to_csv(output_path, index=False)
    logger.info(f"✓ Weights saved to: {output_path}")


def main():
    weights_output = "../data/crop-insurance/output/ct_total_area_gis_weights.csv"

    logger.info("=" * 80)
    logger.info("TOTAL-AREA (GIS) ALLOCATION WEIGHT CALCULATION")
    logger.info("=" * 80)

    tiger_old = read_tiger_county_layer(TIGER_OLD_YEAR)
    tiger_new = read_tiger_county_layer(TIGER_NEW_YEAR)

    old_ct = extract_old_ct_counties(tiger_old)
    new_ct = extract_new_ct_planning_regions(tiger_new)

    weights_df = calculate_total_area_weights_from_gis(old_ct, new_ct)
    save_weights(weights_df, weights_output)

    logger.info("✓ Done.")


if __name__ == "__main__":
    main()
