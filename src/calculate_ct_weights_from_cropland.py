"""
Calculate allocation weights from old CT counties to new planning regions
using CROPLAND AREA (not total area) as the weighting factor.

This is an alternative to the total-area-weighted approach in calculate_ct_weights_from_acreage.py,
focusing specifically on cropland rather than insured acres.

https://quickstats.nass.usda.gov/results/26241C25-DA7E-3439-9DBB-C3EF499C0A24
"""

import pandas as pd
import logging
from typing import Dict, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Connecticut old county FIPS codes
OLD_COUNTY_FIPS = {
    'Fairfield': '09001',
    'Hartford': '09003',
    'Litchfield': '09005',
    'Middlesex': '09007',
    'New Haven': '09009',
    'New London': '09011',
    'Tolland': '09013',
    'Windham': '09015'
}

# New planning region FIPS codes
# Updated to match actual 2024 data column names
NEW_REGION_FIPS = {
    'Capitol': '09901',
    'Lower CT River Valley': '09903',
    'Naugatuck Valley': '09904',
    'Northeastern CT': '09905',
    'Northwest Hills': '09906',
    'South Central CT': '09907',
    'Southeastern CT': '09908',
    'Western CT': '09909'
}

# Known mappings: which old counties feed into which new regions
# Based on official CT town assignments
# Updated to remove Greater Bridgeport (09902) - not in 2024 data
COUNTY_TO_REGION_RELATIONSHIPS = {
    '09001': ['09909'],  # Fairfield → Western CT (Greater Bridgeport merged into Western CT)
    '09003': ['09901', '09906'],  # Hartford → Capitol, Northwest Hills
    '09005': ['09906', '09909'],  # Litchfield → Northwest Hills, Western CT
    '09007': ['09903'],  # Middlesex → Lower CT River Valley (1:1)
    '09009': ['09907', '09904', '09903'],  # New Haven → South Central, Naugatuck, Lower CT River
    '09011': ['09908', '09905'],  # New London → Southeastern, Northeastern
    '09013': ['09905', '09901'],  # Tolland → Northeastern, Capitol
    '09015': ['09905']  # Windham → Northeastern (1:1)
}


def read_crop_insurance_data(filepath: str) -> pd.DataFrame:
    """Read crop insurance benefits CSV file."""
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Successfully read {len(df)} records from {filepath}")
        return df
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        raise


def read_cropland_data(filepath: str) -> pd.DataFrame:
    """
    Read cropland area data for Connecticut counties from USDA NASS.

    Expected format: CSV with columns for county FIPS and cropland acres
    E.g., county_fips, county_name, cropland_acres

    Args:
        filepath: Path to cropland data CSV

    Returns:
        DataFrame with cropland area by county
    """
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Successfully read cropland data from {filepath}")
        logger.info(f"Columns found: {df.columns.tolist()}")

        # Try to identify the correct columns
        # Common USDA NASS column names
        fips_candidates = ['County ANSI', 'county_fips', 'county_code', 'FIPS', 'fips_code']
        acres_candidates = ['Value', 'cropland_acres', 'acres', 'Cropland - Acres', 'AG LAND, CROPLAND - ACRES']

        fips_col = None
        acres_col = None

        # Find FIPS column (prioritize County ANSI)
        for col in fips_candidates:
            if col in df.columns:
                fips_col = col
                break

        # Find acres column
        for col in acres_candidates:
            if col in df.columns:
                acres_col = col
                break

        if fips_col is None:
            raise ValueError(f"Could not find FIPS code column. Available columns: {df.columns.tolist()}")

        if acres_col is None:
            raise ValueError(f"Could not find acres column. Available columns: {df.columns.tolist()}")

        logger.info(f"Using FIPS column: '{fips_col}'")
        logger.info(f"Using acres column: '{acres_col}'")

        # Get State ANSI to construct full FIPS
        if 'State ANSI' in df.columns:
            df['full_fips'] = df['State ANSI'].astype(str).str.zfill(2) + df[fips_col].astype(str).str.zfill(3)
            fips_source = 'full_fips'
        else:
            fips_source = fips_col

        # Standardize column names
        df_clean = df[[fips_source, acres_col]].copy()
        df_clean.columns = ['county_fips', 'cropland_acres']

        # Clean FIPS codes - ensure they're 5-digit strings with leading zeros
        df_clean['county_fips'] = df_clean['county_fips'].astype(str).str.zfill(5)

        # Clean acres values
        # Replace USDA NASS data suppression codes with NaN
        # (D) = Withheld to avoid disclosing data
        # (Z) = Less than half the unit shown
        df_clean['cropland_acres'] = df_clean['cropland_acres'].astype(str).str.strip()
        df_clean['cropland_acres'] = df_clean['cropland_acres'].replace({
            '(D)': None,
            ' (D)': None,
            '(Z)': '0',
            ' (Z)': '0',
            '': None
        })

        # Remove commas and convert to numeric
        df_clean['cropland_acres'] = df_clean['cropland_acres'].str.replace(',', '')
        df_clean['cropland_acres'] = pd.to_numeric(df_clean['cropland_acres'], errors='coerce')

        # Filter for Connecticut only (FIPS codes starting with '09')
        df_clean = df_clean[df_clean['county_fips'].str.startswith('09')]

        if df_clean.empty:
            raise ValueError("No Connecticut counties found in the data")

        # Drop rows with missing data
        missing_data = df_clean[df_clean['cropland_acres'].isna()]
        if not missing_data.empty:
            logger.warning("\nCounties with suppressed/missing cropland data:")
            for _, row in missing_data.iterrows():
                county_name = [k for k, v in OLD_COUNTY_FIPS.items() if v == row['county_fips']]
                county_name = county_name[0] if county_name else 'Unknown'
                logger.warning(f"  {row['county_fips']} ({county_name}): Data suppressed or missing")

        df_clean = df_clean.dropna(subset=['cropland_acres'])

        if df_clean.empty:
            raise ValueError("All Connecticut counties have suppressed/missing cropland data")

        logger.info("\nCropland acres by county:")
        for _, row in df_clean.iterrows():
            county_name = [k for k, v in OLD_COUNTY_FIPS.items() if v == row['county_fips']]
            county_name = county_name[0] if county_name else 'Unknown'
            logger.info(f"  {row['county_fips']} ({county_name}): {row['cropland_acres']:,.0f} acres")

        return df_clean
    except Exception as e:
        logger.error(f"Error reading cropland file {filepath}: {e}")
        raise


def extract_ct_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Extract Connecticut data for 2023 (old counties) and 2024 (new regions)."""
    logger.info("Extracting Connecticut data...")

    # Filter for Connecticut
    ct_df = df[df['state'] == 'Connecticut'].copy()

    if ct_df.empty:
        logger.error("No Connecticut data found!")
        return None, None

    # 2023 data (old counties)
    data_2023 = ct_df[ct_df['year'] == 2023].copy()

    # 2024 data (new planning regions)
    data_2024 = ct_df[ct_df['year'] == 2024].copy()

    logger.info(f"Found {len(data_2023)} records for 2023 (old counties)")
    logger.info(f"Found {len(data_2024)} records for 2024 (new regions)")

    return data_2023, data_2024


def calculate_cropland_weights(cropland_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate allocation weights based on CROPLAND AREA distribution.

    For counties that split into multiple regions, the weight is determined by
    the proportion of cropland area in each destination region.

    Args:
        cropland_data: DataFrame with county_fips and cropland_acres columns

    Returns:
        DataFrame with allocation weights
    """
    logger.info("\nCalculating cropland-based allocation weights...")

    # Create a mapping of county FIPS to cropland acres
    cropland_by_county = cropland_data.set_index('county_fips')['cropland_acres'].to_dict()

    weights = []

    for old_name, old_fips in OLD_COUNTY_FIPS.items():
        # Get cropland acres for this old county
        old_cropland = cropland_by_county.get(old_fips, 0)

        if old_cropland == 0:
            logger.warning(f"No cropland data for {old_name} ({old_fips})")
            continue

        # Get which new regions this county feeds into
        new_region_fips_list = COUNTY_TO_REGION_RELATIONSHIPS.get(old_fips, [])

        if len(new_region_fips_list) == 1:
            # 1:1 mapping - all cropland goes to one region
            new_fips = new_region_fips_list[0]
            new_name = [k for k, v in NEW_REGION_FIPS.items() if v == new_fips][0]
            weights.append({
                'old_fips_code': old_fips,
                'old_county_name': old_name,
                'new_fips_code': new_fips,
                'new_region_name': new_name,
                'allocation_weight': 1.0,
                'old_county_cropland_acres': old_cropland,
                'allocated_cropland_acres': old_cropland,
                'notes': 'Complete 1:1 mapping'
            })
        else:
            # Split mapping - need to distribute based on cropland proportions
            # Get cropland area in each destination region
            total_dest_cropland = 0
            dest_cropland = {}

            for new_fips in new_region_fips_list:
                new_name = [k for k, v in NEW_REGION_FIPS.items() if v == new_fips][0]

                # Find all counties that contribute to this region
                contributing_counties = [
                    cfips for cfips, regions in COUNTY_TO_REGION_RELATIONSHIPS.items()
                    if new_fips in regions
                ]

                # Sum cropland from contributing counties (partial contribution for split counties)
                region_cropland = 0
                for cfips in contributing_counties:
                    county_cropland = cropland_by_county.get(cfips, 0)
                    county_regions = COUNTY_TO_REGION_RELATIONSHIPS.get(cfips, [])

                    # If county only feeds this region, add full amount
                    # If county splits, we'll calculate proportional later
                    if len(county_regions) == 1:
                        region_cropland += county_cropland
                    else:
                        # For split counties, divide equally among destinations for initial estimate
                        region_cropland += county_cropland / len(county_regions)

                dest_cropland[new_fips] = region_cropland
                total_dest_cropland += region_cropland

            # Allocate proportionally based on destination cropland areas
            if total_dest_cropland > 0:
                for new_fips in new_region_fips_list:
                    new_name = [k for k, v in NEW_REGION_FIPS.items() if v == new_fips][0]

                    # Proportion based on estimated cropland in destination region
                    proportion = dest_cropland[new_fips] / total_dest_cropland
                    allocated_acres = old_cropland * proportion

                    weights.append({
                        'old_fips_code': old_fips,
                        'old_county_name': old_name,
                        'new_fips_code': new_fips,
                        'new_region_name': new_name,
                        'allocation_weight': round(proportion, 4),
                        'old_county_cropland_acres': old_cropland,
                        'allocated_cropland_acres': round(allocated_acres, 2),
                        'notes': f'Cropland-weighted allocation ({proportion:.1%})'
                    })
            else:
                logger.warning(f"No destination cropland data for splits from {old_name}")

    weights_df = pd.DataFrame(weights)

    logger.info("\n" + "=" * 80)
    logger.info("CROPLAND-BASED ALLOCATION WEIGHTS")
    logger.info("=" * 80)
    logger.info(weights_df.to_string(index=False))

    return weights_df


def validate_weights(weights_df: pd.DataFrame) -> None:
    """Validate that weights sum to 1.0 for each old county."""
    logger.info("\nValidating weights...")

    weight_sums = weights_df.groupby('old_fips_code')['allocation_weight'].sum()

    all_valid = True
    for fips, total in weight_sums.items():
        county_name = [k for k, v in OLD_COUNTY_FIPS.items() if v == fips][0]
        if abs(total - 1.0) > 0.001:
            logger.warning(f"⚠ Weights for {county_name} sum to {total:.4f} (expected 1.0)")
            all_valid = False
        else:
            logger.info(f"✓ Weights for {county_name} sum to {total:.4f}")

    if all_valid:
        logger.info("\n✓ All weight validations passed!")


def compare_approaches(weights_cropland: pd.DataFrame,
                       data_2023: pd.DataFrame,
                       data_2024: pd.DataFrame) -> pd.DataFrame:
    """
    Apply cropland weights to 2023 data and compare with actual 2024.

    Args:
        weights_cropland: Cropland-based allocation weights
        data_2023: 2023 county-level data
        data_2024: 2024 region-level actual data

    Returns:
        Comparison DataFrame
    """
    logger.info("\n" + "=" * 80)
    logger.info("COMPARING CROPLAND-WEIGHTED APPROACH TO 2024 ACTUALS")
    logger.info("=" * 80)

    # Apply weights to 2023 data
    remapped = data_2023.merge(
        weights_cropland[['old_county_name', 'new_region_name', 'allocation_weight']],
        left_on='county',
        right_on='old_county_name',
        how='left'
    )

    # Calculate weighted acres
    remapped['acres_weighted'] = remapped['acres_insured'] * remapped['allocation_weight']

    # Aggregate by new region
    cropland_method = remapped.groupby('new_region_name')['acres_weighted'].sum().reset_index()
    cropland_method.columns = ['region', 'acres_cropland_method']

    # Get actual 2024 totals
    actual_2024 = data_2024.groupby('county')['acres_insured'].sum().reset_index()
    actual_2024.columns = ['region', 'acres_2024_actual']

    # Compare
    comparison = cropland_method.merge(actual_2024, on='region', how='outer')
    comparison['difference'] = comparison['acres_2024_actual'] - comparison['acres_cropland_method']
    comparison['pct_error'] = (comparison['difference'] / comparison['acres_2024_actual'] * 100).round(2)

    logger.info("\n" + comparison.to_string(index=False))

    # Summary statistics
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
        "-- Cropland-weighted allocation from old CT counties to new planning regions",
        "-- Based on USDA NASS cropland area data (2022)",
        "-- Generated by calculate_ct_weights_from_cropland.py\n",
        "INSERT INTO ${SCHEMA}.ct_county_to_region_weights",
        "(old_fips_code, old_county_name, new_fips_code, new_region_name, allocation_weight, method, notes)",
        "VALUES"
    ]

    value_lines = []
    for _, row in weights_df.iterrows():
        value_lines.append(
            f"  ('{row['old_fips_code']}', '{row['old_county_name']}', "
            f"'{row['new_fips_code']}', '{row['new_region_name']}', "
            f"{row['allocation_weight']:.4f}, 'cropland_weighted', '{row['notes']}')"
        )

    sql_lines.append(',\n'.join(value_lines))
    sql_lines.append(";\n")

    sql = '\n'.join(sql_lines)

    try:
        with open(output_path, 'w') as f:
            f.write(sql)
        logger.info(f"✓ SQL saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error saving SQL to {output_path}: {e}")
        raise


def main():
    """Main execution function."""
    # Input files
    ci_data_file = "../data/crop-insurance/ci_state_county_year_benefits 2014-2024.csv"
    cropland_data_file = "../data/crop-insurance/ct_cropland_acres_by_county_2022.csv"

    # Output files
    weights_output = "../data/crop-insurance/output/ct_cropland_weights.csv"
    remapped_output = "../data/crop-insurance/output/ct_remapped_regions_cropland_2014-2023.csv"
    sql_output = "../queries/insert_ct_cropland_weights.sql"

    try:
        # Read crop insurance data
        logger.info("=" * 80)
        logger.info("CROPLAND-WEIGHTED ALLOCATION WEIGHT CALCULATION")
        logger.info("=" * 80)

        ci_data = read_crop_insurance_data(ci_data_file)

        # Extract CT data for comparison
        data_2023, data_2024 = extract_ct_data(ci_data)

        if data_2023 is None or data_2024 is None:
            raise ValueError("Could not extract CT data for 2023 and 2024")

        # Display 2023 and 2024 summary for reference
        logger.info("\n2023 County Data (acres_insured):")
        county_2023 = data_2023.groupby('county')['acres_insured'].sum()
        for county, acres in county_2023.items():
            logger.info(f"  {county}: {acres:,.0f}")

        logger.info("\n2024 Region Data (acres_insured):")
        region_2024 = data_2024.groupby('county')['acres_insured'].sum()
        for region, acres in region_2024.items():
            logger.info(f"  {region}: {acres:,.0f}")

        # Read cropland data
        cropland_data = read_cropland_data(cropland_data_file)

        # Calculate weights using cropland approach
        weights_df = calculate_cropland_weights(cropland_data)

        # Validate weights
        validate_weights(weights_df)

        # Compare with actual 2024 data
        comparison = compare_approaches(weights_df, data_2023, data_2024)

        # Save weights
        save_weights(weights_df, weights_output)

        # Apply weights to historical data (2014-2023)
        remapped_historical = apply_weights_to_historical_data(ci_data, weights_df, remapped_output)

        # Generate SQL
        generate_sql(weights_df, sql_output)

        logger.info("\n" + "=" * 80)
        logger.info("✓ CROPLAND-WEIGHTED CALCULATION COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"\nOutput files:")
        logger.info(f"  1. Weights: {weights_output}")
        logger.info(f"  2. Remapped historical data (2014-2023): {remapped_output}")
        logger.info(f"  3. SQL: {sql_output}")
        logger.info(f"\nTotal weight records: {len(weights_df)}")
        logger.info("\nNext step: Compare both approaches (acreage vs cropland)")
        logger.info("to see which better predicts 2024 regional values.")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


def apply_weights_to_historical_data(df, weights_df, output_path):
    """
    Apply calculated cropland weights to all Connecticut data from 2014-2023 to create
    remapped data for the new planning regions.

    Args:
        df: Full crop insurance dataframe
        weights_df: Calculated allocation weights
        output_path: Path to save the remapped historical data
    """
    logger.info("\nApplying cropland weights to historical data (2014-2023)...")

    # Filter for Connecticut data 2014-2023
    ct_historical = df[(df['state'] == 'Connecticut') & (df['year'] <= 2023)].copy()

    if ct_historical.empty:
        logger.warning("No historical Connecticut data found!")
        return None

    logger.info(f"Found {len(ct_historical)} Connecticut records from 2014-2023")

    # Merge with weights
    remapped = ct_historical.merge(
        weights_df[['old_county_name', 'new_region_name', 'new_fips_code', 'allocation_weight']],
        left_on='county',
        right_on='old_county_name',
        how='left'
    )

    # Apply weights to all numeric columns
    numeric_cols = ['acres_insured', 'liabilities', 'premium', 'subsidy',
                    'indemnity', 'net_benefit', 'farmer_premium']

    for col in numeric_cols:
        if col in remapped.columns:
            remapped[f'{col}_weighted'] = remapped[col] * remapped['allocation_weight']

    # Also weight policies (though this is approximate)
    remapped['policies_prem_weighted'] = remapped['policies_prem'] * remapped['allocation_weight']

    # Aggregate by new region and year
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

    # Rename columns to remove '_weighted' suffix
    remapped_aggregated.columns = ['year', 'region', 'region_fips', 'policies_prem',
                                   'acres_insured', 'liabilities', 'premium',
                                   'subsidy', 'indemnity', 'net_benefit', 'farmer_premium']

    # Recalculate derived metrics
    remapped_aggregated['loss_ratio'] = remapped_aggregated['indemnity'] / remapped_aggregated['premium']
    remapped_aggregated['benefit_by_pol'] = remapped_aggregated['net_benefit'] / remapped_aggregated['policies_prem']
    remapped_aggregated['benefit_by_acre'] = remapped_aggregated['net_benefit'] / remapped_aggregated['acres_insured']

    # Sort by year and region
    remapped_aggregated = remapped_aggregated.sort_values(['year', 'region'])

    # Save to CSV
    remapped_aggregated.to_csv(output_path, index=False)
    logger.info(f"✓ Saved remapped historical data to: {output_path}")
    logger.info(f"  - Years covered: {remapped_aggregated['year'].min()} to {remapped_aggregated['year'].max()}")
    logger.info(f"  - Total records: {len(remapped_aggregated)}")

    # Show summary by year
    logger.info("\nRemapped data summary by year:")
    year_summary = remapped_aggregated.groupby('year')['acres_insured'].sum()
    for year, acres in year_summary.items():
        logger.info(
            f"  {year}: {acres:,.0f} acres across {len(remapped_aggregated[remapped_aggregated['year'] == year])} regions")

    return remapped_aggregated

if __name__ == "__main__":
    main()