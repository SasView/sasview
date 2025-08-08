.. sasview_files.rst

.. Initial Draft: J Krzywon, Apr 2025
.. Last Updated: J Krzywon, Jul 24, 2025

.. _UserFiles:

SasView User Files
==================

During the installation process and while running the app, SasView creates a number of files that are stored outside
the install location on the end users computer. These files include configurations, plugin models, compiled plugins,
documentation, and example files. Please refer to the specific section to find where each type of file is stored.

File paths that start with the '~' character refer to the user directory, which is typically `C:\\\\Users\\<username>` in
Windows, `/Users/<username>` in MacOS, and `/home/<username>` in most Linux distributions.

This document is specific to v6.1.0 and beyond. Previous versions of SasView stored user files in the
`~/.sasview` directory.

**For users who wish to use versions both newer and older than v6.1, do not delete the contents
of the `~/.sasview` directory.**


:ref:`Config_Files`, :ref:`Log_Files`, :ref:`Plugin_Files`, :ref:`Compiled_Files`, :ref:`Documentation`, :ref:`Example_Data`

.. _Config_Files:

Configuration Files
--------------------
SasView stores two types of config file on the user disk, a general configuration file for each major version of sasview,
and a categories file that allows the end user to change how their models are organized in the fitting perspective. The
general configuration file, config-<v>.json is a json file that stores a mapping of config variables to their updated values.
This file is only generated and stored locally if something in the :ref:`Preferences` panel has been modified. The categories
file, categories.json, stores the user-preferred model organization, allowing a user to add model categories, move models
into new categories, and not show certain models. More information on this feature is available in :ref:`Category_Manager`.

OS-specific file locations for configuration files:
 - Windows: ~/AppData/Local/sasview/SasView/
 - MacOS: ~/Library/Application Support/SasView/
 - Linux: ~/.config/SasView/

.. _Log_Files:

Log Files
---------
SasView creates a time-stamped log file that includes all messages entered into the log explorer, as well as a number of
other messages related to application startup and shutdown.

OS-specific file locations for log files:
 - Windows: ~/AppData/Local/sasview/SasView/Logs/
 - MacOS: ~/Library/Logs/SasView/
 - Linux: ~/.local/state/SasView/

.. _Plugin_Files:

Plugin Files
------------
Plugin models, whether they be written by the user (:ref:`Writing_a_Plugin`), downloaded from the
`model marketplace <https://marketplace.sasview.org/>`_, or sent from another SasView user, should be stored in a
specific location to allow SasView to find them.

OS-specific file locations for plugin files:
 - Windows: ~/AppData/Local/sasview/SasView/plugin_models/
 - MacOS: ~/Library/Application Support/SasView/plugin_models/
 - Linux: ~/.local/share/SasView/plugin_models

.. _Compiled_Files:

Complied Model Files
------------
The fitting module, when a model is selected, compiles each model in an on-demand process. The compiled file will include
all form factors and structure factors used to create the model, and will be compiled based on the GPU optimization
currently in use. These models are stored in a parallel directory to the plugin models, but end users do not need to add
any files to this directory.

OS-specific file locations for compiled model files:
 - Windows: ~/AppData/Local/sasview/SasView/compiled_models/
 - MacOS: ~/Library/Application Support/SasView/compiled_models/
 - Linux: ~/.local/share/SasView/compiled_models

.. _Documentation:

Documentation
-------------
SasView moves its documentation into a user location when launching the app, if the documentation does not already exist.
Each version of SasView has its own documentation that may be different between versions, so a separate directory is used
for each version of the doc files.

OS-specific file locations for documentation:
 - Windows: ~/AppData/Local/sasview/SasView/<sasview.version>/doc/
 - MacOS: ~/Library/Application Support/SasView/<sasview.version>/doc/
 - Linux: ~/.local/share/SasView/<sasview.version>/doc/

.. _Example_Data:

Example Data
------------
SasView supplies a number of example data files that may be used to orient yourself with the application. More information
on the included files is available in the :ref:`testdata_help`.

OS-specific file locations for example data:
 - Windows: ~/AppData/Local/sasview/SasView/example_data/
 - MacOS: ~/Library/Application Support/SasView/example_data/
 - Linux: ~/.local/share/SasView/example_data
