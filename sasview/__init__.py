__version__ = "4.0.0-alpha"
__build__ = "GIT_COMMIT"
try:
    import subprocess
    git_revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'])
    __build__ = str(git_revision).strip()
except:
    import logging
    import sys
    logging.warning("Error while determining build number\n  %s" % sys.exc_value)
