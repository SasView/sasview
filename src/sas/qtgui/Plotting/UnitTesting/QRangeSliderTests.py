import sys
import unittest

from PyQt5 import QtCore, QtWidgets

# set up import paths
import sas.qtgui.path_prepare

# Local
from sas.qtgui.MainWindow.GuiManager import GuiManager
from sas.qtgui.MainWindow.MainWindow import MainSasViewWindow
from sas.qtgui.Plotting.PlotterData import Data1D
import sas.qtgui.Plotting.Plotter as Plotter
from sas.qtgui.Plotting.QRangeSlider import QRangeSlider
from sas.qtgui.Plotting.LinearFit import LinearFit

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)


class QRangeSlidersTest(unittest.TestCase):
    '''Test the QRangeSliders'''

    def setUp(self):
        '''Create the ScaleProperties'''
        class MainWindow(MainSasViewWindow):
            # Main window of the application
            def __init__(self, reactor, parent=None):
                screen_resolution = QtCore.QRect(0, 0, 640, 480)
                super(MainWindow, self).__init__(screen_resolution, parent)

                # define workspace for dialogs.
                self.workspace = QtWidgets.QMdiArea(self)
                self.setCentralWidget(self.workspace)

        self.manager = GuiManager(MainWindow(None))
        self.plotter = Plotter.Plotter(None, quickplot=True)
        self.data = Data1D(x=[0,0.1,0.2,0.3,0.4], y=[1000,100,10,1,0.1])
        self.data.name = "Test QRangeSliders class"
        self.data.show_q_range_sliders = True
        self.data.slider_update_on_move = True
        self.manager.filesWidget.updateModel(self.data, self.data.name)
        self.slider = None

    def testUnplottedDefaults(self):
        '''Test the QRangeSlider class in its default state when it is not plotted'''
        self.plotter.plot(self.data)
        self.assertRaises(AssertionError, lambda: QRangeSlider(self.plotter, self.plotter.ax))
        self.slider = QRangeSlider(self.plotter, self.plotter.ax, data=self.data)
        self.assertIsNotNone(self.slider.base)
        self.assertIsNotNone(self.slider.data)
        self.assertTrue(self.slider.updateOnMove)
        self.assertTrue(self.slider.has_move)
        self.assertTrue(self.slider.is_visible)
        self.assertIsNone(self.slider.line_min.input)
        self.assertIsNone(self.slider.line_min.setter)
        self.assertIsNone(self.slider.line_min.getter)
        self.assertIsNone(self.slider.line_min.perspective)
        self.assertIsNone(self.slider.line_max.input)
        self.assertIsNone(self.slider.line_max.setter)
        self.assertIsNone(self.slider.line_max.getter)
        self.assertIsNone(self.slider.line_max.perspective)

    def testFittingSliders(self):
        '''Test the QRangeSlider class within the context of the Fitting perspective'''
        # Ensure fitting prespective is active and send data to it
        self.manager.perspectiveChanged('Fitting')
        fitting = self.manager.perspective()
        self.manager.filesWidget.sendData()
        widget = fitting.currentTab
        # Create slider on base data set
        self.data.slider_update_on_move = False
        self.data.slider_tab_name = widget.modelName()
        self.data.slider_perspective_name = 'Fitting'
        self.data.slider_high_q_input = ['options_widget', 'txtMaxRange']
        self.data.slider_high_q_setter = ['options_widget', 'updateMaxQ']
        self.data.slider_low_q_input = ['options_widget', 'txtMinRange']
        self.data.slider_low_q_setter = ['options_widget', 'updateMinQ']
        # FIXME: Perspective grabbing method in QRangeSlider class is touchy...
        self.plotter.plot(self.data)
        # Check inp0uts are linked properly.
        self.assertEqual(len(self.plotter.sliders), 1)

    def testInvariantSliders(self):
        '''Test the QRangeSlider class within the context of the Invariant perspective'''
        pass

    def testInversionSliders(self):
        '''Test the QRangeSlider class within the context of the Inversion perspective'''
        pass

    def testLinearFitSliders(self):
        '''Test the QRangeSlider class within the context of the Linear Fit tool'''
        self.plotter.plot(self.data)
        linearFit = LinearFit(self.plotter, self.data, (min(self.data.x), max(self.data.x)),
                              (min(self.data.x), max(self.data.x)))
        linearFit.fit(None)
        q_sliders = linearFit.q_sliders
        # Ensure base values match
        self.assertAlmostEqual(min(self.data.x), float(linearFit.txtFitRangeMin.text()))
        # Check QRangeSlider defaults and connections
        self.assertIsNotNone(q_sliders)
        self.assertEqual(q_sliders.line_min.input, linearFit.txtFitRangeMin)
        self.assertEqual(q_sliders.line_max.input, linearFit.txtFitRangeMax)

        # Move slider and ensure text input matches
        q_sliders.line_min.move(self.data.x[1], self.data.y[1], None)
        self.assertAlmostEqual(q_sliders.line_min.x, float(linearFit.txtFitRangeMin.text()))
        q_sliders.line_max.move(self.data.x[-2], self.data.y[-2], None)
        self.assertAlmostEqual(q_sliders.line_max.x, float(linearFit.txtFitRangeMax.text()))

        # Edit text input and ensure QSlider position matches
        linearFit.txtFitRangeMin.setText(f'{self.data.x[1]}')
        self.assertAlmostEqual(q_sliders.line_min.x, float(linearFit.txtFitRangeMin.text()))
        linearFit.txtFitRangeMax.setText(f'{self.data.x[-2]}')
        self.assertAlmostEqual(q_sliders.line_max.x, float(linearFit.txtFitRangeMax.text()))


if __name__ == "__main__":
    unittest.main()
