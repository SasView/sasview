"""
    Check dependencies
"""
import sys
print sys.path

try:
    import matplotlib
    print "matplotlib ", matplotlib.__version__
except:
    print "No matplotlib"
    
try:
    import wx
    print "wx ", wx.__version__
except:
    print "No wx"
    
try:
    import scipy
    print "scipy ", scipy.__version__
except:
    print "No scipy"
    
try:
    import numpy
    print "numpy ", numpy.__version__
except:
    print "No numpy"
    
try:
    import lxml.etree
    print "lxml ", lxml.etree.__version__
except:
    print "No lxml"
    
try:
    import reportlab
    print "reportlab ", reportlab.Version
except:
    print "No reportlab"
    
    