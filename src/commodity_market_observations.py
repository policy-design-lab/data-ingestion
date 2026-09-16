"""Normalization helpers for USDA FAS PSD observation rows."""

# TODO: Keeping this file as a stub for now.

from typing import Optional, Tuple

# Column names in a PSD "Export All Data" CSV.
CSV_COLUMNS = (
    "Commodity_Code",
    "Country_Code",
    "Market_Year",
    "Calendar_Year",
    "Month",
    "Attribute_ID",
    "Unit_ID",
    "Value",
)

NormalizedValues = Tuple[Optional[float], Optional[float], Optional[float]]


def normalize_value(raw_value: float, unit_family: str, multiplier_to_base: float) -> NormalizedValues:
    """
    Converts a raw PSD value into base units.

    Returns (value_mt, value_hectares, value_per_ha). Only the entry matching the
    unit family is populated; families without a commodity-independent conversion
    (bushels, ratios, counts) return all None and keep the raw value only.
    """
    scaled = float(raw_value) * float(multiplier_to_base)
    if unit_family == "mass":
        return scaled, None, None
    if unit_family == "area":
        return None, scaled, None
    if unit_family == "yield":
        return None, None, scaled
    return None, None, None
