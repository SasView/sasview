#!/usr/bin/env python

import os
import sys
import xmlrunner
import unittest
import imp
from os.path import abspath, dirname, split as splitpath, join as joinpath

import logging
import logging.config
LOGGER_CONFIG_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini')
logging.config.fileConfig(LOGGER_CONFIG_FILE, disable_existing_loggers=False)
logger = logging.getLogger()

run_py = joinpath(dirname(dirname(abspath(__file__))), 'run.py')
run = imp.load_source('sasview_run', run_py)
run.prepare()
#print "\n".join(sys.path)
test_path,test_file = splitpath(abspath(sys.argv[1]))
print "=== testing:",sys.argv[1]
#print test_path, test_file
sys.argv = [sys.argv[0]]
os.chdir(test_path)
sys.path.insert(0, test_path)
test = imp.load_source('tests',test_file)
unittest.main(test, testRunner=xmlrunner.XMLTestRunner(output='logs'))
