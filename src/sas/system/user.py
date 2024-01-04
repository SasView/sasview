import os
import socket
import hashlib
from sas.system.config import config


_USER_DIR = os.path.join(os.path.expanduser("~"), '.sasview')

def uid() -> str:
    """ Unique identifier for machine/user combination """
    if config.REPORTING_DEVELOPER_NAME == "":

        hostname = socket.gethostname()
        username = os.getlogin()

        uid = hashlib.md5((hostname+" "+username).encode()).hexdigest()

        return uid

    else:
        return config.REPORTING_DEVELOPER_NAME



def get_user_dir(create_if_nonexistent=True):
    """
    The directory where the per-user configuration is stored.

    Returns ~/.sasview, creating it if it does not already exist.
    """
    global _USER_DIR # TODO: Why is this global?

    if create_if_nonexistent and not os.path.exists(_USER_DIR):
            os.mkdir(_USER_DIR)

    return _USER_DIR

