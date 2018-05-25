import sys
import time
import numpy
import unittest
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtTest import QTest

from PyQt5.QtCore import Qt
from unittest.mock import MagicMock
from unittest.mock import patch

# set up import paths
import path_prepare

from mpl_toolkits.mplot3d import Axes3D
from UnitTesting.TestUtils import QtSignalSpy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from sas.qtgui.Calculators.GenericScatteringCalculator import GenericScatteringCalculator
from sas.qtgui.Calculators.GenericScatteringCalculator import Plotter3D

from sas.qtgui.MainWindow.DataManager import DataManager
from sas.qtgui.MainWindow.GuiManager import GuiManager
from sas.qtgui.Utilities.GuiUtils import *
from sas.sascalc.calculator import sas_gen

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class GenericScatteringCalculatorTest(unittest.TestCase):
    """Test the GenericScatteringCalculator"""
    def setUp(self):
        """Create the GenericScatteringCalculator"""
        class dummy_manager(object):
            def communicator(self):
                return Communicate()

        self.widget = GenericScatteringCalculator(dummy_manager())

    def tearDown(self):
        """Destroy the GenericScatteringCalculator"""
        self.widget.close()
        self.widget = None


    def testDefaults(self):
        """Test the GUI in its default state"""
        self.assertIsInstance(self.widget, QtWidgets.QWidget)
        self.assertEqual(self.widget.windowTitle(), "Generic SAS Calculator")

        self.assertIn('trigger_plot_3d', dir(self.widget))

        # Buttons
        self.assertEqual(self.widget.txtData.text(), "Default SLD Profile")
        self.assertEqual(self.widget.cmdLoad.text(), "Load")
        self.assertEqual(self.widget.cmdDraw.text(), "Draw")
        self.assertEqual(self.widget.cmdCompute.text(), "Compute")
        self.assertEqual(self.widget.cmdReset.text(), "Reset")
        self.assertEqual(self.widget.cmdClose.text(), "Close")
        self.assertEqual(self.widget.cmdHelp.text(), "Help")
        self.assertEqual(self.widget.cmdDrawpoints.text(), "Draw Points")
        self.assertEqual(self.widget.cmdSave.text(), "Save SLD Data")

        self.assertEqual(self.widget.txtBackground.text(), '0.0')
        self.assertEqual(self.widget.txtScale.text(), '1.0')
        self.assertEqual(self.widget.txtSolventSLD.text(), '0.0')
        self.assertEqual(self.widget.txtTotalVolume.text(), '216000.0')
        self.assertEqual(self.widget.txtUpFracIn.text(), '1.0')
        self.assertEqual(self.widget.txtUpFracOut.text(), '1.0')
        self.assertEqual(self.widget.txtUpTheta.text(), '0.0')
        self.assertEqual(self.widget.txtNoQBins.text(), '50')
        self.assertEqual(self.widget.txtQxMax.text(), '0.3')
        self.assertEqual(self.widget.txtNoPixels.text(), '1000')
        self.assertEqual(self.widget.txtMx.text(), '0')
        self.assertEqual(self.widget.txtMy.text(), '0')
        self.assertEqual(self.widget.txtMz.text(), '0')
        self.assertEqual(self.widget.txtNucl.text(), '6.97e-06')
        self.assertEqual(self.widget.txtXnodes.text(), '10')
        self.assertEqual(self.widget.txtYnodes.text(), '10')
        self.assertEqual(self.widget.txtZnodes.text(), '10')
        self.assertEqual(self.widget.txtXstepsize.text(), '6')
        self.assertEqual(self.widget.txtYstepsize.text(), '6')
        self.assertEqual(self.widget.txtZstepsize.text(), '6')

        # Comboboxes
        self.assertFalse(self.widget.cbOptionsCalc.isVisible())
        self.assertFalse(self.widget.cbOptionsCalc.isEditable())
        self.assertEqual(self.widget.cbOptionsCalc.count(), 2)
        self.assertEqual(self.widget.cbOptionsCalc.currentIndex(), 0)
        self.assertListEqual([self.widget.cbOptionsCalc.itemText(i) for i in
                              range(self.widget.cbOptionsCalc.count())],
                             ['Fixed orientation', 'Debye full avg.'])

        self.assertEqual(self.widget.cbShape.count(), 2)
        self.assertEqual(self.widget.cbShape.currentIndex(), 0)
        self.assertListEqual([self.widget.cbShape.itemText(i) for i in
                              range(self.widget.cbShape.count())],
                             ['Rectangular', 'Ellipsoid'])
        self.assertFalse(self.widget.cbShape.isEditable())
        # disable buttons
        self.assertFalse(self.widget.cmdSave.isEnabled())
        self.assertFalse(self.widget.cmdDraw.isEnabled())
        self.assertFalse(self.widget.cmdDrawpoints.isEnabled())

    def testHelpButton(self):
        """ Assure help file is shown """
        self.widget.manager.showHelp = MagicMock()
        self.widget.onHelp()
        self.assertTrue(self.widget.manager.showHelp.called_once())
        args = self.widget.manager.showHelp.call_args
        self.assertIn('sas_calculator_help.html', args[0][0])

    def testValidator(self):
        """ Test the inputs when validators had been defined """
        # Background, Volume and Scale should be positive
        txtEdit_positive = [self.widget.txtBackground,
                            self.widget.txtTotalVolume,
                            self.widget.txtScale]

        for item in txtEdit_positive:
            item.setText('-1')
            state = item.validator().validate(item.text(), 0)[0]
            self.assertEqual(state, QtGui.QValidator.Invalid)

        for item in txtEdit_positive:
            item.setText('2')
            state = item.validator().validate(item.text(), 0)[0]
            self.assertEqual(state, QtGui.QValidator.Acceptable)

        for item in txtEdit_positive:
            item.setText('abc')
            state = item.validator().validate(item.text(), 0)[0]
            self.assertEqual(state, QtGui.QValidator.Invalid)

        # Fraction of spin up between 0 and 1
        txtEdit_0_1 = [self.widget.txtUpFracIn, self.widget.txtUpFracOut]

        for item in txtEdit_0_1:
            item.setText('-1.04546')
            state = item.validator().validate(item.text(), 0)[0]
            self.assertEqual(state, QtGui.QValidator.Invalid)

        for item in txtEdit_0_1:
            item.setText('2.00000')
            state = item.validator().validate(item.text(), 0)[0]
            self.assertEqual(state, QtGui.QValidator.Invalid)

        for item in txtEdit_0_1:
            item.setText('0.000000005')
            state = item.validator().validate(item.text(), 0)[0]
            self.assertEqual(state, QtGui.QValidator.Acceptable)

        # Test text edits related to Q:
        # 0< Qmax < 1000, 2 <= Qbins <= 1000
        txtEdit_q_values = [self.widget.txtNoQBins, self.widget.txtQxMax]
        for item in txtEdit_q_values:
            item.setText('-1.01')
            state = item.validator().validate(item.text(), 0)[0]
            self.assertEqual(state, QtGui.QValidator.Invalid)

        for item in txtEdit_q_values:
            item.setText('1500.01')
            state = item.validator().validate(item.text(), 0)[0]
            self.assertEqual(state, QtGui.QValidator.Invalid)

        self.widget.txtNoQBins.setText('1.5')
        self.assertEqual(
            self.widget.txtNoQBins.validator().validate(item.text(), 0)[0],
            QtGui.QValidator.Invalid)

        self.widget.txtQxMax.setText('1.5')
        self.assertEqual(
            self.widget.txtQxMax.validator().validate(item.text(), 0)[0],
            QtGui.QValidator.Acceptable)

    def testLoadedSLDData(self):
        """
        Load sld data and check modifications of GUI
        """
        filename = os.path.join("UnitTesting", "sld_file.sld")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[filename, ''])
        self.widget.loadFile()

        # check modification of text in Load button
        self.assertEqual(self.widget.cmdLoad.text(), 'Loading...')
        # wait a bit for data to be loaded
        time.sleep(0.1)
        # check updated values in ui, read from loaded file
        self.assertEqual(self.widget.txtData.text(), 'sld_file.sld')
        self.assertEqual(self.widget.txtTotalVolume.text(), '402408.0')
        self.assertEqual(self.widget.txtNoPixels.text(), '552')
        self.assertFalse(self.widget.txtNoPixels.isEnabled())

        # check disabled TextEdits according to data format
        self.assertFalse(self.widget.txtUpFracIn.isEnabled())
        self.assertFalse(self.widget.txtUpFracOut.isEnabled())
        self.assertFalse(self.widget.txtUpFracOut.isEnabled())
        self.assertFalse(self.widget.txtNoPixels.isEnabled())

        # check enabled draw buttons
        self.assertTrue(self.widget.cmdDraw.isEnabled())
        self.assertTrue(self.widget.cmdDrawpoints.isEnabled())
        self.widget.show()
        self.assertTrue(self.widget.isVisible())
        self.assertFalse(self.widget.cbOptionsCalc.isVisible())

        # check that text of loadButton is back to initial state
        self.assertEqual(self.widget.cmdLoad.text(), 'Load')
        # check values and enabled / disabled for
        # Mx,y,z x,y,znodes and x,y,zstepsize buttons
        self.assertFalse(self.widget.txtMx.isEnabled())
        self.assertAlmostEqual(float(self.widget.txtMx.text()), 8.0795e-07, 4)
        self.assertFalse(self.widget.txtMy.isEnabled())
        self.assertAlmostEqual(float(self.widget.txtMy.text()), 8.0795e-07, 4)
        self.assertFalse(self.widget.txtMz.isEnabled())
        self.assertAlmostEqual(float(self.widget.txtMz.text()), 3.1739e-07, 4)
        self.assertTrue(self.widget.txtNucl.isEnabled())
        self.assertEqual(self.widget.txtNucl.text(), '0')

        self.assertFalse(self.widget.txtXnodes.isEnabled())
        self.assertEqual(self.widget.txtXnodes.text(), '10')
        self.assertFalse(self.widget.txtYnodes.isEnabled())
        self.assertEqual(self.widget.txtYnodes.text(), '10')
        self.assertFalse(self.widget.txtZnodes.isEnabled())
        self.assertEqual(self.widget.txtZnodes.text(), '10')

        self.assertFalse(self.widget.txtXstepsize.isEnabled())
        self.assertEqual(self.widget.txtXstepsize.text(), '9')
        self.assertFalse(self.widget.txtYstepsize.isEnabled())
        self.assertEqual(self.widget.txtYstepsize.text(), '9')
        self.assertFalse(self.widget.txtZstepsize.isEnabled())
        self.assertEqual(self.widget.txtZstepsize.text(), '9')

        self.assertTrue(self.widget.sld_data.is_data)

        # self.assertTrue(self.widget.trigger_plot_3d)


    def testLoadedPDBButton(self):
        """
        Load pdb data and check modifications of GUI
        """
        filename = os.path.join("UnitTesting", "diamdsml.pdb")

        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[filename, ''])
        self.widget.loadFile()

        # check modification of text in Load button
        self.assertEqual(self.widget.cmdLoad.text(), 'Loading...')

        time.sleep(1)
        # check updated values in ui, read from loaded file
        # TODO to be changed
        self.assertEqual(self.widget.txtData.text(), 'diamdsml.pdb')
        self.assertEqual(self.widget.txtTotalVolume.text(), '170.950584161')
        self.assertEqual(self.widget.txtNoPixels.text(), '18')

        # check disabled TextEdits according to data format
        self.assertFalse(self.widget.txtUpFracIn.isEnabled())
        self.assertFalse(self.widget.txtUpFracOut.isEnabled())
        self.assertFalse(self.widget.txtUpFracOut.isEnabled())
        self.assertFalse(self.widget.txtNoPixels.isEnabled())
        # check enabled draw buttons
        self.assertTrue(self.widget.cmdDraw.isEnabled())
        self.assertTrue(self.widget.cmdDrawpoints.isEnabled())
        # fixed orientation
        self.widget.show()
        self.assertTrue(self.widget.isVisible())
        self.assertTrue(self.widget.cbOptionsCalc.isVisible())
        # check that text of loadButton is back to initial state
        self.assertEqual(self.widget.cmdLoad.text(), 'Load')
        self.assertTrue(self.widget.cmdLoad.isEnabled())

        # check values and enabled / disabled for
        # Mx,y,z x,y,znodes and x,y,zstepsize buttons
        self.assertFalse(self.widget.txtMx.isEnabled())
        self.assertEqual(self.widget.txtMx.text(), '0')
        self.assertFalse(self.widget.txtMy.isEnabled())
        self.assertEqual(self.widget.txtMy.text(), '0')
        self.assertFalse(self.widget.txtMz.isEnabled())
        self.assertEqual(self.widget.txtMz.text(), '0')
        self.assertFalse(self.widget.txtNucl.isEnabled())
        self.assertAlmostEqual(float(self.widget.txtNucl.text()), 7.0003e-06, 4)

        self.assertFalse(self.widget.txtXnodes.isEnabled())
        self.assertEqual(self.widget.txtXnodes.text(), 'NaN')
        self.assertFalse(self.widget.txtYnodes.isEnabled())
        self.assertEqual(self.widget.txtYnodes.text(), 'NaN')
        self.assertFalse(self.widget.txtZnodes.isEnabled())
        self.assertEqual(self.widget.txtZnodes.text(), 'NaN')

        self.assertFalse(self.widget.txtXstepsize.isEnabled())
        self.assertEqual(self.widget.txtXstepsize.text(), 'NaN')
        self.assertFalse(self.widget.txtYstepsize.isEnabled())
        self.assertEqual(self.widget.txtYstepsize.text(), 'NaN')
        self.assertFalse(self.widget.txtZstepsize.isEnabled())
        self.assertEqual(self.widget.txtZstepsize.text(), 'NaN')

        self.assertTrue(self.widget.sld_data.is_data)

    # TODO
    def testLoadedOMFButton(self):
        """
        Load omf data and check modifications of GUI
        """
        filename = os.path.join("UnitTesting", "A_Raw_Example-1.omf")

        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[filename, ''])
        self.widget.loadFile()
        self.assertEqual(self.widget.cmdLoad.text(), 'Loading...')
        time.sleep(2)

        self.assertEqual(self.widget.txtData.text(), 'A_Raw_Example-1.omf')
        self.assertEqual(self.widget.txtTotalVolume.text(), '128000000.0')
        self.assertEqual(self.widget.txtNoPixels.text(), '16000')

        # check disabled TextEdits according to data format
        self.assertFalse(self.widget.txtUpFracIn.isEnabled())
        self.assertFalse(self.widget.txtUpFracOut.isEnabled())
        self.assertFalse(self.widget.txtUpFracOut.isEnabled())
        self.assertFalse(self.widget.txtNoPixels.isEnabled())

        # check enabled draw buttons
        self.assertTrue(self.widget.cmdDraw.isEnabled())
        self.assertTrue(self.widget.cmdDrawpoints.isEnabled())

        # check that text of loadButton is back to initial state
        self.assertEqual(self.widget.cmdLoad.text(), 'Load')
        self.assertTrue(self.widget.cmdLoad.isEnabled())

        # check values and enabled / disabled for
        # Mx,y,z x,y,znodes and x,y,zstepsize buttons
        self.assertFalse(self.widget.txtMx.isEnabled())
        self.assertAlmostEqual(float(self.widget.txtMx.text()), 7.855e-09, 4)
        self.assertFalse(self.widget.txtMy.isEnabled())
        self.assertAlmostEqual(float(self.widget.txtMy.text()), 4.517e-08, 4)
        self.assertFalse(self.widget.txtMz.isEnabled())
        self.assertAlmostEqual(float(self.widget.txtMz.text()), 9.9511e-10, 4)
        self.assertTrue(self.widget.txtNucl.isEnabled())
        self.assertEqual(self.widget.txtNucl.text(), '0')

        self.assertFalse(self.widget.txtXnodes.isEnabled())
        self.assertEqual(self.widget.txtXnodes.text(), '40')
        self.assertFalse(self.widget.txtYnodes.isEnabled())
        self.assertEqual(self.widget.txtYnodes.text(), '40')
        self.assertFalse(self.widget.txtZnodes.isEnabled())
        self.assertEqual(self.widget.txtZnodes.text(), '10')

        self.assertFalse(self.widget.txtXstepsize.isEnabled())
        self.assertEqual(self.widget.txtXstepsize.text(), '20')
        self.assertFalse(self.widget.txtYstepsize.isEnabled())
        self.assertEqual(self.widget.txtYstepsize.text(), '20')
        self.assertFalse(self.widget.txtZstepsize.isEnabled())
        self.assertEqual(self.widget.txtZstepsize.text(), '20')

    def testReset(self):
        """
        Test reset button when GUI has been modified
        """
        # modify gui
        self.widget.txtBackground.setText('50.0')
        # apply reset
        self.widget.onReset()
        # check that we get back to the initial state
        self.assertEqual(self.widget.txtBackground.text(), '0.0')

    # TODO check plots
    def testCompute(self):
        """
        Test compute button
        """
        # load data
        filename = os.path.join("UnitTesting", "diamdsml.pdb")

        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[filename, ''])
        self.widget.loadFile()
        time.sleep(1)
        QTest.mouseClick(self.widget.cmdCompute, Qt.LeftButton)
        # check modification of text of Compute button
        self.assertEqual(self.widget.cmdCompute.text(), 'Wait...')
        self.assertFalse(self.widget.cmdCompute.isEnabled())

        #self.widget.complete([numpy.ones(1), numpy.zeros(1), numpy.zeros(1)], update=None)
        #self.assertEqual(self.widget.cmdCompute.text(), 'Compute')
        #self.assertTrue(self.widget.cmdCompute.isEnabled())

    # TODO
    def testDrawButton(self):
        """
        Test Draw buttons for 3D plots with and without arrows
        """
        self.assertFalse(self.widget.cmdDraw.isEnabled())
        filename = os.path.join("UnitTesting", "diamdsml.pdb")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[filename,''])
        self.widget.loadFile()
        self.assertEqual(self.widget.cmdLoad.text(), 'Loading...')
        time.sleep(1)

        self.assertTrue(self.widget.cmdDraw.isEnabled())
        QTest.mouseClick(self.widget.cmdDraw, Qt.LeftButton)

        self.assertTrue(self.widget.cmdDrawpoints.isEnabled())
        QTest.mouseClick(self.widget.cmdDrawpoints, Qt.LeftButton)

    def testCloseButton(self):
        closeButton = self.widget.cmdClose
        QTest.mouseClick(closeButton, Qt.LeftButton)

    def testSaveFile(self):
        """
        Test Save feature to .sld file
        """
        filename = os.path.join("UnitTesting", "sld_file.sld")

        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[filename, ''])
        self.widget.loadFile()

        time.sleep(0.1)

        filename1 = "test"
        QtWidgets.QFileDialog.getSaveFileName = MagicMock(return_value=[filename1, ''])

        QTest.mouseClick(self.widget.cmdSave, Qt.LeftButton)
        self.widget.onSaveFile()
        self.assertTrue(os.path.isfile(filename1 + '.sld'))
        self.assertTrue(os.path.getsize(filename1 + '.sld') > 0)

        os.remove("test.sld")


class Plotter3DTest(unittest.TestCase):
    """ Test 3D plots in real space.
    The implementation is temporarily in the same script as the Generic SAS
    calculator"""
    def setUp(self):
        """create"""
        parent_test = MagicMock()
        self.plotter = Plotter3D(parent=parent_test, graph_title='test')
        self.data = sas_gen.MagSLD(numpy.array([1.0, 2.0, 3.0, 4.0]),
                                   numpy.array([10.0, 11.0, 12.0, 13.0]),
                                   numpy.array([0.1, 0.2, 0.3, 0.4]),
                                   numpy.zeros(4),
                                   numpy.zeros(4),
                                   numpy.zeros(4),
                                   numpy.zeros(4))
        self.data.sld_n = [0, 6.97e-06, 6.97e-06, 6.97e-06]
        self.data.set_pix_type('pixel')
        self.data.pix_symbol = numpy.repeat('pixel', 4)

    def tearDown(self):
        """ Destroy"""
        self.plotter = None
        self.data = None

    def testDataProperty(self):
        self.plotter.data = self.data
        self.assertEqual(self.plotter.data, self.data)
        self.assertTrue(self.plotter.graph_title, 'test')
        self.assertFalse(self.plotter.data.has_conect)

    def testShowNoPlot(self):
        FigureCanvas.draw_idle = MagicMock()
        FigureCanvas.draw = MagicMock()
        self.plotter.showPlot(data=None)
        self.assertFalse(FigureCanvas.draw_idle.called)
        self.assertFalse(FigureCanvas.draw.called)

    def testShow3DPlot(self):
        FigureCanvas.draw = MagicMock()
        Axes3D.plot = MagicMock()

        self.plotter.data = self.data
        self.plotter.showPlot(data=self.plotter.data)
        self.assertTrue(Axes3D.plot.called)
        self.assertTrue(FigureCanvas.draw.called)


if __name__ == "__main__":
    unittest.main()
