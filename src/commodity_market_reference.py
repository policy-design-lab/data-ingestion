"""Load USDA FAS PSD reference lookups (countries, commodities, attributes, units).

The PSD "Export Reference Tables" downloads are named *.xls but are actually HTML
tables, so they are parsed with the standard library rather than pandas or xlrd.
"""

import html.parser
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_REFERENCE_DIR = Path(__file__).resolve().parent.parent / "data" / "commodity-market" / "reference"

# PSD Attribute_Id -> (metric_key, include_in_api).
# metric_key values drive the pivot in v_commodity_trade_by_country_year.
API_ATTRIBUTE_MAP = {
    "28": ("production", True),
    "88": ("exports", True),
    "57": ("imports", True),
    "125": ("consumption", True),
    "176": ("ending_stocks", True),
    "4": ("area_harvested", False),
    "20": ("beginning_stocks", False),
    "7": ("crush", False),
    "86": ("total_supply", False),
    "178": ("total_distribution", False),
    "184": ("yield", False),
}

# PSD country codes that differ from the ISO-style codes used in API responses.
# PSD assigns CN to Comoros, so remapping China onto CN also requires moving
# Comoros to its own ISO code, otherwise two countries share one API code.
API_COUNTRY_CODE_MAP = {
    "CH": "CN",  # China
    "CN": "KM",  # Comoros
}

# Commodity codes that need a stable, hand-picked API slug.
API_COMMODITY_SLUGS = {
    "2222000": "soybeans",
}

# Bushels per metric ton, by commodity. Only set where bushels are meaningful.
# A soybean bushel is 60 lb (27.2155422 kg), so 1 MT is 1000 / 27.2155422 bushels.
BUSHELS_PER_MT = {
    "2222000": 36.7437,  # soybeans
}

# PSD Unit_Id -> (unit_family, multiplier_to_base).
# Base units: MT for mass, hectares for area, MT/ha for yield.
# Units whose conversion depends on the commodity (bushels, bales per hectare)
# are deliberately classified as "other" so no incorrect normalization happens.
UNIT_CLASSIFICATION = {
    "1": ("other", 1),                 # (1000 BUSHES) - bushel conversion is commodity specific
    "2": ("mass", 60),                 # (1000 60 KG BAGS)
    "3": ("count", 1000),              # (1000 COLONIES)
    "4": ("area", 1000),               # (1000 HA)
    "5": ("count", 1000),              # (1000 HEAD)
    "6": ("other", 1000),              # (1000 HL)
    "7": ("mass", 1000),               # (1000 MT CWE)
    "8": ("mass", 1000),               # (1000 MT)
    "9": ("count", 1000),              # (1000 PCS)
    "10": ("count", 1000),             # (1000 TREES)
    "11": ("ratio", 1),                # (Dec. Fraction)
    "12": ("area", 1),                 # (HA)
    "13": ("area", 1),                 # (HECTARES)
    "14": ("mass", 0.001),             # (KG)
    "15": ("count", 1000000),          # (MIL HEAD)
    "16": ("count", 1000000),          # (MIL PCS)
    "17": ("count", 1000000),          # (MILLION TREES)
    "18": ("mass", 1),                 # (MT RAW EQ)
    "19": ("mass", 1),                 # (MT RAW EW)
    "20": ("mass", 1),                 # (MT RE)
    "21": ("mass", 1),                 # (MT)
    "22": ("mass", 1),                 # (MT, Net Weight)
    "23": ("ratio", 1),                # (PERCENT)
    "24": ("ratio", 1),                # (RATIO)
    "25": ("other", 1000),             # (1000 CUBIC METERS)
    "26": ("yield", 1),                # (MT/HA)
    "27": ("mass", 217.7243),          # 1000 480 lb. Bales
    "28": ("other", 1),                # (Bales/HA)
    "29": ("yield", 0.001),            # (KG/HA)
    "30": ("area", 0.40468564),        # ACRES
    "31": ("other", 1),                # BUSHELS
    "32": ("mass", 0.045359237),       # HUNDREDWEIGHT (100 lb)
    "33": ("ratio", 1),                # MILLING RATE
    "34": ("other", 1),                # BUSHELS/TON
    "35": ("ratio", 1),                # IMPORT MILLING RATE
    "36": ("other", 1),                # Bushels
    "37": ("mass", 0.90718474),        # SHORT TONS
    "38": ("mass", 453.59237),         # MILLION LBS
    "39": ("mass", 453592.37),         # BILLION LBS
    "40": ("count", 1),                # (HEAD)
    "41": ("count", 1),                # (PEOPLE)
    "42": ("other", 1),                # (MONTHS)
}

UNKNOWN_UNIT = ("other", 1)

_HEADER_CELLS = {"country code", "commodity code", "attribute id", "unit id"}


class _HtmlTableParser(html.parser.HTMLParser):
    """Collects the rows of every table in an HTML document."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self._row = []
        self._cell = ""
        self._in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag in ("td", "th"):
            self._in_cell = True
            self._cell = ""

    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            self._in_cell = False
            self._row.append(self._cell.strip())
        elif tag == "tr":
            if self._row:
                self.rows.append(self._row)
            self._row = []

    def handle_data(self, data):
        if self._in_cell:
            self._cell += data


def parse_reference_file(path: Path) -> List[List[str]]:
    """Returns the data rows of a PSD reference file, without the header row."""
    parser = _HtmlTableParser()
    parser.feed(path.read_text(errors="replace"))
    rows = []
    for row in parser.rows:
        if len(row) < 2 or not row[0]:
            continue
        if row[0].strip().lower() in _HEADER_CELLS:
            continue
        rows.append(row)
    return rows


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug[:50] if slug else "unknown"


def load_reference_tables(cursor, schema_name: str, reference_dir: Optional[Path] = None) -> Dict[str, int]:
    """Loads all four PSD lookups. Returns a count of rows loaded per table."""
    ref_dir = Path(reference_dir) if reference_dir else DEFAULT_REFERENCE_DIR
    counts = {
        "countries": _load_countries(cursor, schema_name, ref_dir / "countries.xls"),
        "measurement_units": _load_units(cursor, schema_name, ref_dir / "units.xls"),
        "market_attributes": _load_attributes(cursor, schema_name, ref_dir / "attributes.xls"),
        "market_commodities": _load_commodities(cursor, schema_name, ref_dir / "commodities.xls"),
    }
    _ensure_synthetic_countries(cursor, schema_name)
    logger.info("PSD reference data loaded: %s", counts)
    return counts


def _ensure_synthetic_countries(cursor, schema_name: str) -> None:
    """Inserts non-PSD country rows needed by bilateral export flows."""
    sql = (
        f"INSERT INTO {schema_name}.countries (code, name, api_code) VALUES (%s, %s, %s) "
        "ON CONFLICT (code) DO UPDATE "
        "SET name = EXCLUDED.name, api_code = EXCLUDED.api_code"
    )
    cursor.execute(sql, ("ROW", "Rest of World", "ROW"))


def _load_countries(cursor, schema_name: str, path: Path) -> int:
    sql = (
        f"INSERT INTO {schema_name}.countries (code, name, api_code) VALUES (%s, %s, %s) "
        "ON CONFLICT (code) DO UPDATE "
        "SET name = EXCLUDED.name, api_code = EXCLUDED.api_code"
    )
    count = 0
    for row in parse_reference_file(path):
        code, name = row[0], row[1]
        cursor.execute(sql, (code, name, API_COUNTRY_CODE_MAP.get(code, code)))
        count += 1
    return count


def _load_units(cursor, schema_name: str, path: Path) -> int:
    sql = (
        f"INSERT INTO {schema_name}.measurement_units (code, name, unit_family, multiplier_to_base) "
        "VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (code) DO UPDATE "
        "SET name = EXCLUDED.name, unit_family = EXCLUDED.unit_family, "
        "multiplier_to_base = EXCLUDED.multiplier_to_base"
    )
    count = 0
    for row in parse_reference_file(path):
        unit_id, unit_name = row[0], row[1]
        family, multiplier = UNIT_CLASSIFICATION.get(unit_id, UNKNOWN_UNIT)
        if unit_id not in UNIT_CLASSIFICATION:
            logger.warning("Unclassified PSD unit %s (%s), stored without normalization", unit_id, unit_name)
        cursor.execute(sql, (unit_id, unit_name, family, multiplier))
        count += 1
    return count


def _load_attributes(cursor, schema_name: str, path: Path) -> int:
    sql = (
        f"INSERT INTO {schema_name}.market_attributes (psd_attribute_id, name, metric_key, include_in_api) "
        "VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (psd_attribute_id) DO UPDATE "
        "SET name = EXCLUDED.name, metric_key = EXCLUDED.metric_key, "
        "include_in_api = EXCLUDED.include_in_api"
    )
    count = 0
    for row in parse_reference_file(path):
        attribute_id, name = row[0], row[1]
        metric_key, include_in_api = API_ATTRIBUTE_MAP.get(
            attribute_id, ("psd_{}".format(attribute_id), False)
        )
        cursor.execute(sql, (attribute_id, name, metric_key, include_in_api))
        count += 1
    return count


def _load_commodities(cursor, schema_name: str, path: Path) -> int:
    sql = (
        f"INSERT INTO {schema_name}.market_commodities (code, name, api_slug, bushels_per_mt) "
        "VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (code) DO UPDATE "
        "SET name = EXCLUDED.name, api_slug = EXCLUDED.api_slug, "
        "bushels_per_mt = EXCLUDED.bushels_per_mt"
    )
    count = 0
    for row in parse_reference_file(path):
        code, name = row[0], row[1]
        api_slug = API_COMMODITY_SLUGS.get(code) or slugify(name)
        cursor.execute(sql, (code, name, api_slug, BUSHELS_PER_MT.get(code)))
        count += 1
    return count
