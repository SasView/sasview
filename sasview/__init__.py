__version__ = "4.0b1"
__build__ = "GIT_COMMIT"
try:
    import logging
    import subprocess
    import os
    FNULL = open(os.devnull, 'w')
    git_revision = subprocess.check_output(['git describe --tags'],
    #git_revision = subprocess.check_output(['pwd'],
                    stderr=FNULL,
                    shell=True)
    __build__ = str(git_revision).strip()
except subprocess.CalledProcessError as cpe:
    logging.warning("Error while determining build number\n  Using command:\n %s \n Output:\n %s"% (cpe.cmd,cpe.output))
