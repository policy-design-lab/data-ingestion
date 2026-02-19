
!pip install geopandas folium openpyxl pyproj shapely branca --quiet

import pandas as pd
import geopandas as gpd
import folium
from google.colab import files
from IPython.display import display, HTML


# 1. UPLOAD USDA SNAP FILE

print("Upload the USDA SNAP Congressional District Excel file")
uploaded = files.upload()
snap_file = list(uploaded.keys())[0]

snap_df = pd.read_excel(snap_file)


# 2. LOAD CENSUS 118th CONGRESSIONAL DISTRICTS
cds = gpd.read_file(
    "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_cd118_500k.zip"
).to_crs(epsg=4326)

cds["STATEFP"] = cds["STATEFP"].astype(str).str.zfill(2)
cds["CD118FP"] = cds["CD118FP"].astype(str).str.zfill(2)
cds["GEOID"] = cds["STATEFP"] + cds["CD118FP"]


# 3. BUILD GEOID FROM USDA fipscd

snap_df["fipscd"] = (
    snap_df["fipscd"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.zfill(4)
)

snap_df["STATEFP"] = snap_df["fipscd"].str[:2]
snap_df["CD118FP"] = snap_df["fipscd"].str[2:]
snap_df["GEOID"] = snap_df["STATEFP"] + snap_df["CD118FP"]


# 4. RENAME COLUMNS FOR DISPLAY

snap_df = snap_df.rename(columns={
    "congressional_district_name": "District",
    "state": "State",
    "hh_total": "Total Households",
    "hh_snap": "SNAP Households",
    "hh_snap_pct": "SNAP %",
    "hh_total_poverty_pct": "Household Poverty %",
    "medhhinc": "Median Household Income ($)",
    "hh_snap_children_pct": "SNAP HH w/ Children %",
    "hh_snap_disabled_pct": "SNAP HH w/ Disabled %",
    "hh_snap_60plus_pct": "SNAP HH Age 60+ %"
})


# 5. MERGE (1-TO-1 DISTRICT JOIN)

cds = cds.merge(
    snap_df,
    on="GEOID",
    how="left"
)

print("Total Census districts:", len(cds))
print("Districts with SNAP data:", cds["SNAP %"].notna().sum())


# 6. BUILD MAP

m = folium.Map(
    location=[39.5, -98.35],
    zoom_start=4,
    tiles="cartodbpositron",
    control_scale=True
)

folium.Choropleth(
    geo_data=cds,
    data=cds,
    columns=["GEOID", "SNAP %"],
    key_on="feature.properties.GEOID",
    fill_color="YlOrRd",
    fill_opacity=0.85,
    line_opacity=0.25,
    nan_fill_color="#f0f0f0",
    legend_name="Households Participating in SNAP (%)"
).add_to(m)

folium.GeoJson(
    cds,
    style_function=lambda x: {"fillOpacity": 0},
    highlight_function=lambda x: {
        "weight": 2,
        "color": "black",
        "fillOpacity": 0.9
    },
    tooltip=folium.GeoJsonTooltip(
        fields=[
            "District",
            "State",
            "Total Households",
            "SNAP Households",
            "SNAP %",
            "Household Poverty %",
            "Median Household Income ($)",
            "SNAP HH w/ Children %",
            "SNAP HH w/ Disabled %",
            "SNAP HH Age 60+ %"
        ],
        sticky=True,
        localize=True
    )
).add_to(m)

display(HTML(m._repr_html_()))




