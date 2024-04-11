# Generate the matrix of jobs to run tests, build docs, build installers
#
# run `python .github/workflows/matrix.py --json` to see the output
#
# Philosophy:
# - test everything
# - get unittest results back as fast as possible, burning extra CPU time
#   to do that if necessary
# - sphinx is slow, build documentation separately to running the unittests
# - pyinstaller is slow, run it separately to running the unittests

import json
import sys

pretty = "--json" in sys.argv


jobs = []

# List of OS images to use for release builds
# Notes on OS selection:
# - macos
# - windows
# - linux: the release that is used defines the oldest distro on which
#   the Linux pyinstaller output will run as libc is still
#   dynamically linked by pyinstaller.
#   https://pyinstaller.readthedocs.io/en/stable/usage.html#making-gnu-linux-apps-forward-compatible
os_release_list = [
    'ubuntu-20.04',
    'windows-latest',
    'macos-latest',
]

# List of OS images to use for release tests
os_test_list = os_release_list + [
    'ubuntu-latest',
]

# List of python versions to use for release builds
python_release_list = [
    '3.11',
]

# List of python versions to use for tests
python_test_list = python_release_list + [
    '3.9',
    '3.10'
]


def truthy(val):
    # the json importer in the github actions doesn't cope with true, false,
    # or none particularly nicely; making this output only 0/1 as integers
    # simplifies all the conditionals in the yml file.
    return int(bool(val))


def entry(job_name="Job", os=None, pyver=None, tests=None, docs=None, installer=None):
    # Stuff the values into a dict that will appear in the json;
    # make sure all entries have all keys even if not specified for that
    # job so that validating the matrix or fallbacks for missing keys are
    # not needed in the yml file.
    return {
        'job_name': job_name,
        'os': os or os_release_list[0],
        'python-version': pyver or python_release_list[0],
        'tests': truthy(tests),
        'docs': truthy(docs),
        'installer': truthy(installer),
    }


## Construct the list of jobs for build+test
# Test all the OS/pyver combinations as quickly as possible to get unittest
# results back to the author; docs and installer are much slower, so
# leave them for a separate build.
for os in os_test_list:
    for pyver in python_test_list:
        jobs.append(
            entry(
                job_name = f"Test ({os}, {pyver})",
                os = os,
                pyver = pyver,
                tests = True,
                docs = False,
                installer = False,
            )
        )


## Construct the list of jobs for the installer
# Building the installer needs the docs but not the tests; this is a simple
# time optimisation to get the installer built faster, since the tests
# take a bit of time to run and are already run in the 'test' jobs.
for os in os_release_list:
    for pyver in python_release_list:
        jobs.append(
            entry(
                job_name = f"Installer ({os}, {pyver})",
                os = os,
                pyver = pyver,
                tests = False,
                docs = True,
                installer = True,
            )
        )

if not pretty:
    print("matrix=", end='')

print(json.dumps(jobs, indent=4 if pretty else None))
