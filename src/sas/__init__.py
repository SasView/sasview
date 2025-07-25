from sas.system.version import __version__
from sas.system import config

__all__ = ["config", "__version__"]

# TODO: fix logger-config circular dependency
# Load the config file
config.load()

