Running Tests
=============

Tests are stored in subdirectories of the test directory, as
*package/test/utest_\*.py*.   Other files in the test subdirectory are
data, expected output and other support files.  Before running any tests
you must first run *setup.py build* in the root.  Tests are run against the
current source directory with run magic to find the compiled code, so you
only need to rebuild between tests if you are modifying the C code.

Tests can be run in Eclipse (or other IDE) by selecting *utest_sasview.py*
and selecting run.  This will run all of the tests.  To run tests for one
one package, edit the *utest_sasview.py* run command and add the package
directory to the command arguments.  To run an individual test,
select *run_one.py* and edit the command arguments to include the path to
the desired test file.
