Data Manager
============

The Data Manager in SasView is responsible for tracking all data, and its interactions with other data. For this purpose, 'data' refers to:

+ Data objects (SasData)
+ Perspectives
+ Fits
+ Theory items
+ Plots

The data manager can keep track of associations between data. This means that data can access other data that is associated with. Examples include:

+ SasData objects associated with plots. In this sense, a plot needs to access a particular SasData object so it can plot it, so an associated is created.
+ Fits can be associated with SasData so that it is clear which data the Fit is fitting.

For all tracked data, the Data Manager should be the **single point of truth.** Generally, copies of objects should not be kept, and all objects should refer to the Data Manager. Because of this, certain things must be avoided:

+ Perspectives should not keep copies of data. Instead, they should always refer back to the Data Manager for their data. Sometimes it is useful to create a property to do this automatically (see the perspective creation tutorial).

Adding data to the data manager
------------------------------------------------------

The Data Manager is a property in the GuiManager class (``_data_manager``). It will also usually be added to perspectives during instantiation.

Once you have instantiated an object which you needs to be tracked in the Data Manager, you can use the `add_data` method.::
  
  data_manager.add_data(data)

To create an association between two data, you can use the ``make_association`` method::

  data_manager.make_association(data1, data2)

Both ``data1``, and ```data2`` must be tracked in the data manager before you can make an association between them. Additionally, the ``data_manager`` module contains ``valid_associations`` which is a list of pairs. If there is no pair for ``data1``, and ``data2``, ``make_association`` will fail with a ``ValueError``.
