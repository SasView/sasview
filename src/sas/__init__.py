from sas.system import config
from sas.system.version import __version__

__all__ = ["config", "__version__"]

# TODO: fix logger-config circular dependency
# Load the config file
config.load()

