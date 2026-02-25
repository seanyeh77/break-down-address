import importlib as _importlib

_ATTRS = {
    "to_half_width": ".text",
    "to_full_width": ".text",
    "remove_prefix": ".text",
    "get_num_from_str": ".text",
}


def __getattr__(name):
    if name in _ATTRS:
        module = _importlib.import_module(_ATTRS[name], __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_ATTRS.keys())
