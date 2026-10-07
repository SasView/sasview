Creating a Perspective
======================

This tutorial will walk you through the basic steps of creating a new perspective.

Creating the Perspective class
------------------------------------

All perspective need to be based on the ``Perspective`` base class. In doing so, you must override some methods which tell the data explorer the type of data the perspective can accept:

+ ``supported_data``: this property returns a set of the different data it expects. For most perspectives, this may only be ``SasData``, but you may also want to add ``Trend``.
+ ``supports_multiple_data``: this returns a boolean flag. If its set to ``False``, the user can only send one data object to it. Generally, you'll want to keep this as ``False`` unless your perspective does consider multiple data objects *at the same time*. While previously perspectives had tabs, this is no longer the case. If the user wants to analyse multiple data objects at the same time, they are now encouraged to create multiple instances of the perspective. Therefore, perspectives shouldn't implement tabbing logic themselves.

``Perspective`` itself is based on ``QDialog``, meaning the perspective class you create will also be a Dialog class, so you can add your GUI components to that object as well.

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

    @property
    @override
    def supported_data(self) -> set[type[TrackedData]]:
        return {SasData}

    @property
    @override
    def supports_multiple_data(self) -> bool:
        return True

For the constructor, we need to take in both the data manager, and the parent widget. These values are then provided when the perspective is created. We don't need to do anything with the parent other than pass it up to the super constructor, as this is just passed to QT for use internally.

The snippet overrides the ``title`` property. This is shown on the data explorer, so its important that you set this to something recognisable.

We also need to specify the data the perspective can accept. Since the perspective will show statistics for only one ``SasData`` object at a time, we want ``supports_multiple_data`` to be ``False``. And we don't want to accept any other item like a ``Trend``, so we keep ``supported_data`` to a set of just the ``SasData`` type.

Remember that the ``Perspective`` class is based on ``QDialog``, so we can now start to add our layout alongside other GUI controls to our constructor.::

    def __init__(self, data_manager: NewDataManager, parent: QWidget | None = None):
        super().__init__(data_manager, parent)

        self.data_loaded_label = QLabel("No data loaded.")
        self.std_label = QLabel("")
        self.calculate_button = QPushButton("Calculate")
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.data_loaded_label)
        self.layout.addWidget(self.std_label)
        self.layout.addWidget(self.calculate_button)

For this example, we've just gone for a simple vertical layout with some labels we're going to set later once we've got some data.

The ```newAssociation`` method is called whenever data (or other objects) are sent to the perspective. Usually, you won't want to perform any calculations at this stage because the user might want to tweak parameters before running them. Instead, this method should be used to update the display of the perspective to reflect the data that just got sent to it. So in this example, we just want to make sure the ``self.data_loaded_label`` reflects the name of the data we've just loaded.::

    @override
    def newAssocation(self):
        datum = cast(SasData, self.associatedData[0])
        self.data_loaded_label.setText(datum.name)

Notice in particular how we're accessing the data. As discussed in the data manager documentation, the data manager has to be the single source of truth for all data in SasView. As such, we shouldn't be keeping a copy of the data internally. Instead, we use the handy ``associatedData`` property which is defined in the ``Perspective`` base class. To keep type checkers happy, we also cast it to ``SasData``, because we know through the ``supported_data`` property we defined earlier that ``associatedData`` will only contain a ``SasData`` object.

Now, for the perspective to appear in the data explorer, we need to add it to the ``perspectives`` dictionary in ``refactored_data_explorer.py``.::

  "Statistics Tutorial Perspective": StatisticsPerspective

The name on the left hand side will be seen when the user creates the new perspective. 


