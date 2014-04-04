"""
Called by Makefile.  Invokes sphinx-apidoc so that we may build the
developer documentation.

Having a separate python program to do this is preferable to trying to
work out what platform and python version we have (e.g. "lib/lib.win32-2.6")
from inside the makefile.
"""

import subprocess
import os
import sys
from distutils.util import get_platform

platform = '.%s-%s'%(get_platform(),sys.version[:3])
build_lib = os.path.abspath('../../build/lib'+platform)

subprocess.call([
	"sphinx-apidoc",
	"-o", "source/api",
	"-d", "8",
	build_lib])