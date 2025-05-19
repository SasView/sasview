Running Tests
=============

Tests are stored in subdirectories of the test directory, as
*package/utest_\*.py*. Test data, expected output and other support files
should be in a subdirectory of the unit test directory.

Tests are run as part of CI using the standard `pytest` runner::

  python -m pytest -v -s test

It is possible to run just one set of tests by specifying the filename
or the entire test name on the commandline::

  python -m pytest -v -s test/config/utest_config.py
  python -m pytest -v -s test/config/utest_config.py::TestConfig::test_bad_config_file_structure

Tests can be run in Eclipse (or other IDE) by selecting *utest_sasview.py*
and selecting run. This will run all of the tests. To run tests for one
one package, edit the *utest_sasview.py* run command and add the package
directory to the command arguments. To run an individual test,
select *run_one.py* and edit the command arguments to include the path to
the desired test file.
