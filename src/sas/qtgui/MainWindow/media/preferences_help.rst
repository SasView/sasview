.. preferences_help.rst

.. J Krzywon wrote initial draft August 2022
.. Last Updated: J Krzywon, October 2022

.. _Preferences:

Preferences
============

SasView has a number of user-settable options available. For information on a specific preference, navigate to the
appropriate page heading. Not all preferences are housed here, but will be eventually.

A number of these preferences will only apply to the current SasView window and will reset when closing. Others,
labelled *persistent* in this document, will be retained for the next time SasView is run.

:ref:`Plot_Preferences`, :ref:`Display_Preferences`

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

**QT Screen Scale Factor**: A percent scaling factor that is applied all element sizes within the GUI. A restart of
SasView is required to take effect. *persistent*

**Automatic Screen Scale Factor**: enables automatic scaling, based on the monitor's pixel density. This won't change the
size of point-sized fonts, since point is a physical measurement unit. Multiple screens may get different scale factors.
*persistent*
