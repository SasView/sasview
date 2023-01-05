# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Run sasview from an installed bundle
"""

import sys


sys.dont_write_bytecode = True

from sas.sasview.MainWindow.MainWindow import run_sasview

run_sasview()
