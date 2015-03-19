__version__ = "3.1.0"
__build__ = "1"
try:
    import subprocess
    d = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
    __build__ = str(d).strip()
except:
    import logging
    import sys
    logging.warning("Error while determining build number\n  %s" % sys.exc_value)
