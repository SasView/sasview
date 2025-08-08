import pytest
from PySide6.QtWidgets import QTableWidgetItem

from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy

# Local
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.PluginDefinition import PluginDefinition
from sas.qtgui.Utilities.PythonSyntax import PythonHighlighter


class PluginDefinitionTest:
    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the PluginDefinition'''
        w = PluginDefinition(None)
        yield w
        w.close()

    def testDefaults(self, widget):
        """Test the GUI in its default state"""
        assert isinstance(widget.highlight, PythonHighlighter)
        assert isinstance(widget.parameter_dict, dict)
        assert isinstance(widget.pd_parameter_dict, dict)

        assert len(widget.model) == 6
        assert "filename" in widget.model.keys()
        assert "overwrite" in widget.model.keys()
        assert "description" in widget.model.keys()
        assert "parameters" in widget.model.keys()
        assert "pd_parameters" in widget.model.keys()
        assert "text" in widget.model.keys()

    def testOnOverwrite(self, widget):
        """See what happens when the overwrite checkbox is selected"""
        spy_signal = QtSignalSpy(widget, widget.modelModified)

        # check the default
        assert not widget.chkOverwrite.isChecked()

        # Change the state
        widget.chkOverwrite.setChecked(True)

        # Check the signal
        assert spy_signal.count() == 1

        # model dict updated
        assert widget.model['overwrite']

    def testOnPluginNameChanged(self, widget):
        """See what happens when the name of the plugin changes"""
        spy_signal = QtSignalSpy(widget, widget.modelModified)

        # Change the name
        new_text = "Duck season"
        widget.txtName.setText(new_text)
        widget.txtName.editingFinished.emit()

        # Check the signal
        assert spy_signal.count() == 1

        # model dict updated
        assert widget.model['filename'] == new_text

    def testOnDescriptionChanged(self, widget):
        """See what happens when the description of the plugin changes"""
        spy_signal = QtSignalSpy(widget, widget.modelModified)

        # Change the name
        new_text = "Rabbit season"
        widget.txtDescription.setText(new_text)
        widget.txtDescription.editingFinished.emit()

        # Check the signal
        assert spy_signal.count() == 1

        # model dict updated
        assert widget.model['description'] == new_text

    def testOnParamsChanged(self, widget):
        """See what happens when parameters change"""
        spy_signal = QtSignalSpy(widget, widget.modelModified)

        # number of rows. default=1
        assert widget.tblParams.rowCount() == 1

        # number of columns. default=2
        assert widget.tblParams.columnCount() == 2

        # Change the param
        new_param = "shoot"
        widget.tblParams.setItem(0,0,QTableWidgetItem(new_param))
        #widget.tblParams.editingFinished.emit()


        # Check the signal
        assert spy_signal.count() == 1

        # model dict updated
        assert widget.model['parameters'] == {0: (new_param, None)}

        # Change the value
        new_value = "BOOM"
        widget.tblParams.setItem(0,1,QTableWidgetItem(new_value))

        # Check the signal
        assert spy_signal.count() == 2

        # model dict updated
        assert widget.model['parameters'] == {0: (new_param, new_value)}

        # See that the number of rows increased
        assert widget.tblParams.rowCount() == 2

    def testOnPDParamsChanged(self, widget):
        """See what happens when pd parameters change"""
        spy_signal = QtSignalSpy(widget, widget.modelModified)

        # number of rows. default=1
        assert widget.tblParamsPD.rowCount() == 1

        # number of columns. default=2
        assert widget.tblParamsPD.columnCount() == 2

        # Change the param
        new_param = "shoot"
        widget.tblParamsPD.setItem(0,0,QTableWidgetItem(new_param))

        # Check the signal
        assert spy_signal.count() == 1

        # model dict updated
        assert widget.model['pd_parameters'] == {0: (new_param, None)}

        # Change the value
        new_value = "BOOM"
        widget.tblParamsPD.setItem(0,1,QTableWidgetItem(new_value))

        # Check the signal
        assert spy_signal.count() == 2

        # model dict updated
        assert widget.model['pd_parameters'] == {0: (new_param, new_value)}

        # See that the number of rows increased
        assert widget.tblParamsPD.rowCount() == 2

    def testOnFunctionChanged(self, widget):
        """See what happens when the model text changes"""
        spy_signal = QtSignalSpy(widget, widget.modelModified)

        # Change the text
        new_model = "1\n2\n"
        widget.txtFunction.setPlainText(new_model)

        # Check the signal
        assert spy_signal.count() == 1

        # model dict updated
        assert widget.model['text'] == new_model.rstrip()
