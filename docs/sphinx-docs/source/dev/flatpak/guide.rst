Flatpak maintenance
===================

The ``flatpak_update_script.py`` generates the manifest files required
to package SasView as a Flatpak. It ensures all the Python dependencies
are up to date with the same versions used for the Ubuntu pins.

This document talks a bit about why this script is needed, and it
explains its requirements. If all you want to do is build the Flatpak,
skip to ‘Setting up requirements’

Why the script is needed
------------------------

The Flatpak includes a manifest file which essentially tells Flatpak how
to build the SasView container. This manifest needs to specify all the
application’s dependencies *including pip dependencies.* During the
build, the Flatpak doesn’t have any network access (this is to ensure it
can produce reproducible builds) so all pip packages need to be
specified in the manifest, including dependencies of dependencies.

It is usually recommended that Flatpaks build all their dependencies
from source. However, this can cause a lot of issues because we depend
on non-Python pip packages including packages which contain Rust code.
Building these packages involves pulling in Cargo dependencies which
also need to be fetched before the build container runs. Because of
these issues, many of our packages are fetched in using prebuilt wheels.
A list of these packages is in the ``build_tools/prefer_wheels.txt``
file.

The ``flatpak_update_script.py`` generates the Flatpak manifest files.
It should be run during every release, and the output files should be
moved to the SasView flathub repository.

How to use the script
---------------------

Requirements
~~~~~~~~~~~~

You must run this script on a Linux system with Flatpak installed. This
is because the script needs to inspect the Flatpak SDK to determine the
correct wheel to pull in.

The script uses `PEP
723 <https://packaging.python.org/en/latest/specifications/inline-script-metadata/#inline-script-metadata>`__
to define its dependencies, so you shouldn’t need to install them
manually. It is recommended to run this script with uv, as uv has a
parser for PEP 723 which will automatically create a separate
environment with the correct dependencies.

You need to have the `flatpak pip
generator <https://github.com/flatpak/flatpak-builder-tools/tree/master/pip>`__
script on your path. You should also make sure the
``requirements-release-ubuntu-latest.txt`` file has *pinned*
dependencies generated through ``uv pip freeze``.

Guided tutorial
~~~~~~~~~~~~~~~

Setting up requirements.
^^^^^^^^^^^^^^^^^^^^^^^^

Instructions on installing uv are `available
here <https://docs.astral.sh/uv/getting-started/installation/>`__.

If you don’t already have Flatpak installed on the machine you are
running, you can find instructions for your particular distro by
visiting the `Flathub setup guide <https://flathub.org/en/setup>`__.

To generate the pins, make sure you’ve synced the virtual environment
that uv manages with:

.. code:: sh

   uv sync 

Then run:

.. code:: sh

   uv pip freeze > build_tools/requirements-release-ubuntu-latest.txt

Running the script.
^^^^^^^^^^^^^^^^^^^

The script has a shebang at the top, so you’ll just need to mark it as
executable:

.. code:: sh

   chmod +x build_tools/flatpak_update_script.py

And then you can run the script like any Unix executable. You need to be
in the ``build_tools`` directory.

.. code:: sh

   cd build_tools
   ./flatpak_update_script.py --sasview-version 6.2.0

You can replace ‘6.2.0’ with whichever SasView version you are building
for.

Outputs
~~~~~~~

The script will output to the ``outputs`` directory by default, though
you can change this using the ``--output-dir`` flag. Once the script has
run, you should replace the files in the `Flatpak
repo <https://github.com/flathub/org.sasview.sasview>`__ with the files
the script has generated, and try to build the Flatpak.

Troubleshooting
===============

During the Flatpak build, a package fails to build from source
--------------------------------------------------------------

This is probably because a new dependency got added to SasView, and that
package can’t be easily built from source. To resolve this issue, you
can add this package name to the ``build_tools/prefer_wheels.txt`` file.
Rerun the script, and it will use the prebuilt wheel for manifest file
instead of the source tarball.
