Creating a Perspective
======================

This tutorial will walk you through the basic steps of creating a new perspective.

Creating the Perspective class
------------------------------------

All perspective need to be based on the `Perspective` base class. In doing so, you must override some methods which tell the data explorer the type of data the perspective can accept:

+ `supported_data`: this property returns a set of the different data it expects. For most perspectives, this may only be `SasData`, but you may also want to add `Trend`.
+ ``supports_multiple_data``: this returns a boolean flag. If its set to ``False``, the user can only send one data object to it. Generally, you'll want to keep this as ``False`` unless your perspective does consider multiple data objects *at the same time*. While previously perspectives had tabs, this is no longer the case. If the user wants to analyse multiple data objects at the same time, they are now encouraged to create multiple instances of the perspective. Therefore, perspectives shouldn't implement tabbing logic themselves.

  `Perspective` itself is based on `QDialog`, meaning the perspective class you create will also be a Dialog class, so you can add your GUI components to that object as well.

Worked example
--------------------------

In this example, we will create a perspective which will take in one SasData object, and display some data metrics about it. The metrics won't be that interesting for small angle scattering data, but this is mostly just to give an example of how we would turn this into a perspective.

We firstly need to create the Perspective class::
    class StatisticsPerspective(Perspective):
        def __init__(self, data_manager: DataManager, parent: QWidget | None = None) -> None:
            super().__init__(data_manager, parent)
            # TODO: Add GUI controls.

    @property
    @override
    def title(self) -> str:
        return "Statistics Perspective"

    # TODO: There are other overrides to set.

For the constructor, we need to take in both the data manager, and the parent widget. These values are then provided when the perspective is created. We don't need to do anything with the parent other than pass it up to the super constructor, as this is just passed to QT for use internally.

The snippet overrides the ``title`` property. This is shown on the data explorer, so its important that you set this to something recognisable.

Remember that the ``Perspective`` class is based on ``QDialog``, so we can now start to add GUI controls to our constructor.

The ```newAssociation`` method is called whenever data (or other objects) are sent to the perspective. Usually, you won't want to perform any calculations at this stage because the user might want to tweak parameters before running them. Instead, this method should be used to update the display of the perspective to reflect the data that just got sent to it.
