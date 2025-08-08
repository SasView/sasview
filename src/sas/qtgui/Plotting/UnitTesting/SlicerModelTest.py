
import pytest
from PySide6 import QtGui

# Local
from sas.qtgui.Plotting.SlicerModel import SlicerModel


class SlicerModelTest:
    '''Test the SlicerModel'''

    @pytest.fixture(autouse=True)
    def model(self, qapp):
        '''Create/Destroy the SlicerModel'''
        class SModel(SlicerModel):
            params = {"a":1, "b":2}
            def __init__(self):
                SlicerModel.__init__(self)
            def getParams(self):
                return self.params
            def setParams(self, par):
                self.params = par
        m = SModel()

        yield m

    def testBaseClass(self, qapp):
        '''Assure that SlicerModel contains pure virtuals'''
        model = SlicerModel()
        with pytest.raises(NotImplementedError):
            model.setParams()
        with pytest.raises(NotImplementedError):
            model.setModelFromParams()

    def testDefaults(self, model):
        '''Test the GUI in its default state'''
        assert isinstance(model.model(), QtGui.QStandardItemModel)

    def testSetModelFromParams(self, model):
        '''Test the model update'''
        # Add a row to params
        new_dict = model.getParams()
        new_dict["c"] = 3
        model.setParams(new_dict)

        # Call the update
        model.setModelFromParams()

        # Check the new model.
        assert model.model().rowCount() == 3
        assert model.model().columnCount() == 2

    def testSetParamsFromModel(self, model):
        ''' Test the parameters update'''
        # First - the default model
        model.setModelFromParams()
        assert model.model().rowCount() == 2
        assert model.model().columnCount() == 2

        # Add a row
        item1 = QtGui.QStandardItem("c")
        item2 = QtGui.QStandardItem(3)
        model.model().appendRow([item1, item2])
        # Check the new model. The update should be automatic
        assert model.model().rowCount() == 3
        assert model.model().columnCount() == 2
