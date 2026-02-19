# SNAP Congressional District Mapping (118th Congress)

## Overview

This code generates an interactive map of SNAP participation by U.S. Congressional District using official USDA district-level SNAP data and Census 118th Congressional District boundaries.

The script performs the following:

1. Loads USDA SNAP Congressional District Excel data  
2. Cleans and standardizes district identifiers (`fipscd`)  
3. Downloads official 118th Congressional District shapefile from Census  
4. Constructs GEOIDs for merge  
5. Performs a 1-to-1 district merge  
6. Renders an interactive map (can hover over states and districts)

This module was originally developed in Google Colab for district-level validation and exploratory visualization.

---

## Repository Structure

```
data/
  cat-snap-congressional-district-data-export.xlsx

src/
  snap_analysis/
    snap_analysis.py
    README.md
```

---

## Data Sources

### 1. USDA SNAP Congressional District File

File location in repo:

```
data/cat-snap-congressional-district-data-export.xlsx
```

Expected columns:

- `fipscd`
- `congressional_district_name`
- `state`
- `hh_total`
- `hh_snap`
- `hh_snap_pct`
- `hh_total_poverty_pct`
- `medhhinc`
- `hh_snap_children_pct`
- `hh_snap_disabled_pct`
- `hh_snap_60plus_pct`

The `fipscd` field represents:

```
STATEFP (2 digits) + DISTRICT (2 digits)
```

Example:

```
0103 → Alabama District 03
```

---

### 2. Census 118th Congressional District Boundaries

Downloaded dynamically from:

https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_cd118_500k.zip

- 118th Congress
- 500k resolution shapefile
- Reprojected to EPSG:4326 for web mapping compatibility

---

## Environment Setup

Tested with:

```
Python 3.9+
```

Install required packages:

```bash
pip install geopandas folium openpyxl pyproj shapely branca
```

---

## How to Run

### Option 1: Google Colab (Original Workflow)

1. Run the script.
2. Upload the USDA SNAP Excel file when prompted.
3. The script will:
   - Clean `fipscd`
   - Construct GEOID
   - Merge SNAP data with Census district geometry
   - Render an interactive map inline

---

### Option 2: Run Locally 

Modify the file loading section in `snap_analysis.py`:

Replace:

```python
from google.colab import files
uploaded = files.upload()
snap_file = list(uploaded.keys())[0]
snap_df = pd.read_excel(snap_file)
```

With:

```python
snap_df = pd.read_excel("data/cat-snap-congressional-district-data-export.xlsx")
```

Then run:

```bash
python src/snap_analysis/snap_analysis.py
```

---

## Processing Logic

### GEOID Construction

USDA `fipscd` is converted to a zero-padded 4-digit string:

```
STATEFP = first 2 digits
CD118FP = last 2 digits
GEOID = STATEFP + CD118FP
```

Census GEOID is constructed as:

```
GEOID = STATEFP + CD118FP
```

Merge is performed on:

```
GEOID
```

This produces a 1-to-1 join between SNAP data and district geometries.

---

## Output

An interactive map showing:

- SNAP participation percentage by district (color scale)
- Hover tooltip displaying:
  - District name
  - Total households
  - SNAP households
  - SNAP %
  - Poverty %
  - Median household income
  - SNAP household demographic breakdowns






