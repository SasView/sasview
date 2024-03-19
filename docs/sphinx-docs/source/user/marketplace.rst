.. _marketplace:

Model Marketplace
=================
The `Model Marketplace <https://marketplace.sasview.org/>`_ allows members
of the SAS Community to contribute plug-in fitting models for *SasView*
for all to use.

.. note:: 
    These plug-in models require SasView version 4.0 or later. However, 
    not *all* models may work with *every* version of SasView because 
    of changes to our API.

Contributed models should be written in Python (only version 2.7.x is
currently supported) or, if computational speed is an issue, in a
combination of Python and C. You only need to upload the .py/.c source
code files to the Marketplace!

Please put a comment in your code to indicate which version of SasView you 
wrote the model for.

For guidance on how to write a plugin model see :ref:`Writing_a_Plugin` . It
may also be helpful to examine the library models in
the */sasmodels-data/models* sub-folder of your SasView installation directory.

The Marketplace also provides the option to upload a SasView text file of
the scattering function data computed by your model. If you do this a graph
of the scattering function will appear under the Marketplace entry for
your model.

.. note::
    The SasView Development Team regret to say that they do not have the
    resources to fix the bugs or polish the code in every model contributed
    to the Marketplace!
