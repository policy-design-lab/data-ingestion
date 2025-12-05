"""
Calculate allocation weights from old CT counties (8) to new CT planning regions (COGs)
using TOTAL AREA (GIS polygon intersection) as the weighting factor.

weight(county -> region) = Area(county ∩ region) / Area(county)

Outputs:
  1) ct_total_area_gis_weights.csv
  2) ct_remapped_regions_total_area_gis_2014-2023.csv
  3) insert_ct_total_area_gis_weights.sql

Key robustness features:
  - Extract planning regions by GEOID (09110..09190 + 09120 optional), NOT by NAME.
  - Force GEOID / STATEFP / COUNTYFP to properly zero-padded strings.
  - Keep polygon parts only after overlay (drop lines/points).
  - Drop tiny slivers, renormalize weights per county to sum to 1.
  - Hard-fail if any expected planning region (09901..09909 excluding 09902) is missing.
"""

import logging
from typing import Dict, Tuple, Optional, Set, List

import pandas as pd
import numpy as np
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
AREA_CRS = "EPSG:5070"  # NAD83 / Conus Albers (equal-area, good for m² area)

TIGER_OLD_YEAR = 2021
TIGER_NEW_YEAR = 2024
TIGER_COUNTY_URL = "https://www2.census.gov/geo/tiger/TIGER{year}/COUNTY/tl_{year}_us_county.zip"

# If your downstream assumes Greater Bridgeport is merged into Western CT, keep True.
MERGE_GREATER_BRIDGEPORT_INTO_WESTERN_CT = True

# Drop tiny overlay slivers then renormalize weights per county
SLIVER_WEIGHT_EPS = 1e-6

# -----------------------------------------------------------------------------
# Old county FIPS (8 counties)
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# New planning region FIPS (8 regions used in your 2024 CI data)
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# TIGER GEOID (county-equivalent) -> internal region name.
# NOTE: 09120 is Greater Bridgeport in some TIGER vintages. We merge to Western CT.
# -----------------------------------------------------------------------------
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

EXPECTED_OLD_GEOIDS: Set[str] = set(OLD_COUNTY_FIPS.values())
EXPECTED_NEW_GEOIDS: Set[str] = set(TIGER_GEOID_TO_INTERNAL_REGION.keys())
EXPECTED_INTERNAL_REGION_FIPS: Set[str] = set(NEW_REGION_FIPS.values())

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _zfill_series(s: pd.Series, width: int) -> pd.Series:
    return (
        s.astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .str.zfill(width)
    )


def standardize_tiger_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Ensure TIGER string columns are correctly zero-padded.
    """
    gdf = gdf.copy()
    if "GEOID" in gdf.columns:
        gdf["GEOID"] = _zfill_series(gdf["GEOID"], 5)
    if "STATEFP" in gdf.columns:
        gdf["STATEFP"] = _zfill_series(gdf["STATEFP"], 2)
    if "COUNTYFP" in gdf.columns:
        gdf["COUNTYFP"] = _zfill_series(gdf["COUNTYFP"], 3)
    return gdf


def make_valid_gdf(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Fix invalid geometries and drop empties.
    """
    gdf = gdf.copy()
    gdf["geometry"] = gdf["geometry"].apply(lambda g: make_valid(g) if g is not None else None)
    gdf = gdf[~gdf["geometry"].isna() & ~gdf["geometry"].is_empty].copy()
    return gdf


def polygonal_only(geom):
    """
    Keep Polygon / MultiPolygon components (drop lines/points or empty).
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


# -----------------------------------------------------------------------------
# IO
# -----------------------------------------------------------------------------
def read_crop_insurance_data(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    logger.info(f"Successfully read {len(df)} records from {filepath}")
    return df


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
    out = ct[ct["GEOID"].isin(EXPECTED_OLD_GEOIDS)].copy()
    if len(out) != 8:
        cols = [c for c in ["GEOID", "NAME", "NAMELSAD", "STATEFP", "COUNTYFP"] if c in ct.columns]
        logger.error("CT preview:\n" + ct[cols].sort_values("GEOID").head(120).to_string(index=False))
        raise ValueError(f"Expected 8 old CT counties, found {len(out)}.")
    logger.info("Old CT counties kept: " + ", ".join(out.sort_values("GEOID")["NAME"].tolist()))
    return out


def extract_new_ct_planning_regions(tiger_new: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Robust extraction: Select CT planning regions by GEOID set.
    Also hard-debug missing GEOIDs to catch formatting issues.
    """
    ct = tiger_new.copy()
    ct["STATEFP"] = _zfill_series(ct["STATEFP"], 2)
    ct["GEOID"] = _zfill_series(ct["GEOID"], 5)

    ct = ct[ct["STATEFP"] == "09"].copy()

    available = set(ct["GEOID"].unique())
    missing_geoids = sorted(EXPECTED_NEW_GEOIDS - available)

    if missing_geoids:
        cols = [c for c in ["GEOID", "NAME", "NAMELSAD", "COUNTYFP", "LSAD"] if c in ct.columns]
        logger.error(f"Missing expected planning-region GEOIDs: {missing_geoids}")
        logger.error("CT GEOIDs present (sample): " + ", ".join(sorted(list(available))[:60]))
        logger.error("CT preview:\n" + ct[cols].sort_values("GEOID").head(160).to_string(index=False))
        raise ValueError("TIGER CT planning regions incomplete or GEOID formatting mismatch.")

    out = ct[ct["GEOID"].isin(EXPECTED_NEW_GEOIDS)].copy()
    logger.info(f"CT planning regions kept: {len(out)}")
    logger.info("Planning-region GEOIDs kept: " + ", ".join(sorted(out["GEOID"].unique())))
    return out


# -----------------------------------------------------------------------------
# Total-area weights
# -----------------------------------------------------------------------------
def calculate_total_area_weights_from_gis(old_ct: gpd.GeoDataFrame, new_ct: gpd.GeoDataFrame) -> pd.DataFrame:
    logger.info("\nCalculating TOTAL-AREA allocation weights via GIS intersection...")

    if old_ct.crs is None or new_ct.crs is None:
        raise ValueError("CRS missing on one or both TIGER layers.")

    # Reproject & validate
    old_p = make_valid_gdf(old_ct.to_crs(AREA_CRS))
    new_p = make_valid_gdf(new_ct.to_crs(AREA_CRS))
    logger.info(f"Reprojected to {AREA_CRS} and validated geometries.")

    old_p = old_p[["GEOID", "NAME", "geometry"]].rename(columns={"GEOID": "old_geoid", "NAME": "old_name"})
    new_p = new_p[["GEOID", "geometry"]].rename(columns={"GEOID": "new_geoid"})

    # Denominator per old county
    old_p["old_area_m2"] = old_p.geometry.area

    logger.info("Computing polygon intersections (overlay)...")
    inter = gpd.overlay(old_p, new_p, how="intersection", keep_geom_type=False)
    if inter.empty:
        raise ValueError("Overlay produced 0 rows. Check extraction and TIGER years.")

    # Keep polygonal parts only
    inter["geometry"] = inter["geometry"].apply(polygonal_only)
    inter = inter.dropna(subset=["geometry"]).set_geometry("geometry")
    inter = inter[~inter.geometry.is_empty].copy()
    if inter.empty:
        raise ValueError("After extracting polygon parts, no geometries remain.")

    inter["inter_area_m2"] = inter.geometry.area

    # Map GEOID -> internal region name -> internal fips
    inter["new_region_name"] = inter["new_geoid"].map(TIGER_GEOID_TO_INTERNAL_REGION)
    unmapped = inter[inter["new_region_name"].isna()]["new_geoid"].value_counts()
    if not unmapped.empty:
        logger.error("Unmapped planning-region GEOIDs present:\n" + unmapped.to_string())
        raise ValueError("Some new_geoid values were not mapped; fix TIGER_GEOID_TO_INTERNAL_REGION.")

    inter["new_fips_code"] = inter["new_region_name"].map(NEW_REGION_FIPS)

    # Aggregate intersection area by (old county, region)
    by_pair = inter.groupby(["old_geoid", "old_name", "new_fips_code", "new_region_name"], as_index=False).agg(
        allocated_area_m2=("inter_area_m2", "sum"),
        old_area_m2=("old_area_m2", "first"),
    )

    # Compute weights
    by_pair["allocation_weight"] = by_pair["allocated_area_m2"] / by_pair["old_area_m2"]

    # Drop tiny slivers then renormalize per county
    by_pair = by_pair[by_pair["allocation_weight"] >= SLIVER_WEIGHT_EPS].copy()
    by_pair["allocation_weight"] = by_pair.groupby("old_geoid")["allocation_weight"].transform(lambda s: s / s.sum())
    by_pair["allocated_area_m2"] = by_pair["old_area_m2"] * by_pair["allocation_weight"]

    # Build final weights df
    out = by_pair.rename(columns={"old_geoid": "old_fips_code", "old_name": "old_county_name"}).copy()
    out["allocation_weight"] = out["allocation_weight"].astype(float).round(6)
    out["old_county_total_area_m2"] = out["old_area_m2"].astype(float).round(2)
    out["allocated_area_m2"] = out["allocated_area_m2"].astype(float).round(2)

    out["notes"] = (
        f"GIS area intersection (TIGER {TIGER_OLD_YEAR} counties × TIGER {TIGER_NEW_YEAR} planning regions), "
        f"projected {AREA_CRS}"
        + (", Bridgeport merged into Western CT" if MERGE_GREATER_BRIDGEPORT_INTO_WESTERN_CT else "")
    )

    out = out[[
        "old_fips_code", "old_county_name",
        "new_fips_code", "new_region_name",
        "allocation_weight", "old_county_total_area_m2", "allocated_area_m2",
        "notes"
    ]].sort_values(["old_fips_code", "new_fips_code"]).reset_index(drop=True)

    return out


def validate_weights(weights_df: pd.DataFrame) -> None:
    """
    1) Weights must sum to 1 for each old county.
    2) ALL expected planning regions must appear somewhere in weights_df.
       Missing 09904/09906 is exactly what caused your -15% statewide loss.
    """
    logger.info("\nValidating weights...")

    sums = weights_df.groupby("old_fips_code")["allocation_weight"].sum()
    bad = sums[(sums < 0.999) | (sums > 1.001)]
    if not bad.empty:
        logger.error("Weights do not sum to 1.0 for these counties:\n" + bad.to_string())
        raise ValueError("Weights validation failed (sums not ~1).")

    present = set(weights_df["new_fips_code"].astype(str).unique())
    missing = sorted(EXPECTED_INTERNAL_REGION_FIPS - present)
    if missing:
        logger.error(f"Missing planning regions in weights_df: {missing}")
        raise ValueError("Weights are missing one or more expected planning regions.")

    logger.info("✓ Weights look valid: sums ~1 and all expected regions appear.")


# -----------------------------------------------------------------------------
# Apply weights to historical CI (2014-2023)
# -----------------------------------------------------------------------------
def apply_weights_to_historical_data(ci_df: pd.DataFrame, weights_df: pd.DataFrame, output_path: str) -> pd.DataFrame:
    logger.info("\nApplying TOTAL-AREA weights to historical CI data (2014-2023)...")

    ct_hist = ci_df[(ci_df["state"] == "Connecticut") & (ci_df["year"] <= 2023)].copy()
    if ct_hist.empty:
        raise ValueError("No Connecticut historical CI data (<=2023) found.")

    remapped = ct_hist.merge(
        weights_df[["old_county_name", "new_region_name", "new_fips_code", "allocation_weight"]],
        left_on="county",
        right_on="old_county_name",
        how="left"
    )

    missing = remapped[remapped["allocation_weight"].isna()]["county"].value_counts()
    if not missing.empty:
        logger.error("These counties did not match weights:\n" + missing.to_string())
        raise ValueError("County name mismatch between CI and weights. Fix merge keys.")

    numeric_cols = [
        "acres_insured",
        "liabilities",
        "premium",
        "subsidy",
        "indemnity",
        "net_benefit",
        "farmer_premium",
        "policies_prem",
    ]

    for col in numeric_cols:
        if col in remapped.columns:
            remapped[f"{col}_weighted"] = remapped[col] * remapped["allocation_weight"]

    agg = remapped.groupby(["year", "new_region_name", "new_fips_code"], as_index=False).agg({
        "policies_prem_weighted": "sum",
        "acres_insured_weighted": "sum",
        "liabilities_weighted": "sum",
        "premium_weighted": "sum",
        "subsidy_weighted": "sum",
        "indemnity_weighted": "sum",
        "net_benefit_weighted": "sum",
        "farmer_premium_weighted": "sum",
    })

    agg = agg.rename(columns={
        "new_region_name": "region",
        "new_fips_code": "region_fips",
        "policies_prem_weighted": "policies_prem",
        "acres_insured_weighted": "acres_insured",
        "liabilities_weighted": "liabilities",
        "premium_weighted": "premium",
        "subsidy_weighted": "subsidy",
        "indemnity_weighted": "indemnity",
        "net_benefit_weighted": "net_benefit",
        "farmer_premium_weighted": "farmer_premium",
    })

    # Derived metrics
    agg["loss_ratio"] = agg["indemnity"] / agg["premium"].replace({0: pd.NA})
    agg["benefit_by_pol"] = agg["net_benefit"] / agg["policies_prem"].replace({0: pd.NA})
    agg["benefit_by_acre"] = agg["net_benefit"] / agg["acres_insured"].replace({0: pd.NA})

    # Ensure every year includes all 8 regions
    for y, g in agg.groupby("year"):
        present = set(g["region_fips"].astype(str).unique())
        missing = sorted(EXPECTED_INTERNAL_REGION_FIPS - present)
        if missing:
            logger.error(f"Year {y} missing regions: {missing}")
            raise ValueError("Remap output missing regions; weights/mapping are incomplete.")

    agg = agg.sort_values(["year", "region_fips"]).reset_index(drop=True)
    agg.to_csv(output_path, index=False)
    logger.info(f"✓ Saved remapped historical data to: {output_path}")
    return agg


# -----------------------------------------------------------------------------
# Save outputs
# -----------------------------------------------------------------------------
def save_weights(weights_df: pd.DataFrame, output_path: str) -> None:
    weights_df.to_csv(output_path, index=False)
    logger.info(f"✓ Weights saved to: {output_path}")


def generate_sql(weights_df: pd.DataFrame, output_path: str) -> None:
    sql_lines = [
        "-- Total-area (GIS) allocation from old CT counties to new planning regions",
        f"-- TIGER {TIGER_OLD_YEAR} counties × TIGER {TIGER_NEW_YEAR} planning regions",
        f"-- Area CRS: {AREA_CRS}",
        "-- Generated by calculate_ct_weights_from_total_area_gis.py\n",
        "INSERT INTO ${SCHEMA}.ct_county_to_region_weights",
        "(old_fips_code, old_county_name, new_fips_code, new_region_name, allocation_weight, method, notes)",
        "VALUES"
    ]

    vals = []
    for _, r in weights_df.iterrows():
        vals.append(
            f"  ('{r['old_fips_code']}', '{r['old_county_name']}', "
            f"'{r['new_fips_code']}', '{r['new_region_name']}', "
            f"{float(r['allocation_weight']):.6f}, 'total_area_gis', '{r['notes']}')"
        )

    sql_lines.append(",\n".join(vals))
    sql_lines.append(";\n")

    with open(output_path, "w") as f:
        f.write("\n".join(sql_lines))

    logger.info(f"✓ SQL saved to: {output_path}")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    # Inputs
    ci_data_file = "../data/crop-insurance/ci_state_county_year_benefits 2014-2024.csv"

    # Outputs
    weights_output = "../data/crop-insurance/output/ct_total_area_gis_weights.csv"
    remapped_output = "../data/crop-insurance/output/ct_remapped_regions_total_area_gis_2014-2023.csv"
    sql_output = "../queries/insert_ct_total_area_gis_weights.sql"

    logger.info("=" * 80)
    logger.info("TOTAL-AREA (GIS) ALLOCATION WEIGHT CALCULATION")
    logger.info("=" * 80)

    # Read CI
    ci_df = read_crop_insurance_data(ci_data_file)

    # Read TIGER layers
    tiger_old = read_tiger_county_layer(TIGER_OLD_YEAR)
    tiger_new = read_tiger_county_layer(TIGER_NEW_YEAR)

    # Extract CT old and CT planning regions
    old_ct = extract_old_ct_counties(tiger_old)
    new_ct = extract_new_ct_planning_regions(tiger_new)

    # Compute weights
    weights_df = calculate_total_area_weights_from_gis(old_ct, new_ct)
    validate_weights(weights_df)
    save_weights(weights_df, weights_output)

    # Apply weights to historical CI
    apply_weights_to_historical_data(ci_df, weights_df, remapped_output)

    # SQL insert
    generate_sql(weights_df, sql_output)

    logger.info("\n✓ TOTAL-AREA (GIS) CALCULATION COMPLETE")
    logger.info(f"  Weights:  {weights_output}")
    logger.info(f"  Remapped: {remapped_output}")
    logger.info(f"  SQL:      {sql_output}")


if __name__ == "__main__":
    main()
