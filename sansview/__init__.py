__version__ = "2.2.0"
__build__ = "1"
try:
    import pkg_resources
    d = pkg_resources.get_distribution("sansview")
    rev = int(d.parsed_version[5])
    __build__ = str(rev)
except:
    try:
        import os
        if os.path.isfile("BUILD_NUMBER"):
            f=open("BUILD_NUMBER",'r')
            buff = f.read().strip()
            if len(buff)<50:
                __build__ = buff
    except:
        import logging
        import sys
        logging.warning("Error while determining build number\n  %s" % sys.exc_value)
