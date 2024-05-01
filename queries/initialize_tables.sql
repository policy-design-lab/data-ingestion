-- Populate states table

INSERT INTO pdl.states
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
       ('WY', 'Wyoming');


-- Titles
INSERT INTO pdl.titles(name, description)
VALUES ('Title I: Commodities',
        'Title I, Commodities cover price and income support for the farmers who raise widely-produced and traded non-perishable crops, like corn, soybeans, wheat, cotton and rice – as well as dairy and sugar. The title also includes agricultural disaster assistance. The map shows the total benefits paid to farmers from of the commodities programs by state from 2018-2022.');
INSERT INTO pdl.titles(name, description)
VALUES ('Title II: Conservation',
        'Title II of the law authorizes the Farm Bill’s conservation programs. The programs in this title programs help agricultural producers and landowners adopt conservation activities on private farm and forest lands. In general, conservation activities are intended to protect and improve water quality and quantity, soil health, wildlife habitat, and air quality. The map shows the total benefit of the conservation program by state from 2018-2022.');
INSERT INTO pdl.titles(name, description)
VALUES ('Title IV: Nutrition',
        'The Supplemental Nutrition Assistance Program [SNAP] provides financial assistance to low-income families to help cover the cost of food. Benefits can only be used to purchase food products and are provided in electronic format similar to a credit card and known as the Electronic Benefit Transfer (EBT) card. The map shows the total SNAP costs of the nutrition title by state from 2018-2022.');
INSERT INTO pdl.titles(name, description)
VALUES ('Title IX: Crop Insurance',
        'Crop Insurance provides farmers with the option to purchase insurance policies on the acres of crops they plant to help manage the risks of farming, including to indemnify against losses in yields, crop or whole farm revenue, crop margins and other risks. The program also offsets the cost of the insurance policies through premium subsidies. In addition, the program provides Administrative and Operating (A&O) subsidies to the private crop insurance companies who provide federal crop insurance to farmers. The map shows the total farmer net benefitbenefit of the crop insurance program by state from 2018-2022.');

-- Title: 1 - Subtitles
INSERT INTO pdl.subtitles(title_id, name)
SELECT id, 'Total Commodities Programs, Subtitle A'
FROM pdl.titles
WHERE name = 'Title I: Commodities';

INSERT INTO pdl.subtitles(title_id, name)
SELECT id, 'Dairy Margin Coverage, Subtitle D'
FROM pdl.titles
WHERE name = 'Title I: Commodities';

INSERT INTO pdl.subtitles(title_id, name)
SELECT id, 'Supplemental Agricultural Disaster Assistance, Subtitle E'
FROM pdl.titles
WHERE name = 'Title I: Commodities';

-- Title: 1 - Subtitle A - Programs
INSERT INTO pdl.programs(name, title_id, subtitle_id)
SELECT 'Agriculture Risk Coverage (ARC)',
       id,
       (SELECT id FROM pdl.subtitles WHERE name = 'Total Commodities Programs, Subtitle A')
FROM pdl.titles
WHERE name = 'Title I: Commodities';

INSERT INTO pdl.programs(name, title_id, subtitle_id)
SELECT 'Price Loss Coverage (PLC)',
       id,
       (SELECT id FROM pdl.subtitles WHERE name = 'Total Commodities Programs, Subtitle A')
FROM pdl.titles
WHERE name = 'Title I: Commodities';

-- Title: 1 - Subtitle D - Programs
-- N/A

-- Title: 1 - Subtitle E - Programs
INSERT INTO pdl.programs(name, title_id, subtitle_id)
SELECT 'Emergency Assistance for Livestock, Honey Bees, and Farm-Raised Fish Program (ELAP)',
       id,
       (SELECT id FROM pdl.subtitles WHERE name = 'Supplemental Agricultural Disaster Assistance, Subtitle E')
FROM pdl.titles
WHERE name = 'Title I: Commodities';

INSERT INTO pdl.programs(name, title_id, subtitle_id)
SELECT 'Livestock Forage Program (LFP)',
       id,
       (SELECT id FROM pdl.subtitles WHERE name = 'Supplemental Agricultural Disaster Assistance, Subtitle E')
FROM pdl.titles
WHERE name = 'Title I: Commodities';

INSERT INTO pdl.programs(name, title_id, subtitle_id)
SELECT 'Livestock Indemnity Payments (LIP)',
       id,
       (SELECT id FROM pdl.subtitles WHERE name = 'Supplemental Agricultural Disaster Assistance, Subtitle E')
FROM pdl.titles
WHERE name = 'Title I: Commodities';

INSERT INTO pdl.programs(name, title_id, subtitle_id)
SELECT 'Tree Assistance Program (TAP)',
       id,
       (SELECT id FROM pdl.subtitles WHERE name = 'Supplemental Agricultural Disaster Assistance, Subtitle E')
FROM pdl.titles
WHERE name = 'Title I: Commodities';


-- Title: 1 - Subtitle A - ARC Program - Subprograms
INSERT INTO pdl.sub_programs(program_id, name)
SELECT id, 'Agriculture Risk Coverage County Option (ARC-CO)'
FROM pdl.programs
WHERE name = 'Agriculture Risk Coverage (ARC)';

INSERT INTO pdl.sub_programs(program_id, name)
SELECT id, 'Agriculture Risk Coverage Individual Coverage (ARC-IC)'
FROM pdl.programs
WHERE name = 'Agriculture Risk Coverage (ARC)';

-- Supplemental Nutrition Assistance Program (SNAP)
INSERT INTO pdl.programs(name, title_id)
SELECT 'Supplemental Nutrition Assistance Program (SNAP)', id
FROM pdl.titles
WHERE name = 'Title IV: Nutrition';