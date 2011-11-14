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

# Release version 2.0
SANSMODELS = "1.0.0"
DATALOADER = "1.0.0"
GUIFRAME   = "1.0.1"
SANSVIEW   = "2.0.1"
PLOTTOOLS  = "1.0.0"
UTIL       = "1.0.0"
PARK       = "1.2.1"
PARK_INTEG = "1.0.1"
PRVIEW     = "1.0.0"
PR_INV     = "1.0.0"
CALCULATOR = "1.0.0"
CALC_VIEW  = "1.0.0"
INVARIANT  = "1.0.0"
INV_VIEW   = "1.0.0"
FIT_VIEW   = "1.0.1"

# URLs for SVN repos
SANSMODELS_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/sansmodels-%s" % SANSMODELS
DATALOADER_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/sansdataloader-%s" % DATALOADER
GUIFRAME_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/sansguiframe-%s" % GUIFRAME
PLOTTOOLS_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/common-releases/plottools-%s" % PLOTTOOLS
UTIL_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/common-releases/util-%s" % UTIL
SANSVIEW_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/sansview-%s" % SANSVIEW
FIT_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/fittingview-%s" % FIT_VIEW
PARK_INTEG_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/park_integration-%s" % PARK_INTEG
PARK_URL = "svn://danse.us/park/releases/park-%s" % PARK
PRVIEW_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/inversionview-%s" % PRVIEW
PR_INV_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/pr_inversion-%s" % PR_INV
CALC_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/sanscalculator-%s" % CALCULATOR
CALC_VIEW_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/calculatorview-%s" % CALC_VIEW
INV_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/sansinvariant-%s" % INVARIANT
INV_VIEW_URL = "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/invariantview-%s" % INV_VIEW

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

    try:
        import periodictable
    except:
        logging.error("periodictable missing")
        
    if os.system("gcc -dumpversion")==1:
        logging.error("missing mingw")

def install_pkg(install_dir, setup_dir, url):
    """
        Check a package out and install it
        
        @param install_dir: directory to put the code in
        @param setup_dir: relative location of the setup.py script
        @param url: URL of the SVN repo
    """
    #print "PYTHON, LIB_FOLDER=====",PYTHON, LIB_FOLDER
    logging.info("Installing %s" % url)
    try:
        if not os.path.isdir(install_dir):
            os.mkdir(install_dir)
        os.chdir(install_dir)
        build_num = os.path.basename(os.getcwd())   
        os.system("%s checkout -q %s" % (SVN, url))        
        os.chdir(setup_dir)
        if setup_dir.count('sansview') > 0:
            conf_file = open('local_config.py', 'rw')
            conf = conf_file.read()
            conf = '__build__ = %s %s \n'% (build_num, time.localtime()) +\
                     conf
            conf_file.write(conf)
            conf_file.close()
            print "install_dir", build_num,'__build__ = %s %s \n'% (build_num, time.localtime())
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
        install_pkg(".", "sansdataloader-%s" % DATALOADER, DATALOADER_URL)
    else:
        install_pkg(".", "sansdataloader", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/sansdataloader")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "sansmodels-%s" % SANSMODELS, SANSMODELS_URL)
    else:
        install_pkg(".", "sansmodels", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/sansmodels")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "sansguiframe-%s" % GUIFRAME, GUIFRAME_URL)
    else:
        install_pkg(".", "sansguiframe", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/sansguiframe")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "plottools-%s" % PLOTTOOLS, PLOTTOOLS_URL)
    else:
        install_pkg(".", "plottools", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/plottools")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "util-%s" % UTIL, UTIL_URL)
    else:
        install_pkg(".", "util", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/sansutil")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "park_integration-%s" % PARK_INTEG, PARK_INTEG_URL)
    else:
        install_pkg(".", "park_integration", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/park_integration")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "inversionview-%s" % PRVIEW, PRVIEW_URL)
    else:
        install_pkg(".", "inversionview", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/inversionview")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "pr_inversion-%s" % PR_INV, PR_INV_URL)
    else:
        install_pkg(".", "pr_inversion", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/pr_inversion")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "sansinvariant-%s" % INVARIANT, INV_URL)
    else:
        install_pkg(".", "sansinvariant", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/sansinvariant")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "invariantview-%s" % INV_VIEW, INV_VIEW_URL)
    else:
        install_pkg(".", "invariantview", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/invariantview")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "calculatorview-%s" % CALC_VIEW, CALC_VIEW_URL)
    else:
        install_pkg(".", "calculatorview", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/calculatorview")
    
    os.chdir(wd)
    if release:
        install_pkg(".", "sanscalculator-%s" % CALCULATOR, CALC_URL)
    else:
        install_pkg(".", "sanscalculator", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/sanscalculator")


    os.chdir(wd)
    if release:
        install_pkg(".", "park-%s" % PARK, PARK_URL)
    else:
        install_pkg(".", "park-1.2", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/park-1.2")
        
    os.chdir(wd)
    if release:
        install_pkg(".", "fittingview-%s" % FIT_VIEW, FIT_URL)
    else:
        install_pkg(".", "fittingview", "https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/fittingview")
            
    os.chdir(wd)
    if release:
        os.system("%s checkout -q %s" % (SVN, SANSVIEW_URL))
    else:
        os.system("%s checkout -q https://sansviewproject.svn.sourceforge.net/svnroot/sansviewproject/trunk/sansview" % SVN)
    # put build number to local_config
    try:
        build_num = os.path.basename(wd).split('_')[1] 
        if sys.argv[1]=="-r":
            sansview_folder = "sansview-%s" % (SANSVIEW) 
        else:
            sansview_folder = "sansview"  
        # try to make the sansview dir writable 
        try:
            if sys.platform == 'darwin':
                os.system("chmod -R g+w %s"% sansview_foler) 
            else:
                os.system("chmod 777 -R %s"% sansview_foler)
        except:
            pass
        os.chdir(sansview_folder)
        if os.getcwd().count('sansview') > 0:
            conf_file = open('local_config.py', 'r')
            conf = ''
            import datetime
            for line in conf_file.readlines():
                if line.count('__build__'):
                    conf += "__build__ = '%s-%s' \n"% (build_num, datetime.date.today())
                else:
                    conf += line
            conf_file.close()
            conf_file = open('local_config.py', 'w')
            conf_file.write(conf)
            conf_file.close()
    except:
        pass
    os.chdir(wd)
    
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
                    os.path.join(libdir, 'park'),
                    os.path.join(libdir, 'sans'),
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
            print GUIFRAME_URL 
            print PLOTTOOLS_URL 
            print UTIL_URL 
            print SANSVIEW_URL
            print PARK_INTEG_URL 
            print PARK_URL 
            print PRVIEW 
            print PR_INV 
            print FIT_URL
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
    
