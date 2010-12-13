# 
# Script to get source from SVN and build SansView
#
# Read the release notes to make ensure that the required software is installed.
#
# SVN must be installed:
# http://subversion.tigris.org/servlets/ProjectDocumentList?folderID=91
#
#
# On Windows: 
#   - make sure svn.exe in on the path. You might need to log out and log back in again after installing SVN.
#
#   - Inno Setup must be installed
#
#   - py2exe must be installed 
#
#   - mingw must be installed
#
# On Mac:
#   - py2app must be installed
#   - macholib must be installed to use py2app
#   - modulegraph must be installed to use py2app
#
# Usage:
# python build_sansview [command]
# [command] can be any of the following:
#   -h: lists the command line options
#   -r: Builds a SansView using the released modules.
#   -t: Builds SansView from the trubuild_sank.
#   -i: Builds a Windows installer from the release version.
#   -n: Print out the dependencies for the release notes

import os
import sys
import shutil
import logging

# Installation folder
import time
timestamp = int(time.time())
CWD    = os.getcwd()
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

# Release version 1.3.1
SANSMODELS = "0.4.7"
DATALOADER = "0.2.7"
GUICOMM    = "0.1.5"
GUIFRAME   = "0.2.0"
SANSVIEW   = "1.3.1"
PLOTTOOLS  = "0.1.9"
UTIL       = "0.1.5"
PARK       = "1.2.1"
PARK_INTEG = "0.1.5"
PRVIEW     = "0.3.3"
PR_INV     = "0.2.5"
CALCULATOR = "0.1.1"
CALC_VIEW  = "0.1.1"
INVARIANT  = "0.1.1"
INV_VIEW   = "0.1.1"
THEORY_VIEW= "0.1.1"
ELEMENTS = "1.2"

# URLs for SVN repos
SANSMODELS_URL = "svn://danse.us/sans/releases/sansmodels-%s" % SANSMODELS
DATALOADER_URL = "svn://danse.us/sans/releases/DataLoader-%s" % DATALOADER
GUICOMM_URL = "svn://danse.us/sans/releases/guicomm-%s" % GUICOMM
GUIFRAME_URL = "svn://danse.us/sans/releases/guiframe-%s" % GUIFRAME
PLOTTOOLS_URL = "svn://danse.us/common/releases/plottools-%s/trunk" % PLOTTOOLS
UTIL_URL = "svn://danse.us/common/releases/util-%s" % UTIL
SANSVIEW_URL = "svn://danse.us/sans/releases/sansview-%s" % SANSVIEW
PARK_INTEG_URL = "svn://danse.us/sans/releases/park_integration-%s" % PARK_INTEG
PARK_URL = "svn://danse.us/park/releases/park-%s" % PARK
PRVIEW_URL = "svn://danse.us/sans/releases/prview-%s" % PRVIEW
PR_INV_URL = "svn://danse.us/sans/releases/pr_inversion-%s" % PR_INV
CALC_URL = "svn://danse.us/sans/releases/calculator-%s" % CALCULATOR
CALC_VIEW_URL = "svn://danse.us/sans/releases/calculatorview-%s" % CALC_VIEW
INV_URL = "svn://danse.us/sans/releases/Invariant-%s" % INVARIANT
INV_VIEW_URL = "svn://danse.us/sans/releases/invariantview-%s" % INV_VIEW
THEO_VIEW_URL = "svn://danse.us/sans/releases/theoryview-%s" % THEORY_VIEW
ELEMENTS_URL = "svn://danse.us/common/elements/releases/elements-%s" % ELEMENTS

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
        Check the SansView code out
    """
    wd = os.getcwd()
    
    os.chdir(wd)
    if release:
        install_pkg(".", "DataLoader-%s" % DATALOADER, DATALOADER_URL)
    else:
        install_pkg(".", "DataLoader", "svn://danse.us/sans/trunk/DataLoader")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "sansmodels-%s/src" % SANSMODELS, SANSMODELS_URL)
    else:
        install_pkg(".", "sansmodels/src", "svn://danse.us/sans/trunk/sansmodels")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "guicomm-%s" % GUICOMM, GUICOMM_URL)
    else:
        install_pkg(".", "guicomm", "svn://danse.us/sans/trunk/guicomm")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "guiframe-%s" % GUIFRAME, GUIFRAME_URL)
    else:
        install_pkg(".", "guiframe", "svn://danse.us/sans/trunk/guiframe")
    
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
        install_pkg(".", "park_integration-%s" % PARK_INTEG, PARK_INTEG_URL)
    else:
        install_pkg(".", "park_integration", "svn://danse.us/sans/trunk/park_integration")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "prview-%s" % PRVIEW, PRVIEW_URL)
    else:
        install_pkg(".", "prview", "svn://danse.us/sans/trunk/prview")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "pr_inversion-%s" % PR_INV, PR_INV_URL)
    else:
        install_pkg(".", "pr_inversion", "svn://danse.us/sans/trunk/pr_inversion")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "Invariant-%s" % INVARIANT, INV_URL)
    else:
        install_pkg(".", "Invariant", "svn://danse.us/sans/trunk/Invariant")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "invariantview-%s" % INV_VIEW, INV_VIEW_URL)
    else:
        install_pkg(".", "invariantview", "svn://danse.us/sans/trunk/invariantview")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "calculatorview-%s" % CALC_VIEW, CALC_VIEW_URL)
    else:
        install_pkg(".", "calculatorview", "svn://danse.us/sans/trunk/calculatorview")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "calculator-%s" % CALCULATOR, CALC_URL)
    else:
        install_pkg(".", "calculator", "svn://danse.us/sans/trunk/calculator")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "theoryview-%s" % THEORY_VIEW, THEO_VIEW_URL)
    else:
        install_pkg(".", "theoryview", "svn://danse.us/sans/trunk/theoryview")

    os.chdir(wd)
    if release:
        install_pkg(".", "elements-%s" % ELEMENTS, ELEMENTS_URL)
    else:
        install_pkg("elements", "trunk", "svn://danse.us/common/elements/trunk")

    os.chdir(wd)
    if release:
        install_pkg(".", "park-%s" % PARK, PARK_URL)
    else:
        install_pkg(".", "park-1.2", "svn://danse.us/park/branches/park-1.2")
    
    os.chdir(wd)
    if release:
        os.system("%s checkout -q %s" % (SVN, SANSVIEW_URL))
    else:
        os.system("%s checkout -q svn://danse.us/sans/trunk/sansview" % SVN)
    
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
                    os.path.join(libdir, 'DataLoader'),
                    os.path.join(libdir, 'park'),
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
    print "In order to build a clean version of SansView, this script"
    print "deletes anything found under site-packages for the following"
    print "modules:"
    print "   - danse"
    print "   - data_util"
    print "   - DataLoader"
    print "   - park"
    print "   - sans"
    print "   - sans_extension\n"
    answer = raw_input("Do you want to delete those modules [Y] or continue with a dirty installation [N]? [Y|N]")
    return answer.upper()=="Y"
        
if __name__ == "__main__": 
    print "Build script for SansView %s" % SANSVIEW
    
    if len(sys.argv)==1:
        # If there is no argument, build the installer
        sys.argv.append("-i")
        
    if len(sys.argv)>1:
        # Help
        if sys.argv[1]=="-h":
            print "Usage:"
            print "    python build_sansview [command]\n"
            print "[command] can be any of the following:"
            print "    -h: lists the command line options"
            print "    -r: Builds a SansView using the released modules"
            print "    -t: Builds SansView from the trunk"
            print "    -i: Builds an installer from the release version [Windows only]"        
            print "    -n: Print out the dependencies for the release notes"
        elif sys.argv[1]=="-n":
            # Print out release URLs
            print SANSMODELS_URL 
            print DATALOADER_URL 
            print GUICOMM_URL 
            print GUIFRAME_URL 
            print PLOTTOOLS_URL 
            print UTIL_URL 
            print SANSVIEW_URL
            print PARK_INTEG_URL 
            print PARK_URL 
            print PRVIEW 
            print PR_INV 
        else:
            logging.info("Build script for SansView %s" % SANSVIEW)
                    
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
                    os.chdir("sansview-%s" % (SANSVIEW))
                    os.system("%s setup_exe.py py2exe --extrapath \"%s\python25\lib\site-packages\"" % (PYTHON, LIB_FOLDER))
                    os.system("%s/Q installer.iss" % INNO)
                    shutil.copy2(os.path.join("Output","setupSansView.exe"), 
                                 os.path.join(CWD, "setupSansView_%s.exe" % str(timestamp)))
                elif sys.platform=='darwin':
                    logging.info("Building Mac application from release version")
                    os.chdir("sansview-%s" % (SANSVIEW))
                    os.system("%s setup_mac.py py2app" % PYTHON)                    
                    
    raw_input("Press enter to continue\n")
    
