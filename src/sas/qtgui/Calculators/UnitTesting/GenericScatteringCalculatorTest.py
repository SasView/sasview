import os
import time
from pathlib import Path
from unittest.mock import MagicMock

import numpy
import pytest
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mpl_toolkits.mplot3d import Axes3D
from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from sas.qtgui.Calculators.GenericScatteringCalculator import GenericScatteringCalculator, Plotter3D
from sas.qtgui.Plotting.PlotterBase import PlotHelper
from sas.qtgui.Utilities.GuiUtils import Communicate
from sas.sascalc.calculator import sas_gen


class GenericScatteringCalculatorTest:
    """Test the GenericScatteringCalculator"""

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        """Create/Destroy the GenericScatteringCalculator"""
        class dummy_manager:
            def communicator(self):
                return Communicate()

        w = GenericScatteringCalculator(dummy_manager())

        yield w

        w.close()

    def testDefaults(self, widget):
        """Test the GUI in its default state"""
        assert isinstance(widget, QtWidgets.QWidget)
        assert widget.windowTitle() == "Generic Scattering Calculator"

        assert 'trigger_plot_3d' in dir(widget)

        # Buttons
        assert widget.txtNucData.text() == "No File Loaded"
        assert widget.cmdNucLoad.text() == "Load"
        assert widget.cmdDraw.text() == "Draw"
        assert widget.cmdCompute.text() == "Compute"
        assert widget.cmdReset.text() == "Reset"
        assert widget.cmdClose.text() == "Close"
        assert widget.cmdHelp.text() == "Help"
        assert widget.cmdDrawpoints.text() == "Draw Points"
        assert widget.cmdSave.text() == "Save SLD Data"

        assert widget.txtBackground.text() == '0.0'
        assert widget.txtScale.text() == '1.0'
        assert widget.txtSolventSLD.text() == '0.0'
        assert widget.txtTotalVolume.text() == '216000.0'
        assert widget.txtUpFracIn.text() == '1.0'
        assert widget.txtUpFracOut.text() == '1.0'
        assert widget.txtUpTheta.text() == '0.0'
        assert widget.txtNoQBins.text() == '30'
        assert widget.txtQxMax.text() == '0.3'
        assert widget.txtNoPixels.text() == '1000'
        assert widget.txtMx.text() == '0.0'
        assert widget.txtMy.text() == '0.0'
        assert widget.txtMz.text() == '0.0'
        assert widget.txtNucl.text() == '6.97e-06'
        assert widget.txtXnodes.text() == '10'
        assert widget.txtYnodes.text() == '10'
        assert widget.txtZnodes.text() == '10'
        assert widget.txtXstepsize.text() == '6'
        assert widget.txtYstepsize.text() == '6'
        assert widget.txtZstepsize.text() == '6'

        # Comboboxes
        assert not widget.cbOptionsCalc.isVisible()
        assert not widget.cbOptionsCalc.isEditable()
        assert widget.cbOptionsCalc.count() == 3
        assert widget.cbOptionsCalc.currentIndex() == 0
        assert [widget.cbOptionsCalc.itemText(i) for i in
                                range(widget.cbOptionsCalc.count())] == \
                                ['Fixed orientation', 'Debye full avg.', 'Debye full avg. w/ β(Q)',]

        assert widget.cbShape.count() == 1
        assert widget.cbShape.currentIndex() == 0
        assert [widget.cbShape.itemText(i) for i in
                                range(widget.cbShape.count())] == \
                                ['Rectangular']
                                #['Rectangular', 'Ellipsoid'])
        assert not widget.cbShape.isEditable()
        # disable buttons
        assert widget.cmdSave.isEnabled()
        assert widget.cmdDraw.isEnabled()
        assert widget.cmdDrawpoints.isEnabled()

    def testHelpButton(self, widget, mocker):
        """ Assure help file is shown """
        mocker.patch.object(widget.manager, 'showHelp', create=True)
        widget.onHelp()
        widget.manager.showHelp.assert_called_once()
        args = widget.manager.showHelp.call_args
        assert 'sas_calculator_help.html' in args[0][0]

    def testValidator(self, widget):
        """ Test the inputs when validators had been defined """
        # Background, Volume and Scale should be positive
        txtEdit_positive = [widget.txtBackground,
                            widget.txtTotalVolume,
                            widget.txtScale]

        for item in txtEdit_positive:
            item.setText('-1')
            state = item.validator().validate(item.text(), 0)[0]
            assert state == QtGui.QValidator.Invalid

        for item in txtEdit_positive:
            item.setText('2')
            state = item.validator().validate(item.text(), 0)[0]
            assert state == QtGui.QValidator.Acceptable

        for item in txtEdit_positive:
            item.setText('abc')
            state = item.validator().validate(item.text(), 0)[0]
            assert state == QtGui.QValidator.Invalid

        # Fraction of spin up between 0 and 1
        txtEdit_0_1 = [widget.txtUpFracIn, widget.txtUpFracOut]

        for item in txtEdit_0_1:
            item.setText('-1.04546')
            state = item.validator().validate(item.text(), 0)[0]
            assert state == QtGui.QValidator.Invalid

        for item in txtEdit_0_1:
            item.setText('2.00000')
            state = item.validator().validate(item.text(), 0)[0]
            assert state == QtGui.QValidator.Invalid

        for item in txtEdit_0_1:
            item.setText('0.000000005')
            state = item.validator().validate(item.text(), 0)[0]
            assert state == QtGui.QValidator.Acceptable

        # Test text edits related to Q:
        # 0< Qmax < 1000, 2 <= Qbins <= 1000
        txtEdit_q_values = [widget.txtNoQBins, widget.txtQxMax]
        for item in txtEdit_q_values:
            item.setText('-1.01')
            state = item.validator().validate(item.text(), 0)[0]
            assert state == QtGui.QValidator.Invalid

        for item in txtEdit_q_values:
            item.setText('1500.01')
            state = item.validator().validate(item.text(), 0)[0]
            assert (state == QtGui.QValidator.Intermediate or state == QtGui.QValidator.Invalid)

        widget.txtNoQBins.setText('1.5')
        assert widget.txtNoQBins.validator().validate(item.text(), 0)[0] == \
            QtGui.QValidator.Invalid

        widget.txtQxMax.setText('1.5')
        assert widget.txtQxMax.validator().validate(item.text(), 0)[0] == \
            QtGui.QValidator.Acceptable

    def testLoadedSLDData(self, widget, mocker):
        """
        Load sld data and check modifications of GUI
        """
        filename = str(Path("./src/sas/qtgui/UnitTesting/sld_file.sld").absolute())
        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=[filename, ''])
        widget.cmdMagLoad.click()

        # check modification of text in Load button
        assert widget.cmdMagLoad.text() == 'Loading...'
        # wait a bit for data to be loaded
        time.sleep(0.1)
        QtWidgets.QApplication.processEvents()

        # check updated values in ui, read from loaded file
        assert widget.txtMagData.text() == 'sld_file.sld'
        assert widget.txtTotalVolume.text() == '402408.0'
        assert widget.txtNoPixels.text() == '552'
        assert not widget.txtNoPixels.isEnabled()

        # check disabled TextEdits according to data format
        assert widget.txtUpFracIn.isEnabled()
        assert widget.txtUpFracOut.isEnabled()
        assert widget.txtUpFracOut.isEnabled()
        assert not widget.txtNoPixels.isEnabled()

        # check enabled draw buttons
        assert widget.cmdDraw.isEnabled()
        assert widget.cmdDrawpoints.isEnabled()
        widget.show()
        assert widget.isVisible()
        assert not widget.cbOptionsCalc.isVisible()

        # check that text of loadButton is back to initial state
        assert widget.cmdNucLoad.text() == 'Load'
        # check values and enabled / disabled for
        # Mx,y,z x,y,znodes and x,y,zstepsize buttons
        assert not widget.txtMx.isEnabled()
        assert float(widget.txtMx.text()) == pytest.approx(8.0795e-07, rel=1e-4)
        assert not widget.txtMy.isEnabled()
        assert float(widget.txtMy.text()) == pytest.approx(8.0795e-07, rel=1e-4)
        assert not widget.txtMz.isEnabled()
        assert float(widget.txtMz.text()) == pytest.approx(3.1739e-07, rel=1e-4)
        assert widget.txtNucl.isEnabled()
        assert widget.txtNucl.text() == '0.0'

        assert not widget.txtXnodes.isEnabled()
        assert widget.txtXnodes.text() == '10'
        assert not widget.txtYnodes.isEnabled()
        assert widget.txtYnodes.text() == '10'
        assert not widget.txtZnodes.isEnabled()
        assert widget.txtZnodes.text() == '10'

        assert not widget.txtXstepsize.isEnabled()
        assert widget.txtXstepsize.text() == '9'
        assert not widget.txtYstepsize.isEnabled()
        assert widget.txtYstepsize.text() == '9'
        assert not widget.txtZstepsize.isEnabled()
        assert widget.txtZstepsize.text() == '9'

        assert widget.mag_sld_data.is_data

        # assert widget.trigger_plot_3d

    def testLoadedPDBButton(self, widget, mocker):
        """
        Load pdb data and check modifications of GUI
        """
        filename = str(Path("./src/sas/qtgui/UnitTesting/diamdsml.pdb").absolute())

        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=[filename, ''])
        widget.cmdNucLoad.click()

        # check modification of text in Load button
        assert widget.cmdNucLoad.text() == 'Loading...'

        time.sleep(1)
        QtWidgets.QApplication.processEvents()

        # check updated values in ui, read from loaded file
        assert widget.txtNucData.text() == 'diamdsml.pdb'
        assert float(widget.txtTotalVolume.text()) == pytest.approx(163.18417, abs=1e-5)
        assert widget.txtNoPixels.text() == '18'

        # check disabled TextEdits according to data format
        assert not widget.txtUpFracIn.isEnabled()
        assert not widget.txtUpFracOut.isEnabled()
        assert not widget.txtUpFracOut.isEnabled()
        assert not widget.txtNoPixels.isEnabled()
        # check enabled draw buttons
        assert widget.cmdDraw.isEnabled()
        assert widget.cmdDrawpoints.isEnabled()
        # fixed orientation
        widget.show()
        assert widget.isVisible()
        assert widget.cbOptionsCalc.isVisible()
        # check that text of loadButton is back to initial state
        assert widget.cmdNucLoad.text() == 'Load'
        assert widget.cmdNucLoad.isEnabled()

        # check values and enabled / disabled for
        # Mx,y,z x,y,znodes and x,y,zstepsize buttons
        assert widget.txtMx.isEnabled()
        assert widget.txtMx.text() == '0.0'
        assert widget.txtMy.isEnabled()
        assert widget.txtMy.text() == '0.0'
        assert widget.txtMz.isEnabled()
        assert widget.txtMz.text() == '0.0'
        assert not widget.txtNucl.isEnabled()
        assert float(widget.txtNucl.text()) == pytest.approx(7.3322e-06, rel=1e-4)

        assert not widget.txtXnodes.isEnabled()
        assert widget.txtXnodes.text() == 'NaN'
        assert not widget.txtYnodes.isEnabled()
        assert widget.txtYnodes.text() == 'NaN'
        assert not widget.txtZnodes.isEnabled()
        assert widget.txtZnodes.text() == 'NaN'

        assert not widget.txtXstepsize.isEnabled()
        assert widget.txtXstepsize.text() == 'NaN'
        assert not widget.txtYstepsize.isEnabled()
        assert widget.txtYstepsize.text() == 'NaN'
        assert not widget.txtZstepsize.isEnabled()
        assert widget.txtZstepsize.text() == 'NaN'

        assert widget.nuc_sld_data.is_data

    def testLoadedOMFButton(self, widget, mocker):
        """
        Load omf data and check modifications of GUI
        """
        filename = str(Path("./src/sas/qtgui/UnitTesting/A_Raw_Example-1.omf").absolute())

        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=[filename, ''])
        widget.cmdMagLoad.click()

        # check modification of text in Load button
        assert widget.cmdMagLoad.text() == 'Loading...'
        # wait a bit for data to be loaded
        time.sleep(0.1)
        QtWidgets.QApplication.processEvents()

        assert widget.txtMagData.text() == 'A_Raw_Example-1.omf'
        assert widget.txtTotalVolume.text() == '128000000.0'
        assert widget.txtNoPixels.text() == '16000'

        # check disabled TextEdits according to data format
        assert widget.txtUpFracIn.isEnabled()
        assert widget.txtUpFracOut.isEnabled()
        assert widget.txtUpFracOut.isEnabled()
        assert not widget.txtNoPixels.isEnabled()

        # check enabled draw buttons
        assert widget.cmdDraw.isEnabled()
        assert widget.cmdDrawpoints.isEnabled()

        # check that text of loadButton is back to initial state
        assert widget.cmdMagLoad.text() == 'Load'
        assert widget.cmdMagLoad.isEnabled()

        # check values and enabled / disabled for
        # Mx,y,z x,y,znodes and x,y,zstepsize buttons
        assert not widget.txtMx.isEnabled()
        assert float(widget.txtMx.text()) == pytest.approx(8.0019e-09, rel=1e-4)
        assert not widget.txtMy.isEnabled()
        assert float(widget.txtMy.text()) == pytest.approx(4.6014e-08, rel=1e-4)
        assert not widget.txtMz.isEnabled()
        assert float(widget.txtMz.text()) == pytest.approx(1.0137e-09, rel=1e-4)
        assert widget.txtNucl.isEnabled()
        assert widget.txtNucl.text() == '0.0'

        assert not widget.txtXnodes.isEnabled()
        assert widget.txtXnodes.text() == '40'
        assert not widget.txtYnodes.isEnabled()
        assert widget.txtYnodes.text() == '40'
        assert not widget.txtZnodes.isEnabled()
        assert widget.txtZnodes.text() == '10'

        assert not widget.txtXstepsize.isEnabled()
        assert widget.txtXstepsize.text() == '20'
        assert not widget.txtYstepsize.isEnabled()
        assert widget.txtYstepsize.text() == '20'
        assert not widget.txtZstepsize.isEnabled()
        assert widget.txtZstepsize.text() == '20'

    def testReset(self, widget):
        """
        Test reset button when GUI has been modified
        """
        # modify gui
        widget.txtBackground.setText('50.0')
        # apply reset
        widget.onReset()
        # check that we get back to the initial state
        assert widget.txtBackground.text() == '0.0'

    def testCompute(self, widget, mocker):
        """
        Test compute button
        """
        # load data
        filename = str(Path("./src/sas/qtgui/UnitTesting/diamdsml.pdb").absolute())

        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=[filename, ''])
        widget.cmdNucLoad.click()

        # check modification of text in Load button
        assert widget.cmdNucLoad.text() == 'Loading...'
        # wait a bit for data to be loaded
        time.sleep(0.1)
        QtWidgets.QApplication.processEvents()
        QTest.mouseClick(widget.cmdCompute, Qt.LeftButton)
        # check modification of text of Compute button
        assert widget.cmdCompute.text() == 'Cancel'
        assert widget.cmdCompute.isEnabled()

        #widget.complete([numpy.ones(1), numpy.zeros(1), numpy.zeros(1)], update=None)
        #assert widget.cmdCompute.text() == 'Compute'
        #assert widget.cmdCompute.isEnabled()

    def testDrawButton(self, widget, mocker):
        """
        Test Draw buttons for 3D plots with and without arrows
        """
        assert widget.cmdDraw.isEnabled()
        filename = str(Path("./src/sas/qtgui/UnitTesting/diamdsml.pdb").absolute())
        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=[filename,''])
        widget.cmdNucLoad.click()

        # check modification of text in Load button
        assert widget.cmdNucLoad.text() == 'Loading...'
        # wait a bit for data to be loaded
        time.sleep(0.1)
        QtWidgets.QApplication.processEvents()

        assert widget.cmdDraw.isEnabled()
        QTest.mouseClick(widget.cmdDraw, Qt.LeftButton)

        assert widget.cmdDrawpoints.isEnabled()
        QTest.mouseClick(widget.cmdDrawpoints, Qt.LeftButton)

    def testCloseButton(self, widget):
        closeButton = widget.cmdClose
        QTest.mouseClick(closeButton, Qt.LeftButton)

    def testSaveFile(self, widget, mocker):
        """
        Test Save feature to .sld file
        """
        filename = str(Path("./src/sas/qtgui/UnitTesting/sld_file.sld").absolute())

        mocker.patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=[filename, ''])
        widget.cmdMagLoad.click()

        time.sleep(0.1)
        QtWidgets.QApplication.processEvents()

        filename1 = str(Path("./src/sas/qtgui/UnitTesting/test").absolute())
        mocker.patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=[filename1, ''])

        #QTest.mouseClick(widget.cmdSave, Qt.LeftButton)
        widget.cmdSave.click()
        QtWidgets.QApplication.processEvents()

        assert os.path.isfile(filename1 + '.sld')
        assert os.path.getsize(filename1 + '.sld') > 0

        os.remove(filename1 + ".sld")


class Plotter3DTest:
    """ Test 3D plots in real space.
    The implementation is temporarily in the same script as the Generic SAS
    calculator"""

    @pytest.fixture(autouse=True)
    def plotter(self, qapp):
        """Create/Destroy the Plotter"""
        parent_test = MagicMock()
        p = Plotter3D(None, parent=parent_test, graph_title='test')

        yield p

        PlotHelper.clear()

    @pytest.fixture(autouse=True)
    def data(self):
        """Create/Destroy the plottable data"""
        d = sas_gen.MagSLD(
            numpy.array([1.0, 2.0, 3.0, 4.0]),
            numpy.array([10.0, 11.0, 12.0, 13.0]),
            numpy.array([0.1, 0.2, 0.3, 0.4]),
            numpy.zeros(4),
            numpy.zeros(4),
            numpy.zeros(4),
            numpy.zeros(4)
        )
        d.sld_n = [0, 6.97e-06, 6.97e-06, 6.97e-06]
        d.set_pix_type('pixel')
        d.pix_symbol = numpy.repeat('pixel', 4)

        yield d

    def testDataProperty(self, plotter, data):
        plotter.data = data
        assert plotter.data == data
        assert plotter.graph_title, 'test'
        assert not plotter.data.has_conect

    def testShowNoPlot(self, plotter, mocker):
        mocker.patch.object(FigureCanvas, 'draw_idle')
        mocker.patch.object(FigureCanvas, 'draw')
        plotter.showPlot(data=None)
        assert not FigureCanvas.draw_idle.called
        assert not FigureCanvas.draw.called

    def testShow3DPlot(self, plotter, data, mocker):
        mocker.patch.object(FigureCanvas, 'draw')
        mocker.patch.object(Axes3D, 'plot')

        plotter.data = data
        plotter.showPlot(data=data)
        Axes3D.plot.assert_called()
        FigureCanvas.draw.assert_called()
