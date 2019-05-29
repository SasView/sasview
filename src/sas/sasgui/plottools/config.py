# This program is public domain
"""
Configure plotter for plottools.

This must be imported first in __init__.py for plottools.

If your application uses matplotlib outside plottools, then
please do the following at the start of your application:

    # Select matplotlib version and backend
    import sas.sasgui.plottools.config

Note that plottools requires particular versions of matplotlib
and a particular backend.  As of this writing it is the WXAgg
backend for matplotlib>=0.98.

The plottools package uses pkg_resources if available to select
the correct version of matplotlib.  If you need multiple matplotlib
versions in your path, be sure to use "easy_install -m" for all
of them.  If a version is installed without "-m" that does not
meet the requirements, then pkg_resources.require() will fail,
even if you have installed a suitable version with "-m".  In this
case you will need to fix up your site-packages directory,
probably by removing site-packages/matplotlib and the associated
egg file for that version, and reinstalling with "-m".  You may
also need to edit site-packages/easy-install.pth.
"""
import sys

__all__ = []

#plot_version = "0.98"
#plot_backend = "WXAgg"
print("SET MPL BACKEND TO Qt5")
plot_backend = "Qt5Agg"

# Sort out matplotlib version
import matplotlib
#try:
#    import pkg_resources
#    pkg_resources.require("matplotlib>=" + plot_version)
#except:
#    from distutils.version import LooseVersion as Version
#    if Version(matplotlib.__version__) < Version(plot_version):
#        msg = "Matplotlib version must be %s or newer" % (plot_version, )
#        raise ImportError(msg)

# Sort out matplotlib backend
#import matplotlib
if 'matplotlib.backends' not in sys.modules:
    # if no backend yet, be sure to use the correct one
    matplotlib.use(plot_backend)
elif matplotlib.get_backend() != plot_backend:
    # if a backend has already been selected, make sure it is the correct one.
    #raise ImportError("Matplotlib not using backend " + plot_backend)
    pass

# set global plot style
param = 'legend.handletextpad'
if param not in matplotlib.rcParams: param = 'legend.handletextsep'
matplotlib.rcParams[param] = 0.05
matplotlib.rcParams['legend.numpoints'] = 1
#matplotlib.rcParams['interactive'] = True


# this should happen after initial matplotlib configuration
#from .toolbar import NavigationToolBar
#from matplotlib.backends import backend_wxagg
#backend_wxagg.NavigationToolbar2WxAgg = NavigationToolBar

# CRUFT: bumps 0.7.5.6 and older uses wrong toolbar
#backend_wxagg.NavigationToolbar2Wx = NavigationToolBar
