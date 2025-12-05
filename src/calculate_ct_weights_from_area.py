"""
Calculate allocation weights from old CT counties to new planning regions
using TOTAL AREA (not cropland) as the weighting factor.

This implements the "area approach" with *exact* geometry intersection:
  weight(county -> region) = Area(county ∩ region) / Area(county)

GIS layers:
  - Old CT counties (legacy 8 counties) from TIGER/Line COUNTY (e.g., 2021)
  - New CT planning regions (COG county-equivalents) from TIGER/Line COUNTY (e.g., 2024)

Projection:
  - Reproject both layers to EPSG:5070 (NAD83 / Conus Albers, equal-area) before area math

Key change vs earlier version:
  - Map planning regions by TIGER GEOID (09110..09190) instead of by NAME/NAMELSAD strings.
    This avoids string mismatches that can collapse everything to weight=1.

Notes:
  - CT planning regions GEOIDs (county-equivalents):
      09110 Capitol
      09120 Greater Bridgeport
      09130 Lower CT River Valley
      09140 Naugatuck Valley
      09150 Northeastern CT
      09160 Northwest Hills
      09170 South Central CT
      09180 Southeastern CT
      09190 Western CT
  - If your business logic expects 8 regions (no Greater Bridgeport), this script merges
    09120 into Western CT by default.

Requires:
  geopandas, shapely, pyproj, fiona, pandas
"""

import pandas as pd
import geopandas as gpd
import logging
from typing import Tuple, Optional, Dict

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Constants / Mappings
# -----------------------------------------------------------------------------

# Connecticut old county FIPS codes (legacy 8 counties)
OLD_COUNTY_FIPS: Dict[str, str] = {
    'Fairfield': '09001',
    'Hartford': '09003',
    'Litchfield': '09005',
    'Middlesex': '09007',
    'New Haven': '09009',
    'New London': '09011',
    'Tolland': '09013',
    'Windham': '09015'
}

# New planning region FIPS codes (your internal 2024 data codes, not TIGER GEOIDs)
NEW_REGION_FIPS: Dict[str, str] = {
    'Capitol': '09901',
    'Lower CT River Valley': '09903',
    'Naugatuck Valley': '09904',
    'Northeastern CT': '09905',
    'Northwest Hills': '09906',
    'South Central CT': '09907',
    'Southeastern CT': '09908',
    'Western CT': '09909'
}

# If your 2024 dataset does NOT include Greater Bridgeport as its own region,
# keep this True (Bridgeport merged into Western CT).
MERGE_GREATER_BRIDGEPORT_INTO_WESTERN_CT = True

# TIGER/Line years
TIGER_OLD_YEAR = 2021  # legacy county boundaries
TIGER_NEW_YEAR = 2024  # planning regions as county-equivalents

# TIGER COUNTY layer URL template
TIGER_COUNTY_URL = "https://www2.census.gov/geo/tiger/TIGER{year}/COUNTY/tl_{year}_us_county.zip"

# Equal-area CRS for area computations
AREA_CRS = "EPSG:5070"

# CT planning region GEOIDs (county-equivalents)
CT_PLANNING_REGION_GEOIDS = {"09110", "09120", "09130", "09140", "09150", "09160", "09170", "09180", "09190"}

# Map TIGER GEOID -> internal region name (keys in NEW_REGION_FIPS)
TIGER_GEOID_TO_INTERNAL_REGION: Dict[str, str] = {
    "09110": "Capitol",
    "09130": "Lower CT River Valley",
    "09140": "Naugatuck Valley",
    "09150": "Northeastern CT",
    "09160": "Northwest Hills",
    "09170": "South Central CT",
    "09180": "Southeastern CT",
    "09190": "Western CT",
    # Greater Bridgeport (if merging)
    "09120": "Western CT" if MERGE_GREATER_BRIDGEPORT_INTO_WESTERN_CT else "Greater Bridgeport"
}


# -----------------------------------------------------------------------------
# IO: Crop insurance data (for comparing vs 2024 actuals and remapping 2014-2023)
# -----------------------------------------------------------------------------

def read_crop_insurance_data(filepath: str) -> pd.DataFrame:
    """Read crop insurance CSV file."""
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Successfully read {len(df)} records from {filepath}")
        return df
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        raise


def extract_ct_data(df: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Extract Connecticut data for 2023 (old counties) and 2024 (new regions)."""
    logger.info("Extracting Connecticut data...")

    ct_df = df[df['state'] == 'Connecticut'].copy()
    if ct_df.empty:
        logger.error("No Connecticut data found!")
        return None, None

    data_2023 = ct_df[ct_df['year'] == 2023].copy()
    data_2024 = ct_df[ct_df['year'] == 2024].copy()

    logger.info(f"Found {len(data_2023)} records for 2023 (old counties)")
    logger.info(f"Found {len(data_2024)} records for 2024 (new regions)")
    return data_2023, data_2024


# -----------------------------------------------------------------------------
# IO: TIGER/Line
# -----------------------------------------------------------------------------

def read_tiger_county_layer(year: int) -> gpd.GeoDataFrame:
    """Read TIGER/Line COUNTY layer for a given year."""
    url = TIGER_COUNTY_URL.format(year=year)
    try:
        logger.info(f"Reading TIGER/Line COUNTY {year}: {url}")
        gdf = gpd.read_file(url)
        logger.info(f"Loaded {len(gdf)} features from TIGER {year}")
        logger.info(f"Original CRS (TIGER {year}): {gdf.crs}")
        return gdf
    except Exception as e:
        logger.error(f"Error reading TIGER/Line {year} COUNTY layer: {e}")
        raise


def extract_old_ct_counties(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Filter TIGER COUNTY layer to the 8 legacy CT counties by GEOID."""
    needed = {"STATEFP", "GEOID", "NAME", "geometry"}
    missing = needed - set(gdf.columns)
    if missing:
        raise ValueError(f"TIGER layer missing columns {missing}. Columns: {gdf.columns.tolist()}")

    old_geoids = set(OLD_COUNTY_FIPS.values())
    out = gdf[(gdf["STATEFP"] == "09") & (gdf["GEOID"].isin(old_geoids))].copy()

    if out.empty:
        raise ValueError("No old CT counties found after filtering. Check TIGER year and GEOIDs.")

    logger.info(f"Old CT counties features kept: {len(out)}")
    logger.info("Old counties: " + ", ".join(out.sort_values("GEOID")["NAME"].tolist()))
    return out


def extract_new_ct_planning_regions(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Filter TIGER COUNTY layer to CT planning regions (county-equivalents) by GEOID."""
    needed = {"STATEFP", "GEOID", "NAME", "geometry"}
    missing = needed - set(gdf.columns)
    if missing:
        raise ValueError(f"TIGER layer missing columns {missing}. Columns: {gdf.columns.tolist()}")

    ct = gdf[gdf["STATEFP"] == "09"].copy()
    out = ct[ct["GEOID"].astype(str).isin(CT_PLANNING_REGION_GEOIDS)].copy()

    if out.empty:
        cols = [c for c in ["GEOID", "NAME", "NAMELSAD", "COUNTYFP", "LSAD"] if c in ct.columns]
        logger.error("No CT planning regions found. Here are CT COUNTY rows (first 20):")
        logger.error("\n" + ct[cols].head(20).to_string(index=False))
        raise ValueError("No CT planning regions found in this TIGER year/file.")

    logger.info(f"CT planning regions features kept: {len(out)}")
    logger.info("Planning region GEOIDs: " + ", ".join(sorted(out["GEOID"].astype(str).unique())))
    # Helpful label display
    label_col = "NAMELSAD" if "NAMELSAD" in out.columns else "NAME"
    logger.info("Regions: " + ", ".join(out.sort_values("GEOID")[label_col].tolist()))
    return out


# -----------------------------------------------------------------------------
# Total-area (GIS) weights via polygon intersection
# -----------------------------------------------------------------------------

def calculate_total_area_weights_from_gis(old_counties: gpd.GeoDataFrame,
                                         new_regions: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Calculate allocation weights using exact polygon intersection areas.

    Output columns:
      old_fips_code, old_county_name, new_fips_code, new_region_name, allocation_weight,
      old_county_total_area_m2, allocated_area_m2, notes
    """
    logger.info("\nCalculating TOTAL-AREA (GIS intersection) allocation weights...")

    if old_counties.crs is None or new_regions.crs is None:
        raise ValueError("CRS missing on one or both layers.")

    # Reproject to equal-area CRS
    old_p = old_counties.to_crs(AREA_CRS)
    new_p = new_regions.to_crs(AREA_CRS)
    logger.info(f"Reprojected both layers to {AREA_CRS} for area math.")

    # Prep minimal columns
    old_p = old_p[["GEOID", "NAME", "geometry"]].rename(columns={"GEOID": "old_geoid", "NAME": "old_name"})
    new_p = new_p[["GEOID", "NAME", "geometry"]].rename(columns={"GEOID": "new_geoid", "NAME": "new_name"})

    # Intersections
    logger.info("Computing polygon intersections (overlay)...")
    inter = gpd.overlay(old_p, new_p, how="intersection", keep_geom_type=False)
    inter = inter[inter.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

    if inter.empty:
        raise ValueError("No polygon intersections found; check inputs/CRS.")

    inter["inter_area_m2"] = inter.geometry.area

    # Sanity logs BEFORE mapping
    logger.info("Intersections per old county:\n" + inter["old_geoid"].value_counts().to_string())
    logger.info(f"Unique planning region GEOIDs in intersections: {inter['new_geoid'].nunique()}")

    # Map planning region GEOID -> internal region name
    inter["mapped_region_name"] = inter["new_geoid"].astype(str).map(TIGER_GEOID_TO_INTERNAL_REGION)

    unmapped = inter[inter["mapped_region_name"].isna()]["new_geoid"].value_counts()
    if not unmapped.empty:
        logger.error("Unmapped new_geoid values:\n" + unmapped.to_string())

    inter = inter.dropna(subset=["mapped_region_name"])
    if inter.empty:
        raise ValueError("After GEOID mapping, no planning regions remain. Check TIGER_GEOID_TO_INTERNAL_REGION.")

    # County totals (denominator)
    county_totals = inter.groupby(["old_geoid", "old_name"], as_index=False)["inter_area_m2"].sum().rename(
        columns={"inter_area_m2": "old_county_total_area_m2"}
    )

    # Numerators by (county, mapped_region)
    by_pair = inter.groupby(["old_geoid", "old_name", "mapped_region_name"], as_index=False)["inter_area_m2"].sum()
    by_pair = by_pair.merge(county_totals, on=["old_geoid", "old_name"], how="left")
    by_pair["allocation_weight"] = by_pair["inter_area_m2"] / by_pair["old_county_total_area_m2"]

    # Build output
    weights = []
    for _, row in by_pair.iterrows():
        old_fips = str(row["old_geoid"]).zfill(5)
        old_name = str(row["old_name"])

        new_region_name = str(row["mapped_region_name"])
        if new_region_name not in NEW_REGION_FIPS:
            logger.warning(f"Mapped region '{new_region_name}' not in NEW_REGION_FIPS; skipping row.")
            continue

        weights.append({
            "old_fips_code": old_fips,
            "old_county_name": old_name,
            "new_fips_code": NEW_REGION_FIPS[new_region_name],
            "new_region_name": new_region_name,
            "allocation_weight": round(float(row["allocation_weight"]), 6),
            "old_county_total_area_m2": round(float(row["old_county_total_area_m2"]), 2),
            "allocated_area_m2": round(float(row["inter_area_m2"]), 2),
            "notes": (
                f"GIS area intersection (TIGER {TIGER_OLD_YEAR} counties × TIGER {TIGER_NEW_YEAR} planning regions), "
                f"projected {AREA_CRS}"
                + (", Bridgeport merged into Western CT" if MERGE_GREATER_BRIDGEPORT_INTO_WESTERN_CT else "")
            )
        })

    weights_df = pd.DataFrame(weights)

    logger.info("\n" + "=" * 80)
    logger.info("TOTAL-AREA (GIS) ALLOCATION WEIGHTS")
    logger.info("=" * 80)
    logger.info(weights_df.sort_values(["old_fips_code", "new_fips_code"]).to_string(index=False))

    return weights_df


def validate_weights(weights_df: pd.DataFrame) -> None:
    """Validate that weights sum to 1.0 for each old county."""
    logger.info("\nValidating weights...")

    weight_sums = weights_df.groupby('old_fips_code')['allocation_weight'].sum()

    all_valid = True
    for fips, total in weight_sums.items():
        county_name = [k for k, v in OLD_COUNTY_FIPS.items() if v == fips]
        county_name = county_name[0] if county_name else fips
        if abs(total - 1.0) > 0.001:
            logger.warning(f"⚠ Weights for {county_name} sum to {total:.6f} (expected 1.0)")
            all_valid = False
        else:
            logger.info(f"✓ Weights for {county_name} sum to {total:.6f}")

    if all_valid:
        logger.info("\n✓ All weight validations passed!")


def compare_approaches(weights_df: pd.DataFrame,
                       data_2023: pd.DataFrame,
                       data_2024: pd.DataFrame) -> pd.DataFrame:
    """
    Apply area weights to 2023 data and compare with actual 2024.
    """
    logger.info("\n" + "=" * 80)
    logger.info("COMPARING TOTAL-AREA (GIS) APPROACH TO 2024 ACTUALS")
    logger.info("=" * 80)

    remapped = data_2023.merge(
        weights_df[['old_county_name', 'new_region_name', 'allocation_weight']],
        left_on='county',
        right_on='old_county_name',
        how='left'
    )

    remapped['acres_weighted'] = remapped['acres_insured'] * remapped['allocation_weight']

    area_method = remapped.groupby('new_region_name')['acres_weighted'].sum().reset_index()
    area_method.columns = ['region', 'acres_area_method']

    actual_2024 = data_2024.groupby('county')['acres_insured'].sum().reset_index()
    actual_2024.columns = ['region', 'acres_2024_actual']

    comparison = area_method.merge(actual_2024, on='region', how='outer')
    comparison['difference'] = comparison['acres_2024_actual'] - comparison['acres_area_method']
    comparison['pct_error'] = (comparison['difference'] / comparison['acres_2024_actual'] * 100).round(2)

    logger.info("\n" + comparison.to_string(index=False))
    logger.info(f"\nMean Absolute % Error: {abs(comparison['pct_error']).mean():.2f}%")
    logger.info(f"Max % Error: {abs(comparison['pct_error']).max():.2f}%")

    return comparison


def save_weights(weights_df: pd.DataFrame, output_path: str) -> None:
    """Save weights to CSV file."""
    try:
        weights_df.to_csv(output_path, index=False)
        logger.info(f"\n✓ Weights saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error saving weights to {output_path}: {e}")
        raise


def generate_sql(weights_df: pd.DataFrame, output_path: str) -> None:
    """Generate SQL for inserting weights into database."""
    sql_lines = [
        "-- Total-area (GIS) allocation from old CT counties to new planning regions",
        f"-- TIGER {TIGER_OLD_YEAR} counties × TIGER {TIGER_NEW_YEAR} planning regions; projected {AREA_CRS}",
        "-- Generated by calculate_ct_weights_from_area.py\n",
        "INSERT INTO ${SCHEMA}.ct_county_to_region_weights",
        "(old_fips_code, old_county_name, new_fips_code, new_region_name, allocation_weight, method, notes)",
        "VALUES"
    ]

    value_lines = []
    for _, row in weights_df.iterrows():
        value_lines.append(
            f"  ('{row['old_fips_code']}', '{row['old_county_name']}', "
            f"'{row['new_fips_code']}', '{row['new_region_name']}', "
            f"{row['allocation_weight']:.6f}, 'total_area_gis', '{row['notes']}')"
        )

    sql_lines.append(',\n'.join(value_lines))
    sql_lines.append(";\n")

    try:
        with open(output_path, 'w') as f:
            f.write('\n'.join(sql_lines))
        logger.info(f"✓ SQL saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error saving SQL to {output_path}: {e}")
        raise


def apply_weights_to_historical_data(df, weights_df, output_path):
    """
    Apply calculated weights to all Connecticut data from 2014-2023 to create
    remapped data for the new planning regions.
    """
    logger.info("\nApplying weights to historical data (2014-2023)...")

    ct_historical = df[(df['state'] == 'Connecticut') & (df['year'] <= 2023)].copy()
    if ct_historical.empty:
        logger.warning("No historical Connecticut data found!")
        return None

    logger.info(f"Found {len(ct_historical)} Connecticut records from 2014-2023")

    remapped = ct_historical.merge(
        weights_df[['old_county_name', 'new_region_name', 'new_fips_code', 'allocation_weight']],
        left_on='county',
        right_on='old_county_name',
        how='left'
    )

    numeric_cols = ['acres_insured', 'liabilities', 'premium', 'subsidy',
                    'indemnity', 'net_benefit', 'farmer_premium']

    for col in numeric_cols:
        if col in remapped.columns:
            remapped[f'{col}_weighted'] = remapped[col] * remapped['allocation_weight']

    remapped['policies_prem_weighted'] = remapped['policies_prem'] * remapped['allocation_weight']

    agg_dict = {
        'policies_prem_weighted': 'sum',
        'acres_insured_weighted': 'sum',
        'liabilities_weighted': 'sum',
        'premium_weighted': 'sum',
        'subsidy_weighted': 'sum',
        'indemnity_weighted': 'sum',
        'net_benefit_weighted': 'sum',
        'farmer_premium_weighted': 'sum'
    }

    remapped_aggregated = remapped.groupby(['year', 'new_region_name', 'new_fips_code']).agg(agg_dict).reset_index()

    remapped_aggregated.columns = ['year', 'region', 'region_fips', 'policies_prem',
                                   'acres_insured', 'liabilities', 'premium',
                                   'subsidy', 'indemnity', 'net_benefit', 'farmer_premium']

    remapped_aggregated['loss_ratio'] = remapped_aggregated['indemnity'] / remapped_aggregated['premium']
    remapped_aggregated['benefit_by_pol'] = remapped_aggregated['net_benefit'] / remapped_aggregated['policies_prem']
    remapped_aggregated['benefit_by_acre'] = remapped_aggregated['net_benefit'] / remapped_aggregated['acres_insured']

    remapped_aggregated = remapped_aggregated.sort_values(['year', 'region'])
    remapped_aggregated.to_csv(output_path, index=False)

    logger.info(f"✓ Saved remapped historical data to: {output_path}")
    logger.info(f"  - Years covered: {remapped_aggregated['year'].min()} to {remapped_aggregated['year'].max()}")
    logger.info(f"  - Total records: {len(remapped_aggregated)}")

    return remapped_aggregated


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    """Main execution function."""
    # Input files
    ci_data_file = "../data/crop-insurance/ci_state_county_year_benefits 2014-2024.csv"

    # Output files
    weights_output = "../data/crop-insurance/output/ct_total_area_gis_weights.csv"
    remapped_output = "../data/crop-insurance/output/ct_remapped_regions_total_area_gis_2014-2023.csv"
    sql_output = "../queries/insert_ct_total_area_gis_weights.sql"

    try:
        logger.info("=" * 80)
        logger.info("TOTAL-AREA (GIS) ALLOCATION WEIGHT CALCULATION")
        logger.info("=" * 80)

        ci_data = read_crop_insurance_data(ci_data_file)

        data_2023, data_2024 = extract_ct_data(ci_data)
        if data_2023 is None or data_2024 is None:
            raise ValueError("Could not extract CT data for 2023 and 2024")

        logger.info("\n2023 County Data (acres_insured):")
        for county, acres in data_2023.groupby('county')['acres_insured'].sum().items():
            logger.info(f"  {county}: {acres:,.0f}")

        logger.info("\n2024 Region Data (acres_insured):")
        for region, acres in data_2024.groupby('county')['acres_insured'].sum().items():
            logger.info(f"  {region}: {acres:,.0f}")

        # Read TIGER layers and extract CT polygons
        tiger_old = read_tiger_county_layer(TIGER_OLD_YEAR)
        tiger_new = read_tiger_county_layer(TIGER_NEW_YEAR)

        old_ct = extract_old_ct_counties(tiger_old)
        new_ct = extract_new_ct_planning_regions(tiger_new)

        # Calculate weights using exact GIS area intersections
        weights_df = calculate_total_area_weights_from_gis(old_ct, new_ct)

        # Validate weights
        validate_weights(weights_df)

        # Compare with actual 2024 data (optional but useful)
        _ = compare_approaches(weights_df, data_2023, data_2024)

        # Save weights
        save_weights(weights_df, weights_output)

        # Apply weights to historical data (2014-2023)
        _ = apply_weights_to_historical_data(ci_data, weights_df, remapped_output)

        # Generate SQL
        generate_sql(weights_df, sql_output)

        logger.info("\n" + "=" * 80)
        logger.info("✓ TOTAL-AREA (GIS) CALCULATION COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"\nOutput files:")
        logger.info(f"  1. Weights: {weights_output}")
        logger.info(f"  2. Remapped historical data (2014-2023): {remapped_output}")
        logger.info(f"  3. SQL: {sql_output}")
        logger.info(f"\nTotal weight records: {len(weights_df)}")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
