__version__ = "2.2.0"
__build__ = "1"
try:
    import pkg_resources
    d = pkg_resources.get_distribution("sasview")
    __build__ = str(d.version)
except:
    try:
        import os
        dir = os.path.dirname(__file__)
        filepath = os.path.join(dir, "BUILD_NUMBER")
        if os.path.isfile(filepath):
            f=open(filepath, 'r')
            buff = f.read().strip()
            if len(buff)<50:
                __build__ = buff
    except:
        import logging
        import sys
        logging.warning("Error while determining build number\n  %s" % sys.exc_value)
