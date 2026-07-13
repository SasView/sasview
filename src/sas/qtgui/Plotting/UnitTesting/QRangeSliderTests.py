from unittest.mock import MagicMock, patch

import pytest

# Local
from PySide6.QtWidgets import QMdiArea

import sas.qtgui.Plotting.Plotter as Plotter
from sas.qtgui.MainWindow.GuiManager import GuiManager
from sas.qtgui.MainWindow.MainWindow import MainSasViewWindow
from sas.qtgui.Plotting.LinearFit import LinearFit
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.QRangeSlider import QRangeSlider


@pytest.fixture(scope="session", autouse=True)
def patch_heavyweight_calculators():
    """Prevent heavyweight calculator widgets from being instantiated during tests.

    - MuMag: calls plt.figure() twice in __init__, causing 'too many figures' warnings.
    - Shape2SAS: uses Q3DScatter (OpenGL), which crashes under the offscreen platform.
    """
    with (
        patch("sas.qtgui.MainWindow.GuiManager.MuMag", MagicMock),
        patch("sas.qtgui.MainWindow.GuiManager.Shape2SAS", MagicMock),
    ):
        yield


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
        self.data = Data1D(x=[0.001,0.1,0.2,0.3,0.4], y=[1000,100,10,1,0.1], dy=[100,10,1,0.1,0.01])
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

    @pytest.mark.parametrize(
        "checkbox, start, end",
        [
            ("chkHighQ_ex", "txtPorodStart_ex", "txtPorodEnd_ex"),
            ("chkLowQ_ex", None, "txtGuinierEnd_ex"),
        ],
        ids=["High Q", "Low Q"]
    )
    def testInvariantSliders(self, checkbox, start, end, slidersetup):
        """Test the QRangeSlider class within the context of the Invariant perspective.

        After the refactor, invariant sliders are purely visual.
        They are positioned by reading a the extrapolation parameters at creation time,
        and do NOT maintain a live connection to the text-field inputs.
        Dragging a slider must never update the text fields in the perspective.
        """

        self.current_perspective = "Invariant"
        self.manager.perspectiveChanged(self.current_perspective)
        widget = self.manager.perspective()
        chk_widget = getattr(widget, checkbox)
        end_widget = getattr(widget, end)
        start_widget = getattr(widget, start) if start else None
        chk_widget.setChecked(True)
        self.manager.filesWidget.sendData()

        assert widget._data is self.data, "Perspective should have received the data from the manager"
        assert end_widget.text() != ""
        if start_widget:
            assert start_widget.text() != ""

        # Mirror the slider attributes exactly as plot_result() sets them
        self.data.show_q_range_sliders = True
        self.data.slider_update_on_move = False
        self.data.slider_perspective_name = self.current_perspective
        self.data.slider_low_q_input = start_widget.text() if start_widget else 1e-5
        self.data.slider_high_q_input = end_widget.text()

        self.plotter.plot(self.data)
        self.slider = QRangeSlider(self.plotter, self.plotter.ax, data=self.data)

        assert len(self.plotter.sliders) == 1
        assert not self.slider.updateOnMove, "Invariant sliders should not update on move"

        # Moving the slider should not update the text fields
        if start_widget:
            original_start = start_widget.text()
        original_end = end_widget.text()

        self.slider.line_min.move(self.data.x[1], self.data.y[1], None)
        self.slider.line_max.move(self.data.x[-2], self.data.y[-2], None)

        if start_widget:
            assert start_widget.text() == original_start
        assert end_widget.text() == original_end

        # Editing the text fields should update the sliders
        if start_widget:
            start_widget.setText(f"{self.data.x[1]}")
            assert self.slider.line_min.x == pytest.approx(float(start_widget.text()), abs=1e-7)
        end_widget.setText(f"{self.data.x[-2]}")
        assert self.slider.line_max.x == pytest.approx(float(end_widget.text()), abs=1e-7)

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
        self.data.slider_low_q_input = ['currentTab', 'minQInput']
        self.data.slider_low_q_setter = ['currentTab', 'updateMinQ']
        self.data.slider_high_q_input = ['currentTab', 'maxQInput']
        self.data.slider_high_q_setter = ['currentTab', 'updateMaxQ']
        self.plotter.plot(self.data)
        self.slider = QRangeSlider(self.plotter, self.plotter.ax, data=self.data)
        # Check inputs are linked properly.
        assert len(self.plotter.sliders) == 1
        slider = self.plotter.sliders.pop(list(self.plotter.sliders.keys())[0])
        assert slider.line_min.setter == widget.updateMinQ
        assert slider.line_max.setter == widget.updateMaxQ
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
