import logging

import pytest
from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from twisted.internet import threads

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Invariant.InvariantPerspective import InvariantWindow
from sas.qtgui.Perspectives.Invariant.InvariantUtils import WIDGETS
from sas.qtgui.Plotting.PlotterData import Data1D

BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'


class InvariantPerspectiveTest:
    """Test the Invariant Perspective Window"""

    @pytest.fixture(autouse=True)
    def widget(self, qapp, mocker):
        '''Create/Destroy the Invariant Perspective Window'''

        class MainWindow:
            def __init__(self):
                self.model = QtGui.QStandardItemModel()

            def plotData(self, data_to_plot):
                pass

        class dummy_manager:
            def __init__(self):
                self.filesWidget = MainWindow()

            def communicator(self):
                return GuiUtils.Communicate()

            def communicate(self):
                return GuiUtils.Communicate()

            def createGuiData(self, data_to_plot):
                # Pass data back - testing module - production createGuiData returns a QStandardItem
                return data_to_plot

        w = InvariantWindow(dummy_manager())
        # Real data taken from src/sas/sasview/test/id_data/AOT_Microemulsion-Core_Contrast.xml
        # Using hard-coded data to limit sascalc imports in gui tests
        self.data = Data1D(
            x=[0.009, 0.011, 0.013, 0.015, 0.017, 0.019, 0.021, 0.023, 0.025, 0.027, 0.029, 0.031, 0.033, 0.035, 0.037,
               0.039, 0.041, 0.043, 0.045, 0.047, 0.049, 0.051, 0.053, 0.055, 0.057, 0.059, 0.061, 0.063, 0.065, 0.067,
               0.069, 0.071, 0.073, 0.075, 0.077, 0.079, 0.081, 0.083, 0.085, 0.087, 0.089, 0.091, 0.093, 0.095, 0.097,
               0.099, 0.101, 0.103, 0.105, 0.107, 0.109, 0.111, 0.113, 0.115, 0.117, 0.119, 0.121, 0.123, 0.125, 0.127,
               0.129, 0.131, 0.133, 0.135, 0.137, 0.139, 0.141, 0.143, 0.145, 0.147, 0.149, 0.151, 0.153, 0.155, 0.157,
               0.159, 0.161, 0.163, 0.165, 0.167, 0.169, 0.171, 0.173, 0.175, 0.177, 0.179, 0.181, 0.183, 0.185, 0.187,
               0.189, 0.191, 0.193, 0.195, 0.197, 0.199, 0.201, 0.203, 0.205, 0.207, 0.209, 0.211, 0.213, 0.215, 0.217,
               0.219, 0.221, 0.223, 0.225, 0.227, 0.229, 0.231, 0.233, 0.235, 0.237, 0.239, 0.241, 0.243, 0.245, 0.247,
               0.249, 0.251, 0.253, 0.255, 0.257, 0.259, 0.261, 0.263, 0.265, 0.267, 0.269, 0.271, 0.273, 0.275, 0.277,
               0.279, 0.281],
            y=[8.66097, 9.07765, 8.74335, 8.97573, 8.01969, 8.50362, 8.21644, 8.5445, 8.25839, 8.385, 8.19833, 8.174,
               8.10893, 7.90257, 7.92779, 7.77999, 7.55967, 7.73146, 7.64145, 7.43904, 7.26281, 7.10242, 6.98253,
               6.83064, 6.53401, 6.27756, 6.01229, 5.99131, 5.59393, 5.51664, 5.19822, 4.69725, 4.52997, 4.36966,
               4.01681, 3.84049, 3.5466, 3.37086, 3.1624, 3.06238, 2.76881, 2.56018, 2.29906, 2.28571, 1.97973, 1.91372,
               1.72878, 1.63685, 1.45134, 1.43389, 1.29589, 1.09998, 1.0428, 0.844519, 0.85536, 0.739303, 0.631377,
               0.559972, 0.633137, 0.52837, 0.486401, 0.502888, 0.461518, 0.33547, 0.331639, 0.349024, 0.249295,
               0.297506, 0.251353, 0.236603, 0.278925, 0.16754, 0.212138, 0.123197, 0.151296, 0.145861, 0.107422,
               0.160706, 0.10401, 0.0695233, 0.0858619, 0.0557327, 0.185915, 0.0549312, 0.0743549, 0.0841899, 0.0192474,
               0.175221, 0.0693162, 0.00162097, 0.220803, 0.0846662, 0.0384855, 0.0520236, 0.0679774, -0.0879282,
               0.00403708, -0.00827498, -0.00896538, 0.0221027, -0.0835404, -0.0781585, 0.0794712, -0.0727371, 0.098657,
               0.0987721, 0.122134, -0.030629, 0.0393085, -0.0782109, 0.0317806, 0.029647, -0.0138577, -0.188901,
               0.0535632, -0.0459497, 0.113408, 0.220107, -0.118426, -0.141306, 0.016238, 0.113952, 0.0471965,
               -0.0771868, -0.493606, -0.15584, 0.21327, -0.407363, -0.280523, -0.466429, -0.530037, -0.478568,
               0.128986, -0.291653, 1.73235, -0.896776, -0.75682],
            dy=[0.678276, 0.415207, 0.33303, 0.266251, 0.229252, 0.207062, 0.187379, 0.17513, 0.163151, 0.156304,
                0.14797, 0.143222, 0.138323, 0.133951, 0.13133, 0.126702, 0.123018, 0.120643, 0.117301, 0.113626,
                0.110662, 0.107456, 0.105039, 0.103433, 0.100548, 0.0989847, 0.0968156, 0.095656, 0.0937742, 0.0925144,
                0.0908407, 0.0888284, 0.0873638, 0.0868543, 0.085489, 0.0837383, 0.0834827, 0.0826536, 0.0812838,
                0.0807788, 0.079466, 0.0768171, 0.0760352, 0.0758398, 0.0727553, 0.0721901, 0.0718478, 0.069903,
                0.0699271, 0.0696514, 0.0676085, 0.06646, 0.0660002, 0.065734, 0.0646517, 0.0656619, 0.0647612,
                0.0637924, 0.0642538, 0.0629895, 0.0639606, 0.0637953, 0.0652337, 0.0649452, 0.0641606, 0.0647814,
                0.0651144, 0.0648872, 0.0646956, 0.0653164, 0.0663626, 0.0658608, 0.0679627, 0.0683039, 0.0692465,
                0.0684029, 0.0707, 0.0705329, 0.0710867, 0.0731431, 0.0735345, 0.0754963, 0.0760707, 0.0753411,
                0.0797642, 0.0805604, 0.0829111, 0.0832278, 0.0839577, 0.0854591, 0.0887341, 0.0923975, 0.0915219,
                0.0950556, 0.0976872, 0.0995643, 0.0999596, 0.105209, 0.10344, 0.111867, 0.116788, 0.114219, 0.122584,
                0.126881, 0.131794, 0.130641, 0.139389, 0.141378, 0.149533, 0.153647, 0.1576, 0.163981, 0.179607,
                0.169998, 0.182096, 0.19544, 0.208226, 0.20631, 0.211599, 0.261127, 0.248377, 0.268117, 0.248487,
                0.30063, 0.311092, 0.307792, 0.346191, 0.433197, 0.425931, 0.432325, 0.415476, 0.458327, 0.501942,
                0.526654, 0.671965, 0.605943, 0.772724])
        mocker.patch.object(GuiUtils, 'dataFromItem', return_value=self.data)
        self.fakeData = QtGui.QStandardItem("test")

        yield w

        """Destroy the DataOperationUtility"""
        w.setClosable(True)
        w.close()

    def testDefaults(self, widget):
        """Test the GUI in its default state"""

        assert isinstance(widget, QtWidgets.QDialog)
        assert isinstance(widget.model, QtGui.QStandardItemModel)

        # name for displaying in the DataExplorer combo box
        assert widget.name == "Invariant"
        assert widget.windowTitle() == "Invariant Perspective"
        assert widget.title == widget.windowTitle()

        assert widget._data is None
        assert widget._path == ''

        self.checkControlDefaults(widget)

        # content of line edits
        assert widget.txtName.text() == ''
        assert widget.txtTotalQMin.text() == '0.0'
        assert widget.txtTotalQMax.text() == '0.0'
        assert widget.txtBackgd.text() == '0.0'
        assert widget.txtScale.text() == '1.0'
        assert widget.txtContrast.text() == '8e-06'
        assert widget.txtExtrapolQMin.text() == '1e-05'
        assert widget.txtExtrapolQMax.text() == '10'
        assert widget.txtPowerLowQ.text() == '4'
        assert widget.txtPowerHighQ.text() == '4'

        # number of tabs
        assert widget.tabWidget.count() == 2
        # default tab
        assert widget.tabWidget.currentIndex() == 0
        # tab's title
        assert widget.tabWidget.tabText(0) == 'Invariant'
        assert widget.tabWidget.tabText(1) == 'Options'

        # Tooltips
        assert widget.cmdStatus.toolTip() == \
                         "Get more details of computation such as fraction from extrapolation"
        assert widget.txtInvariantTot.toolTip() == "Total invariant [Q*], including extrapolated regions."
        assert widget.txtExtrapolQMin.toolTip() == "The minimum extrapolated q value."
        assert widget.txtPowerHighQ.toolTip() == "Exponent to apply to the Power_law function."
        assert widget.txtNptsHighQ.toolTip() == \
                         "Number of Q points to consider\n while extrapolating the high-Q region"
        assert widget.chkHighQ.toolTip() == "Check to extrapolate data at high-Q"
        assert widget.txtNptsLowQ.toolTip() == \
                         "Number of Q points to consider\nwhile extrapolating the low-Q region"
        assert widget.chkLowQ.toolTip() == "Check to extrapolate data at low-Q"
        assert widget.cmdCalculate.toolTip() == "Compute invariant"
        assert widget.txtPowerLowQ.toolTip() == "Exponent to apply to the Power_law function."

        # Validators
        assert isinstance(widget.txtNptsLowQ.validator(), QtGui.QIntValidator)
        assert isinstance(widget.txtNptsHighQ.validator(), QtGui.QIntValidator)
        assert isinstance(widget.txtExtrapolQMin.validator(), GuiUtils.DoubleValidator)
        assert isinstance(widget.txtExtrapolQMax.validator(), GuiUtils.DoubleValidator)
        assert isinstance(widget.txtPowerLowQ.validator(), GuiUtils.DoubleValidator)
        assert isinstance(widget.txtPowerHighQ.validator(), GuiUtils.DoubleValidator)
        assert isinstance(widget.txtBackgd.validator(), GuiUtils.DoubleValidator)
        assert isinstance(widget.txtContrast.validator(), GuiUtils.DoubleValidator)
        assert isinstance(widget.txtScale.validator(), GuiUtils.DoubleValidator)
        assert isinstance(widget.txtPorodCst.validator(), GuiUtils.DoubleValidator)

    def checkControlDefaults(self, widget):
        # All values in this list should assert to False
        false_list = [
            widget._allow_close, widget.allowBatch(),
            # disabled buttons
            widget.cmdStatus.isEnabled(), widget.cmdCalculate.isEnabled(),
            # read only text boxes
            widget.txtBackgd.isReadOnly(), widget.txtScale.isReadOnly(), widget.txtContrast.isReadOnly(),
            widget.txtPorodCst.isReadOnly(), widget.txtNptsLowQ.isReadOnly(),
            widget.txtNptsHighQ.isReadOnly(), widget.txtName.isEnabled(),
            widget.txtExtrapolQMin.isReadOnly(), widget.txtExtrapolQMax.isReadOnly(),
            # unchecked check boxes
            widget.chkLowQ.isChecked(), widget.chkHighQ.isChecked(),
            # radio buttons exclusivity
            widget.rbGuinier.autoExclusive(), widget.rbPowerLawLowQ.autoExclusive()
            ]
        # All values in this list should assert to True
        true_list = [
            # Enable buttons
            widget.txtExtrapolQMax.isEnabled(), widget.txtExtrapolQMin.isEnabled(),
            # enabled text boxes
            widget.txtVolFract.isReadOnly(), widget.txtVolFractErr.isReadOnly(),
            widget.txtSpecSurf.isReadOnly(), widget.txtSpecSurfErr.isReadOnly(),
            widget.txtInvariantTot.isReadOnly(), widget.txtInvariantTotErr.isReadOnly(),
            # radio buttons exclusivity
            widget.rbFixLowQ.autoExclusive(), widget.rbFitLowQ.autoExclusive(),
            widget.rbFixHighQ.autoExclusive(), widget.rbFitHighQ.autoExclusive()
            ]
        assert all(v is False for v in false_list)
        assert all(v is True for v in true_list)

    def testOnCalculate(self, widget, mocker):
        """ Test onCompute function """
        mocker.patch.object(widget, 'calculateInvariant')
        widget.cmdCalculate.setEnabled(True)
        QTest.mouseClick(widget.cmdCalculate, Qt.LeftButton)
        assert widget.calculateInvariant.called_once()

    def testCalculateInvariant(self, widget, mocker):
        """ """
        mocker.patch.object(threads, 'deferToThread')
        widget.calculateInvariant()
        assert threads.deferToThread.called
        assert threads.deferToThread.call_args_list[0][0][0].__name__ == 'calculateThread'

        assert widget.cmdCalculate.text() == 'Calculating...'
        assert not widget.cmdCalculate.isEnabled()

    def testUpdateFromModel(self, widget):
        """
        update the globals based on the data in the model
        """
        widget.updateFromModel()
        assert widget._background == float(widget.model.item(WIDGETS.W_BACKGROUND).text())
        assert widget._contrast == float(widget.model.item(WIDGETS.W_CONTRAST).text())
        assert widget._scale == float(widget.model.item(WIDGETS.W_SCALE).text())
        assert widget._low_extrapolate == \
                         (str(widget.model.item(WIDGETS.W_ENABLE_LOWQ).text()) == 'true')
        assert widget._low_points == float(widget.model.item(WIDGETS.W_NPTS_LOWQ).text())
        assert widget._low_guinier == (str(widget.model.item(WIDGETS.W_LOWQ_GUINIER).text()) == 'true')
        assert widget._low_fit == (str(widget.model.item(WIDGETS.W_LOWQ_FIT).text()) == 'true')
        assert widget._low_power_value == float(widget.model.item(WIDGETS.W_LOWQ_POWER_VALUE).text())
        assert widget._high_extrapolate == \
                         (str(widget.model.item(WIDGETS.W_ENABLE_HIGHQ).text()) == 'true')
        assert widget._high_points == float(widget.model.item(WIDGETS.W_NPTS_HIGHQ).text())
        assert widget._high_fit == (str(widget.model.item(WIDGETS.W_HIGHQ_FIT).text()) == 'true')
        assert widget._high_power_value == \
                         float(widget.model.item(WIDGETS.W_HIGHQ_POWER_VALUE).text())

    def testCheckLength(self, widget, mocker):
        """
        Test validator for number of points for extrapolation
         Error if it is larger than the distribution length
        """
        mocker.patch.object(logging, 'warning')
        widget.txtNptsLowQ.setEnabled(True)

        widget.setData([self.fakeData])
        # Set number of points to 1 larger than the data
        widget.txtNptsLowQ.setText(str(len(self.data.x) + 1))

        BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'
        # Ensure a warning is issued in the GUI that the number of points is too large
        assert BG_COLOR_ERR in widget.txtNptsLowQ.styleSheet()
        assert logging.warning.called_once_with()
        assert not widget.cmdCalculate.isEnabled()

    def testExtrapolationQRange(self, widget):
        """
        Test changing the extrapolated Q-range
        """
        # Set values to invalid points and be sure the calculation cannot be run
        widget.txtNptsLowQ.setText('4')
        widget.txtNptsHighQ.setText('4')
        widget.txtExtrapolQMin.setText('0.8')
        widget.txtExtrapolQMax.setText('0.2')
        widget.setData([self.fakeData])
        assert not widget.cmdCalculate.isEnabled()
        # Set Qmin to a valid value, but leave Qmax invalid - should not be able to calculate
        widget.txtExtrapolQMin.setText('0.001')
        assert not widget.cmdCalculate.isEnabled()
        # Set Qmax to a valid value - calculation should now be possible
        widget.txtExtrapolQMax.setText('100.0')
        assert widget.cmdCalculate.isEnabled()

    def testUpdateFromGui(self, widget):
        """ """
        widget.txtBackgd.setText('0.22')
        assert str(widget.model.item(WIDGETS.W_BACKGROUND).text()) == '0.22'

    def testLowGuinierAndPowerToggle(self, widget):
        """ """
        # enable all tested radiobuttons
        widget.rbGuinier.setEnabled(True)
        widget.rbPowerLawLowQ.setEnabled(True)
        widget.txtNptsLowQ.setEnabled(True)
        # record initial status
        status_ini = widget.rbGuinier.isChecked()
        # mouse click to run function
        QTest.mouseClick(widget.rbGuinier, Qt.LeftButton)
        # check that status changed
        assert widget.rbGuinier.isChecked() != status_ini
        status_fin = widget.rbGuinier.isChecked()
        assert widget.rbPowerLawLowQ.isChecked() == (not status_fin)
        assert widget.txtPowerLowQ.isEnabled() == \
                         all([not status_fin, not widget._low_fit])

    def testHighQToggle(self, widget):
        """ Test enabling / disabling for check box High Q extrapolation """
        widget.chkHighQ.setChecked(True)
        assert widget.chkHighQ.isChecked()
        # Check base state when high Q fit toggled
        assert widget.rbFitHighQ.isChecked()
        assert not widget.rbFixHighQ.isChecked()
        assert widget.rbFitHighQ.isEnabled()
        assert widget.rbFixHighQ.isEnabled()
        assert widget.txtNptsHighQ.isEnabled()
        assert not widget.txtPowerHighQ.isEnabled()
        # Toggle between fit and fix
        widget.rbFixHighQ.setChecked(True)
        assert not widget.rbFitHighQ.isChecked()
        assert widget.rbFixHighQ.isChecked()
        assert widget.txtPowerHighQ.isEnabled()
        # Change value and be sure model updates
        widget.txtPowerHighQ.setText("11")
        assert widget.model.item(WIDGETS.W_HIGHQ_POWER_VALUE).text() == '11'
        # Check Qmax of plot
        widget.txtExtrapolQMax.setText('100')
        assert widget.txtExtrapolQMax.text() == '100'
        # Run the calculation
        widget.setData([self.fakeData])
        widget.calculateThread('high')
        # Ensure the extrapolation plot is generated
        assert widget.high_extrapolation_plot is not None
        # Ensure Qmax for the plot is equal to Qmax entered into the extrapolation limits
        assert max(widget.high_extrapolation_plot.x) == pytest.approx(100.0, abs=1e-7)
        # Ensure radio buttons unchanged
        assert not widget.rbFitHighQ.isChecked()
        assert widget.rbFixHighQ.isChecked()
        assert widget.txtPowerHighQ.text() == '11'

    def testLowQToggle(self, widget):
        """ Test enabling / disabling for check box Low Q extrapolation """
        widget.chkLowQ.setChecked(True)
        status_chkLowQ = widget.chkLowQ.isChecked()
        assert status_chkLowQ
        # Check base state
        assert widget.rbGuinier.isEnabled()
        assert widget.rbPowerLawLowQ.isEnabled()
        assert widget.txtNptsLowQ.isEnabled()
        assert widget.rbFitLowQ.isEnabled()
        assert widget.rbFixLowQ.isEnabled()
        assert widget.rbGuinier.isChecked()
        assert widget.rbFitLowQ.isChecked()
        # Click the Power Law radio button
        widget.rbPowerLawLowQ.setChecked(True)
        assert not widget.rbGuinier.isChecked()
        assert widget.rbFitLowQ.isChecked()
        assert not widget.txtPowerLowQ.isEnabled()
        # Return to the Guinier
        widget.rbGuinier.setChecked(True)
        assert widget.txtNptsLowQ.isEnabled() == \
                         all([status_chkLowQ, widget._low_guinier, widget._low_fit])

        widget.calculateInvariant()
        # Ensure radio buttons unchanged
        assert widget.rbGuinier.isChecked()
        assert widget.rbFitLowQ.isChecked()

    def testSetupModel(self, widget):
        """ Test default settings of model"""

        assert widget.model.item(WIDGETS.W_NAME).text() == widget._path
        assert widget.model.item(WIDGETS.W_QMIN).text() == '0.0'
        assert widget.model.item(WIDGETS.W_QMAX).text() == '0.0'
        assert widget.model.item(WIDGETS.W_BACKGROUND).text() == str(widget._background)
        assert widget.model.item(WIDGETS.W_CONTRAST).text() == str(widget._contrast)
        assert widget.model.item(WIDGETS.W_SCALE).text() == str(widget._scale)
        assert str(widget.model.item(WIDGETS.W_POROD_CST).text()) in ['', str(widget._porod)]

        assert str(widget.model.item(WIDGETS.W_ENABLE_HIGHQ).text()).lower() == 'false'
        assert str(widget.model.item(WIDGETS.W_ENABLE_LOWQ).text()).lower() == 'false'
        assert str(widget.model.item(WIDGETS.W_LOWQ_GUINIER).text()).lower() == 'true'
        assert str(widget.model.item(WIDGETS.W_LOWQ_FIT).text()).lower() == 'true'
        assert str(widget.model.item(WIDGETS.W_HIGHQ_FIT).text()).lower() == 'true'

        assert str(widget.model.item(WIDGETS.W_NPTS_LOWQ).text()) == str(10)
        assert widget.model.item(WIDGETS.W_NPTS_HIGHQ).text() == str(10)
        assert str(widget.model.item(WIDGETS.W_LOWQ_POWER_VALUE).text()) == '4'
        assert str(widget.model.item(WIDGETS.W_HIGHQ_POWER_VALUE).text()) == '4'

    def testSetupMapper(self, widget):
        """ """
        assert isinstance(widget.mapper, QtWidgets.QDataWidgetMapper)
        assert widget.mapper.orientation() == 2
        assert widget.mapper.model() == widget.model

    def testSerialization(self, widget):
        """ Serialization routines """
        assert hasattr(widget, 'isSerializable')
        assert widget.isSerializable()
        widget.setData([self.fakeData])
        self.checkFakeDataState(widget)
        data_return = GuiUtils.dataFromItem(widget._model_item)
        data_id = str(data_return.id)
        # Test three separate serialization routines
        state_all = widget.serializeAll()
        state_one = widget.serializeCurrentPage()
        page = widget.getPage()
        # Pull out params from state
        params = state_all[data_id]['invar_params']
        # Tests
        assert len(state_all) == len(state_one)
        assert len(state_all) == 1
        # getPage should include an extra param 'data_id' removed by serialize
        assert len(params) != len(page)
        assert len(params) == 24
        assert len(page) == 25

    def testLoadParams(self, widget):
        widget.setData([self.fakeData])
        self.checkFakeDataState(widget)
        pageState = widget.getPage()
        widget.updateFromParameters(pageState)
        self.checkFakeDataState(widget)
        widget.removeData([self.fakeData])
        self.checkControlDefaults(widget)

    def testRemoveData(self, widget):
        widget.setData([self.fakeData])
        self.checkFakeDataState(widget)
        # Removing something not already in the perspective should do nothing
        widget.removeData([])
        self.checkFakeDataState(widget)
        # Be sure the defaults hold true after data removal
        widget.removeData([self.fakeData])
        self.checkControlDefaults(widget)

    def checkFakeDataState(self, widget):
        """ Ensure the state is constant every time the fake data set loaded """
        assert widget._data is not None

        # push buttons enabled
        assert not widget.cmdStatus.isEnabled()
        assert not widget.cmdCalculate.isEnabled()

        # disabled, read only line edits
        assert not widget.txtName.isEnabled()
        assert widget.txtVolFract.isReadOnly()
        assert widget.txtVolFractErr.isReadOnly()

        assert widget.txtSpecSurf.isReadOnly()
        assert widget.txtSpecSurfErr.isReadOnly()

        assert widget.txtInvariantTot.isReadOnly()
        assert widget.txtInvariantTotErr.isReadOnly()

        assert not widget.txtBackgd.isReadOnly()
        assert not widget.txtScale.isReadOnly()
        assert not widget.txtContrast.isReadOnly()
        assert not widget.txtPorodCst.isReadOnly()

        assert widget.txtExtrapolQMin.isEnabled()
        assert widget.txtExtrapolQMax.isEnabled()

        assert not widget.txtNptsLowQ.isReadOnly()
        assert not widget.txtNptsHighQ.isReadOnly()

        assert widget.txtTotalQMin.isReadOnly()
        assert widget.txtTotalQMax.isReadOnly()

        # content of line edits
        assert widget.txtName.text() == 'data'
        assert widget.txtTotalQMin.text() == '0.009'
        assert widget.txtTotalQMax.text() == '0.281'
        assert widget.txtBackgd.text() == '0.0'
        assert widget.txtScale.text() == '1.0'
        assert widget.txtContrast.text() == '8e-06'
        assert widget.txtExtrapolQMin.text() == '1e-05'
        assert widget.txtExtrapolQMax.text() == '10'
        assert widget.txtPowerLowQ.text() == '4'
        assert widget.txtPowerHighQ.text() == '4'

        # unchecked checkboxes
        assert not widget.chkLowQ.isChecked()
        assert not widget.chkHighQ.isChecked()
