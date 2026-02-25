import importlib as _importlib

_ATTRS = {
    "find_chars_in_str": ".parser",
    "find_pattern": ".parser",
    "convert_address": ".parser",
    "apply_async_wrapper": ".parser",
    "addrss_data_qualify": ".qualify",
    "combine_address": ".qualify",
}


def __getattr__(name):
    if name in _ATTRS:
        module = _importlib.import_module(_ATTRS[name], __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_ATTRS.keys())
