-- Drop and recreate a state-level summary view from county records
DROP VIEW IF EXISTS ${SCHEMA}.payments_by_state_from_counties;

CREATE VIEW ${SCHEMA}.payments_by_state_from_counties AS
SELECT
  pbc.title_id,
  NULL::integer AS subtitle_id,
  pbc.program_id,
  NULL::integer AS sub_program_id,
  NULL::integer AS sub_sub_program_id,
  NULL::integer AS practice_category_id,
  c.state_code,
  pbc.year,

  -- Aggregated amounts to mirror payments table shape
  SUM(pbc.payment)                         AS payment,
  NULL::bigint                             AS recipient_count,
  SUM(pbc.base_acres)                      AS base_acres,
  NULL::bigint                             AS farm_count,
  NULL::bigint                             AS contract_count,
  NULL::text                               AS practice_code,
  NULL::text                               AS practice_code_variant,
  SUM(pbc.premium_policy_count)            AS premium_policy_count,
  SUM(pbc.liability_amount)                AS liability_amount,
  SUM(pbc.premium_amount)                  AS premium_amount,
  SUM(pbc.premium_subsidy_amount)          AS premium_subsidy_amount,
  SUM(pbc.indemnity_amount)                AS indemnity_amount,
  SUM(pbc.farmer_premium_amount)           AS farmer_premium_amount,

  -- Weighted loss ratio at state level
  CASE
    WHEN SUM(pbc.premium_amount) > 0
      THEN (SUM(pbc.indemnity_amount)::numeric / NULLIF(SUM(pbc.premium_amount), 0))
    ELSE NULL
  END                                       AS loss_ratio,

  SUM(pbc.net_farmer_benefit_amount)        AS net_farmer_benefit_amount
FROM ${SCHEMA}.payments_by_counties pbc
JOIN ${SCHEMA}.counties c
  ON c.fips_code = pbc.county_fips_code
GROUP BY
  pbc.title_id,
  pbc.program_id,
  pbc.year,
  c.state_code;