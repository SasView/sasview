import sys
import logging
import unittest
from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock
from unittest.mock import create_autospec

from twisted.internet import threads

from sas.qtgui.Perspectives.Invariant.InvariantPerspective import InvariantWindow
from sas.qtgui.Perspectives.Invariant.InvariantDetails import DetailsDialog
from sas.qtgui.Perspectives.Invariant.InvariantUtils import WIDGETS
from sas.qtgui.Plotting.PlotterData import Data1D

import sas.qtgui.Utilities.GuiUtils as GuiUtils

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'


class InvariantPerspectiveTest(unittest.TestCase):
    """Test the Invariant Perspective Window"""
    def setUp(self):
        """Create the Invariant Perspective Window"""

        class MainWindow(object):
            def __init__(self):
                self.model = QtGui.QStandardItemModel()

            def plotData(self, data_to_plot):
                pass

        class dummy_manager(object):
            def __init__(self):
                self.filesWidget = MainWindow()

            def communicator(self):
                return GuiUtils.Communicate()

            def communicate(self):
                return GuiUtils.Communicate()

            def createGuiData(self, data_to_plot):
                # Pass data back - testing module - production createGuiData returns a QStandardItem
                return data_to_plot

        self.widget = InvariantWindow(dummy_manager())
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
        GuiUtils.dataFromItem = MagicMock(return_value=self.data)
        self.fakeData = QtGui.QStandardItem("test")

    def tearDown(self):
        """Destroy the DataOperationUtility"""
        self.widget.setClosable(True)
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        """Test the GUI in its default state"""

        self.assertIsInstance(self.widget, QtWidgets.QDialog)
        self.assertIsInstance(self.widget.model, QtGui.QStandardItemModel)

        # name for displaying in the DataExplorer combo box
        self.assertEqual(self.widget.name, "Invariant")
        self.assertEqual(self.widget.windowTitle(), "Invariant Perspective")
        self.assertEqual(self.widget.title(), self.widget.windowTitle())

        self.assertIsNone(self.widget._data)
        self.assertEqual(self.widget._path, '')

        self.checkControlDefaults()

        # content of line edits
        self.assertEqual(self.widget.txtName.text(), '')
        self.assertEqual(self.widget.txtTotalQMin.text(), '0.0')
        self.assertEqual(self.widget.txtTotalQMax.text(), '0.0')
        self.assertEqual(self.widget.txtBackgd.text(), '0.0')
        self.assertEqual(self.widget.txtScale.text(), '1.0')
        self.assertEqual(self.widget.txtContrast.text(), '8e-06')
        self.assertEqual(self.widget.txtExtrapolQMin.text(), '1e-05')
        self.assertEqual(self.widget.txtExtrapolQMax.text(), '10')
        self.assertEqual(self.widget.txtPowerLowQ.text(), '4')
        self.assertEqual(self.widget.txtPowerHighQ.text(), '4')

        # number of tabs
        self.assertEqual(self.widget.tabWidget.count(), 2)
        # default tab
        self.assertEqual(self.widget.tabWidget.currentIndex(), 0)
        # tab's title
        self.assertEqual(self.widget.tabWidget.tabText(0), 'Invariant')
        self.assertEqual(self.widget.tabWidget.tabText(1), 'Options')

        # Tooltips
        self.assertEqual(self.widget.cmdStatus.toolTip(),
                         "Get more details of computation such as fraction from extrapolation" )
        self.assertEqual(self.widget.txtInvariantTot.toolTip(), "Total invariant [Q*], including extrapolated regions.")
        self.assertEqual(self.widget.txtExtrapolQMin.toolTip(), "The minimum extrapolated q value.")
        self.assertEqual(self.widget.txtPowerHighQ.toolTip(), "Exponent to apply to the Power_law function.")
        self.assertEqual(self.widget.txtNptsHighQ.toolTip(),
                         "Number of Q points to consider\n while extrapolating the high-Q region")
        self.assertEqual(self.widget.chkHighQ.toolTip(), "Check to extrapolate data at high-Q")
        self.assertEqual(self.widget.txtNptsLowQ.toolTip(),
                         "Number of Q points to consider\nwhile extrapolating the low-Q region")
        self.assertEqual(self.widget.chkLowQ.toolTip(), "Check to extrapolate data at low-Q")
        self.assertEqual(self.widget.cmdCalculate.toolTip(), "Compute invariant")
        self.assertEqual(self.widget.txtPowerLowQ.toolTip(), "Exponent to apply to the Power_law function." )

        # Validators
        self.assertIsInstance(self.widget.txtNptsLowQ.validator(), QtGui.QIntValidator)
        self.assertIsInstance(self.widget.txtNptsHighQ.validator(), QtGui.QIntValidator)
        self.assertIsInstance(self.widget.txtExtrapolQMin.validator(), GuiUtils.DoubleValidator)
        self.assertIsInstance(self.widget.txtExtrapolQMax.validator(), GuiUtils.DoubleValidator)
        self.assertIsInstance(self.widget.txtPowerLowQ.validator(), GuiUtils.DoubleValidator)
        self.assertIsInstance(self.widget.txtPowerHighQ.validator(), GuiUtils.DoubleValidator)
        self.assertIsInstance(self.widget.txtBackgd.validator(), GuiUtils.DoubleValidator)
        self.assertIsInstance(self.widget.txtContrast.validator(), GuiUtils.DoubleValidator)
        self.assertIsInstance(self.widget.txtScale.validator(), GuiUtils.DoubleValidator)
        self.assertIsInstance(self.widget.txtPorodCst.validator(), GuiUtils.DoubleValidator)

    def checkControlDefaults(self):
        # All values in this list should assert to False
        false_list = [
            self.widget._allow_close, self.widget.allowBatch(),
            # disabled buttons
            self.widget.cmdStatus.isEnabled(), self.widget.cmdCalculate.isEnabled(),
            # read only text boxes
            self.widget.txtBackgd.isReadOnly(), self.widget.txtScale.isReadOnly(), self.widget.txtContrast.isReadOnly(),
            self.widget.txtPorodCst.isReadOnly(), self.widget.txtNptsLowQ.isReadOnly(),
            self.widget.txtNptsHighQ.isReadOnly(), self.widget.txtName.isEnabled(),
            self.widget.txtExtrapolQMin.isReadOnly(), self.widget.txtExtrapolQMax.isReadOnly(),
            # unchecked check boxes
            self.widget.chkLowQ.isChecked(), self.widget.chkHighQ.isChecked(),
            # radio buttons exclusivity
            self.widget.rbGuinier.autoExclusive(), self.widget.rbPowerLawLowQ.autoExclusive()
            ]
        # All values in this list should assert to True
        true_list = [
            # Enable buttons
            self.widget.txtExtrapolQMax.isEnabled(), self.widget.txtExtrapolQMin.isEnabled(),
            # enabled text boxes
            self.widget.txtVolFract.isReadOnly(), self.widget.txtVolFractErr.isReadOnly(),
            self.widget.txtSpecSurf.isReadOnly(), self.widget.txtSpecSurfErr.isReadOnly(),
            self.widget.txtInvariantTot.isReadOnly(), self.widget.txtInvariantTotErr.isReadOnly(),
            # radio buttons exclusivity
            self.widget.rbFixLowQ.autoExclusive(), self.widget.rbFitLowQ.autoExclusive(),
            self.widget.rbFixHighQ.autoExclusive(), self.widget.rbFitHighQ.autoExclusive()
            ]
        self.assertTrue(all(v is False for v in false_list))
        self.assertTrue(all(v is True for v in true_list))

    def testOnCalculate(self):
        """ Test onCompute function """
        self.widget.calculateInvariant = MagicMock()
        self.widget.cmdCalculate.setEnabled(True)
        QTest.mouseClick(self.widget.cmdCalculate, Qt.LeftButton)
        self.assertTrue(self.widget.calculateInvariant.called_once())

    def testCalculateInvariant(self):
        """ """
        threads.deferToThread = MagicMock()
        self.widget.calculateInvariant()
        self.assertTrue(threads.deferToThread.called)
        self.assertEqual(threads.deferToThread.call_args_list[0][0][0].__name__, 'calculateThread')

        self.assertEqual(self.widget.cmdCalculate.text(), 'Calculating...')
        self.assertFalse(self.widget.cmdCalculate.isEnabled())

    def testUpdateFromModel(self):
        """
        update the globals based on the data in the model
        """
        self.widget.updateFromModel()
        self.assertEqual(self.widget._background, float(self.widget.model.item(WIDGETS.W_BACKGROUND).text()))
        self.assertEqual(self.widget._contrast, float(self.widget.model.item(WIDGETS.W_CONTRAST).text()))
        self.assertEqual(self.widget._scale, float(self.widget.model.item(WIDGETS.W_SCALE).text()))
        self.assertEqual(self.widget._low_extrapolate,
                         str(self.widget.model.item(WIDGETS.W_ENABLE_LOWQ).text()) == 'true')
        self.assertEqual(self.widget._low_points, float(self.widget.model.item(WIDGETS.W_NPTS_LOWQ).text()))
        self.assertEqual(self.widget._low_guinier, str(self.widget.model.item(WIDGETS.W_LOWQ_GUINIER).text()) == 'true' )
        self.assertEqual(self.widget._low_fit,str(self.widget.model.item(WIDGETS.W_LOWQ_FIT).text()) == 'true')
        self.assertEqual(self.widget._low_power_value, float(self.widget.model.item(WIDGETS.W_LOWQ_POWER_VALUE).text()))
        self.assertEqual(self.widget._high_extrapolate,
                         str(self.widget.model.item(WIDGETS.W_ENABLE_HIGHQ).text()) == 'true')
        self.assertEqual(self.widget._high_points, float(self.widget.model.item(WIDGETS.W_NPTS_HIGHQ).text()))
        self.assertEqual(self.widget._high_fit, str(self.widget.model.item(WIDGETS.W_HIGHQ_FIT).text()) == 'true')
        self.assertEqual(self.widget._high_power_value,
                         float(self.widget.model.item(WIDGETS.W_HIGHQ_POWER_VALUE).text()))

    def testCheckLength(self):
        """
        Test validator for number of points for extrapolation
         Error if it is larger than the distribution length
        """
        logging.warning = MagicMock()
        self.widget.txtNptsLowQ.setEnabled(True)

        self.widget.setData([self.fakeData])
        # Set number of points to 1 larger than the data
        self.widget.txtNptsLowQ.setText(str(len(self.data.x) + 1))

        BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'
        # Ensure a warning is issued in the GUI that the number of points is too large
        self.assertIn(BG_COLOR_ERR, self.widget.txtNptsLowQ.styleSheet())
        self.assertTrue(logging.warning.called_once_with())
        self.assertFalse(self.widget.cmdCalculate.isEnabled())

    def testExtrapolationQRange(self):
        """
        Test changing the extrapolated Q-range
        """
        # Set values to invalid points and be sure the calculation cannot be run
        self.widget.txtNptsLowQ.setText('4')
        self.widget.txtNptsHighQ.setText('4')
        self.widget.txtExtrapolQMin.setText('0.8')
        self.widget.txtExtrapolQMax.setText('0.2')
        self.widget.setData([self.fakeData])
        self.assertFalse(self.widget.cmdCalculate.isEnabled())
        # Set Qmin to a valid value, but leave Qmax invalid - should not be able to calculate
        self.widget.txtExtrapolQMin.setText('0.001')
        self.assertFalse(self.widget.cmdCalculate.isEnabled())
        # Set Qmax to a valid value - calculation should now be possible
        self.widget.txtExtrapolQMax.setText('100.0')
        self.assertTrue(self.widget.cmdCalculate.isEnabled())

    def testUpdateFromGui(self):
        """ """
        self.widget.txtBackgd.setText('0.22')
        self.assertEqual(str(self.widget.model.item(WIDGETS.W_BACKGROUND).text()), '0.22')

    def testLowGuinierAndPowerToggle(self):
        """ """
        # enable all tested radiobuttons
        self.widget.rbGuinier.setEnabled(True)
        self.widget.rbPowerLawLowQ.setEnabled(True)
        self.widget.txtNptsLowQ.setEnabled(True)
        # record initial status
        status_ini = self.widget.rbGuinier.isChecked()
        # mouse click to run function
        QTest.mouseClick(self.widget.rbGuinier, Qt.LeftButton)
        # check that status changed
        self.assertNotEqual(self.widget.rbGuinier.isChecked(), status_ini)
        status_fin = self.widget.rbGuinier.isChecked()
        self.assertEqual(self.widget.rbPowerLawLowQ.isChecked(), not status_fin)
        self.assertEqual(self.widget.txtPowerLowQ.isEnabled(),
                         all([not status_fin, not self.widget._low_fit]))

    def testHighQToggle(self):
        """ Test enabling / disabling for check box High Q extrapolation """
        self.widget.chkHighQ.setChecked(True)
        self.assertTrue(self.widget.chkHighQ.isChecked())
        # Check base state when high Q fit toggled
        self.assertTrue(self.widget.rbFitHighQ.isChecked())
        self.assertFalse(self.widget.rbFixHighQ.isChecked())
        self.assertTrue(self.widget.rbFitHighQ.isEnabled())
        self.assertTrue(self.widget.rbFixHighQ.isEnabled())
        self.assertTrue(self.widget.txtNptsHighQ.isEnabled())
        self.assertFalse(self.widget.txtPowerHighQ.isEnabled())
        # Toggle between fit and fix
        self.widget.rbFixHighQ.setChecked(True)
        self.assertFalse(self.widget.rbFitHighQ.isChecked())
        self.assertTrue(self.widget.rbFixHighQ.isChecked())
        self.assertTrue(self.widget.txtPowerHighQ.isEnabled())
        # Change value and be sure model updates
        self.widget.txtPowerHighQ.setText("11")
        self.assertEqual(self.widget.model.item(WIDGETS.W_HIGHQ_POWER_VALUE).text(), '11')
        # Check Qmax of plot
        self.widget.txtExtrapolQMax.setText('100')
        self.assertEqual(self.widget.txtExtrapolQMax.text(),'100')
        # Run the calculation
        self.widget.setData([self.fakeData])
        self.widget.calculateThread('high')
        # Ensure the extrapolation plot is generated
        self.assertIsNotNone(self.widget.high_extrapolation_plot)
        # Ensure Qmax for the plot is equal to Qmax entered into the extrapolation limits
        self.assertAlmostEqual(max(self.widget.high_extrapolation_plot.x), 100.0)
        # Ensure radio buttons unchanged
        self.assertFalse(self.widget.rbFitHighQ.isChecked())
        self.assertTrue(self.widget.rbFixHighQ.isChecked())
        self.assertEqual(self.widget.txtPowerHighQ.text(), '11')

    def testLowQToggle(self):
        """ Test enabling / disabling for check box Low Q extrapolation """
        self.widget.chkLowQ.setChecked(True)
        status_chkLowQ = self.widget.chkLowQ.isChecked()
        self.assertTrue(status_chkLowQ)
        # Check base state
        self.assertTrue(self.widget.rbGuinier.isEnabled())
        self.assertTrue(self.widget.rbPowerLawLowQ.isEnabled())
        self.assertTrue(self.widget.txtNptsLowQ.isEnabled())
        self.assertTrue(self.widget.rbFitLowQ.isEnabled())
        self.assertTrue(self.widget.rbFixLowQ.isEnabled())
        self.assertTrue(self.widget.rbGuinier.isChecked())
        self.assertTrue(self.widget.rbFitLowQ.isChecked())
        # Click the Power Law radio button
        self.widget.rbPowerLawLowQ.setChecked(True)
        self.assertFalse(self.widget.rbGuinier.isChecked())
        self.assertTrue(self.widget.rbFitLowQ.isChecked())
        self.assertFalse(self.widget.txtPowerLowQ.isEnabled())
        # Return to the Guinier
        self.widget.rbGuinier.setChecked(True)
        self.assertEqual(self.widget.txtNptsLowQ.isEnabled(),
                         all([status_chkLowQ, self.widget._low_guinier, self.widget._low_fit]))

        self.widget.calculateInvariant()
        # Ensure radio buttons unchanged
        self.assertTrue(self.widget.rbGuinier.isChecked())
        self.assertTrue(self.widget.rbFitLowQ.isChecked())

    def testSetupModel(self):
        """ Test default settings of model"""

        self.assertEqual(self.widget.model.item(WIDGETS.W_NAME).text(), self.widget._path)
        self.assertEqual(self.widget.model.item(WIDGETS.W_QMIN).text(), '0.0')
        self.assertEqual(self.widget.model.item(WIDGETS.W_QMAX).text(), '0.0')
        self.assertEqual(self.widget.model.item(WIDGETS.W_BACKGROUND).text(), str(self.widget._background))
        self.assertEqual(self.widget.model.item(WIDGETS.W_CONTRAST).text(), str(self.widget._contrast))
        self.assertEqual(self.widget.model.item(WIDGETS.W_SCALE).text(), str(self.widget._scale))
        self.assertIn(str(self.widget.model.item(WIDGETS.W_POROD_CST).text()), ['', str(self.widget._porod)])

        self.assertEqual(str(self.widget.model.item(WIDGETS.W_ENABLE_HIGHQ).text()).lower(), 'false')
        self.assertEqual(str(self.widget.model.item(WIDGETS.W_ENABLE_LOWQ).text()).lower(), 'false')
        self.assertEqual(str(self.widget.model.item(WIDGETS.W_LOWQ_GUINIER).text()).lower(), 'true')
        self.assertEqual(str(self.widget.model.item(WIDGETS.W_LOWQ_FIT).text()).lower(), 'true')
        self.assertEqual(str(self.widget.model.item(WIDGETS.W_HIGHQ_FIT).text()).lower(), 'true')

        self.assertEqual(str(self.widget.model.item(WIDGETS.W_NPTS_LOWQ).text()), str(10))
        self.assertEqual(self.widget.model.item(WIDGETS.W_NPTS_HIGHQ).text(), str(10))
        self.assertEqual(str(self.widget.model.item(WIDGETS.W_LOWQ_POWER_VALUE).text()), '4')
        self.assertEqual(str(self.widget.model.item(WIDGETS.W_HIGHQ_POWER_VALUE).text()), '4')

    def testSetupMapper(self):
        """ """
        self.assertIsInstance(self.widget.mapper, QtWidgets.QDataWidgetMapper)
        self.assertEqual(self.widget.mapper.orientation(), 2)
        self.assertEqual(self.widget.mapper.model(), self.widget.model)

    def testSerialization(self):
        """ Serialization routines """
        self.assertTrue(hasattr(self.widget, 'isSerializable'))
        self.assertTrue(self.widget.isSerializable())
        self.widget.setData([self.fakeData])
        self.checkFakeDataState()
        data_return = GuiUtils.dataFromItem(self.widget._model_item)
        data_id = str(data_return.id)
        # Test three separate serialization routines
        state_all = self.widget.serializeAll()
        state_one = self.widget.serializeCurrentPage()
        page = self.widget.getPage()
        # Pull out params from state
        params = state_all[data_id]['invar_params']
        # Tests
        self.assertEqual(len(state_all), len(state_one))
        self.assertEqual(len(state_all), 1)
        # getPage should include an extra param 'data_id' removed by serialize
        self.assertNotEqual(len(params), len(page))
        self.assertEqual(len(params), 24)
        self.assertEqual(len(page), 25)

    def testLoadParams(self):
        self.widget.setData([self.fakeData])
        self.checkFakeDataState()
        pageState = self.widget.getPage()
        self.widget.updateFromParameters(pageState)
        self.checkFakeDataState()
        self.widget.removeData([self.fakeData])
        self.checkControlDefaults()

    def testRemoveData(self):
        self.widget.setData([self.fakeData])
        self.checkFakeDataState()
        # Removing something not already in the perspective should do nothing
        self.widget.removeData([])
        self.checkFakeDataState()
        # Be sure the defaults hold true after data removal
        self.widget.removeData([self.fakeData])
        self.checkControlDefaults()

    def checkFakeDataState(self):
        """ Ensure the state is constant every time the fake data set loaded """
        self.assertIsNotNone(self.widget._data)

        # push buttons enabled
        self.assertFalse(self.widget.cmdStatus.isEnabled())
        self.assertFalse(self.widget.cmdCalculate.isEnabled())

        # disabled, read only line edits
        self.assertFalse(self.widget.txtName.isEnabled())
        self.assertTrue(self.widget.txtVolFract.isReadOnly())
        self.assertTrue(self.widget.txtVolFractErr.isReadOnly())

        self.assertTrue(self.widget.txtSpecSurf.isReadOnly())
        self.assertTrue(self.widget.txtSpecSurfErr.isReadOnly())

        self.assertTrue(self.widget.txtInvariantTot.isReadOnly())
        self.assertTrue(self.widget.txtInvariantTotErr.isReadOnly())

        self.assertFalse(self.widget.txtBackgd.isReadOnly())
        self.assertFalse(self.widget.txtScale.isReadOnly())
        self.assertFalse(self.widget.txtContrast.isReadOnly())
        self.assertFalse(self.widget.txtPorodCst.isReadOnly())

        self.assertTrue(self.widget.txtExtrapolQMin.isEnabled())
        self.assertTrue(self.widget.txtExtrapolQMax.isEnabled())

        self.assertFalse(self.widget.txtNptsLowQ.isReadOnly())
        self.assertFalse(self.widget.txtNptsHighQ.isReadOnly())

        self.assertTrue(self.widget.txtTotalQMin.isReadOnly())
        self.assertTrue(self.widget.txtTotalQMax.isReadOnly())

        # content of line edits
        self.assertEqual(self.widget.txtName.text(), 'data')
        self.assertEqual(self.widget.txtTotalQMin.text(), '0.009')
        self.assertEqual(self.widget.txtTotalQMax.text(), '0.281')
        self.assertEqual(self.widget.txtBackgd.text(), '0.0')
        self.assertEqual(self.widget.txtScale.text(), '1.0')
        self.assertEqual(self.widget.txtContrast.text(), '8e-06')
        self.assertEqual(self.widget.txtExtrapolQMin.text(), '1e-05')
        self.assertEqual(self.widget.txtExtrapolQMax.text(), '10')
        self.assertEqual(self.widget.txtPowerLowQ.text(), '4')
        self.assertEqual(self.widget.txtPowerHighQ.text(), '4')

        # unchecked checkboxes
        self.assertFalse(self.widget.chkLowQ.isChecked())
        self.assertFalse(self.widget.chkHighQ.isChecked())


if __name__ == "__main__":
    unittest.main()
