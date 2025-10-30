try:
    from ._version import __version__
except ImportError:
    __version__ = "6.1.1"

__release_date__ = "2025"
__build__ = "GIT_COMMIT"

__all__ = ["__build__", "__release_date__", "__version__"]
