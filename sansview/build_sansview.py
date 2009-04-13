# 
# Script to get source from SVN and build SansView
#
# Read the release notes to make ensure that the required software is installed.
#
# SVN must be installed:
# http://subversion.tigris.org/servlets/ProjectDocumentList?folderID=91
# Make sure svn.exe in on the path. You might need to log out and log back in again after installing SVN.
#
# Inno Setup must be installed
#
# py2exe must be installed 
#
# mingw must be installed
#
# Usage:
# python build_sansview [command]
# [command] can be any of the following:
#   -h: lists the command line options
#   -r: Builds a SansView using the released modules.
#   -t: Builds SansView from the trunk.
#   -i: Builds an installer from the release version.
#   -n: Print out the dependencies for the release notes

import os
import shutil

PYTHON = "python"
SVN    = "svn"
INNO   = "\"c:\Program Files\Inno Setup 5\ISCC\""

# Release version 0.1.0
SANSMODELS = "0.4.2"
DATALOADER = "0.2.1"
GUICOMM    = "0.1.1"
GUIFRAME   = "0.1.4"
SANSVIEW   = "0.1.0"
PLOTTOOLS  = "0.1.3"
UTIL       = "0.1"
PARK       = "1.2.x"
PARK_INTEG = "0.1.0"

SANSMODELS_URL = "svn://danse.us/sans/releases/sansmodels-%s" % SANSMODELS
DATALOADER_URL = "svn://danse.us/sans/releases/DataLoader-%s" % DATALOADER
GUICOMM_URL = "svn://danse.us/sans/releases/guicomm-%s" % GUICOMM
GUIFRAME_URL = "svn://danse.us/sans/releases/guiframe-%s" % GUIFRAME
PLOTTOOLS_URL = "svn://danse.us/common/releases/plottools-%s/trunk" % PLOTTOOLS
UTIL_URL = "svn://danse.us/common/releases/util-%s" % UTIL
SANSVIEW_URL = "svn://danse.us/sans/releases/sansview-%s" % SANSVIEW
PARK_INTEG_URL = "svn://danse.us/sans/releases/park_integration-%s" % PARK_INTEG
#TODO: need to use the release branch of PARK once it is created
PARK_URL = "svn://danse.us/park/branches/park-1.2"

# Installation folder
import time
timestamp = int(time.time())
INSTALL_FOLDER = "install_%s" % str(timestamp)


def check_system():
    """
        Checks that the system has the necessary modules.
    """
    try:
        import wx
    except:
        print "wxpython missing"
    
    try:
        import matplotlib
    except:
        print "matplotlib missing"
        
    try:
        import numpy
    except:
        print "numpy missing"
        
    try:
        import scipy
    except:
        print "scipy missing"
        
    if os.system("gcc -dumpversion")==1:
         print "missing mingw"

def install_pkg(install_dir, setup_dir, url):
    """
        Check a package out and install it
        
        @param install_dir: directory to put the code in
        @param setup_dir: relative location of the setup.py script
        @param url: URL of the SVN repo
    """
    if not os.path.isdir(install_dir):
        os.mkdir(install_dir)
    os.chdir(install_dir)   
    os.system("%s checkout -q %s" % (SVN, url))        
    os.chdir(setup_dir)
    os.system("%s setup.py build -cmingw32" % PYTHON)
    os.system("%s setup.py install" % PYTHON)
    
def checkout(release=False):
    """
        Check the SansView code out
    """
    wd = os.getcwd()
    
    os.chdir(wd)
    if release:
        install_pkg(".", "sansmodels-%s/src" % SANSMODELS, SANSMODELS_URL)
    else:
        install_pkg(".", "sansmodels/src", "svn://danse.us/sans/trunk/sansmodels")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "DataLoader-%s" % DATALOADER, DATALOADER_URL)
    else:
        install_pkg(".", "DataLoader", "svn://danse.us/sans/trunk/DataLoader")
    
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
    
    #TODO: need a release version of PARK
    os.chdir(wd)
    if release:
        install_pkg(".", "park-1.2", PARK_URL)
    else:
        install_pkg(".", "park-1.2", "svn://danse.us/park/branches/park-1.2")
    
    os.chdir(wd)
    if release:
        os.system("%s checkout %s" % (SVN, SANSVIEW_URL))
    else:
        os.system("%s checkout svn://danse.us/sans/trunk/sansview" % SVN)
    
def prepare():
    # Create a fresh installation folder
    
    if os.path.isdir(INSTALL_FOLDER):
        shutil.rmtree(INSTALL_FOLDER)

    os.mkdir(INSTALL_FOLDER)
    
    # Check that the dependencies are properly installed
    check_system()    
    
    # Move to the installation folder
    os.chdir(INSTALL_FOLDER)    

if __name__ == "__main__": 
    import sys
    
    if len(sys.argv)>1:
        if sys.argv[1]=="-h":
            print "Usage:"
            print "    python build_sansview [command]\n"
            print "[command] can be any of the following:"
            print "    -h: lists the command line options"
            print "    -r: Builds a SansView using the released modules"
            print "    -t: Builds SansView from the trunk"
            print "    -i: Builds an installer from the release version"        
            print "    -n: Print out the dependencies for the release notes"
        elif sys.argv[1]=="-n":
            print SANSMODELS_URL 
            print DATALOADER_URL 
            print GUICOMM_URL 
            print GUIFRAME_URL 
            print PLOTTOOLS_URL 
            print UTIL_URL 
            print SANSVIEW_URL
            print PARK_INTEG 
            print PARK_URL 
        else:
            # Prepare installation folder
            prepare()
            
            # Check the command line argument
            if sys.argv[1]=="-t":
                print "Building trunk version"
                checkout()
            elif sys.argv[1]=="-r":
                print "Building release version"
                checkout(True)
            elif sys.argv[1]=="-i":
                print "Building release version"
                checkout(True)
                print "Building installer from release version"
                os.chdir("sansview-%s" % (SANSVIEW))
                os.system("%s setup_exe.py py2exe" % PYTHON)
                os.system("%s installer.iss" % INNO)
    