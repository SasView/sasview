# 
# Script to get source from SVN and build PrView
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
# python build_prview [command]
# [command] can be any of the following:
#   -h: lists the command line options
#   -r: Builds a PrView using the released modules.
#   -t: Builds PrView from the trunk.
#   -i: Builds an installer from the release version.
#   -n: Print out the dependencies for the release notes


#TODO: touch site danse/__init__.py
#TODO: touch site danse/common/__init__.py


import os
import sys
import shutil
import logging

# Installation folder
import time
timestamp = int(time.time())
INSTALL_FOLDER = "install_%s" % str(timestamp)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='build_%s.log' % str(timestamp),
                    filemode='w')

CWD    = os.getcwd()

# On Windows, the python executable is not always on the path.
# Use its most frequent location as the default.
if sys.platform == 'win32':
    PYTHON = "c:\python25\python"
    BUILD_OPT = '-cmingw32'
else:
    PYTHON = 'python'
    BUILD_OPT = ''

SVN    = "svn"
INNO   = "\"c:\Program Files\Inno Setup 5\ISCC\""

# Release version 0.2.3
DATALOADER = "0.2.4"
GUICOMM    = "0.1.3"
GUIFRAME   = "0.1.7"
PRVIEW     = "0.3.0"
PLOTTOOLS  = "0.1.6"
UTIL       = "0.1.2"
PR_INV = "0.2.2"

# URLs for SVN repos
DATALOADER_URL = "svn://danse.us/sans/releases/DataLoader-%s" % DATALOADER
GUICOMM_URL = "svn://danse.us/sans/releases/guicomm-%s" % GUICOMM
GUIFRAME_URL = "svn://danse.us/sans/releases/guiframe-%s" % GUIFRAME
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
    if not os.path.isdir(install_dir):
        os.mkdir(install_dir)
    os.chdir(install_dir)   
    os.system("%s checkout -q %s" % (SVN, url))        
    os.chdir(setup_dir)
    os.system("%s setup.py -q build %s" % (PYTHON, BUILD_OPT))
    os.system("%s setup.py -q install" % PYTHON)
    
def checkout(release=False):
    """
        Check the PrView code out
    """
    wd = os.getcwd()
    
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
        install_pkg(".", "pr_inversion-%s" % PR_INV, PR_INV_URL)
    else:
        install_pkg(".", "pr_inversion", "svn://danse.us/sans/trunk/pr_inversion")
    
    os.chdir(wd)
    if release:
        os.system("%s checkout -q %s" % (SVN, PRVIEW_URL))
    else:
        os.system("%s checkout -q svn://danse.us/sans/trunk/prview" % SVN)
    
def prepare(wipeout = False, install_folder=INSTALL_FOLDER):
    """
        Prepare the build
    """
    # Remove existing libraries
    if wipeout == True:
        print "Deleting old modules"
        from distutils.sysconfig import get_python_lib
        libdir = get_python_lib()
        old_dirs = [os.path.join(libdir, 'danse'),
                    os.path.join(libdir, 'data_util'),
                    os.path.join(libdir, 'DataLoader'),
                    os.path.join(libdir, 'sans'),
                    os.path.join(libdir, 'sans_extension'),
                    ]
        for d in old_dirs:
            if os.path.isdir(d):
                shutil.rmtree(d)
        
    # Create a fresh installation folder
    if os.path.isdir(install_folder):
        shutil.rmtree(install_folder)

    os.mkdir(install_folder)
    
    # Check that the dependencies are properly installed
    check_system()    
    
    # Move to the installation folder
    os.chdir(install_folder)    

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
    print "   - DataLoader"
    print "   - sans"
    print "   - sans_extension\n"
    answer = raw_input("Do you want to delete those modules [Y] or continue with a dirty installation [N]? [Y|N]")
    return answer.upper()=="Y"
        
if __name__ == "__main__": 
    print "Build script for PrView %s" % PRVIEW
    
    #TODO: add --prefix option
    
    if len(sys.argv)==1:
        # By default, build release version in site-packages without cleanup
        logging.info("Building release version")
        prepare(install_folder="prview")
        checkout(True)
        # Create run script
        f = open("run_prview.py", 'w')
        buff  = "import os, sys, site\n"
        buff += "if __name__ == \"__main__\":\n"
        buff += "    sys.path.append(os.path.join(os.getcwd(),\"prview-%s\"))\n" % PRVIEW
        buff += "    site.addsitedir(os.path.join(os.getcwd(),\"prview-%s\"))\n" % PRVIEW
        buff += "    os.chdir(\"prview-%s\")\n" % PRVIEW
        buff += "    import sansview\n"
        buff += "    sansview.SansView()\n"
        f.write(buff)
        f.close()
        
    elif len(sys.argv)>1:
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
            print GUICOMM_URL 
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
                    logging.info("Building installer from release version")
                    os.chdir("prview-%s" % (PRVIEW))
                    os.system("%s setup_exe.py -q py2exe" % PYTHON)
                    os.system("%s/Q installer.iss" % INNO)
                    shutil.copy2(os.path.join("Output","setupPrView.exe"), 
                                 os.path.join(CWD, "setupPrView_%s.exe" % str(timestamp)))
                    
    
