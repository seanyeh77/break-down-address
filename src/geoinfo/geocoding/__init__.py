import importlib as _importlib

_ATTRS = {
    "get_lonlat": ".google_api",
    "address_get_pos": ".google_api",
    "process_chunk": ".google_api",
}


def __getattr__(name):
    if name in _ATTRS:
        module = _importlib.import_module(_ATTRS[name], __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_ATTRS.keys())
