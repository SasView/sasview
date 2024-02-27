.. preferences_help.rst

.. Initial Draft: J Krzywon, August 2022
.. Last Updated: J Krzywon, December 2, 2022

.. _Preferences:

Preferences
============

SasView has a number of user-settable options available. For information on a specific preference, navigate to the
appropriate page heading. Not all preferences are housed here, but will be eventually.

A number of these preferences will only apply to the current SasView window and will reset when closing. Others,
labelled *persistent* in this document, will be retained for the next time SasView is run.

:ref:`Plot_Preferences`, :ref:`Display_Preferences`, :ref:`GPU_Preferences`, :ref:`Fit_Optimizer_Preferences`

.. _Plot_Preferences:

Plotting Preferences
--------------------
Plotting preferences only apply to new plots. Existing plots will retain existing settings.

**Use full-width plot legends (most compatible)?**: With this option selected, plot legends will always be the full width
of the plot it is on. The legend will also be partially transparent to better view the data. *persistent*

**Use truncated legend entries?**: By selecting this option, legend labels are truncated to a single line of length
*Legend entry line length* leaving only the beginning and end of the label. The central characters will be replaced with
an ellipsis and whitespace. *persistent*

**Legend entry line length**: This defines the maximum number of characters to display in a single line of a plot legend
before wrapping to the next line. *persistent*

.. _Display_Preferences:

Display Preferences
-------------------
The display preferences modify underlying features of our GUI framework, Qt. For more information on each setting,
please read more on the `Qt High DPI Settings <https://doc.qt.io/qt-5/highdpi.html#high-dpi-support-in-qt>`_.

**Theme**: A few basic themes are available for SasView. On selection of a new theme, the window will update as a preview.
Users can create their own themes and store them in `/.sasview/themes/` folder of their user directory. User themes will
use the `Classic` theme as a fall back for any styles not defined in the stylesheet. SasView assumes any file in the directory
is a stylesheet. For more information on writing Qt stylesheets, please see the
`Qt style sheet reference <https://doc.qt.io/qt-6/stylesheet-reference.html>`_ *persistent*

**Font Size** Select the font size that will be used throughout the SasView application. Font sizes defined in User themes
will override this setting.

**QT Screen Scale Factor**: A percent scaling factor that is applied all element sizes within the GUI. A restart of
SasView is required to take effect. *persistent*

**Automatic Screen Scale Factor**: enables automatic scaling, based on the monitor's pixel density. This won't change the
size of point-sized fonts, since point is a physical measurement unit. Multiple screens may get different scale factors.
*persistent*

.. _GPU_Preferences:

GPU Preferences
-------------------------

**GPU Options**: If a *potential* GPU device is present the dialog will show it. The *Test*
button can then be used to check if your system has the necessary drivers to
use it. But also see :ref:`gpu-setup`. *persistent*

.. _Fit_Optimizer_Preferences:

Fit Optimizer Preferences
-------------------------

**Default Fitting Algorithm**: The fitting optimizer that will be set when SasView starts. *persistent*

**Active Fitting Algorithm**: The fitting algorithm currently in use. This will default to the *Default Fitting Algorithm*
when SasView loads. When this changes, settings for the optimizer will update. More information on the various
optimizers can be found at :ref:`optimizer-guide`
