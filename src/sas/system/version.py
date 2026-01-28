try:
    from ._version import __version__
except ImportError:
    __version__ = "6.1.3"

__release_date__ = "2026"
__build__ = "GIT_COMMIT"

__all__ = ["__build__", "__release_date__", "__version__"]
