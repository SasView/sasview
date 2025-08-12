
import pytest

# Local
from PySide6.QtWidgets import QMdiArea

import sas.qtgui.Plotting.Plotter as Plotter
from sas.qtgui.MainWindow.GuiManager import GuiManager
from sas.qtgui.MainWindow.MainWindow import MainSasViewWindow
from sas.qtgui.Plotting.LinearFit import LinearFit
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.QRangeSlider import QRangeSlider


class QRangeSlidersTest:
    '''Test the QRangeSliders'''
    @pytest.fixture(autouse=True)
    def slidersetup(self, qapp):
        '''Create the slider setup'''
        # this is a slightly unusual fixture compared to the others in
        # sasview in that it creates everything within the object as
        # instance variables, and doesn't actually yield anything itself
        class MainWindow(MainSasViewWindow):
            # Main window of the application
            def __init__(self, parent=None):
                #screen_resolution = QtCore.QRect(0, 0, 640, 480)
                #super(MainWindow, self).__init__(screen_resolution, parent)
                super(MainWindow, self).__init__(parent)

                # define workspace for dialogs.
                self.workspace = QMdiArea(self)
                self.setCentralWidget(self.workspace)

        self.manager = GuiManager(MainWindow(None))
        self.plotter = Plotter.Plotter(self.manager.filesWidget, quickplot=True)
        self.data = Data1D(x=[0.001,0.1,0.2,0.3,0.4], y=[1000,100,10,1,0.1])
        self.data.name = "Test QRangeSliders class"
        self.data.show_q_range_sliders = True
        self.data.slider_update_on_move = True
        self.manager.filesWidget.updateModel(self.data, self.data.name)
        self.current_perspective = None
        self.slider = None

        yield

        # cleanup
        self.workspace = None
        self.manager = None
        self.data = None
        self.slider = None
        self.plotter = None

    def testUnplottedDefaults(self, slidersetup):
        '''Test the QRangeSlider class in its default state when it is not plotted'''
        self.plotter.plot(self.data)
        with pytest.raises(AssertionError):
            QRangeSlider(self.plotter, self.plotter.ax)
        self.slider = QRangeSlider(self.plotter, self.plotter.ax, data=self.data)
        assert self.slider.base is not None
        assert self.slider.data is not None
        assert self.slider.updateOnMove
        assert self.slider.has_move
        assert self.slider.is_visible
        assert self.slider.line_min.input is None
        assert self.slider.line_min.setter is None
        assert self.slider.line_min.getter is None
        assert self.slider.line_min.perspective is None
        assert self.slider.line_max.input is None
        assert self.slider.line_max.setter is None
        assert self.slider.line_max.getter is None
        assert self.slider.line_max.perspective is None

    def testFittingSliders(self, slidersetup):
        '''Test the QRangeSlider class within the context of the Fitting perspective'''
        # Ensure fitting perspective is active and send data to it
        self.current_perspective = 'Fitting'
        self.manager.perspectiveChanged(self.current_perspective)
        fitting = self.manager.perspective()
        self.manager.filesWidget.sendData()
        widget = fitting.currentTab
        # Create slider on base data set
        self.data.slider_tab_name = widget.modelName()
        self.data.slider_perspective_name = self.current_perspective
        self.data.slider_high_q_input = ['options_widget', 'txtMaxRange']
        self.data.slider_high_q_setter = ['options_widget', 'updateMaxQ']
        self.data.slider_low_q_input = ['options_widget', 'txtMinRange']
        self.data.slider_low_q_setter = ['options_widget', 'updateMinQ']
        self.plotter.plot(self.data)
        self.slider = QRangeSlider(self.plotter, self.plotter.ax, data=self.data)
        # Check inputs are linked properly.
        assert len(self.plotter.sliders) == 1
        assert self.slider.line_min.setter == widget.options_widget.updateMinQ
        assert self.slider.line_max.setter == widget.options_widget.updateMaxQ
        self.moveSliderAndInputs(widget.options_widget.txtMinRange, widget.options_widget.txtMaxRange)

    def testInvariantSliders(self, slidersetup):
        '''Test the QRangeSlider class within the context of the Invariant perspective'''
        # Ensure invariant prespective is active and send data to it
        self.current_perspective = 'Invariant'
        self.manager.perspectiveChanged(self.current_perspective)
        widget = self.manager.perspective()
        widget._data = self.data
        # Create slider on base data set
        self.data.slider_perspective_name = self.current_perspective
        self.data.slider_low_q_input = ['txtNptsHighQ']
        self.data.slider_low_q_setter = ['set_high_q_extrapolation_lower_limit']
        self.data.slider_low_q_getter = ['get_high_q_extrapolation_lower_limit']
        self.data.slider_high_q_input = ['txtExtrapolQMax']
        self.plotter.plot(self.data)
        self.slider = QRangeSlider(self.plotter, self.plotter.ax, data=self.data)
        # Check inputs are linked properly.
        assert len(self.plotter.sliders) == 1
        # Move slider and ensure text input matches - Npts needs to be checked differently
        self.moveSliderAndInputs(None, widget.txtExtrapolQMax)
        # Check npts after moving line
        self.slider.line_min.move(self.data.x[1], self.data.y[1], None)
        assert float(widget.txtNptsHighQ.text()) == pytest.approx(5, abs=1e-7)
        # Move npts and check slider
        widget.txtNptsHighQ.setText('2')
        assert self.data.x[1]-self.slider.line_min.x == pytest.approx(0, abs=1e-7)

    def testInversionSliders(self, slidersetup):
        '''Test the QRangeSlider class within the context of the Inversion perspective'''
        # Ensure inversion prespective is active and send data to it
        self.current_perspective = 'Inversion'
        self.manager.perspectiveChanged(self.current_perspective)
        inversion = self.manager.perspective()
        self.manager.filesWidget.sendData()
        widget = inversion.currentTab
        self._allowPlots = True
        # Create slider on base data set
        self.data.slider_perspective_name = self.current_perspective
        self.data.slider_low_q_input = ['minQInput']
        self.data.slider_low_q_setter = ['updateMinQ']
        self.data.slider_high_q_input = ['maxQInput']
        self.data.slider_high_q_setter = ['updateMaxQ']
        self.plotter.plot(self.data)
        self.slider = QRangeSlider(self.plotter, self.plotter.ax, data=self.data)
        # Check inputs are linked properly.
        assert len(self.plotter.sliders) == 1
        assert self.slider.line_min.setter == widget.updateMinQ()
        assert self.slider.line_max.setter == widget.updateMaxQ()
        # Move slider and ensure text input matches
        self.moveSliderAndInputs(widget.minQInput, widget.maxQInput)


    def testLinearFitSliders(self, slidersetup):
        '''Test the QRangeSlider class within the context of the Linear Fit tool'''
        self.plotter.plot(self.data)
        linearFit = LinearFit(self.plotter, self.data, (min(self.data.x), max(self.data.x)),
                              (min(self.data.x), max(self.data.x)))
        linearFit.fit(None)
        self.slider = linearFit.q_sliders
        # Ensure base values match
        assert min(self.data.x) == pytest.approx(float(linearFit.txtFitRangeMin.text()), abs=1e-7)
        # Move inputs and sliders and ensure values match
        self.moveSliderAndInputs(linearFit.txtFitRangeMin, linearFit.txtFitRangeMax)

    def moveSliderAndInputs(self, minInput, maxInput):
        '''Helper method to minimize repeated code'''
        # Check QRangeSlider defaults and connections
        assert self.slider is not None

        # Move slider and ensure text input matches
        if minInput:
            #assert self.slider.line_min.input == minInput
            self.slider.line_min.move(self.data.x[1], self.data.y[1], None)
            assert self.slider.line_min.x == pytest.approx(float(minInput.text()), abs=1e-7)
        if maxInput:
            #assert self.slider.line_max.input == maxInput
            self.slider.line_max.move(self.data.x[-2], self.data.y[-2], None)
            assert self.slider.line_max.x == pytest.approx(float(maxInput.text()), abs=1e-7)

        # Edit text input and ensure QSlider position matches
        if minInput:
            minInput.setText(f'{self.data.x[1]}')
            assert self.slider.line_min.x == pytest.approx(float(minInput.text()), abs=1e-7)
        if maxInput:
            maxInput.setText(f'{self.data.x[-2]}')
            assert self.slider.line_max.x == pytest.approx(float(maxInput.text()), abs=1e-7)
