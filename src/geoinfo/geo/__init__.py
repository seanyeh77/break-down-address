import importlib as _importlib

_ATTRS = {
    "town_find_city": ".spatial",
    "coordinate_to_address": ".spatial",
    "get_village_Code_df": ".spatial",
}


def __getattr__(name):
    if name in _ATTRS:
        module = _importlib.import_module(_ATTRS[name], __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_ATTRS.keys())
