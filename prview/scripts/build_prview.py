# 
# Script to get source from SVN and build PrView
#
# Read the release notes to make ensure that the required software is installed.
#
# SVN must be installed:
# http://subversion.tigris.org/servlets/ProjectDocumentList?folderID=91
#
#
# On Windows:
#   - Make sure svn.exe in on the path. You might need to log out and log back in again after installing SVN.
#   - Inno Setup must be installed
#   - py2exe must be installed 
#   - mingw must be installed
#
# In Mac:
#   - py2app must be installed
#   - macholib must be installed to use py2app
#   - modulegraph must be installed to use py2app
#
# Usage:
# python build_prview [command]
# [command] can be any of the following:
#   -h: lists the command line options
#   -r: Builds a PrView using the released modules.
#   -t: Builds PrView from the trunk.
#   -i: Builds an installer from the release version.
#   -n: Print out the dependencies for the release notes

import os
import sys
import shutil
import logging

# Installation folder
import time
timestamp = int(time.time())
CWD = os.getcwd()
INSTALL_FOLDER = "install_%s" % str(timestamp)

# On Windows, the python executable is not always on the path.
# Use its most frequent location as the default.
if sys.platform == 'win32':
    PYTHON = "c:\python25\python"
    LIB_FOLDER = "%s/%s" % (CWD, INSTALL_FOLDER)
else:
    PYTHON = 'python'

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='build_%s.log' % str(timestamp),
                    filemode='w')

SVN    = "svn"
INNO   = "\"c:\Program Files\Inno Setup 5\ISCC\""

# Release version 0.3.3
DATALOADER = "0.2.7"
GUICOMM    = "0.1.5"
GUIFRAME   = "0.2.0"
PRVIEW     = "0.3.3"
PLOTTOOLS  = "0.1.9"
UTIL       = "0.1.5"
PR_INV = "0.2.5"

# URLs for SVN repos
DATALOADER_URL = "svn://danse.us/sans/releases/sansdataloader-%s" % DATALOADER
GUIFRAME_URL = "svn://danse.us/sans/releases/sansguiframe-%s" % GUIFRAME
PLOTTOOLS_URL = "svn://danse.us/common/releases/plottools-%s/trunk" % PLOTTOOLS
UTIL_URL = "svn://danse.us/common/releases/util-%s" % UTIL
PRVIEW_URL = "svn://danse.us/sans/releases/prview-%s" % PRVIEW
PR_INV_URL = "svn://danse.us/sans/releases/pr_inversion-%s" % PR_INV


def check_system():
    """
        Checks that the system has the necessary modules.
    """
    try:
        import wx
    except:
        logging.error("wxpython missing")
    
    try:
        import matplotlib
    except:
        logging.error("matplotlib missing")
        
    try:
        import numpy
    except:
        logging.error("numpy missing")
        
    try:
        import scipy
    except:
        logging.error("scipy missing")
        
    if os.system("gcc -dumpversion")==1:
        logging.error("missing mingw")

def install_pkg(install_dir, setup_dir, url):
    """
        Check a package out and install it
        
        @param install_dir: directory to put the code in
        @param setup_dir: relative location of the setup.py script
        @param url: URL of the SVN repo
    """
    logging.info("Installing %s" % url)
    try:
        if not os.path.isdir(install_dir):
            os.mkdir(install_dir)
        os.chdir(install_dir)   
        os.system("%s checkout -q %s" % (SVN, url))        
        os.chdir(setup_dir)
        if sys.platform == 'win32':
            os.system("%s setup.py -q build -cmingw32" % PYTHON)
            os.system("%s setup.py -q install --root \"%s\"" % (PYTHON, LIB_FOLDER))
        else:
            os.system("%s setup.py build" % PYTHON)
            os.system("%s setup.py install --prefix ~/.local" % PYTHON)
    except:
        logging.error("Install failed for %s" % url)
        logging.error(sys.exc_value)
        raw_input("Press enter to continue\n")
        sys.exit()
    
def checkout(release=False):
    """
        Check the PrView code out
    """
    wd = os.getcwd()
    
    os.chdir(wd)
    if release:
        install_pkg(".", "DataLoader-%s" % DATALOADER, DATALOADER_URL)
    else:
        install_pkg(".", "DataLoader", "svn://danse.us/sans/trunk/sansdataloader")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "guiframe-%s" % GUIFRAME, GUIFRAME_URL)
    else:
        install_pkg(".", "guiframe", "svn://danse.us/sans/trunk/sansguiframe")
    
    os.chdir(wd)
    if release:
        install_pkg("plottools-%s" % PLOTTOOLS, "trunk", PLOTTOOLS_URL)
    else:
        install_pkg("plottools", "trunk", "svn://danse.us/common/plottools/trunk")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "util-%s" % UTIL, UTIL_URL)
    else:
        install_pkg(".", "util", "svn://danse.us/common/util")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "pr_inversion-%s" % PR_INV, PR_INV_URL)
    else:
        install_pkg(".", "pr_inversion", "svn://danse.us/sans/trunk/pr_inversion")
    
    os.chdir(wd)
    if release:
        os.system("%s checkout -q %s" % (SVN, PRVIEW_URL))
    else:
        os.system("%s checkout -q svn://danse.us/sans/trunk/prview" % SVN)
    
def prepare(wipeout = False):
    """
        Prepare the build
        
        @param wipeout: If True, the DANSE modules in the standard site-packages will be
        removed to avoid conflicts.
    """
    # Remove existing libraries
    if wipeout == True:
        logging.info("Deleting DANSES modules in site-packages")
        from distutils.sysconfig import get_python_lib
        libdir = get_python_lib()
        old_dirs = [os.path.join(libdir, 'danse'),
                    os.path.join(libdir, 'data_util'),
                    os.path.join(libdir, 'sansdataloader'),
                    os.path.join(libdir, 'sans'),
                    os.path.join(libdir, 'sans_extension'),
                    ]
        for d in old_dirs:
            if os.path.isdir(d):
                shutil.rmtree(d)
        
    # Create a fresh installation folder
    if os.path.isdir(INSTALL_FOLDER):
        shutil.rmtree(INSTALL_FOLDER)

    os.mkdir(INSTALL_FOLDER)
    
    # Check that the dependencies are properly installed
    check_system()    
    
    # Move to the installation folder
    os.chdir(INSTALL_FOLDER)   

def warning():
    """
        The build script will wipe out part of the site-packages.
        Ask the user whether he wants to proceed.
    """
    print "WARNING!\n"
    print "In order to build a clean version of PrView, this script"
    print "deletes anything found under site-packages for the following"
    print "modules:"
    print "   - danse"
    print "   - data_util"
    print "   - sansdataloader"
    print "   - sans"
    print "   - sans_extension\n"
    answer = raw_input("Do you want to delete those modules [Y] or continue with a dirty installation [N]? [Y|N]")
    return answer.upper()=="Y"
        
if __name__ == "__main__": 
    print "Build script for PrView %s" % PRVIEW
    
    if len(sys.argv)==1:
        # If there is no argument, build the installer
        sys.argv.append("-i")
    
    if len(sys.argv)>1:
        # Help
        if sys.argv[1]=="-h":
            print "Usage:"
            print "    python build_prview [command]\n"
            print "[command] can be any of the following:"
            print "    -h: lists the command line options"
            print "    -r: Builds a PrView using the released modules"
            print "    -t: Builds PrView from the trunk"
            print "    -i: Builds an installer from the release version [Windows only]"        
            print "    -n: Print out the dependencies for the release notes"
        elif sys.argv[1]=="-n":
            # Print out release URLs
            print DATALOADER_URL 
            print GUIFRAME_URL 
            print PLOTTOOLS_URL 
            print UTIL_URL 
            print PRVIEW_URL
            print PR_INV_URL 
        else:
            logging.info("Build script for PrView %s" % PRVIEW)
                    
            # Prepare installation folder
            prepare(warning())
            
            # Check the command line argument
            if sys.argv[1]=="-t":
                logging.info("Building trunk version")
                checkout()
            elif sys.argv[1]=="-r":
                logging.info("Building release version")
                checkout(True)
            elif sys.argv[1]=="-i":
                logging.info("Building release version")
                checkout(True)
                if sys.platform=='win32':
                    logging.info("Building Windows installer from release version")
                    os.chdir("prview-%s" % (PRVIEW))
                    os.system("%s setup_exe.py py2exe --extrapath \"%s\python25\lib\site-packages\"" % (PYTHON, LIB_FOLDER))
                    os.system("%s/Q installer.iss" % INNO)
                    shutil.copy2(os.path.join("Output","setupSansView.exe"), 
                                 os.path.join(CWD, "setupSansView_%s.exe" % str(timestamp)))
                elif sys.platform=='darwin':
                    logging.info("Building Mac application from release version")
                    os.chdir("prview-%s" % (PRVIEW))
                    os.system("%s setup_mac.py py2app" % PYTHON)                    
                    
    raw_input("Press enter to continue\n")
