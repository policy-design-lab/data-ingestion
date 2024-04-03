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



