"""
Frontend utilities module
Contains styling, data fetching, and UI component helpers
"""

from importlib import import_module

__all__ = [
    "apply_custom_styling",
    "create_metric_card",
    "create_custom_card",
    "add_footer",
    "fetch_portfolio_list",
    "fetch_portfolio_tickers",
]

_EXPORT_MODULES = {
    "apply_custom_styling": ".styling",
    "create_metric_card": ".styling",
    "create_custom_card": ".styling",
    "add_footer": ".styling",
    "fetch_portfolio_list": ".yahoo",
    "fetch_portfolio_tickers": ".yahoo",
}


def __getattr__(name: str):
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value
