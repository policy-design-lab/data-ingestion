import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Old Connecticut County FIPS codes (pre-2024)
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

# New Connecticut Planning Region FIPS codes (2024+)
NEW_REGION_FIPS = {
    'Capitol': '09101',
    'Greater Bridgeport': '09102',
    'Lower CT River Valley': '09103',
    'Naugatuck Valley': '09104',
    'Northeastern CT': '09105',
    'Northwest Hills': '09106',
    'South Central CT': '09107',
    'Southeastern CT': '09108',
    'Western CT': '09109'
}

# Mapping: Old County FIPS -> List of New Region FIPS
COUNTY_TO_REGION_RELATIONSHIPS = {
    '09001': ['09102', '09109'],  # Fairfield -> Greater Bridgeport + Western CT
    '09003': ['09101'],  # Hartford -> Capitol Region
    '09005': ['09106'],  # Litchfield -> Northwest Hills
    '09007': ['09103'],  # Middlesex -> Lower CT River Valley
    '09009': ['09104', '09107'],  # New Haven -> Naugatuck Valley + South Central CT
    '09011': ['09108'],  # New London -> Southeastern CT
    '09013': ['09101'],  # Tolland -> Capitol Region
    '09015': ['09105']  # Windham -> Northeastern CT
}


def read_crop_insurance_data(filepath):
    """Read the crop insurance CSV file."""
    logger.info(f"Reading crop insurance data from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} total records")
    return df


def extract_ct_data(df):
    """Extract Connecticut data for 2014-2023 (old counties) and 2024 (new regions)."""
    logger.info("Extracting Connecticut data...")

    # Filter for Connecticut
    ct_df = df[df['state'] == 'Connecticut'].copy()

    if ct_df.empty:
        logger.error("No Connecticut data found!")
        return None, None

    # 2014-2023 data (old counties)
    data_historical = ct_df[ct_df['year'].between(2014, 2023)].copy()

    # 2024 data (new planning regions)
    data_2024 = ct_df[ct_df['year'] == 2024].copy()

    logger.info(f"Found {len(data_historical)} records for 2014-2023 (old counties)")
    logger.info(f"Found {len(data_2024)} records for 2024 (new regions)")

    # Log unique county names to help debug
    if not data_historical.empty:
        logger.info(f"Unique counties in 2014-2023 data: {sorted(data_historical['county'].unique())}")
    if not data_2024.empty:
        logger.info(f"Unique regions in 2024 data: {sorted(data_2024['county'].unique())}")

    return data_historical, data_2024


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

    weights = []

    # Iterate over county names from the actual data
    for old_name in county_2023['county'].unique():
        # Find matching FIPS code
        old_fips = OLD_COUNTY_FIPS.get(old_name)

        if not old_fips:
            logger.warning(f"No FIPS mapping found for county: {old_name}")
            continue

        # Get 2023 acres for this old county
        old_row = county_2023[county_2023['county'] == old_name]
        if old_row.empty:
            logger.warning(f"No 2023 data for {old_name}")
            continue

        old_acres = old_row['acres_insured'].iloc[0]

        # Get which new regions this county feeds into
        new_region_fips_list = COUNTY_TO_REGION_RELATIONSHIPS.get(old_fips, [])

        if not new_region_fips_list:
            logger.warning(f"No region mapping found for county FIPS: {old_fips} ({old_name})")
            continue

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

    weights_df = pd.DataFrame(weights)

    if weights_df.empty:
        logger.error("No weights were calculated! Check county name mappings.")

    return weights_df


def validate_weights(weights_df, data_2023, data_2024):
    """
    Validate that applying weights to 2023 data produces reasonable results
    compared to 2024 data.
    """
    logger.info("\n=== Validating Weights ===")

    if weights_df.empty:
        logger.error("Cannot validate empty weights DataFrame")
        return None

    # Aggregate 2023 by county
    county_2023 = data_2023.groupby('county').agg({
        'acres_insured': 'sum',
        'liabilities': 'sum'
    }).reset_index()

    # Aggregate 2024 by region
    region_2024 = data_2024.groupby('county').agg({
        'acres_insured': 'sum',
        'liabilities': 'sum'
    }).reset_index()

    # Apply weights to 2023 data
    redistributed = []
    for _, weight_row in weights_df.iterrows():
        old_county_name = weight_row['old_county_name']
        new_region_name = weight_row['new_region_name']
        weight = weight_row['allocation_weight']

        county_row = county_2023[county_2023['county'] == old_county_name]
        if not county_row.empty:
            redistributed.append({
                'new_region': new_region_name,
                'acres_redistributed': county_row['acres_insured'].iloc[0] * weight,
                'liabilities_redistributed': county_row['liabilities'].iloc[0] * weight
            })

    if not redistributed:
        logger.error("No redistributed data generated")
        return None

    redistributed_df = pd.DataFrame(redistributed)
    redistributed_summary = redistributed_df.groupby('new_region').sum().reset_index()

    # Compare
    comparison = pd.merge(
        redistributed_summary,
        region_2024,
        left_on='new_region',
        right_on='county',
        how='outer',
        suffixes=('_redistributed_2023', '_actual_2024')
    )

    comparison['acres_diff'] = comparison['acres_insured'] - comparison['acres_redistributed']
    comparison['acres_pct_diff'] = (comparison['acres_diff'] / comparison['acres_insured'] * 100).round(2)

    logger.info("\nRedistribution Validation:")
    logger.info(
        comparison[['new_region', 'acres_redistributed', 'acres_insured', 'acres_diff', 'acres_pct_diff']].to_string())

    return comparison


def generate_sql(weights_df, output_file='ct_weights_insert.sql'):
    """Generate SQL INSERT statements for the weights."""
    if weights_df.empty:
        logger.warning("Cannot generate SQL from empty weights DataFrame")
        return

    logger.info(f"\nGenerating SQL INSERT statements to {output_file}")

    with open(output_file, 'w') as f:
        f.write("-- Connecticut County to Planning Region Allocation Weights\n")
        f.write("-- Generated from 2023 old county and 2024 new region acreage data\n\n")
        f.write("CREATE TABLE IF NOT EXISTS ct_county_region_weights (\n")
        f.write("    old_fips_code VARCHAR(5),\n")
        f.write("    old_county_name VARCHAR(100),\n")
        f.write("    old_county_acres_2023 NUMERIC,\n")
        f.write("    new_fips_code VARCHAR(5),\n")
        f.write("    new_region_name VARCHAR(100),\n")
        f.write("    new_region_acres_2024 NUMERIC,\n")
        f.write("    allocation_weight NUMERIC(10, 4),\n")
        f.write("    notes TEXT\n")
        f.write(");\n\n")

        for _, row in weights_df.iterrows():
            f.write(f"INSERT INTO ct_county_region_weights VALUES (\n")
            f.write(f"    '{row['old_fips_code']}',\n")
            f.write(f"    '{row['old_county_name']}',\n")
            f.write(f"    {row['old_county_acres_2023']},\n")
            f.write(f"    '{row['new_fips_code']}',\n")
            f.write(f"    '{row['new_region_name']}',\n")
            f.write(f"    {row['new_region_acres_2024']},\n")
            f.write(f"    {row['allocation_weight']},\n")
            f.write(f"    '{row['notes']}'\n")
            f.write(f");\n")

    logger.info(f"SQL file generated: {output_file}")


def main():
    # File paths
    input_file = '../data/crop-insurance/ci_state_county_year_benefits 2014-2024.csv'
    weights_output = 'ct_allocation_weights.csv'
    sql_output = 'ct_weights_insert.sql'
    historical_output = 'ct_historical_redistributed_2014-2024.csv'

    # Step 1: Read data
    df = read_crop_insurance_data(input_file)

    # Step 2: Extract CT data (2014-2023 old counties, 2024 new regions)
    data_historical, data_2024 = extract_ct_data(df)

    if data_historical is None or data_2024 is None:
        logger.error("Failed to extract Connecticut data")
        return

    # Step 3: Calculate weights using 2023 vs 2024 comparison
    data_2023 = data_historical[data_historical['year'] == 2023]

    if data_2023.empty:
        logger.error("No 2023 data found!")
        return

    weights_df = calculate_weights_from_acreage(data_2023, data_2024)

    if weights_df.empty:
        logger.error("Failed to calculate weights")
        return

    # Step 4: Save weights
    weights_df.to_csv(weights_output, index=False)
    logger.info(f"\nWeights saved to {weights_output}")
    logger.info("\nCalculated Weights:")
    logger.info(weights_df.to_string())

    # Step 5: Validate weights
    validation_results = validate_weights(weights_df, data_2023, data_2024)

    # Step 6: Generate SQL
    generate_sql(weights_df, sql_output)

    # Step 7: Apply weights to ALL historical years (2014-2023)
    logger.info("\n=== Applying Weights to Historical Data (2014-2023) ===")
    redistributed_historical = apply_weights_to_historical_data(data_historical, weights_df)

    if redistributed_historical.empty:
        logger.error("No historical data was redistributed")
        return

    # Step 8: Add 2024 actual data
    data_2024_formatted = data_2024.copy()
    data_2024_formatted['county_fips_code'] = data_2024_formatted['county'].map(NEW_REGION_FIPS)
    data_2024_formatted['source'] = 'actual_2024'

    # Step 9: Combine all years (2014-2024)
    complete_data = pd.concat([redistributed_historical, data_2024_formatted], ignore_index=True)

    # Step 10: Save complete dataset
    complete_data.to_csv(historical_output, index=False)
    logger.info(f"\nComplete 2014-2024 data saved to {historical_output}")
    logger.info(f"Total records: {len(complete_data)}")
    logger.info(f"  - Redistributed historical (2014-2023): {len(redistributed_historical)}")
    logger.info(f"  - Actual 2024: {len(data_2024_formatted)}")

    # Summary by year
    year_summary = complete_data.groupby('year').agg({
        'acres_insured': 'sum',
        'liabilities': 'sum',
        'county_fips_code': 'count'
    }).rename(columns={'county_fips_code': 'record_count'})

    logger.info("\nYear-by-Year Summary:")
    logger.info(year_summary.to_string())


def apply_weights_to_historical_data(historical_data, weights_df):
    """
    Apply calculated weights to redistribute historical county data (2014-2023)
    to new planning regions.

    Args:
        historical_data: DataFrame with old county data for 2014-2023
        weights_df: DataFrame with allocation weights

    Returns:
        DataFrame with historical data redistributed to new planning regions
    """
    logger.info("Applying weights to redistribute historical data to new regions...")

    results = []

    # Process each year from 2014-2023
    for year in range(2014, 2024):
        year_data = historical_data[historical_data['year'] == year]

        if year_data.empty:
            logger.warning(f"No data found for year {year}")
            continue

        logger.info(f"Processing year {year}...")

        # For each weight row (old county -> new region mapping)
        for _, weight_row in weights_df.iterrows():
            old_county_name = weight_row['old_county_name']
            new_region_name = weight_row['new_region_name']
            new_fips_code = weight_row['new_fips_code']
            weight = weight_row['allocation_weight']

            # Get the old county data for this year
            county_data = year_data[year_data['county'] == old_county_name]

            if county_data.empty:
                continue

            # For each record in the old county (may have multiple crops, etc.)
            for _, record in county_data.iterrows():
                redistributed_record = record.copy()

                # Update the county information to the new region
                redistributed_record['county'] = new_region_name
                redistributed_record['county_fips_code'] = new_fips_code

                # Apply the weight to numeric fields
                numeric_fields = [
                    'acres_insured', 'liabilities', 'premium', 'subsidy',
                    'indemnity', 'farmer_premium', 'net_benefit'
                ]

                for field in numeric_fields:
                    if field in redistributed_record and pd.notna(redistributed_record[field]):
                        redistributed_record[field] = redistributed_record[field] * weight

                # Add metadata
                redistributed_record['source'] = f'redistributed_from_{old_county_name}'
                redistributed_record['allocation_weight'] = weight

                results.append(redistributed_record)

    redistributed_df = pd.DataFrame(results)

    # Log summary
    logger.info(f"\nRedistribution complete:")
    logger.info(f"  - Total redistributed records: {len(redistributed_df)}")
    if not redistributed_df.empty:
        logger.info(f"  - Years covered: {sorted(redistributed_df['year'].unique())}")
        logger.info(f"  - New regions: {sorted(redistributed_df['county'].unique())}")

    return redistributed_df


if __name__ == "__main__":
    main()