"""
Exceptions specific to loading data.
"""


class NoKnownLoaderException(Exception):
    """
    Exception for files with no associated reader based on the file
    extension of the loaded file. This exception should only be thrown by
    loader.py.
    """
    def __init__(self, e=None):
        self.message = e


class DefaultReaderException(Exception):
    """
    Exception for files with no associated reader. This should be thrown by
    default readers only to tell Loader to try the next reader.
    """
    def __init__(self, e=None):
        self.message = e


class FileContentsException(Exception):
    """
    Exception for files with an associated reader, but with no loadable data.
    This is useful for catching loader or file format issues.
    """
    def __init__(self, e=None):
        self.message = e


class DataReaderException(Exception):
    """
    Exception for files that were able to mostly load, but had minor issues
    along the way.
    Any exceptions of this type should be put into the datainfo.errors
    """
    def __init__(self, e=None):
        self.message = e
