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
