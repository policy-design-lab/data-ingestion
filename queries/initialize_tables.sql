-- Populate states table

INSERT INTO ${SCHEMA}.states
VALUES ('AK', 'Alaska'),
       ('AL', 'Alabama'),
       ('AZ', 'Arizona'),
       ('AR', 'Arkansas'),
       ('CA', 'California'),
       ('CO', 'Colorado'),
       ('CT', 'Connecticut'),
       ('DE', 'Delaware'),
       ('DC', 'District of Columbia'),
       ('FL', 'Florida'),
       ('GA', 'Georgia'),
       ('HI', 'Hawaii'),
       ('ID', 'Idaho'),
       ('IL', 'Illinois'),
       ('IN', 'Indiana'),
       ('IA', 'Iowa'),
       ('KS', 'Kansas'),
       ('KY', 'Kentucky'),
       ('LA', 'Louisiana'),
       ('ME', 'Maine'),
       ('MD', 'Maryland'),
       ('MA', 'Massachusetts'),
       ('MI', 'Michigan'),
       ('MN', 'Minnesota'),
       ('MS', 'Mississippi'),
       ('MO', 'Missouri'),
       ('MT', 'Montana'),
       ('NE', 'Nebraska'),
       ('NV', 'Nevada'),
       ('NH', 'New Hampshire'),
       ('NJ', 'New Jersey'),
       ('NM', 'New Mexico'),
       ('NY', 'New York'),
       ('NC', 'North Carolina'),
       ('ND', 'North Dakota'),
       ('OH', 'Ohio'),
       ('OK', 'Oklahoma'),
       ('OR', 'Oregon'),
       ('PA', 'Pennsylvania'),
       ('PR', 'Puerto Rico'),
       ('RI', 'Rhode Island'),
       ('SC', 'South Carolina'),
       ('SD', 'South Dakota'),
       ('TN', 'Tennessee'),
       ('TX', 'Texas'),
       ('UT', 'Utah'),
       ('VT', 'Vermont'),
       ('VA', 'Virginia'),
       ('WA', 'Washington'),
       ('WV', 'West Virginia'),
       ('WI', 'Wisconsin'),
       ('WY', 'Wyoming')
ON CONFLICT DO NOTHING;


-- Titles
INSERT INTO ${SCHEMA}.titles(name, description)
VALUES ('Title I: Commodities',
        'Title I, Commodities cover price and income support for the farmers who raise widely-produced and traded non-perishable crops, like corn, soybeans, wheat, cotton and rice – as well as dairy and sugar. The title also includes agricultural disaster assistance. The map shows the total benefits paid to farmers from of the commodities programs by state from 2018-2022.')
ON CONFLICT DO NOTHING;
INSERT INTO ${SCHEMA}.titles(name, description)
VALUES ('Title II: Conservation',
        'Title II of the law authorizes the Farm Bill’s conservation programs. The programs in this title programs help agricultural producers and landowners adopt conservation activities on private farm and forest lands. In general, conservation activities are intended to protect and improve water quality and quantity, soil health, wildlife habitat, and air quality. The map shows the total benefit of the conservation program by state from 2018-2022.')
ON CONFLICT DO NOTHING;
INSERT INTO ${SCHEMA}.titles(name, description)
VALUES ('Title IV: Nutrition',
        'The Supplemental Nutrition Assistance Program [SNAP] provides financial assistance to low-income families to help cover the cost of food. Benefits can only be used to purchase food products and are provided in electronic format similar to a credit card and known as the Electronic Benefit Transfer (EBT) card. The map shows the total SNAP costs of the nutrition title by state from 2018-2022.')
ON CONFLICT DO NOTHING;
INSERT INTO ${SCHEMA}.titles(name, description)
VALUES ('Title IX: Crop Insurance',
        'Crop Insurance provides farmers with the option to purchase insurance policies on the acres of crops they plant to help manage the risks of farming, including to indemnify against losses in yields, crop or whole farm revenue, crop margins and other risks. The program also offsets the cost of the insurance policies through premium subsidies. In addition, the program provides Administrative and Operating (A&O) subsidies to the private crop insurance companies who provide federal crop insurance to farmers. The map shows the total farmer net benefit of the crop insurance program by state from 2018-2022.')
ON CONFLICT DO NOTHING;

-- Title: 1 - Subtitles
INSERT INTO ${SCHEMA}.subtitles(title_id, name)
SELECT id, 'Total Commodities Programs, Subtitle A'
FROM ${SCHEMA}.titles
WHERE name = 'Title I: Commodities';

INSERT INTO ${SCHEMA}.subtitles(title_id, name)
SELECT id, 'Dairy Margin Coverage, Subtitle D'
FROM ${SCHEMA}.titles
WHERE name = 'Title I: Commodities';

INSERT INTO ${SCHEMA}.subtitles(title_id, name)
SELECT id, 'Supplemental Agricultural Disaster Assistance, Subtitle E'
FROM ${SCHEMA}.titles
WHERE name = 'Title I: Commodities';

-- Title: 1 - Subtitle A - Programs
INSERT INTO ${SCHEMA}.programs(name, title_id, subtitle_id)
SELECT 'Agriculture Risk Coverage (ARC)',
       id,
       (SELECT id FROM ${SCHEMA}.subtitles WHERE name = 'Total Commodities Programs, Subtitle A')
FROM ${SCHEMA}.titles
WHERE name = 'Title I: Commodities';

INSERT INTO ${SCHEMA}.programs(name, title_id, subtitle_id)
SELECT 'Price Loss Coverage (PLC)',
       id,
       (SELECT id FROM ${SCHEMA}.subtitles WHERE name = 'Total Commodities Programs, Subtitle A')
FROM ${SCHEMA}.titles
WHERE name = 'Title I: Commodities';

-- Title: 1 - Subtitle D - Programs
-- N/A

-- Title: 1 - Subtitle E - Programs
INSERT INTO ${SCHEMA}.programs(name, title_id, subtitle_id)
SELECT 'Emergency Assistance for Livestock, Honey Bees, and Farm-Raised Fish Program (ELAP)',
       id,
       (SELECT id FROM ${SCHEMA}.subtitles WHERE name = 'Supplemental Agricultural Disaster Assistance, Subtitle E')
FROM ${SCHEMA}.titles
WHERE name = 'Title I: Commodities';

INSERT INTO ${SCHEMA}.programs(name, title_id, subtitle_id)
SELECT 'Livestock Forage Program (LFP)',
       id,
       (SELECT id FROM ${SCHEMA}.subtitles WHERE name = 'Supplemental Agricultural Disaster Assistance, Subtitle E')
FROM ${SCHEMA}.titles
WHERE name = 'Title I: Commodities';

INSERT INTO ${SCHEMA}.programs(name, title_id, subtitle_id)
SELECT 'Livestock Indemnity Payments (LIP)',
       id,
       (SELECT id FROM ${SCHEMA}.subtitles WHERE name = 'Supplemental Agricultural Disaster Assistance, Subtitle E')
FROM ${SCHEMA}.titles
WHERE name = 'Title I: Commodities';

INSERT INTO ${SCHEMA}.programs(name, title_id, subtitle_id)
SELECT 'Tree Assistance Program (TAP)',
       id,
       (SELECT id FROM ${SCHEMA}.subtitles WHERE name = 'Supplemental Agricultural Disaster Assistance, Subtitle E')
FROM ${SCHEMA}.titles
WHERE name = 'Title I: Commodities';


-- Title: 1 - Subtitle A - ARC Program - Subprograms
INSERT INTO ${SCHEMA}.sub_programs(program_id, name)
SELECT id, 'Agriculture Risk Coverage County Option (ARC-CO)'
FROM ${SCHEMA}.programs
WHERE name = 'Agriculture Risk Coverage (ARC)';

INSERT INTO ${SCHEMA}.sub_programs(program_id, name)
SELECT id, 'Agriculture Risk Coverage Individual Coverage (ARC-IC)'
FROM ${SCHEMA}.programs
WHERE name = 'Agriculture Risk Coverage (ARC)';

-- Title: 2 - Programs
INSERT INTO ${SCHEMA}.programs(title_id, name)
SELECT id, 'Environmental Quality Incentives Program (EQIP)'
FROM ${SCHEMA}.titles
WHERE name = 'Title II: Conservation';

INSERT INTO ${SCHEMA}.programs(title_id, name)
SELECT id, 'Conservation Stewardship Program (CSP)'
FROM ${SCHEMA}.titles
WHERE name = 'Title II: Conservation';

INSERT INTO ${SCHEMA}.programs(title_id, name)
SELECT id, 'Conservation Reserve Program (CRP)'
FROM ${SCHEMA}.titles
WHERE name = 'Title II: Conservation';

INSERT INTO ${SCHEMA}.programs(title_id, name)
SELECT id, 'Agricultural Conservation Easement Program (ACEP)'
FROM ${SCHEMA}.titles
WHERE name = 'Title II: Conservation';

INSERT INTO ${SCHEMA}.programs(title_id, name)
SELECT id, 'Regional Conservation Partnership Program (RCPP)'
FROM ${SCHEMA}.titles
WHERE name = 'Title II: Conservation';

-- EQIP Practice Categories
WITH eqip_program_id AS (SELECT id
                         FROM ${SCHEMA}.programs
                         WHERE name = 'Environmental Quality Incentives Program (EQIP)')
INSERT
INTO ${SCHEMA}.practice_categories(name, display_name, category_grouping, program_id, is_statutory_category)
VALUES ('Land Management', 'Land management', '(6)(A) Practices', (SELECT id from eqip_program_id), TRUE),
       ('Forest Management', 'Forest management', '(6)(A) Practices', (SELECT id from eqip_program_id), TRUE),
       ('Structural', 'Structural', '(6)(A) Practices', (SELECT id from eqip_program_id), TRUE),
       ('Soil Remediation', 'Soil remediation', '(6)(A) Practices', (SELECT id from eqip_program_id), TRUE),
       ('Vegetative', 'Vegetative', '(6)(A) Practices', (SELECT id from eqip_program_id), TRUE),
       ('Other Improvements', 'Other improvements', '(6)(A) Practices', (SELECT id from eqip_program_id), TRUE),
       ('Soil Testing', 'Soil testing', '(6)(A) Practices', (SELECT id from eqip_program_id), TRUE),

       ('Conservation Planning Assessment', 'Conservation planning assessment', '(6)(B) Practices',
        (SELECT id from eqip_program_id), TRUE),
       ('Other Planning', 'Other planning', '(6)(B) Practices', (SELECT id from eqip_program_id), TRUE),
       ('Resource-conserving Crop Rotation', 'Resource-conserving crop rotation', '(6)(B) Practices',
        (SELECT id from eqip_program_id), TRUE),
       ('Soil Health', 'Soil health', '(6)(B) Practices', (SELECT id from eqip_program_id), TRUE),
       ('Comprehensive Nutrient Management', 'Comprehensive Nutrient Mgt.', '(6)(B) Practices',
        (SELECT id from eqip_program_id), TRUE);


-- CSP Practice Categories
WITH csp_program_id AS (SELECT id
                        FROM ${SCHEMA}.programs
                        WHERE name = 'Conservation Stewardship Program (CSP)')
INSERT
INTO ${SCHEMA}.practice_categories(name, display_name, category_grouping, program_id, is_statutory_category)
VALUES ('Cropland', 'Cropland', '2014 Eligible Land', (SELECT id from csp_program_id), FALSE),
       ('Grassland', 'Grassland', '2014 Eligible Land', (SELECT id from csp_program_id), FALSE),
       ('Rangeland', 'Rangeland', '2014 Eligible Land', (SELECT id from csp_program_id), FALSE),
       ('Pastureland', 'Pastureland', '2014 Eligible Land', (SELECT id from csp_program_id), FALSE),
       ('Non-Industrial Private Forestland', 'Non-Industrial Private Forestland (NIPF)', '2014 Eligible Land',
        (SELECT id from csp_program_id), FALSE),

       ('Land Management', 'Land management', '2018 Practices', (SELECT id from csp_program_id), FALSE),
       ('Forest Management', 'Forest management', '2018 Practices', (SELECT id from csp_program_id), FALSE),
       ('Structural', 'Structural', '2018 Practices', (SELECT id from csp_program_id), FALSE),
       ('Soil Remediation', 'Soil remediation', '2018 Practices', (SELECT id from csp_program_id), FALSE),
       -- Check if Existing Activity Payments need to be added as separate category or included in the miscellaneous category
       ('Existing Activity Payments', 'Existing activity payments', '2018 Practices', (SELECT id from csp_program_id),
        FALSE),
       ('Vegetative', 'Vegetative', '2018 Practices', (SELECT id from csp_program_id), FALSE),
       ('Soil Testing', 'Soil testing', '2018 Practices', (SELECT id from csp_program_id), False),
       ('Other Improvements', 'Other improvements', '2018 Practices', (SELECT id from csp_program_id), FALSE),

       ('Bundles', 'Bundles', 'Other CSP', (SELECT id from csp_program_id), FALSE),
       ('Miscellaneous', 'Miscellaneous', 'Other CSP', (SELECT id from csp_program_id), FALSE),
       ('(6)(B) Planning', '(6)(B) Planning', 'Other CSP', (SELECT id from csp_program_id), FALSE);

-- CRP Sub Programs
WITH crp_program_id AS (SELECT id
                        FROM ${SCHEMA}.programs
                        WHERE name = 'Conservation Reserve Program (CRP)')
INSERT
INTO ${SCHEMA}.sub_programs(program_id, name)
VALUES ((SELECT id from crp_program_id), 'Total CRP'),
       ((SELECT id from crp_program_id), 'General Sign-up'),
       ((SELECT id from crp_program_id), 'Continuous Sign-up'),
       ((SELECT id from crp_program_id), 'Grassland');

-- CRP Sub Sub Programs
WITH crp_sub_program_id AS (SELECT id
                            FROM ${SCHEMA}.sub_programs
                            WHERE name = 'Continuous Sign-up')
INSERT
INTO ${SCHEMA}.sub_sub_programs(sub_program_id, name)
VALUES ((SELECT id from crp_sub_program_id), 'CREP Only'),
       ((SELECT id from crp_sub_program_id), 'Continuous Non-CREP'),
       ((SELECT id from crp_sub_program_id), 'Farmable Wetland');

-- Supplemental Nutrition Assistance Program (SNAP)
INSERT INTO ${SCHEMA}.programs(name, title_id)
SELECT 'Supplemental Nutrition Assistance Program (SNAP)', id
FROM ${SCHEMA}.titles
WHERE name = 'Title IV: Nutrition';

-- Crop Insurance
INSERT INTO ${SCHEMA}.programs(name, title_id)
SELECT 'Crop Insurance', id
FROM ${SCHEMA}.titles
WHERE name = 'Title IX: Crop Insurance';