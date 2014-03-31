"""
Checking and reinstalling the external packages
"""
import os
import sys

if sys.platform =='win32':
    IS_WIN = True
else:
    IS_WIN = False
try:
    import setuptools
    print "==> setuptools-%s installed."% setuptools.__version__
    if setuptools.__version__ != '0.6c11':
        print "!!! Recommend to install 0.6c11." 
except:
    print "!!! setuptools-0.6c11 not installed."
try:
    import pyparsing
    print "==> pyparsing-%s installed."% pyparsing.__version__
    if pyparsing.__version__ != '1.5.5':
        print "!!! 1.5.5 recommended."
except:
    print "==> pyparsing-1.5.5 not installed."
try:
    import html5lib
    print "==> html5lib-%s installed."% html5lib.__version__
    if html5lib.__version__.count('0.95') > 0:
        print "!!! 0.95 recommended."
except:
    print "!!! html5lib-0.95 not installed."
try:
    import pyPdf
    print "==> pyPdf-%s installed."% pyPdf.__version__
    if pyPdf.__version__ != '1.13':
	print "!!! 1.13 recommended."
except:
    print "!!! pyPdf-1.13 not installed (optional)."
try:
    import reportlab
    print "==> reportlab-%s installed."% reportlab.__version__
    if reportlab.__version__ != '2.5':
        print "!!! 2.5 recommended"
except:
    print "!!! reportlab-2.5 not installed."
try:
    import lxml
    print "==> lxml-%s installed."% lxml.__version__
    if lxml.__version__ != '2.3':
        print "!!! 2.3 recommended"
except:
    print "!!! lxml-2.3 not installed."
try:
    import Image
    print "==> PIL-%s installed."% Image.VERSION
    if Image.VERSION != '1.1.7':
        print "!!! 1.1.7 recommended."
except:
    print "!!! PIL-1.1.7 not installed."
try:
    import pylint
    print "==> pylint installed."
except:
    print "!!! pylint not installed (optional)."
    #os.system("START /B C:\python26\Scripts\easy_install pylint==0.25.0")
try:
    import periodictable
    print "==> periodictable-%s installed."% periodictable.__version__
    if periodictable.__version__ != '1.3.0':
        print "!!! Recommend to install 1.3.0." 
except:
    print "!!! periodictable-1.3.0 is not installed."
try:
    import numpy
    print "==> numpy-%s installed."% numpy.__version__
    if numpy.__version__ != '1.6.1':
        print "==> Recommend to install 1.6.1 (1.5.1 for MAC)." 
except:
    print "!!! numpy-1.6.1 not installed (1.5.1 for MAC)."
try:
    import scipy
    print "==> scipy-%s installed."% scipy.__version__
    if scipy.__version__ != '0.10.1':
        print "!!! Recommend to install 0.10.1 (1.10.0 for MAC)." 
except:
    print "!!! scipy-0.10.1 not installed (1.10.0 for MAC)."
try:
    import wx
    print "==> wxpython-%s installed."% wx.__version__
    if wx.__version__ != '2.8.12.1':
        print "!!! Recommend to install unicode-2.8.12.1." 
except:
    print "!!! wxpython-unicode-2.8.12.1 not installed."
try:
    import matplotlib
    print "==> matplotlib-%s installed."% matplotlib.__version__
    if matplotlib.__version__ != '1.1.0':
        print "!!! Recommend to install 1.1.0 (1.0.1 for MAC) or higher." 
except:
    print "!!! matplotlib-1.1.0 not installed (1.0.1 for MAC)."
try:
    from ho import pisa
    if pisa.__version__ == '3.0.27':
        print "==> pisa-%s installed."% pisa.__version__
    else:
        print "!!! Incorrect version of pisa installed."
        print "!!! 3.0.27 required."
except:
    print "!!! pisa-3.0.27 not installed."
if IS_WIN:
    try:
        import pywin
        print "==> pywin32 installed."
    except:
        print "!!! pywin32 not installed. Please install pywin32-217."
    try:
        import py2exe
        print "==> py2exe-%s installed."% py2exe.__version__
        if py2exe.__version__ != '0.6.9':
            print "!!! Recommend to install 0.6.9." 
    except:
        print "!!! py2exe-0.6.9 not installed. Installing..."
    try:
        import comtypes
        print "==> comtypes-%s installed."% comtypes.__version__
        if comtypes.__version__ != '0.6.2':
            print "!!! Recommend to install 0.6.2." 
    except:
        print "!!! comtypes-0.6.2 not installed. Installing..."
    print "==> Require subversion = 1.6.0 or lower version."
    print "Installed:"
    os.system("CALL svn --version --quiet")
    print "==> Checking gcc compiler ( >= 4.2 required):"
    os.system("CALL gcc -v")
else:
    try:
        import py2app
        print "==> py2app-%s installed."% py2app.__version__
    except:
        print "!!! py2app not installed (optional for MAC bundling."

