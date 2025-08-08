#!/usr/bin/env python

import logging
import os
import sys
import unittest
from importlib.machinery import SourceFileLoader
from os.path import abspath, dirname
from os.path import join as joinpath
from os.path import split as splitpath

import xmlrunner

logger = logging.getLogger(__name__)
if not logger.root.handlers:
    import logging.config
    LOGGER_CONFIG_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini')
    logging.config.fileConfig(LOGGER_CONFIG_FILE, disable_existing_loggers=False)

if len(sys.argv) < 2:
    logger.error("Use %s <filename to test>",sys.argv[0])
    sys.exit(-1)

run_py = joinpath(dirname(dirname(abspath(__file__))), 'run.py')
run = SourceFileLoader('sasview_run', run_py).load_module()
run.prepare()

#print("\n".join(sys.path))

test_path,test_file = splitpath(abspath(sys.argv[1]))
print("=== testing:",sys.argv[1])
#print(test_path, test_file)

sys.argv = [sys.argv[0]]
os.chdir(test_path)
sys.path.insert(0, test_path)
test = SourceFileLoader('tests', test_file).load_module()
unittest.main(test, testRunner=xmlrunner.XMLTestRunner(output='logs'))
