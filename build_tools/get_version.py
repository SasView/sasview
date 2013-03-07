import os
__revision__ = "0"
__version__ = "0.0.0"
    
import subprocess

def get_svn_revision():
    p = subprocess.Popen("svnversion", shell=True, \
       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    try:
        rev = int(stdout.strip())
        return str(rev)
    except:
        return __revision__

# Get the version number from the sansview module
# Check to see if we are dealing with a release
try:
    import sans.sansview
    __version__ = sans.sansview.__version__
    __revision__ = sans.sansview.__build__
except:
    print "Could not load sansview module"

# Get actual revision number if possible
try:
    rev = get_svn_revision()
    if rev is not None:
        __revision__ = rev
except:
    print "Could not extract revision number"


print "SasView v", __version__, __revision__