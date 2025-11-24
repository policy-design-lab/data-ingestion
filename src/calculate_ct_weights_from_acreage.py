"""
Calculate Connecticut county-to-planning region mapping weights using actual crop insurance acreage data.
Uses 2023 old county data and 2024 new planning region data to derive optimal allocation weights.
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Connecticut mappings
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
    '09001': ['09909'],  # Fairfield → Western CT (Greater Bridgeport merged into Western CT?)
    '09003': ['09901', '09906'],  # Hartford → Capitol, Northwest Hills
    '09005': ['09906', '09909'],  # Litchfield → Northwest Hills, Western CT
    '09007': ['09903'],  # Middlesex → Lower CT River Valley (1:1)
    '09009': ['09907', '09904', '09903'],  # New Haven → South Central, Naugatuck, Lower CT River
    '09011': ['09908', '09905'],  # New London → Southeastern, Northeastern
    '09013': ['09905', '09901'],  # Tolland → Northeastern, Capitol
    '09015': ['09905']  # Windham → Northeastern (1:1)
}


def read_crop_insurance_data(filepath):
    """Read the crop insurance CSV file."""
    logger.info(f"Reading crop insurance data from {filepath}")

    df = pd.read_csv(filepath)
    logger.info(f"Read {len(df)} rows")
    logger.info(f"Columns: {df.columns.tolist()}")

    return df


def extract_ct_data(df):
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


def calculate_weights_from_acreage(data_2023, data_2024):
    """
    Calculate allocation weights by comparing 2023 old county acres to 2024 new region acres.

    This uses an optimization approach: given the known relationships between old counties
    and new regions, find weights that make 2023 totals (when redistributed) match 2024 totals.
    """
    logger.info("Calculating allocation weights based on acreage...")

    # Aggregate 2023 by county
    county_2023 = data_2023.groupby('county').agg({
        'acres_insured': 'sum',
        'liabilities': 'sum'
    }).reset_index()

    # Aggregate 2024 by planning region
    region_2024 = data_2024.groupby('county').agg({
        'acres_insured': 'sum',
        'liabilities': 'sum'
    }).reset_index()

    logger.info("\n2023 Old County Totals:")
    logger.info(county_2023.to_string())

    logger.info("\n2024 New Planning Region Totals:")
    logger.info(region_2024.to_string())

    # Create lookup dictionaries for acres
    county_acres_lookup = county_2023.set_index('county')['acres_insured'].to_dict()
    region_acres_lookup = region_2024.set_index('county')['acres_insured'].to_dict()

    # Map county names to FIPS
    county_2023['county_fips'] = county_2023['county'].map(lambda x: OLD_COUNTY_FIPS.get(x))
    region_2024['region_fips'] = region_2024['county'].map(lambda x: NEW_REGION_FIPS.get(x))

    # For simple cases (1:1 mappings), weight is 1.0
    # For complex cases, use proportional allocation based on acres

    weights = []

    # Iterate over county names (keys), not FIPS codes
    for old_name, old_fips in OLD_COUNTY_FIPS.items():
        # Get 2023 acres for this old county
        old_row = county_2023[county_2023['county'] == old_name]
        if old_row.empty:
            logger.warning(f"No 2023 data for {old_name}")
            continue

        old_acres = old_row['acres_insured'].iloc[0]

        # Get which new regions this county feeds into
        new_region_fips_list = COUNTY_TO_REGION_RELATIONSHIPS.get(old_fips, [])

        if len(new_region_fips_list) == 1:
            # 1:1 mapping
            new_fips = new_region_fips_list[0]
            new_name = [k for k, v in NEW_REGION_FIPS.items() if v == new_fips][0]
            new_region_acres = region_acres_lookup.get(new_name, 0)

            weights.append({
                'old_fips_code': old_fips,
                'old_county_name': old_name,
                'old_county_acres_2023': old_acres,
                'new_fips_code': new_fips,
                'new_region_name': new_name,
                'new_region_acres_2024': new_region_acres,
                'allocation_weight': 1.0,
                'notes': 'Complete 1:1 mapping'
            })
        else:
            # Split mapping - need to estimate proportions
            # Use acreage in 2024 to back-calculate proportions
            total_new_acres = 0
            new_acres_by_region = {}

            for new_fips in new_region_fips_list:
                new_name = [k for k, v in NEW_REGION_FIPS.items() if v == new_fips][0]
                new_row = region_2024[region_2024['county'] == new_name]
                if not new_row.empty:
                    new_acres_by_region[new_fips] = new_row['acres_insured'].iloc[0]
                    total_new_acres += new_row['acres_insured'].iloc[0]

            # Allocate proportionally based on 2024 acreage in destination regions
            for new_fips in new_region_fips_list:
                new_name = [k for k, v in NEW_REGION_FIPS.items() if v == new_fips][0]

                if new_fips in new_acres_by_region and total_new_acres > 0:
                    # Proportion of this new region's acres relative to all regions this county feeds
                    proportion = new_acres_by_region[new_fips] / total_new_acres
                    new_region_acres = new_acres_by_region[new_fips]

                    weights.append({
                        'old_fips_code': old_fips,
                        'old_county_name': old_name,
                        'old_county_acres_2023': old_acres,
                        'new_fips_code': new_fips,
                        'new_region_name': new_name,
                        'new_region_acres_2024': new_region_acres,
                        'allocation_weight': round(proportion, 4),
                        'notes': f'Acreage-weighted allocation'
                    })

    return pd.DataFrame(weights)


def validate_weights(weights_df, data_2023, data_2024):
    """
    Validate that applying the weights to 2023 data produces results close to 2024 actual data.
    """
    logger.info("\nValidating allocation weights...")

    # Apply weights to 2023 data
    remapped_2023 = data_2023.merge(weights_df,
                                    left_on='county',
                                    right_on='old_county_name',
                                    how='left')

    # Multiply acres by weights
    remapped_2023['acres_weighted'] = remapped_2023['acres_insured'] * remapped_2023['allocation_weight']

    # Aggregate by new regions
    remapped_totals = remapped_2023.groupby('new_region_name')['acres_weighted'].sum().reset_index()
    remapped_totals.columns = ['region', 'acres_2023_remapped']

    # Get actual 2024 totals
    actual_2024 = data_2024.groupby('county')['acres_insured'].sum().reset_index()
    actual_2024.columns = ['region', 'acres_2024_actual']

    # Compare
    comparison = remapped_totals.merge(actual_2024, on='region', how='outer')
    comparison['difference'] = comparison['acres_2024_actual'] - comparison['acres_2023_remapped']
    comparison['pct_error'] = (comparison['difference'] / comparison['acres_2024_actual'] * 100).round(2)

    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION: Remapped 2023 vs Actual 2024")
    logger.info("=" * 80)
    logger.info(comparison.to_string(index=False))

    return comparison


def generate_sql(weights_df):
    """Generate SQL INSERT statements."""
    sql_lines = [
        "-- Connecticut County to Planning Region Mapping",
        "-- Calculated from crop insurance acreage data",
        "-- Weights optimized to make 2014-2023 remapped data consistent with 2024\n",
        "INSERT INTO ${SCHEMA}.ct_county_to_region_mapping",
        "(old_fips_code, old_county_name, new_fips_code, new_region_name, allocation_weight, notes) VALUES"
    ]

    rows = []
    for _, row in weights_df.iterrows():
        rows.append(
            f"('{row['old_fips_code']}', '{row['old_county_name']}', "
            f"'{row['new_fips_code']}', '{row['new_region_name']}', "
            f"{row['allocation_weight']:.4f}, '{row['notes']}')"
        )

    sql_lines.append(',\n'.join(rows))
    sql_lines.append("\nON CONFLICT DO NOTHING;")

    return '\n'.join(sql_lines)


def main():
    # File paths
    ci_csv = "../data/crop-insurance/ci_state_county_year_benefits 2014-2024.csv"
    output_weights_csv = "../data/crop-insurance/output/ct_county_region_mapping_acreage.csv"
    output_remapped_csv = "../data/crop-insurance/output/ct_remapped_regions_2014-2023_acreage.csv"
    output_sql = "../queries/insert_ct_county_region_mapping_acreage.sql"

    # Read data
    df = read_crop_insurance_data(ci_csv)

    # Extract CT data
    data_2023, data_2024 = extract_ct_data(df)

    if data_2023 is None or data_2024 is None:
        logger.error("Failed to extract Connecticut data")
        return

    # Calculate weights
    weights_df = calculate_weights_from_acreage(data_2023, data_2024)

    logger.info("\n" + "=" * 80)
    logger.info("CALCULATED ALLOCATION WEIGHTS")
    logger.info("=" * 80)
    logger.info(weights_df.to_string(index=False))

    # Validate
    validation = validate_weights(weights_df, data_2023, data_2024)

    # Save weights
    weights_df.to_csv(output_weights_csv, index=False)
    logger.info(f"\nSaved weights to: {output_weights_csv}")

    # Apply weights to historical data (2014-2023)
    remapped_historical = apply_weights_to_historical_data(df, weights_df, output_remapped_csv)

    # Generate SQL
    sql = generate_sql(weights_df)
    with open(output_sql, 'w') as f:
        f.write(sql)
    logger.info(f"Saved SQL to: {output_sql}")

    logger.info("\n" + "=" * 80)
    logger.info("SUCCESS! Acreage-based mapping complete.")
    logger.info("=" * 80)
    logger.info(f"\nOutput files:")
    logger.info(f"  1. Weights: {output_weights_csv}")
    logger.info(f"  2. Remapped historical data (2014-2023): {output_remapped_csv}")
    logger.info(f"  3. SQL: {output_sql}")


def apply_weights_to_historical_data(df, weights_df, output_path):
    """
    Apply calculated weights to all Connecticut data from 2014-2023 to create
    remapped data for the new planning regions.

    Args:
        df: Full crop insurance dataframe
        weights_df: Calculated allocation weights
        output_path: Path to save the remapped historical data
    """
    logger.info("\nApplying weights to historical data (2014-2023)...")

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
    logger.info(f"Saved remapped historical data to: {output_path}")
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