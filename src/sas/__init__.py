from sas.system.version import __version__

from sas.system import config, user

__all__ = ['config']

# Load the config file
config.load()

