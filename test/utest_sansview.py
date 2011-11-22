import os
import subprocess
import re

SKIPPED_DIRS = ["sansrealspace"]
SANSVIEW_DIR = ".."

def run_tests():
    passed = 0
    failed = 0
    n_tests = 0
    n_errors = 0
    n_failures = 0
    
    for d in os.listdir(SANSVIEW_DIR):
        
        # Check for modules to be skipped
        if d in SKIPPED_DIRS:
            continue
        
        # Go through modules looking for unit tests
        module_dir = os.path.join(SANSVIEW_DIR,d,"test")
        if os.path.isdir(module_dir):
            for f in os.listdir(module_dir):
                file_path = os.path.join(module_dir,f)
                if os.path.isfile(file_path) and f.startswith("utest_") and f.endswith(".py"):
                    module_name,_ = os.path.splitext(f)
                    code = "cd %s;python -c \"import sys;import unittest;sys.path.insert(0, '%s');" % (module_dir, module_dir)
                    code += "from %s import *;" % module_name
                    code += "unittest.main()\""
                    proc = subprocess.Popen(code, shell=True, stdout=subprocess.PIPE, stderr = subprocess.STDOUT)
                    std_out, std_err = proc.communicate()
                    
                    has_failed = False
                    m = re.search("Ran ([0-9]+) tests", std_out)
                    if m is not None:
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
                        print "Result for %s: FAILED" % module_name
                        print std_out
                    else:
                        passed += 1
                        print "Result for %s: SUCCESS" % module_name
                        
    
    print "\n----------------------------------------------"
    print "Results by test modules:"
    print "    PASSED: %d" % passed
    ratio = 100.0*failed/(failed+passed)
    print "    FAILED: %d    (%2.2g%%)" % (failed,ratio) 
    
    print "Results by tests:"
    print "    Tests run:    %d" % n_tests
    print "    Tests failed: %d" % n_failures
    print "    Test errors:  %d" % n_errors 
    print "----------------------------------------------"
    

if __name__ == '__main__':
    run_tests()                    