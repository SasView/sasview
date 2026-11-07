# Available perspectives.
# When adding a new perspective, add it to _load_perspectives() and __all__.
#
# The perspective windows are imported lazily, on first access to
# PERSPECTIVES or to one of the window classes. Importing a submodule
# (e.g. sas.qtgui.Perspectives.Fitting.model) therefore does not load Qt or
# any perspective. The imports stay literal so that PyInstaller still finds them.

__all__ = [
    "PERSPECTIVES",
    "CorfuncWindow",
    "FittingWindow",
    "InvariantWindow",
    "InversionWindow",
    "SizeDistributionWindow",
]


def _load_perspectives() -> dict:
    from .Corfunc.CorfuncPerspective import CorfuncWindow
    from .Fitting.FittingPerspective import FittingWindow
    from .Invariant.InvariantPerspective import InvariantWindow
    from .Inversion.InversionPerspective import InversionWindow
    from .SizeDistribution.SizeDistributionPerspective import SizeDistributionWindow

    perspectives = {
        FittingWindow.name: FittingWindow,
        InvariantWindow.name: InvariantWindow,
        InversionWindow.name: InversionWindow,
        CorfuncWindow.name: CorfuncWindow,
        SizeDistributionWindow.name: SizeDistributionWindow,
    }
    return {
        "PERSPECTIVES": perspectives,
        "CorfuncWindow": CorfuncWindow,
        "FittingWindow": FittingWindow,
        "InvariantWindow": InvariantWindow,
        "InversionWindow": InversionWindow,
        "SizeDistributionWindow": SizeDistributionWindow,
    }


def __getattr__(name: str):
    if name in __all__:
        globals().update(_load_perspectives())
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
