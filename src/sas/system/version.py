from packaging.version import Version

try:
    from ._version import __version__
except ImportError:
    __version__ = "6.1.2"

__release_date__ = "2025"
__version_parsed__ = Version(__version__)

__all__ = ["__version_parsed__", "__release_date__", "__version__"]
