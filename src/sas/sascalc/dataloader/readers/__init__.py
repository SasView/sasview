# Method to associate extensions to default readers
from .associations import read_associations


# Method to return the location of the XML settings file
def get_data_path():
    """
        Return the location of the settings file for the data readers.
    """
    import os
    return os.path.dirname(__file__)
