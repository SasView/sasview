"""
    Check dependencies
"""
import sys
print sys.version

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
    
  
    