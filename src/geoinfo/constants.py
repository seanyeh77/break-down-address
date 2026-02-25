"""
Centralized constants for the geoinfo package.

All magic strings, lookup tables, and configuration values are defined here
so they can be easily maintained and referenced across modules.
"""

# ─── Data / Shapefile Paths ───────────────────────────────────────────────────

VILLAGE_SHP_FILENAME = "VILLAGE_NLSC_1120825.shp"
"""Village shapefile filename used for spatial lookups."""

VILLAGE_DATA_DIR = "data/village"
"""Relative directory (from project root) where village shapefiles are stored."""

# ─── Geocoding ────────────────────────────────────────────────────────────────

GEOCODE_LANGUAGE = "zh-TW"
"""Language parameter for Google Maps geocoding API."""

GEOCODE_BATCH_SIZE = 500
"""Number of rows to process per geocoding batch."""

GEOCODE_OUTPUT_CSV = "Address_output.csv"
"""Default CSV output file for geocoding results."""

# ─── Multiprocessing ─────────────────────────────────────────────────────────

MAX_POOL_SPLITS = 50
"""Maximum number of splits for multiprocessing pool in address parsing."""

# ─── Address Column Names ────────────────────────────────────────────────────

DEFAULT_ADDRESS_COLUMN = "場所地址"
"""Default column name for the address field in input DataFrames."""

DEFAULT_OUTPUT_ADDRESS_COLUMN = "Address2"
"""Default output column name for the combined/standardized address."""

# ─── Direct-Controlled Municipalities (直轄市) ────────────────────────────────

DIRECT_MUNICIPALITIES = frozenset(["臺北市", "新北市", "桃園市", "臺中市", "高雄市"])
"""The six direct-controlled municipalities where 鄉/鎮/市 are renamed to 區.
These are a subset of CITY_TRANSFORM target values."""

# ─── City Name Transform (歷史縣市名稱對照) ──────────────────────────────────

CITY_TRANSFORM = {
    # 縣→市 合併 (對應 COUNTY_CODE_REPLACE 中的代碼轉換)
    "臺北縣": "新北市",  # code: 10001 → 65000
    "桃園縣": "桃園市",  # code: 10003 → 68000
    "台南縣": "台南市",  # code: 10011 → 67000
    "臺中縣": "臺中市",  # code: 10006 → 66000
    "高雄縣": "高雄市",
    # 簡稱 → 全稱
    "新市": "新北市",
    "北縣": "新北市",
    "北市": "臺北市",
    "中縣": "臺中市",
    "中市": "臺中市",
    "桃縣": "桃園市",
    "桃市": "桃園市",
    "高市": "高雄市",
    "嘉縣": "嘉義縣",
    "義市": "嘉義市",
}
"""Mapping of historical/abbreviated city names to current official names.
Related: COUNTY_CODE_REPLACE (same merges expressed as codes)."""

# ─── Town Name Transform (歷史鄉鎮名稱對照) ──────────────────────────────────

TOWN_TRANSFORM = {
    "頭份鎮": "頭份市",
    "員林鎮": "員林市",
}
"""Mapping of old town names to current official names (2015 upgrade to 市)."""

# ─── County Code Replacement (舊縣市代碼對照) ─────────────────────────────────

COUNTY_CODE_REPLACE = {
    "10001": "65000",  # 台北縣 → 新北市
    "10003": "68000",  # 桃園縣 → 桃園市
    "10006": "66000",  # 台中縣 → 台中市
    "10019": "66000",  # 台中市 → 台中市
    "10011": "67000",  # 台南縣 → 台南市
    "10021": "67000",  # 台南市 → 台南市
}
"""Mapping of old county codes to current codes.
Related: CITY_TRANSFORM (same merges expressed as names)."""

# ─── Special Characters (特殊字元) ───────────────────────────────────────────

SPECIAL_CHARS = ["?", "¥", "¶", "«", "�", "󿾴", "*"]
"""Characters that indicate a potentially garbled or invalid address."""

# ─── Character Replace Table (字元替換表) ─────────────────────────────────────

CHAR_REPLACE_MAP = {
    "-": "之",
    "~": "之",
    "号": "號",
    "〸": "十",
    "(": "",
    ")": "",
    ".": "",
    "「": "",
    "」": "",
    "、": "",
    "*": "",
    "/": "",
}
"""Translation table for normalizing address characters."""

# ─── Google API Component Type Mapping ────────────────────────────────────────

GAPI_COMPONENT_MAPPING = {
    "administrative_area_level_1": "縣市3",
    "administrative_area_level_2": "第三級行政區3",
    "administrative_area_level_3": "村里3",
    "route": "路3",
    "neighborhood": "地域3",
    "street_number": "號3",
}
"""Mapping from Google API address component types to output column names."""

# ─── Geocoding Output Columns (Google API 輸出欄位) ──────────────────────────

GEOCODE_OUTPUT_COLUMNS = ["Address3"] + list(GAPI_COMPONENT_MAPPING.values())
"""Columns created by the Google geocoding pipeline.
'Address3' is the formatted_address; the rest are derived from GAPI_COMPONENT_MAPPING."""
