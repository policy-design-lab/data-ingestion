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


-- Wide commodity production and trade metrics by country and market year.
-- PSD publishes a full record each month, so only the newest report per
-- country/commodity/market year is used. The worldwide import share is summed
-- across every ingested country, so all countries must be loaded for it to be correct.
DROP VIEW IF EXISTS ${SCHEMA}.v_commodity_trade_by_country_year;

CREATE VIEW ${SCHEMA}.v_commodity_trade_by_country_year AS
WITH latest_report AS (
    SELECT DISTINCT ON (country_code, commodity_code, market_year)
        country_code,
        commodity_code,
        market_year,
        calendar_year,
        month
    FROM ${SCHEMA}.commodity_market_observations
    ORDER BY
        country_code,
        commodity_code,
        market_year,
        calendar_year DESC,
        month DESC
),
pivoted AS (
    SELECT
        o.market_year,
        COALESCE(c.api_code, c.code)                                  AS country_code,
        c.code                                                        AS psd_country_code,
        c.name                                                        AS country_name,
        cm.code                                                       AS commodity_code,
        cm.api_slug                                                   AS commodity_name,
        cm.bushels_per_mt,
        o.calendar_year,
        o.month                                                       AS report_month,
        MAX(o.value_mt) FILTER (WHERE a.metric_key = 'production')    AS production_mt,
        MAX(o.value_mt) FILTER (WHERE a.metric_key = 'exports')       AS exports_mt,
        MAX(o.value_mt) FILTER (WHERE a.metric_key = 'imports')       AS imports_mt,
        MAX(o.value_mt) FILTER (WHERE a.metric_key = 'consumption')   AS consumption_mt,
        MAX(o.value_mt) FILTER (WHERE a.metric_key = 'ending_stocks') AS ending_stocks_mt
    FROM ${SCHEMA}.commodity_market_observations o
    JOIN latest_report lr
      ON lr.country_code = o.country_code
     AND lr.commodity_code = o.commodity_code
     AND lr.market_year = o.market_year
     AND lr.calendar_year = o.calendar_year
     AND lr.month = o.month
    JOIN ${SCHEMA}.countries c ON c.code = o.country_code
    JOIN ${SCHEMA}.commodities cm ON cm.code = o.commodity_code
    JOIN ${SCHEMA}.market_attributes a ON a.id = o.attribute_id
    WHERE a.include_in_api
      AND o.value_mt IS NOT NULL
    GROUP BY
        o.market_year,
        c.api_code,
        c.code,
        c.name,
        cm.code,
        cm.api_slug,
        cm.bushels_per_mt,
        o.calendar_year,
        o.month
),
world_imports AS (
    SELECT
        commodity_code,
        market_year,
        SUM(imports_mt) AS world_imports_mt
    FROM pivoted
    WHERE imports_mt IS NOT NULL
    GROUP BY commodity_code, market_year
)
SELECT
    p.market_year,
    p.country_code,
    p.psd_country_code,
    p.country_name,
    p.commodity_code,
    p.commodity_name,
    p.calendar_year,
    p.report_month,

    p.production_mt,
    ROUND(p.production_mt * p.bushels_per_mt, 0)     AS production_bushels,
    p.exports_mt,
    ROUND(p.exports_mt * p.bushels_per_mt, 0)        AS exports_bushels,
    p.imports_mt,
    ROUND(p.imports_mt * p.bushels_per_mt, 0)        AS imports_bushels,
    p.consumption_mt,
    ROUND(p.consumption_mt * p.bushels_per_mt, 0)    AS consumption_bushels,
    p.ending_stocks_mt,
    ROUND(p.ending_stocks_mt * p.bushels_per_mt, 0)  AS ending_stocks_bushels,

    ROUND(p.imports_mt / NULLIF(w.world_imports_mt, 0) * 100, 2) AS import_percentage_worldwide
FROM pivoted p
LEFT JOIN world_imports w
  ON w.commodity_code = p.commodity_code
 AND w.market_year = p.market_year;


-- China pork and poultry domestic consumption by market year.
-- Uses the raw PSD value (typically 1000 MT), not value_mt. Poultry is Meat,
-- Chicken (0115000) until ingest confirms broiler (0114200).
DROP VIEW IF EXISTS ${SCHEMA}.v_livestock_demand_by_year;

CREATE VIEW ${SCHEMA}.v_livestock_demand_by_year AS
WITH latest_report AS (
    SELECT DISTINCT ON (country_code, commodity_code, market_year)
        country_code,
        commodity_code,
        market_year,
        calendar_year,
        month
    FROM ${SCHEMA}.commodity_market_observations
    WHERE commodity_code IN ('0113000', '0115000')
    ORDER BY
        country_code,
        commodity_code,
        market_year,
        calendar_year DESC,
        month DESC
)
SELECT
    o.market_year,
    COALESCE(c.api_code, c.code) AS country_code,
    c.name                       AS country_name,
    MAX(o.value) FILTER (WHERE o.commodity_code = '0113000') AS pork_demand,
    MAX(o.value) FILTER (WHERE o.commodity_code = '0115000') AS poultry_demand
FROM ${SCHEMA}.commodity_market_observations o
JOIN latest_report lr
  ON lr.country_code = o.country_code
 AND lr.commodity_code = o.commodity_code
 AND lr.market_year = o.market_year
 AND lr.calendar_year = o.calendar_year
 AND lr.month = o.month
JOIN ${SCHEMA}.countries c ON c.code = o.country_code
JOIN ${SCHEMA}.market_attributes a ON a.id = o.attribute_id
WHERE a.metric_key = 'consumption'
GROUP BY
    o.market_year,
    c.api_code,
    c.code,
    c.name;


-- Origin-to-destination soybean export flows for /pdl/countries/exports.
-- china is the amount to destination API code CN; rest_of_world is destination ROW.
-- top_destinations lists up to three real partners excluding ROW, ordered by amount.
DROP VIEW IF EXISTS ${SCHEMA}.v_commodity_exports_by_origin_year;

CREATE VIEW ${SCHEMA}.v_commodity_exports_by_origin_year AS
WITH ranked_destinations AS (
    SELECT
        f.origin_country_code,
        f.commodity_code,
        f.calendar_year,
        d.name AS destination_name,
        f.amount,
        ROW_NUMBER() OVER (
            PARTITION BY f.origin_country_code, f.commodity_code, f.calendar_year
            ORDER BY f.amount DESC
        ) AS destination_rank
    FROM ${SCHEMA}.commodity_export_flows f
    JOIN ${SCHEMA}.countries d ON d.code = f.destination_country_code
    WHERE COALESCE(d.api_code, d.code) <> 'ROW'
),
top_destinations AS (
    SELECT
        origin_country_code,
        commodity_code,
        calendar_year,
        COALESCE(
            json_agg(
                json_build_object(
                    'country', destination_name,
                    'amount', amount
                )
                ORDER BY destination_rank
            ),
            '[]'::json
        ) AS top_destinations
    FROM ranked_destinations
    WHERE destination_rank <= 3
    GROUP BY origin_country_code, commodity_code, calendar_year
),
totals AS (
    SELECT
        f.calendar_year,
        f.origin_country_code,
        f.commodity_code,
        COALESCE(o.api_code, o.code) AS origin_api_code,
        o.name                       AS origin_country_name,
        cm.api_slug                  AS commodity_name,
        MAX(f.amount) FILTER (
            WHERE COALESCE(d.api_code, d.code) = 'CN'
        ) AS china,
        MAX(f.amount) FILTER (
            WHERE COALESCE(d.api_code, d.code) = 'ROW'
        ) AS rest_of_world
    FROM ${SCHEMA}.commodity_export_flows f
    JOIN ${SCHEMA}.countries o ON o.code = f.origin_country_code
    JOIN ${SCHEMA}.countries d ON d.code = f.destination_country_code
    JOIN ${SCHEMA}.commodities cm ON cm.code = f.commodity_code
    GROUP BY
        f.calendar_year,
        f.origin_country_code,
        f.commodity_code,
        o.api_code,
        o.code,
        o.name,
        cm.api_slug
)
SELECT
    t.calendar_year,
    t.origin_api_code AS origin_country_code,
    t.origin_country_name,
    t.commodity_name,
    t.china,
    t.rest_of_world,
    COALESCE(td.top_destinations, '[]'::json) AS top_destinations
FROM totals t
LEFT JOIN top_destinations td
  ON td.origin_country_code = t.origin_country_code
 AND td.commodity_code = t.commodity_code
 AND td.calendar_year = t.calendar_year;