__version__ = "4.0.0-alpha"
__build__ = "GIT_COMMIT"
try:
    import subprocess
    import os
    FNULL = open(os.devnull, 'w')
    git_revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                    stderr=FNULL,
                    shell=True)
    __build__ = str(git_revision).strip()
except:
    import logging
    import sys
    logging.warning("Error while determining build number\n  %s" % sys.exc_value)
