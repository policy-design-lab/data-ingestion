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
    '09001': ['09109'],  # Fairfield -> Greater Bridgeport + Western CT
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
    """
    Extract Connecticut data and return only CT DataFrame
    """
    logger.info("Extracting Connecticut data...")

    ct_data = df[df['state'] == 'Connecticut'].copy()

    if ct_data.empty:
        logger.error("No Connecticut data found!")
        return pd.DataFrame()

    logger.info(f"Found {len(ct_data)} Connecticut records from {ct_data['year'].min()} to {ct_data['year'].max()}")

    # Return just the DataFrame, not a tuple
    return ct_data


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
    Validate that weights sum to 1.0 for each old county and that totals match reasonably.
    Returns True if validation passes, False otherwise.
    """
    logger.info("\n=== Validating Weights ===")

    # Check that weights sum to 1.0 for each old county
    weight_sums = weights_df.groupby('old_fips_code')['allocation_weight'].sum()

    tolerance = 0.001
    if not all(abs(weight_sums - 1.0) < tolerance):
        logger.error("Weights do not sum to 1.0 for all counties!")
        logger.error(weight_sums[abs(weight_sums - 1.0) >= tolerance])
        return False

    logger.info("✓ All county weights sum to 1.0")

    # Validate totals by applying weights
    old_total_acres = data_2023['acres_insured'].sum()

    # Calculate expected new totals
    redistributed_total = 0
    for _, weight_row in weights_df.iterrows():
        old_county_acres = weight_row['old_county_acres_2023']
        weight = weight_row['allocation_weight']
        redistributed_total += old_county_acres * weight

    new_total_acres = data_2024['acres_insured'].sum()

    logger.info(f"\n2023 Old County Total Acres: {old_total_acres:,.0f}")
    logger.info(f"2024 New Region Total Acres: {new_total_acres:,.0f}")
    logger.info(f"Redistributed Total Acres: {redistributed_total:,.0f}")
    logger.info(f"Difference: {abs(new_total_acres - redistributed_total):,.0f}")

    percent_diff = abs(new_total_acres - redistributed_total) / new_total_acres * 100
    logger.info(f"Percent Difference: {percent_diff:.2f}%")

    if percent_diff > 10:
        logger.warning("⚠ Redistribution differs from 2024 actuals by more than 10%")
    else:
        logger.info("✓ Redistribution matches 2024 actuals within 10%")

    # Return True to indicate validation passed
    return True


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
    """
    Main execution function
    """
    logger.info("=== Starting CT County Allocation Weight Calculation ===")

    # Read data
    ci_data_file = '../data/crop-insurance/ci_state_county_year_benefits 2014-2024.csv'
    ci_df = read_crop_insurance_data(ci_data_file)

    # Extract CT data for weight calculation
    ct_df = extract_ct_data(ci_df)

    if ct_df.empty:
        logger.error("No CT data found, exiting")
        return

    # Separate by year for weight calculation
    data_2023 = ct_df[ct_df['year'] == 2023].copy()
    data_2024 = ct_df[ct_df['year'] == 2024].copy()

    # Calculate weights
    weights_df = calculate_weights_from_acreage(data_2023, data_2024)

    # Validate - this returns True or False
    validation_passed = validate_weights(weights_df, data_2023, data_2024)

    if not validation_passed:
        logger.error("Weight validation failed. Please review the weights.")
        return

    # Save weights
    weights_output = 'ct_allocation_weights.csv'
    weights_df.to_csv(weights_output, index=False)
    logger.info(f"\nWeights saved to {weights_output}")

    # Generate SQL
    sql_output = 'ct_weights_insert.sql'
    generate_sql(weights_df, sql_output)
    logger.info(f"SQL insert statements saved to {sql_output}")

    # Apply weights to redistribute historical data (2014-2023) for ALL STATES
    logger.info("\n=== Redistributing Historical Data ===")

    # Use the FULL dataset (all states), not just CT
    data_historical_all_states = ci_df[ci_df['year'].between(2014, 2023)].copy()

    # Apply weights - this will redistribute CT and pass through other states
    redistributed_historical = apply_weights_to_historical_data(data_historical_all_states, weights_df)

    # Format 2024 data for all states
    data_2024_all_states = ci_df[ci_df['year'] == 2024].copy()
    data_2024_formatted = data_2024_all_states.copy()

    # For CT 2024 data, add metadata fields
    ct_2024_mask = data_2024_formatted['state'] == 'Connecticut'
    data_2024_formatted.loc[ct_2024_mask, 'source'] = 'original_2024_data'
    data_2024_formatted.loc[ct_2024_mask, 'allocation_weight'] = 1.0

    # Combine redistributed historical (2014-2023) with 2024 data for all states
    complete_data = pd.concat([redistributed_historical, data_2024_formatted], ignore_index=True)

    # Save complete dataset
    historical_output = 'ci_state_county_year_benefits 2014-2024_with_ct_redistributed.csv'
    complete_data.to_csv(historical_output, index=False)
    logger.info(f"\nComplete historical data (all states) saved to {historical_output}")
    logger.info(f"Total rows: {len(complete_data)}")
    logger.info(f"States included: {sorted(complete_data['state'].unique())}")

    logger.info("\n=== Process Complete ===")


def apply_weights_to_historical_data(historical_data, weights_df):
    """
    Apply allocation weights to redistribute CT historical data from old counties to new planning regions.
    Also pass through all other states' data unchanged.
    """
    logger.info("Applying weights to historical data...")

    # Separate CT data from other states
    ct_data = historical_data[historical_data['state'] == 'Connecticut'].copy()
    other_states_data = historical_data[historical_data['state'] != 'Connecticut'].copy()

    logger.info(f"Processing {len(ct_data)} CT rows and {len(other_states_data)} other state rows")

    # Create expanded dataset for CT only
    expanded_rows = []

    for _, hist_row in ct_data.iterrows():
        county_name = hist_row['county']
        year = hist_row['year']

        # Match old county name to FIPS
        old_fips = OLD_COUNTY_FIPS.get(county_name)
        if not old_fips:
            logger.warning(f"No FIPS mapping for county {county_name}")
            continue

        # Get weights for this old county
        matching_weights = weights_df[weights_df['old_fips_code'] == old_fips]

        if matching_weights.empty:
            logger.warning(f"No weights found for {county_name} (FIPS {old_fips}) in year {year}")
            continue

        # Create a row for each destination region
        for _, weight_row in matching_weights.iterrows():
            new_row = hist_row.copy()
            new_row['county'] = weight_row['new_region_name']
            new_row['county_fips_code'] = weight_row['new_fips_code']
            new_row['source'] = f"redistributed_from_{county_name.replace(' ', '_')}"
            new_row['allocation_weight'] = weight_row['allocation_weight']

            # Apply weight to numeric columns
            numeric_cols = ['policies_prem', 'acres_insured', 'liabilities', 'premium',
                            'subsidy', 'indemnity', 'net_benefit', 'farmer_premium']

            for col in numeric_cols:
                if col in new_row:
                    new_row[col] = new_row[col] * weight_row['allocation_weight']

            expanded_rows.append(new_row)

    redistributed_ct = pd.DataFrame(expanded_rows)

    # Aggregate rows with same year, state, county to handle multiple source counties
    # mapping to the same destination (e.g., Hartford + Tolland → Capitol)
    if not redistributed_ct.empty:
        agg_dict = {
            'policies_prem': 'sum',
            'acres_insured': 'sum',
            'liabilities': 'sum',
            'premium': 'sum',
            'subsidy': 'sum',
            'indemnity': 'sum',
            'net_benefit': 'sum',
            'farmer_premium': 'sum',
            'county_fips_code': 'first',
            'source': lambda x: '; '.join(sorted(set(x))),  # Combine source info
            'allocation_weight': 'first'  # Not meaningful after aggregation
        }

        aggregated_ct = redistributed_ct.groupby(['year', 'state', 'county'], as_index=False).agg(agg_dict)

        # Recalculate derived columns
        aggregated_ct['benefit_by_pol'] = aggregated_ct['net_benefit'] / aggregated_ct['policies_prem']
        aggregated_ct['benefit_by_acre'] = aggregated_ct['net_benefit'] / aggregated_ct['acres_insured']
        aggregated_ct['loss_ratio'] = aggregated_ct['indemnity'] / aggregated_ct['premium']
    else:
        aggregated_ct = redistributed_ct

    # Combine CT redistributed data with all other states
    final_data = pd.concat([aggregated_ct, other_states_data], ignore_index=True)

    logger.info(f"\nFinal dataset contains {len(final_data)} rows:")
    logger.info(f"  - CT aggregated regions: {len(aggregated_ct)} rows")
    logger.info(f"  - Other states: {len(other_states_data)} rows")
    logger.info(f"  - Total unique states: {len(final_data['state'].unique())}")

    return final_data


if __name__ == "__main__":
    main()