import os
import sys
import xmlrunner
import unittest
import imp
from os.path import abspath, dirname, split as splitpath, join as joinpath

run_py = joinpath(dirname(dirname(abspath(__file__))), 'run.py')
#print run_py
run = imp.load_source('sasview_run', run_py)
run.prepare()
#print "\n".join(sys.path)
test_path,test_file = splitpath(sys.argv[1])
print "test file",sys.argv[1]
#print test_path, test_file
sys.argv = [sys.argv[0]]
os.chdir(test_path)
sys.path.insert(0, test_path)
test = imp.load_source('tests',test_file)
unittest.main(test, testRunner=xmlrunner.XMLTestRunner(output='logs'))

