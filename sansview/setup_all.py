# 
# Script for linux to setup all SansView internal packages (Not on sansview itself)
#
# Usage:
# python setup_all.py 

import os
import sys
import shutil
import logging

# Installation folder
import time
timestamp = int(time.time())
CWD    = os.getcwd()

# On Windows, the python executable is not always on the path.
# Use its most frequent location as the default.
if sys.platform == 'win32':
    PYTHON = "c:\python25\python"
    
else:
    PYTHON = 'python'


# Release version 1.9
SANSMODELS = "0.9.1"
DATALOADER = "0.9"
GUIFRAME   = "0.9.1"
SANSVIEW   = "1.9.1"
PLOTTOOLS  = "0.9.1"
UTIL       = "0.9.1"
PARK       = "1.2.1"
PARK_INTEG = "0.9.1"
PRVIEW     = "0.9.1"
PR_INV     = "0.9"
CALCULATOR = "0.9.1"
CALC_VIEW  = "0.9"
INVARIANT  = "0.9.1"
INV_VIEW   = "0.9"
FIT_VIEW   = "0.9.1"


def check_system():
    """
        Checks that the system has the necessary modules.
    """
    is_ok = True
    try:
        import wx
        if not wx.__version__.count('2.8.11') and \
             not wx.__version__.count('2.8.12'):
            print "wx: Recommending version 2.8.11 or 2.8.12"
    except:
        is_ok = False
        print "Error: wxpython 2.8.11 (12) missing"
        logging.error("wxpython missing")
    
    try:
        import matplotlib
        if not matplotlib.__version__.count('0.99.0') and \
             not matplotlib.__version__.count('0.99.1'):
            print "matplotlib: Recommending version 0.99.0 or 0.99.1"
    except:
        is_ok = False
        print "Error: matplotlib 0.99.0 (1) missing"
        logging.error("matplotlib missing")
        
    try:
        import numpy 
        if not numpy.__version__.count('1.4.1'):
            print "numpy: Recommending version 1.4.1"
    except:
        is_ok = False
        print "Error: numpy 1.4.1 missing"
        logging.error("numpy missing")
        
    try:
        import scipy 
        if not scipy.__version__.count('0.7.2'):
            print "scipy: Recommending version 0.7.2"
    except:
        is_ok = False
        print "Error: scipy 0.7.2 missing"
        logging.error("scipy missing")

    try:
        import periodictable
        if not periodictable.__version__.count('1.3.0'):
            print "periodictable: Recommending version 1.3.0"
    except:
        print "Trying to install perodic table..."
        try:
            os.system("easy_install periodictable")
            print "installed periodictable"
        except:
            is_ok = False
            print "easy_install periodictable failed"
            logging.error("periodictable missing")
    
     
    try:
        if sys.platform.count("win32")> 0:
            from wx.lib.pdfwin import PDFWindow   
    except:
        is_ok = False
        print "comtypes missing"
        logging.error("comtypes missing")
        
    try:
        if sys.platform.count("win32")> 0:
            import win32com
    except:
        is_ok = False
        print "pywin32 missing"
        logging.error("pywin32 missing")
            
    try:
        import pyparsing
    except:
        try:
            os.system("easy_install pyparsing")
            print "installed pyparsing"
        except:
            is_ok = False
            print "easy_install pyparsing failed"
            logging.error("pyparsing missing")
              
    if os.system("gcc -dumpversion")==1:
        is_ok = False
        logging.error("missing mingw")
    
    return is_ok


def install_pkg(setup_dir):
    """
        Check a package out and install it
        
        @param install_dir: directory to put the code in
        @param setup_dir: relative location of the setup.py script
        @param url: URL of the SVN repo
    """
    #print "PYTHON, LIB_FOLDER=====",PYTHON
    #logging.info("Installing Pakages" )
    try:   
        os.chdir(setup_dir) 
        os.system("%s setup.py install" % PYTHON)    
    except:
        logging.error("Install failed on %s"% setup_dir)
        logging.error(sys.exc_value)
        raw_input("Press enter to continue\n")
        sys.exit()

def install(release=False):
    """
        Check the SansView code out
    """
    wd = os.getcwd()
    os.chdir(wd)
    
    if release:
        install_pkg("sansdataloader-%s" % DATALOADER)
    else:
        install_pkg("sansdataloader")
    
    os.chdir(wd)
    if release:
        install_pkg("sansmodels-%s" % SANSMODELS)
    else:
        install_pkg("sansmodels")
    
    os.chdir(wd)
    if release:
        install_pkg("sansguiframe-%s" % GUIFRAME)
    else:
        install_pkg("sansguiframe")
    
    os.chdir(wd)
    if release:
        install_pkg("plottools-%s" % PLOTTOOLS)
    else:
        install_pkg("plottools")
    
    os.chdir(wd)
    if release:
        install_pkg("util-%s" % UTIL)
    else:
        install_pkg("util")
    
    os.chdir(wd)
    if release:
        install_pkg("park_integration-%s" % PARK_INTEG)
    else:
        install_pkg("park_integration")
    
    os.chdir(wd)
    if release:
        install_pkg("inversionview-%s" % PRVIEW)
    else:
        install_pkg("inversionview")
    
    os.chdir(wd)
    if release:
        install_pkg("pr_inversion-%s" % PR_INV)
    else:
        install_pkg("pr_inversion")
    
    os.chdir(wd)
    if release:
        install_pkg("sansinvariant-%s" % INVARIANT)
    else:
        install_pkg("sansinvariant")
    
    os.chdir(wd)
    if release:
        install_pkg("invariantview-%s" % INV_VIEW)
    else:
        install_pkg("invariantview")
    
    os.chdir(wd)
    if release:
        install_pkg("calculatorview-%s" % CALC_VIEW)
    else:
        install_pkg("calculatorview")
    
    os.chdir(wd)
    if release:
        install_pkg("sanscalculator-%s" % CALCULATOR)
    else:
        install_pkg("sanscalculator")


    os.chdir(wd)
    if release:
        install_pkg("park-%s" % PARK)
    else:
        install_pkg("park-1.2")
        
    os.chdir(wd)
    if release:
        install_pkg("fittingview-%s" % FIT_VIEW)
    else:
        install_pkg("fittingview")
            
    os.chdir(wd)
    if release:
        setup_dir = "sansview-%s" % SANSVIEW
    else:
        setup_dir = "sansview" 
        
    # run sansview
    try:
        os.chdir(setup_dir) 
        os.system("%s sansview.py" % PYTHON) 
    except:
        pass
           
    # try to make the sansview dir writable to everyone
    os.chdir(wd) 
    try:
        os.system("chmod 777 -R %s"% setup_dir)
    except:
        print "Could not give a permission to everyone for %s." % setup_dir

            
def prepare(wipeout = True):
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
                  
        
if __name__ == "__main__": 
    
    if check_system():    
        if len(sys.argv)==1:
            # If there is no argument, build the installer
            sys.argv.append("-t")
            
        if len(sys.argv)>1:
            # Help
            if sys.argv[1]=="-h":
                print "Usage:"
                print "    python build_sansview [command]\n"
                print "[command] can be any of the following:"
                print "    -h: lists the command line options"
                print "    -r: Builds a SansView using the released modules"
                print "    -t: Builds SansView from the trunk"       

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
                print "Warning: This script will delete the previous SansView packages..."
                prepare()
                # Check the command line argument
                if sys.argv[1]=="-t":
                    logging.info("Building from trunk version")
                    install()
                else:
                    logging.info("Building from release version")
                    install(True)
   
    

        raw_input("Press enter to continue\n")
    
    else:
        raw_input("Press enter and install the missing packages before re-run this scripts.\n")