"""
geoinfo - A package for Taiwanese address parsing, standardization, and geocoding.

This package provides tools for:
- Breaking down Taiwanese addresses into components (city, town, village, road, etc.)
- Geo-spatial lookups using shapefiles
- Data qualification and credibility scoring
- Google Maps API geocoding

All public functions are accessible via this package's namespace:
    from geoinfo import break_address_statardize, to_half_width, ...
"""

import importlib as _importlib


def __getattr__(name):
    """Lazy import: only load a sub-module when one of its symbols is accessed."""
    _MODULES = {
        # utils.text
        "to_half_width": "geoinfo.utils.text",
        "to_full_width": "geoinfo.utils.text",
        "remove_prefix": "geoinfo.utils.text",
        "get_num_from_str": "geoinfo.utils.text",
        # geo.spatial
        "town_find_city": "geoinfo.geo.spatial",
        "coordinate_to_address": "geoinfo.geo.spatial",
        "get_village_Code_df": "geoinfo.geo.spatial",
        # address.parser
        "find_chars_in_str": "geoinfo.address.parser",
        "find_pattern": "geoinfo.address.parser",
        "convert_address": "geoinfo.address.parser",
        "apply_async_wrapper": "geoinfo.address.parser",
        # address.qualify
        "addrss_data_qualify": "geoinfo.address.qualify",
        "combine_address": "geoinfo.address.qualify",
        # geocoding.google_api
        "get_lonlat": "geoinfo.geocoding.google_api",
        "address_get_pos": "geoinfo.geocoding.google_api",
        "process_chunk": "geoinfo.geocoding.google_api",
        # pipeline
        "address_standardize": "geoinfo.pipeline",
        "get_df_address_info": "geoinfo.pipeline",
        "break_address_statardize": "geoinfo.pipeline",
        "break_address_qualify": "geoinfo.pipeline",
        "break_address_combine": "geoinfo.pipeline",
        "break_address_get_lonlat": "geoinfo.pipeline",
    }

    if name in _MODULES:
        module = _importlib.import_module(_MODULES[name])
        return getattr(module, name)
    raise AttributeError(f"module 'geoinfo' has no attribute {name!r}")


__all__ = [
    # Text utilities
    "to_half_width",
    "to_full_width",
    "remove_prefix",
    "get_num_from_str",
    # Geo-spatial
    "town_find_city",
    "coordinate_to_address",
    "get_village_Code_df",
    # Address parsing
    "find_chars_in_str",
    "find_pattern",
    "convert_address",
    "apply_async_wrapper",
    # Qualification
    "addrss_data_qualify",
    "combine_address",
    # Geocoding
    "get_lonlat",
    "address_get_pos",
    "process_chunk",
    # Pipeline
    "address_standardize",
    "get_df_address_info",
    "break_address_statardize",
    "break_address_qualify",
    "break_address_combine",
    "break_address_get_lonlat",
]
