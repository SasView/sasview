"""
    Check dependencies
"""
import sys
print sys.version

def check_deps():
    try:
        import matplotlib
        print "matplotlib ", matplotlib.__version__
    except:
        print "No matplotlib: recommending 1.1.0"
        
    try:
        import wx
        print "wx ", wx.__version__
    except:
        print "No wx: recommending 2.8.12.1"
        
    try:
        import scipy
        print "scipy ", scipy.__version__
    except:
        print "No scipy: recommending 0.10.0"
        
    try:
        import numpy
        print "numpy ", numpy.__version__
    except:
        print "No numpy: recommending 1.1.0"
        
    try:
        import lxml.etree
        print "lxml ", lxml.etree.__version__
    except:
        print "No lxml: recommend 2.3.0"
        
    try:
        import reportlab
        print "reportlab ", reportlab.Version
    except:
        print "No reportlab"
        
    try:
        import PIL
        print "PIL"
    except:
        print "No PIL"
        
    # The following is necessary to build an app
    try:
        import py2app
        print "py2app ", py2app.__version__
    except:
        print "No py2app: recommending version >= 0.6.4"
        
    try:
        import altgraph
        print "altgraph ", altgraph.__version__
    except:
        print "No altgraph"    
        
    try:
        import modulegraph
        print "modulegraph ", modulegraph.__version__
    except:
        print "No modulegraph: recommending version >= 0.9.1"
        
    try:
        import macholib
        print "macholib ", macholib.__version__
    except:
        print "No macholib: recommending version >= 1.4.3"
        
    try:
        import ho.pisa
        print "ho.pisa ", ho.pisa.__version__
    except:
        print "No pisa"
    
    
def check_system():
    """
        Checks that the system has the necessary modules.
        This is an early and more complete variation of the system
        check in check_deps()
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
            os.system("easy_install 'pyparsing==1.5.5'")
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

check_deps()
    