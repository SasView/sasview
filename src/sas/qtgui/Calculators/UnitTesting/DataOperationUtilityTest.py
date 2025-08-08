
import pytest
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from sas.qtgui.Calculators.DataOperationUtilityPanel import DataOperationUtilityPanel
from sas.qtgui.MainWindow.DataState import DataState
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D
from sas.qtgui.Utilities.GuiUtils import Communicate

BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'

class DataOperationUtilityTest:

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        """Create/Destroy the DataOperationUtilityPanel"""
        class dummy_manager:
            def communicator(widget):
                return Communicate()

        w = DataOperationUtilityPanel(dummy_manager())

        yield w

        w.close()
        w = None


    def testDefaults(self, widget, mocker):
        """Test the GUI in its default state"""

        assert isinstance(widget, QtWidgets.QDialog)

        assert widget.windowTitle() == "Data Operation"
        assert widget.groupBox.title() == "Data Operation " \
                                                        "[ + (add); " \
                                                        "- (subtract); " \
                                                        "* (multiply); " \
                                                        "/ (divide); " \
                                                        "| (append)]"
        # size
        assert widget.size().height() == 425
        assert widget.size().width() == 951

        # content of line edits
        assert widget.txtNumber.text() == '1.0'
        assert widget.txtOutputData.text() == 'MyNewDataName'

        # content of comboboxes and default text / index
        assert not widget.cbData1.isEditable()
        assert widget.cbData1.count() == 1
        assert widget.cbData1.currentText() == \
                            'No Data Available'

        assert not widget.cbData2.isEditable()
        assert widget.cbData2.count() == 1
        assert widget.cbData2.currentText() == \
                            'No Data Available'

        assert not widget.cbOperator.isEditable()
        assert widget.cbOperator.count() == 5
        assert widget.cbOperator.currentText() == '+'
        assert [widget.cbOperator.itemText(i) for i in
                                range(widget.cbOperator.count())] == \
                                ['+', '-', '*', '/', '|']

        # Tooltips
        assert str(widget.cmdCompute.toolTip()) == "Generate the Data " \
                                                            "and send to Data " \
                                                            "Explorer."
        assert str(widget.cmdClose.toolTip()) == "Close this panel."
        assert str(widget.cmdHelp.toolTip()) == \
                            "Get help on Data Operations."
        assert widget.txtNumber.toolTip() == "If no Data2 loaded, " \
                                                "enter a number to be " \
                                                "applied to Data1 using " \
                                                "the operator"
        assert str(widget.cbOperator.toolTip()) == "Add: +\n" \
                                                            "Subtract: - \n" \
                                                            "Multiply: *\n" \
                                                            "Divide: /\n" \
                                                            "Append(Combine): |"

        assert not widget.cmdCompute.isEnabled()
        assert not widget.txtNumber.isEnabled()

        assert isinstance(widget.layoutOutput, QtWidgets.QHBoxLayout)
        assert isinstance(widget.layoutData1, QtWidgets.QHBoxLayout)
        assert isinstance(widget.layoutData2, QtWidgets.QHBoxLayout)

        # To store input datafiles
        assert widget.filenames is None
        assert widget.list_data_items == []
        assert widget.data1 is None
        assert widget.data2 is None
        # To store the result
        assert widget.output is None
        assert not widget.data2OK
        assert not widget.data1OK

        mocker.patch.object(widget, 'newPlot')
        assert widget.newPlot.called_once()
        assert widget.newPlot.called_once()
        assert widget.newPlot.called_once()

    def testHelp(self, widget, mocker):
        """ Assure help file is shown """
        mocker.patch.object(widget.manager, 'showHelp', create=True)
        widget.onHelp()
        assert widget.manager.showHelp.called_once()
        args = widget.manager.showHelp.call_args
        assert 'data_operator_help.html' in args[0][0]

    def testOnReset(self, widget):
        """ Test onReset function """
        # modify gui
        widget.txtNumber.setText('2.3')
        widget.onReset()
        assert widget.txtNumber.text() == '1.0'

    def testOnClose(self, widget):
        """ test Closing window """
        closeButton = widget.cmdClose
        QTest.mouseClick(closeButton, Qt.LeftButton)

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testOnCompute(self, widget, mocker):
        """ Test onCompute function """

        # define the data
        widget.data1 = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                                    dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])
        widget.data2 = 1

        # mock update of plot
        mocker.patch.object(widget, 'updatePlot')

        # enable onCompute to run (check on data type)
        mocker.patch.object(widget, 'onCheckChosenData', return_value=True)

        # run onCompute
        widget.onCompute()

        # check output:
        # x unchanged, y incremented by 1 (=data2) and updatePlot called
        assert widget.output.x.tolist() == \
                                widget.data1.x.tolist()
        assert widget.output.y.tolist() == [12.0, 13.0, 14.0]
        assert widget.updatePlot.called_once()

        mocker.patch.object(widget, 'onPrepareOutputData')

        assert widget.onPrepareOutputData.called_once()

    def testOnSelectData1(self, widget, mocker):
        """ Test ComboBox for Data1 """
        # Case 1: no data loaded
        widget.onSelectData1()
        assert widget.data1 is None
        assert not widget.data1OK
        assert not widget.cmdCompute.isEnabled()

        # Case 2: data1 is a datafile
        mocker.patch.object(widget, 'filenames', return_value={'datafile1': 'details'})
        mocker.patch.object(widget, 'updatePlot')

        widget.cbData1.addItems(['Select Data', 'datafile1'])
        widget.cbData1.setCurrentIndex(widget.cbData1.count()-1)
        assert widget.updatePlot.called_once()
        # Compute button disabled if data2OK == False
        assert widget.cmdCompute.isEnabled() == widget.data2OK

    def testOnSelectData2(self, widget, mocker):
        """ Test ComboBox for Data2 """
        mocker.patch.object(widget, 'updatePlot', )
        # Case 1: no data loaded
        widget.onSelectData2()
        assert widget.data2 is None
        assert not widget.data2OK
        assert not widget.cmdCompute.isEnabled()

        # Case 2: when empty combobox
        widget.cbData2.clear()
        widget.onSelectData2()
        assert not widget.txtNumber.isEnabled()
        assert not widget.cmdCompute.isEnabled()

        # Case 3: when Data2 is Number
        # add 'Number' to combobox Data2
        widget.cbData2.addItem('Number')
        # select 'Number' for cbData2
        widget.cbData2.setCurrentIndex(widget.cbData2.count()-1)
        widget.onSelectData2()
        # check that line edit is now enabled
        assert widget.txtNumber.isEnabled()
        # Compute button enabled only if data1OK True
        assert widget.cmdCompute.isEnabled() == widget.data1OK
        assert isinstance(widget.data2, float)
        # call updatePlot
        assert widget.updatePlot.called_once()

        # Case 4: when Data2 is a file
        mocker.patch.object(widget, 'filenames', return_value={'datafile2': 'details'})
        widget.cbData2.addItems(['Select Data', 'Number', 'datafile2'])
        widget.cbData2.setCurrentIndex(widget.cbData2.count() - 1)
        assert widget.updatePlot.called_once()
        # editing of txtNumber is disabled when Data2 is a file
        assert not widget.txtNumber.isEnabled()
        # Compute button enabled only if data1OK True
        assert widget.cmdCompute.isEnabled() == \
                            widget.data1OK
        # call updatePlot
        assert widget.updatePlot.called_once()

    def testUpdateCombobox(self, widget):
        """ Test change of contents of comboboxes for Data1 and Data2 """
        # Create input data
        data1 = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                        dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        data2 = Data2D(image=[0.1] * 4,
                        qx_data=[1.0, 2.0, 3.0, 4.0],
                        qy_data=[10.0, 11.0, 12.0, 13.0],
                        dqx_data=[0.1, 0.2, 0.3, 0.4],
                        dqy_data=[0.1, 0.2, 0.3, 0.4],
                        q_data=[1, 2, 3, 4],
                        xmin=-1.0, xmax=5.0,
                        ymin=-1.0, ymax=15.0,
                        zmin=-1.0, zmax=20.0)

        filenames = {'datafile2': DataState(data2),
                                    'datafile1': DataState(data1)}

        # call function
        widget.updateCombobox(filenames)

        # check modifications of comboboxes
        AllItemsData1 = [widget.cbData1.itemText(indx)
                            for indx in range(widget.cbData1.count())]
        assert AllItemsData1 == ['Select Data',
                                                'datafile2',
                                                'datafile1']

        AllItemsData2 = [widget.cbData2.itemText(indx)
                            for indx in range(widget.cbData2.count())]
        assert AllItemsData2 == \
                                ['Select Data', 'Number',
                                'datafile2', 'datafile1']

    def testOnSelectOperator(self, widget):
        """ Change GUI when operator changed """
        assert widget.lblOperatorApplied.text() == widget.cbOperator.currentText()

        widget.cbOperator.setCurrentIndex(2)
        assert widget.lblOperatorApplied.text() == \
                            widget.cbOperator.currentText()

    def testOnInputCoefficient(self, widget):
        """
        Check input of number when a coefficient is required for operation
        """
        # clear input for coefficient -> error
        widget.txtNumber.clear()
        # check that color of background changed to notify error
        assert BG_COLOR_ERR in widget.txtNumber.styleSheet()


    def testCheckChosenData(self, widget):
        """ Test check of data compatibility """
        # set the 2 following to True since we want to check
        # the compatibility of dimensions
        widget.data1OK = True
        widget.data2OK = True

        # Case 1: incompatible dimensions
        widget.data1 = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                                    dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        widget.data2 = Data2D(image=[0.1] * 4,
                            qx_data=[1.0, 2.0, 3.0, 4.0],
                            qy_data=[10.0, 11.0, 12.0, 13.0],
                            dqx_data=[0.1, 0.2, 0.3, 0.4],
                            dqy_data=[0.1, 0.2, 0.3, 0.4],
                            q_data=[1, 2, 3, 4],
                            xmin=-1.0, xmax=5.0,
                            ymin=-1.0, ymax=15.0,
                            zmin=-1.0, zmax=20.0)

        assert not widget.onCheckChosenData()

        # Case 2 : compatible 1 dimension
        widget.data1 = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                                    dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        widget.data2 = Data1D(x=[1.0, 2.0, 3.0], y=[1.0, 2.0, 3.0],
                                    dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        assert widget.onCheckChosenData()

        # Case 3: compatible 2 dimension
        widget.data1 = Data2D(image=[0.1] * 4,
                                    qx_data=[1.0, 2.0, 3.0, 4.0],
                                    qy_data=[10.0, 11.0, 12.0, 13.0],
                                    dqx_data=[0.1, 0.2, 0.3, 0.4],
                                    dqy_data=[0.1, 0.2, 0.3, 0.4],
                                    q_data=[1, 2, 3, 4],
                                    xmin=-1.0, xmax=5.0,
                                    ymin=-1.0, ymax=15.0,
                                    zmin=-1.0, zmax=20.0)

        widget.data2 = Data2D(image=[0.1] * 4,
                                    qx_data=[1.0, 2.0, 3.0, 4.0],
                                    qy_data=[10.0, 11.0, 12.0, 13.0],
                                    dqx_data=[0.1, 0.2, 0.3, 0.4],
                                    dqy_data=[0.1, 0.2, 0.3, 0.4],
                                    q_data=[1, 2, 3, 4],
                                    xmin=-1.0, xmax=5.0,
                                    ymin=-1.0, ymax=15.0,
                                    zmin=-1.0, zmax=20.0)

        assert widget.onCheckChosenData()

        # Case 4: Different 1D
        widget.data1 = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                                    dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        widget.data2 = Data1D(x=[0.0, 1.0, 2.0], y=[1.0, 2.0, 3.0],
                                    dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        assert not widget.onCheckChosenData()

        # Case 5: Data2 is a Number
        widget.cbData2.clear()
        widget.cbData2.addItem('Number')
        widget.cbData2.setCurrentIndex(0)
        assert widget.cbData2.currentText() == 'Number'
        assert widget.onCheckChosenData()

    def testOnCheckOutputName(self, widget):
        """ Test OutputName for result of operation """
        widget.txtOutputData.clear()
        assert not widget.onCheckOutputName()

        widget.list_data_items = ['datafile1', 'datafile2']
        widget.txtOutputData.setText('datafile0')
        assert widget.onCheckOutputName()
        assert '' in widget.txtOutputData.styleSheet()

        widget.txtOutputData.clear()
        widget.txtOutputData.setText('datafile1')
        assert not widget.onCheckOutputName()
        assert BG_COLOR_ERR in widget.txtOutputData.styleSheet()

    def testFindId(self, widget):
        """ Test function to find id of file in list of filenames"""
        data_for_id = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                                    dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        widget.filenames = {'datafile2': DataState(data_for_id),
                                    'datafile1': DataState(data_for_id)}

        id_out = widget._findId('datafile2')
        assert id_out == 'datafile2'

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testExtractData(self, widget):
        """
        Test function to extract data to be computed from input filenames
        """
        data1 = Data1D(x=[1.0, 2.0, 3.0], y=[11.0, 12.0, 13.0],
                        dx=[0.1, 0.2, 0.3], dy=[0.1, 0.2, 0.3])

        data2 = Data2D(image=[0.1] * 4,
                                    qx_data=[1.0, 2.0, 3.0, 4.0],
                                    qy_data=[10.0, 11.0, 12.0, 13.0],
                                    dqx_data=[0.1, 0.2, 0.3, 0.4],
                                    dqy_data=[0.1, 0.2, 0.3, 0.4],
                                    q_data=[1, 2, 3, 4],
                                    xmin=-1.0, xmax=5.0,
                                    ymin=-1.0, ymax=15.0,
                                    zmin=-1.0, zmax=20.0)

        widget.filenames = {'datafile2': DataState(data2),
                                    'datafile1': DataState(data1)}
        output1D = widget._extractData('datafile1')
        assert isinstance(output1D, Data1D)

        output2D = widget._extractData('datafile2')
        assert isinstance(output2D, Data2D)

    # TODO
    def testOnPrepareOutputData(self, widget):
        """ """
        pass
