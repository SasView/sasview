"""
Scrip to clone tagged version of bumps to SasView build system

bumps must be at the same level as the Jenkins %WORKSPACE (i.e. Jenkins_job_name)

../Jenkins_job_name/ == ../%WORKSPACE/

../Jenkins_job_name/                  - Working dir for Jenkins jobs

../Jenkins_job_name/build_tools/      - working directory for build files

../bumps/                             - directory for bumps files.
                                      - see ../Jenkins_job_name/docs/sphinx-docs/build-sphinx.py   

"""


import subprocess
import os
import shutil
import errno, stat


BUMPS_BRANCH = "v0.7.5.5"
BUMPS_REPO = 'https://github.com/bumps/bumps'
CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUMPS_TARGET = os.path.join(CURRENT_SCRIPT_DIR,  "..", "..", "bumps")


if os.path.isdir(BUMPS_TARGET):
    os.chdir(BUMPS_TARGET)
    out_tag=subprocess.check_output(["git","tag"])
    os.chdir(CURRENT_SCRIPT_DIR)
    if (out_tag.rstrip() in BUMPS_BRANCH):
        print "bumps version " + BUMPS_BRANCH + " is allready on disk - exit git clone bumps"
        quit()





def _remove_dir(dir_path):
    """Removes the given directory."""
    if os.path.isdir(dir_path):
        print "Removing \"%s\"... " % dir_path
        shutil.rmtree(dir_path,ignore_errors=False,onerror=errorRemoveReadonly)
           


def errorRemoveReadonly(func, path, exc):
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        # change the file to be readable,writable,executable: 0777
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  
        # retry
        func(path)
    else:
        print "Error"



def clean():
    """
    Clean the Bumps target directory.
    """
    print "=== Remove old Bumps Target ==="
    _remove_dir(BUMPS_TARGET)


clean()





p = subprocess.Popen(["git","clone", "--branch="+BUMPS_BRANCH,"--depth=1", BUMPS_REPO, BUMPS_TARGET],
                     stdin=subprocess.PIPE, 
                     stdout=subprocess.PIPE) 

output = p.communicate('S\nL\n')[0]
print output
