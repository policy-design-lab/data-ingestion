-- select state_code as state, sum(total_payment) as total_payments
-- from pdl.statistics
-- where sub_program_id = 100
-- and year >= 2014 and year <= 2021
-- group by state_code
-- order by total_payments desc;

-- find total payments for Title I: Commodities Programs, Subtitle A for each state
-- needed for /pdl/titles/title-i/subtitles/subtitle-a/state-distribution API endpoint
-- select pdl.payments.state_code as state,
--        pdl.subtitles.name      as sub_title_name,
--        sum(payment)            as total_payment_in_dollars,
--        round(sum(payment) /
--              (select sum(payment) from pdl.payments where subtitle_id = 100 and year >= 2014 and year <= 2021) * 100,
--              2)                as total_payment_in_percentage_nationwide
-- from pdl.payments
--          join pdl.subtitles on pdl.payments.subtitle_id = pdl.subtitles.id
-- where subtitle_id = 100
-- group by state_code, pdl.subtitles.name
-- order by total_payment_in_percentage_nationwide desc;


-- select state_code as state, sum(payment) as total_payments
-- from pdl.payments
-- where subtitle_id = 100
-- and year >= 2014 and year <= 2021
-- group by state_code
-- order by total_payments desc;


-- find total payments and percentage of total payment for each state for subtitle_id  = 101
-- select state_code as state, pdl.subtitles.name as sub_title_name, sum(payment) as total_payment_in_dollars, round(sum(payment) / (select sum(payment) from pdl.payments where subtitle_id = 101 and year >= 2014 and year <= 2021) * 100, 2) as total_payment_in_percentage_nationwide from pdl.payments
-- join pdl.subtitles on pdl.payments.subtitle_id = pdl.subtitles.id
-- where subtitle_id = 101
-- group by state_code, pdl.subtitles.name
-- order by total_payment_in_percentage_nationwide desc;


-- select state_code as state, sum(payment) as total_payments
-- from pdl.payments
-- where subtitle_id = 101
-- and year >= 2014 and year <= 2021
-- group by state_code
-- order by total_payments desc;

-- find total payments for subtitle_id = 101
-- select pdl.payments.state_code as state, pdl.subtitles.name as sub_title_name, sum(payment) as total_payment_in_dollars,
--        round(sum(payment) /
--              (select sum(payment) from pdl.payments where subtitle_id = 101 and year >= 2014 and year <= 2021) * 100, 2) as total_payment_in_percentage_nationwide from pdl.payments
-- join pdl.subtitles on pdl.payments.subtitle_id = pdl.subtitles.id
-- where pdl.payments.subtitle_id = 101
-- group by pdl.payments.state_code, pdl.subtitles.name
-- order by total_payment_in_percentage_nationwide desc;

-- find total payments for subtitle_id = 102
-- select pdl.payments.state_code as state, pdl.subtitles.name as sub_title_name, sum(payment) as total_payment_in_dollars,
--        round(sum(payment) /
--              (select sum(payment) from pdl.payments where subtitle_id = 102 and year >= 2014 and year <= 2021) * 100, 2) as total_payment_in_percentage_nationwide from pdl.payments
-- join pdl.subtitles on pdl.payments.subtitle_id = pdl.subtitles.id
-- where pdl.payments.subtitle_id = 102
-- group by pdl.payments.state_code, pdl.subtitles.name
-- order by total_payment_in_percentage_nationwide desc;


-- find total payments for title_id = 100
-- select state_code as state, sum(payment) as total_payments
-- from pdl.payments
-- where title_id = 100
--   and year >= 2014
--   and year <= 2021
-- group by state_code
-- order by total_payments desc;

-- find total payment and percentage of total payment for each state with title_id = 100 (Title I: Commodities)
--
-- select pdl.payments.state_code as state,
--        pdl.titles.name         as title_name,
--        sum(payment)            as total_payment_in_dollars,
--        round(sum(payment) /
--              (select sum(payment) from pdl.payments where title_id = 100 and year >= 2014 and year <= 2021) * 100,
--              2)                as total_payment_in_percentage_nationwide
-- from pdl.payments
--          join pdl.titles on pdl.payments.title_id = pdl.titles.id
-- where pdl.payments.title_id = 100
--   and year >= 2014
--   and year <= 2021
-- group by pdl.payments.state_code, pdl.titles.name
-- order by total_payment_in_percentage_nationwide desc;


-- find total payments for title_id = 100
select sum(payment) as total_payments
from pdl.payments
where title_id = 100
  and year >= 2014
  and year <= 2018;


-- find total payments for program id = 100 and program name grouped by state from payments table
-- needed for /pdl/titles/title-i/subtitles/subtitle-a/state-distribution API endpoint
-- select state_code as state, pdl.programs.name as program_name, sum(payment) as total_payments
-- from pdl.payments
--          join pdl.programs on pdl.payments.program_id = pdl.programs.id
-- where program_id = 100
--   and year >= 2014
--   and year <= 2021
-- group by state_code, pdl.programs.name
-- order by total_payments desc;


-- Commodity production and trade metrics from USDA FAS PSD data.
-- country_code is the API-facing code, so China is CN even though PSD stores CH.
-- needed for the commodity trade API endpoint
-- select market_year, country_code, country_name, commodity_name,
--        production_mt, production_bushels,
--        exports_mt, exports_bushels,
--        imports_mt, consumption_mt, ending_stocks_mt,
--        import_percentage_worldwide
-- from pdl.v_commodity_trade_by_country_year
-- where commodity_name = 'soybeans'
--   and country_code in ('US', 'CN', 'BR')
--   and market_year = 2024
-- order by country_name;


-- China pork and poultry domestic consumption by market year.
-- needed for the livestock demand API endpoint
-- select market_year, country_code, pork_demand, poultry_demand
-- from pdl.v_livestock_demand_by_year
-- where country_code = 'CN'
-- order by market_year;


-- US county planted acres for soybeans.
-- needed for the planted-acres API endpoint
-- select a.calendar_year,
--        a.county_fips_code as id,
--        'fips' as id_type,
--        'county' as level,
--        c.name as name,
--        a.planted_acres as total_acres
-- from pdl.county_crop_planted_acres a
-- join pdl.counties c on c.fips_code = a.county_fips_code
-- where a.crop_code = 'soybeans'
--   and a.calendar_year = 2012
-- order by a.county_fips_code;


-- Bilateral soybean export destinations for US, Brazil, and Argentina.
-- needed for /pdl/countries/exports
-- select calendar_year, origin_country_code, origin_country_name, commodity_name,
--        china, rest_of_world, top_destinations
-- from pdl.v_commodity_exports_by_origin_year
-- where commodity_name = 'soybeans'
--   and origin_country_code in ('US', 'BR', 'AR')
-- order by calendar_year, origin_country_name;


-- Country socioeconomic indicators (GDP per capita, population).
-- needed for /pdl/countries/{countrycode}/socioeconomic
-- select s.calendar_year, s.gdp_per_capita, s.total_population, s.urban_population
-- from pdl.country_socioeconomic_indicators s
-- join pdl.countries c on c.code = s.country_code
-- where coalesce(c.api_code, c.code) = 'CN'
-- order by s.calendar_year;

