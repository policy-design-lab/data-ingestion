## Connecticut County Remapping Scripts

Connecticut reorganized its county structure in 2024, transitioning from 8 traditional counties to 9 planning regions. Three different methodologies have been developed to calculate allocation weights for redistributing historical crop insurance data (2014-2023) to align with the new regional boundaries.

For detailed methodology information, see `src/Connecticut-Remapping/CT_Remapping_Methods_Presentation.pptx`.

### Overview of Methods

| Script | Method | Data Source | Description |
|--------|--------|-------------|-------------|
| `calculate_ct_weights_from_acreage.py` | **Acreage-Based** | Crop Insurance Data (2023-2024) | Uses actual insured acreage from crop insurance records to calculate proportional weights |
| `calculate_ct_weights_from_area.py` | **Geographic Area** | Census TIGER/Line Shapefiles | Uses geographic land area to determine allocation proportions |
| `calculate_ct_weights_from_cropland.py` | **Cropland Data** | USDA Cropland Data Layer (CDL) | Uses actual cropland coverage to calculate weights |

#### Outputs
- `ct_allocation_weights_area.csv` - Area-based allocation weights
- `ct_weights_area_insert.sql` - SQL insert statements
- `ct_historical_redistributed_area_2014-2024.csv` - Historical data redistributed using area-based weights

#### Running the Script
`python calculate_ct_weights_from_acreage.py`
`python calculate_ct_weights_from_area.py`
`python calculate_ct_weights_from_cropland.py`

#### Todos
This needs improvement. https://github.com/policy-design-lab/data-ingestion/issues/89