__revision__ = filter(str.isdigit, "$Revision$")
__version__ = "0.0.0"
try:
    import sans.sansview
    __version__ = sans.sansview.__version__
except:
    print "Could not load sansview module"