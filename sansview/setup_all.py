# Note: This script should be moved the upper folder to run properly.
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


def check_system():
    """
        Checks that the system has the necessary modules.
    """
    is_ok = True
    msg = ''
    try:
        import wx
        if not wx.__version__.count('2.8.11') and \
             not wx.__version__.count('2.8.12'):
            mesg = "wx: Recommending version 2.8.11 or 2.8.12"
            msg += mesg + "\n"
            print mesg
    except:
        is_ok = False
        mesg = "Error: wxpython 2.8.11 (12) missing"
        msg += mesg + "\n"
        print mesg
        logging.error("wxpython missing")
    
    try:
        import matplotlib
        if not matplotlib.__version__.count('0.99.0') and \
             not matplotlib.__version__.count('0.99.1'):
            mesg = "matplotlib: Recommending version 0.99.0 or 0.99.1"
            msg += mesg + "\n"
            print mesg
    except:
        is_ok = False
        mesg = "Error: matplotlib 0.99.0 (1) missing"
        msg += mesg + "\n"
        print mesg
        logging.error("matplotlib missing")
        
    try:
        import numpy 
        if not numpy.__version__.count('1.4.1'):
            mesg = "numpy: Recommending version 1.4.1"
            msg += mesg + "\n"
            print mesg
    except:
        is_ok = False
        mesg = "Error: numpy 1.4.1 missing"
        msg += mesg + "\n"
        print mesg
        logging.error("numpy missing")
        
    try:
        import scipy 
        if not scipy.__version__.count('0.7.2'):
            mesg = "scipy: Recommending version 0.7.2"
            msg += mesg + "\n"
            print mesg
    except:
        is_ok = False
        mesg = "Error: scipy 0.7.2 missing"
        msg += mesg + "\n"
        print mesg
        logging.error("scipy missing")

    try:
        import periodictable
        if not periodictable.__version__.count('1.3.0'):
            mesg = "periodictable: Recommending version 1.3.0"
            msg += mesg + "\n"
            print mesg
    except:
        print "Trying to install perodic table..."
        try:
            os.system("easy_install periodictable")
            print "installed periodictable"
        except:
            is_ok = False
            mesg = "Error: periodictable missing"
            msg += mesg + "\n"
            print "easy_install periodictable failed"
            logging.error("periodictable missing")
    
     
    try:
        if sys.platform.count("win32")> 0:
            from wx.lib.pdfwin import PDFWindow   
    except:
        is_ok = False
        mesg = "comtypes missing"
        msg += mesg + "\n"
        print mesg
        logging.error("comtypes missing")
        
    try:
        if sys.platform.count("win32")> 0:
            import win32com
    except:
        is_ok = False
        mesg = "pywin32 missing"
        msg += mesg + "\n"
        print mesg
        logging.error("pywin32 missing")
            
    try:
        import pyparsing
    except:
        try:
            os.system("easy_install pyparsing")
            print "installed pyparsing"
        except:
            is_ok = False
            mesg = "pyparsing missing"
            msg += mesg + "\n"
            print mesg
            print "easy_install pyparsing failed"
            logging.error("pyparsing missing")
              
    if os.system("gcc -dumpversion")==1:
        is_ok = False
        mesg = "missing mingw/gcc"
        msg += mesg + "\n"
        print mesg
        logging.error("missing mingw/gcc")
    
    return is_ok, msg


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
        print "Installation %s successful.." % setup_dir  
    except:
        logging.error("Installation failed on %s"% setup_dir)
        logging.error(sys.exc_value)
        raw_input("Press enter to continue\n")
        sys.exit()

def install(release=False):
    """
        Check the SansView code out
    """
    wd = os.getcwd()
    os.chdir(wd)
    for folder in os.listdir(wd):
        if os.path.isdir(os.path.join(wd, folder)):
            if folder.count('sansview') > 0:
                setup_dir = folder
            try:
                install_pkg(folder)
            except:
                pass
        os.chdir(wd)

        
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
    
    is_ok, _msg = check_system()
    if is_ok:    
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

            else:
                logging.info("Build script for SansView")
                print "Warning: This script will delete the previous SansView packages..."
                prepare()
                # Check the command line argument
                if sys.argv[1]=="-t":
                    logging.info("Building from trunk version")
                    install()
                else:
                    logging.info("Building from release version")
                    install(True)
   
    
        print _msg
        raw_input("Press enter to continue\n")
    
    else:
        print _msg
        raw_input("Press enter and install the missing packages before re-run this scripts.\n")