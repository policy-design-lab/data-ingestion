-- Connecticut County to Planning Region Mapping
-- Calculated from crop insurance acreage data
-- Weights optimized to make 2014-2023 remapped data consistent with 2024

INSERT INTO ${SCHEMA}.ct_county_to_region_mapping
(old_fips_code, old_county_name, new_fips_code, new_region_name, allocation_weight, notes) VALUES
('09001', 'Fairfield', '09909', 'Western CT', 1.0000, 'Complete 1:1 mapping'),
('09003', 'Hartford', '09901', 'Capitol', 0.8054, 'Acreage-weighted allocation'),
('09003', 'Hartford', '09906', 'Northwest Hills', 0.1946, 'Acreage-weighted allocation'),
('09005', 'Litchfield', '09906', 'Northwest Hills', 0.9076, 'Acreage-weighted allocation'),
('09005', 'Litchfield', '09909', 'Western CT', 0.0924, 'Acreage-weighted allocation'),
('09007', 'Middlesex', '09903', 'Lower CT River Valley', 1.0000, 'Complete 1:1 mapping'),
('09009', 'New Haven', '09907', 'South Central CT', 0.2556, 'Acreage-weighted allocation'),
('09009', 'New Haven', '09904', 'Naugatuck Valley', 0.6314, 'Acreage-weighted allocation'),
('09009', 'New Haven', '09903', 'Lower CT River Valley', 0.1130, 'Acreage-weighted allocation'),
('09011', 'New London', '09908', 'Southeastern CT', 0.4754, 'Acreage-weighted allocation'),
('09011', 'New London', '09905', 'Northeastern CT', 0.5246, 'Acreage-weighted allocation'),
('09013', 'Tolland', '09905', 'Northeastern CT', 0.3734, 'Acreage-weighted allocation'),
('09013', 'Tolland', '09901', 'Capitol', 0.6266, 'Acreage-weighted allocation'),
('09015', 'Windham', '09905', 'Northeastern CT', 1.0000, 'Complete 1:1 mapping')

ON CONFLICT DO NOTHING;