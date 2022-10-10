import os

_USER_DIR = None

def make_user_dir():
    """
    Create the user directory ~/.sasview if it doesn't already exist.
    """
    path = os.path.join(os.path.expanduser("~"),'.sasview')
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def get_user_dir(create_if_nonexistent=True):
    """
    The directory where the per-user configuration is stored.

    Returns ~/.sasview, creating it if it does not already exist.
    """
    global _USER_DIR
    if create_if_nonexistent and not _USER_DIR:
        _USER_DIR = make_user_dir()
    return _USER_DIR

