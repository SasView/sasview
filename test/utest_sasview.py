#!/usr/bin/env python
import os
import subprocess
import re
import sys

import logging
import logging.config
LOGGER_CONFIG_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logging.ini')
logging.config.fileConfig(LOGGER_CONFIG_FILE)
logger = logging.getLogger(__name__)

try:
    import xmlrunner
except:
    logger.error("xmlrunner needs to be installed to run these tests")
    logger.error("Try easy_install unittest-xml-reporting")
    sys.exit(1)

# Check whether we have matplotlib installed
HAS_MPL_WX = True
try:
    import matplotlib
    import wx
except:
    HAS_MPL_WX = False

SKIPPED_DIRS = ["sasrealspace", "calculatorview"]
if not HAS_MPL_WX:
    SKIPPED_DIRS.append("sasguiframe")

#COMMAND_SEP = ';'
#if os.name == 'nt':
#    COMMAND_SEP = '&'

def run_tests(dirs=None, all=False):
    test_root = os.path.abspath(os.path.dirname(__file__))
    run_one_py = os.path.join(test_root, 'run_one.py')
    passed = 0
    failed = 0
    n_tests = 0
    n_errors = 0
    n_failures = 0
    
    for d in (dirs if dirs else os.listdir(test_root)):
        
        # Check for modules to be skipped
        if d in SKIPPED_DIRS:
            continue
        

        # Go through modules looking for unit tests
        module_dir = os.path.join(test_root, d, "test")
        if os.path.isdir(module_dir):
            for f in os.listdir(module_dir):
                file_path = os.path.join(module_dir,f)
                if os.path.isfile(file_path) and f.startswith("utest_") and f.endswith(".py"):
                    module_name,_ = os.path.splitext(f)
                    code = '"%s" %s %s'%(sys.executable, run_one_py, file_path)
                    proc = subprocess.Popen(code, shell=True, stdout=subprocess.PIPE, stderr = subprocess.STDOUT)
                    std_out, std_err = proc.communicate()
                    #print std_out
                    #sys.exit()
                    has_failed = True
                    m = re.search("Ran ([0-9]+) test", std_out)
                    if m is not None:
                        has_failed = False
                        n_tests += int(m.group(1))

                    m = re.search("FAILED \(errors=([0-9]+)\)", std_out)
                    if m is not None:
                        has_failed = True
                        n_errors += int(m.group(1))
                    
                    m = re.search("FAILED \(failures=([0-9]+)\)", std_out)
                    if m is not None:
                        has_failed = True
                        n_failures += int(m.group(1))
                    
                    if has_failed:
                        failed += 1
                        print "Result for %s (%s): FAILED" % (module_name, module_dir)
                        print std_out
                    else:
                        passed += 1
                        print "Result for %s: SUCCESS" % module_name

    print "\n----------------------------------------------"
    if n_tests == 0:
        print "No tests."
    else:
        print "Results by test modules:"
        print "    PASSED: %d" % passed
        ratio = 100.0*failed/(failed+passed)
        print "    FAILED: %d    (%.0f%%)" % (failed,ratio)

        print "Results by tests:"
        print "    Tests run:    %d" % n_tests
        print "    Tests failed: %d" % n_failures
        print "    Test errors:  %d" % n_errors
    print "----------------------------------------------"
    
    return failed

if __name__ == '__main__':
    all = (len(sys.argv) > 1 and sys.argv[1] == '-all')
    dirs = sys.argv[1:] if not all else sys.argv[2:]
    if run_tests(dirs=dirs, all=all)>0:
        sys.exit(1)
    
