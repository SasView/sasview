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

        self.widget = InvariantWindow(dummy_manager())
        data = Data1D(
            x=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            y=[10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
            dy=[0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01])
        GuiUtils.dataFromItem = MagicMock(return_value=data)
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
        self.widget.txtNptsLowQ.setText('25')

        BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'
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
        # Run the calculation
        self.widget.calculateInvariant()
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

        # content of line edits
        self.assertEqual(self.widget.txtName.text(), 'data')
        self.assertEqual(self.widget.txtTotalQMin.text(), '0.1')
        self.assertEqual(self.widget.txtTotalQMax.text(), '1.0')
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
