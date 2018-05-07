import sys
import time
import numpy
import logging
import unittest
from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import create_autospec

from twisted.internet import threads

from sas.qtgui.Perspectives.Invariant.InvariantPerspective import InvariantWindow
from sas.qtgui.Perspectives.Invariant.InvariantDetails import DetailsDialog
from sas.qtgui.Perspectives.Invariant.InvariantUtils import WIDGETS
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.MainWindow.GuiManager import GuiManager
from sas.qtgui.MainWindow.DataExplorer import DataExplorerWindow

import sas.qtgui.Utilities.GuiUtils as GuiUtils

#if not QtWidgets.QApplication.instance():
app = QtWidgets.QApplication(sys.argv)

BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'

class InvariantPerspectiveTest(unittest.TestCase):
    """Test the Invariant Perspective Window"""
    def setUp(self):
        """Create the Invariant Perspective Window"""

        class MainWindow(object):
            def __init__(self):
                self.model = QtGui.QStandardItemModel()

        class dummy_manager(object):
            def __init__(self):
                self.filesWidget = MainWindow()

            def communicator(self):
                return GuiUtils.Communicate()

            def communicate(self):
                return GuiUtils.Communicate()

        self.widget = InvariantWindow(dummy_manager())

    def tearDown(self):
        """Destroy the DataOperationUtility"""
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        """Test the GUI in its default state"""

        self.assertIsInstance(self.widget, QtWidgets.QDialog)

        self.assertEqual(self.widget.windowTitle(), "Invariant Perspective")

        # name for displaying in the DataExplorer combo box
        self.assertEqual(self.widget.name, "Invariant")

        self.assertIsInstance(self.widget.model, QtGui.QStandardItemModel)

        self.assertIsNone(self.widget._data)
        self.assertEqual(self.widget._path, '')
        self.assertFalse(self.widget._allow_close)

        # disabled pushbuttons
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
        self.assertEqual(self.widget.txtName.text(), '')
        self.assertEqual(self.widget.txtTotalQMin.text(), '0.0')
        self.assertEqual(self.widget.txtTotalQMax.text(), '0.0')
        self.assertEqual(self.widget.txtBackgd.text(), '0.0')
        self.assertEqual(self.widget.txtScale.text(), '1.0')
        self.assertEqual(self.widget.txtContrast.text(), '1.0')
        self.assertEqual(self.widget.txtExtrapolQMin.text(), '1e-05')
        self.assertEqual(self.widget.txtExtrapolQMax.text(), '10')
        self.assertEqual(self.widget.txtPowerLowQ.text(), '4')
        self.assertEqual(self.widget.txtPowerHighQ.text(), '4')

        # unchecked checkboxes
        self.assertFalse(self.widget.chkLowQ.isChecked())
        self.assertFalse(self.widget.chkHighQ.isChecked())

        # number of tabs
        self.assertEqual(self.widget.tabWidget.count(), 2)
        # default tab
        self.assertEqual(self.widget.tabWidget.currentIndex(), 0)
        # tab's title
        self.assertEqual(self.widget.tabWidget.tabText(0), 'Invariant')
        self.assertEqual(self.widget.tabWidget.tabText(1), 'Options')

        # Tooltips
        self.assertEqual(self.widget.cmdStatus.toolTip(), "Get more details of computation such as fraction from extrapolation" )

        self.assertEqual(self.widget.txtInvariantTot.toolTip(), "Total invariant [Q*], including extrapolated regions.")

        self.assertEqual(self.widget.txtExtrapolQMin.toolTip(), "The minimum extrapolated q value.")

        self.assertEqual(self.widget.txtPowerHighQ.toolTip(),"Exponent to apply to the Power_law function.")

        self.assertEqual(self.widget.txtNptsHighQ.toolTip(), "Number of Q points to consider\n while extrapolating the high-Q region")

        self.assertEqual(self.widget.chkHighQ.toolTip(), "Check to extrapolate data at high-Q")

        self.assertEqual(self.widget.txtNptsLowQ.toolTip(), "Number of Q points to consider\nwhile extrapolating the low-Q region")

        self.assertEqual(self.widget.chkLowQ.toolTip(), "Check to extrapolate data at low-Q")

        self.assertEqual(self.widget.cmdCalculate.toolTip(), "Compute invariant")

        self.assertEqual(self.widget.txtPowerLowQ.toolTip(), "Exponent to apply to the Power_law function." )

        # Validators
        self.assertIsInstance(self.widget.txtNptsLowQ.validator(), QtGui.QIntValidator)
        self.assertIsInstance(self.widget.txtNptsHighQ.validator(), QtGui.QIntValidator)
        self.assertIsInstance(self.widget.txtPowerLowQ.validator(), GuiUtils.DoubleValidator)
        self.assertIsInstance(self.widget.txtPowerHighQ.validator(), GuiUtils.DoubleValidator)

        self.assertIsInstance(self.widget.txtBackgd.validator(), GuiUtils.DoubleValidator)
        self.assertIsInstance(self.widget.txtContrast.validator(), GuiUtils.DoubleValidator)
        self.assertIsInstance(self.widget.txtScale.validator(), GuiUtils.DoubleValidator)
        self.assertIsInstance(self.widget.txtPorodCst.validator(), GuiUtils.DoubleValidator)

        # Test autoexclusivity of radiobuttons
        # Low Q
        self.assertFalse(self.widget.rbGuinier.autoExclusive())
        self.assertFalse(self.widget.rbPowerLawLowQ.autoExclusive())
        self.assertTrue(self.widget.rbFixLowQ.autoExclusive())
        self.assertTrue(self.widget.rbFitLowQ.autoExclusive())
        # High Q
        self.assertTrue(self.widget.rbFixHighQ.autoExclusive())
        self.assertTrue(self.widget.rbFitHighQ.autoExclusive())

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

    # TODO
    def testPlotResult(self):
        """ """
        pass
        # create fake input
        # data = Data1D(x=[1, 2], y=[3, 4])
        # GuiUtils.dataFromItem = MagicMock(return_value=data)
        # # self.widget._manager.filesWidget.model = MagicMock()
        # item = QtGui.QStandardItem("test")

        # run function
        # self.widget.plotResult = MagicMock(return_value=None) # (item)
        # self.widget.plotResult(item)
        # self.assertTrue(self.widget.plotResult.called_once())


        # self.assertTrue(self.widget.cmdCalculate.isEnabled())
        # self.assertEqual(self.widget.cmdCalculate.text(), 'Calculate')
        # self.assertEqual(self.widget._data.x[0], 1)
        # self.assertEqual(self.widget._data.x[1], 2)
        # self.assertEqual(self.widget._data.y[0], 3)
        # self.assertEqual(self.widget._data.y[1], 4)

    def notestHelp(self):
        """ Assure help file is shown """
        # this should not rise
        self.widget.onHelp()

    def testAllowBatch(self):
        """ """
        self.assertFalse(self.widget.allowBatch())

    def testTitle(self):
        """
        Test Perspective name
        """
        self.assertEqual(self.widget.title(), "Invariant panel")

    def testOnStatus(self):
        """
        Test Display of Invariant Details
        """
        # enable click on Calculate button
        self.widget.cmdStatus.setEnabled(True)

        invariant_details_dialog = create_autospec(DetailsDialog)

        self.widget.detailsDialog = invariant_details_dialog

        # click on button
        QTest.mouseClick(self.widget.cmdStatus, Qt.LeftButton)

        invariant_details_dialog.showDialog.assert_called_once_with()

    def testUpdateFromModel(self):
        """
        update the globals based on the data in the model
        """
        self.widget.updateFromModel()
        self.assertEqual(self.widget._background,
                         float(self.widget.model.item(WIDGETS.W_BACKGROUND).text()))
        self.assertEqual(self.widget._contrast,
                         float(self.widget.model.item(WIDGETS.W_CONTRAST).text()))
        self.assertEqual(self.widget._scale, float(self.widget.model.item(WIDGETS.W_SCALE).text()))
        self.assertEqual(self.widget._low_extrapolate,
                         str(self.widget.model.item(WIDGETS.W_ENABLE_LOWQ).text()) == 'true')
        self.assertEqual(self.widget._low_points,
                         float(self.widget.model.item(WIDGETS.W_NPTS_LOWQ).text()))

        self.assertEqual(self.widget._low_guinier, str(self.widget.model.item(WIDGETS.W_LOWQ_GUINIER).text()) == 'true' )

        self.assertEqual(self.widget._low_fit,str(self.widget.model.item(WIDGETS.W_LOWQ_FIT).text()) == 'true')
        self.assertEqual(self.widget._low_power_value, float(self.widget.model.item(WIDGETS.W_LOWQ_POWER_VALUE).text()))

        self.assertEqual(self.widget._high_extrapolate,str(self.widget.model.item(WIDGETS.W_ENABLE_HIGHQ).text()) == 'true')
        self.assertEqual(self.widget._high_points,
                         float(self.widget.model.item(WIDGETS.W_NPTS_HIGHQ).text()))
        self.assertEqual(self.widget._high_fit,str(self.widget.model.item(WIDGETS.W_HIGHQ_FIT).text()) == 'true')

        self.assertEqual(self.widget._high_power_value, float(self.widget.model.item(WIDGETS.W_HIGHQ_POWER_VALUE).text()))

    def testEnabling(self):
        """ """

        self.widget.cmdStatus.setEnabled(False)

        self.widget.enabling()

        self.assertTrue(self.widget.cmdStatus.isEnabled())

    def testCheckLength(self):
        """
        Test validator for number of points for extrapolation
         Error if it is larger than the distribution length
        """
        logging.warning = MagicMock()
        self.widget.txtNptsLowQ.setEnabled(True)

        self.widget._data = Data1D(x=[1, 2], y=[1, 2])
        self.widget.txtNptsLowQ.setText('9')

        # QTest.keyClicks(self.widget.txtNptsLowQ, '9')
        # QTest.keyClick(self.widget.txtNptsLowQ, QtCore.Qt.Key_Return)

        BG_COLOR_ERR = 'background-color: rgb(244, 170, 164);'
        # print 'style ',self.widget.txtNptsLowQ.styleSheet()
        self.assertIn(BG_COLOR_ERR, self.widget.txtNptsLowQ.styleSheet())
        self.assertTrue(logging.warning.called_once_with())
        self.assertFalse(self.widget.cmdCalculate.isEnabled())

    def testModelChanged(self):
        """ """
        self.widget.lowQToggle = MagicMock()
        status_ini = self.widget.model.item(WIDGETS.W_ENABLE_LOWQ).text()
        if status_ini == 'true':
            status_fin = 'false'
        else:
            status_fin = 'true'

        self.widget.model.setItem(WIDGETS.W_ENABLE_LOWQ, QtGui.QStandardItem(status_fin))

        if status_fin:
            self.assertTrue(self.widget._low_extrapolate)
        else:
            self.assertFalse(self.widget._low_extrapolate)

        self.assertTrue(self.widget.lowQToggle.called_once_with())

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

    def testLowFitAndFixToggle(self):
        """ """
        status = True
        # run function to test
        self.widget.lowFitAndFixToggle(status)
        self.assertEqual(self.widget._low_fit, status)
        self.assertNotEqual(self.widget.txtPowerLowQ.isEnabled(), status)

    def testHiFitAndFixToggle(self):
        status = True
        self.widget.hiFitAndFixToggle(status)
        self.assertEqual(self.widget.txtPowerHighQ.isEnabled(), not status)

    def testHighQToggle(self):
        """ Test enabling / disabling for check box High Q extrapolation """
        status_chkHighQ = self.widget.chkHighQ.isChecked()
        self.widget.highQToggle(status_chkHighQ)

        self.assertEqual(self.widget.rbFitHighQ.isEnabled(), status_chkHighQ)
        self.assertEqual(self.widget.rbFixHighQ.isEnabled(), status_chkHighQ)
        self.assertEqual(self.widget.txtNptsHighQ.isEnabled(), status_chkHighQ)
        self.assertEqual(self.widget.txtPowerHighQ.isEnabled(), status_chkHighQ)

        # change checked status of chkHighQ
        self.widget.chkHighQ.setChecked(True)
        status_chkHighQ = self.widget.chkHighQ.isChecked()
        self.assertEqual(self.widget.rbFitHighQ.isEnabled(), status_chkHighQ)
        self.assertEqual(self.widget.rbFixHighQ.isEnabled(), status_chkHighQ)
        self.assertEqual(self.widget.txtNptsHighQ.isEnabled(), status_chkHighQ)
        self.assertEqual(self.widget.txtPowerHighQ.isEnabled(),
                         status_chkHighQ)

    def testLowQToggle(self):
        """ Test enabling / disabling for check box Low Q extrapolation """
        status_chkLowQ = self.widget.chkLowQ.isChecked()

        self.assertEqual(self.widget.rbGuinier.isEnabled(), status_chkLowQ)
        self.assertEqual(self.widget.rbPowerLawLowQ.isEnabled(), status_chkLowQ)
        self.assertEqual(self.widget.txtNptsLowQ.isEnabled(), status_chkLowQ)

        self.assertEqual(self.widget.rbFitLowQ.isVisible(), self.widget.rbPowerLawLowQ.isChecked())
        self.assertEqual(self.widget.rbFixLowQ.isVisible(), self.widget.rbPowerLawLowQ.isChecked())
        self.assertEqual(self.widget.rbFitLowQ.isEnabled(), status_chkLowQ)
        self.assertEqual(self.widget.rbFixLowQ.isEnabled(), status_chkLowQ)

        self.assertEqual(self.widget.txtNptsLowQ.isEnabled(),
                         all([status_chkLowQ, not self.widget._low_guinier, not self.widget._low_fit]))

    def testSetupModel(self):
        """ Test default settings of model"""
        self.assertEqual(self.widget.model.item(WIDGETS.W_FILENAME).text(),
                         self.widget._path)

        self.assertEqual(self.widget.model.item(WIDGETS.W_QMIN).text(), '0.0')

        self.assertEqual(self.widget.model.item(WIDGETS.W_QMAX).text(), '0.0')

        self.assertEqual(self.widget.model.item(WIDGETS.W_BACKGROUND).text(),
                         str(self.widget._background))

        self.assertEqual(self.widget.model.item(WIDGETS.W_CONTRAST).text(),
                         str(self.widget._contrast))

        self.assertEqual(self.widget.model.item(WIDGETS.W_SCALE).text(),
                         str(self.widget._scale))

        self.assertIn(str(self.widget.model.item(WIDGETS.W_POROD_CST).text()),
                      ['', str(self.widget._porod)])

        self.assertEqual(
            str(self.widget.model.item(WIDGETS.W_ENABLE_HIGHQ).text()).lower(),
            'false')

        self.assertEqual(
            str(self.widget.model.item(WIDGETS.W_ENABLE_LOWQ).text()).lower(),
            'false')

        self.assertEqual(
            str(self.widget.model.item(WIDGETS.W_NPTS_LOWQ).text()),
            str(10))

        self.assertEqual(self.widget.model.item(WIDGETS.W_NPTS_HIGHQ).text(),
                         str(10))

        self.assertEqual(
            str(self.widget.model.item(WIDGETS.W_LOWQ_GUINIER).text()).lower(),
            'true')

        self.assertEqual(
            str(self.widget.model.item(WIDGETS.W_LOWQ_FIT).text()).lower(),
            'true')

        self.assertEqual(
            str(self.widget.model.item(WIDGETS.W_LOWQ_POWER_VALUE).text()), '4')

        self.assertEqual(
            str(self.widget.model.item(WIDGETS.W_HIGHQ_FIT).text()).lower(),
            'true')

        self.assertEqual(
            str(self.widget.model.item(WIDGETS.W_HIGHQ_POWER_VALUE).text()),
            '4')

    # TODO
    def testSetupMapper(self):
        """ """
        self.assertIsInstance(self.widget.mapper, QtWidgets.QDataWidgetMapper)

        self.assertEqual(self.widget.mapper.orientation(), 2)

        self.assertEqual(self.widget.mapper.model(), self.widget.model)

    def testSetData(self):
        """ """
        self.widget.updateGuiFromFile = MagicMock()

        data = Data1D(x=[1, 2], y=[1, 2])
        GuiUtils.dataFromItem = MagicMock(return_value=data)
        item = QtGui.QStandardItem("test")
        self.widget.setData([item])

        self.assertTrue(self.widget.updateGuiFromFile.called_once())

    def TestCheckQExtrapolatedData(self):
        """
        Test Match status of low or high-Q extrapolated data checkbox in
        DataExplorer with low or high-Q extrapolation checkbox in invariant
        panel
        """
        # Low-Q check box ticked
        self.widget.chkLowQ.setCheckStatus(QtCore.Qt.Checked)
        GuiUtils.updateModelItemStatus = MagicMock()

        self.assertTrue(GuiUtils.updateModelItemStatus.called_once())


if __name__ == "__main__":
    unittest.main()
