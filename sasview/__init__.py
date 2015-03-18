__version__ = "3.1.0"
__build__ = "1"
try:
    import pkg_resources
    d = pkg_resources.get_distribution("sasview")
    __build__ = str(d.version)
except:
    import logging
    import sys
    logging.warning("Error while determining build number\n  %s" % sys.exc_value)
