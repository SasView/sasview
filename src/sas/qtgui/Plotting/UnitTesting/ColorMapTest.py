
import matplotlib as mpl
import pytest
from PySide6 import QtGui, QtWidgets

mpl.use("Qt5Agg")


import sas.qtgui.Plotting.Plotter2D as Plotter2D

# Local
from sas.qtgui.Plotting.ColorMap import ColorMap
from sas.qtgui.Plotting.PlotterData import Data2D
from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy


class ColorMapTest:
    '''Test the ColorMap'''

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the ColorMap'''
        plotter = Plotter2D.Plotter2D(None, quickplot=True)

        data = Data2D(image=[0.1]*4,
                           qx_data=[1.0, 2.0, 3.0, 4.0],
                           qy_data=[10.0, 11.0, 12.0, 13.0],
                           dqx_data=[0.1, 0.2, 0.3, 0.4],
                           dqy_data=[0.1, 0.2, 0.3, 0.4],
                           q_data=[1,2,3,4],
                           xmin=-1.0, xmax=5.0,
                           ymin=-1.0, ymax=15.0,
                           zmin=-1.0, zmax=20.0)

        # setup failure: 2022-09
        # The data object does not have xmin/xmax etc set in it; the values
        # are initially set by Data2D's call to PlottableData2D.__init__
        # but are then *unset* by call to LoadData2D.__init__ since they
        # are not explicitly passed to that constructor, and that constructor
        # saves all values. Lack of xmin/xmax etc means that the following
        # instantiation of the ColorMap class fails.

        data.title="Test data"
        data.id = 1
        w = ColorMap(parent=plotter, data=data)

        yield w

        '''Destroy the GUI'''
        w.close()

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testDefaults(self, widget):
        '''Test the GUI in its default state'''
        assert isinstance(widget, QtWidgets.QDialog)

        assert widget._cmap_orig == "jet"
        assert len(widget.all_maps) == 150
        assert len(widget.maps) == 75
        assert len(widget.rmaps) == 75

        assert widget.lblWidth.text() == "0"
        assert widget.lblHeight.text() == "0"
        assert widget.lblQmax.text() == "18"
        assert widget.lblStopRadius.text() == "-1"
        assert not widget.chkReverse.isChecked()
        assert widget.cbColorMap.count() == 75
        assert widget.cbColorMap.currentIndex() == 60

        # validators
        assert isinstance(widget.txtMinAmplitude.validator(), QtGui.QDoubleValidator)
        assert isinstance(widget.txtMaxAmplitude.validator(), QtGui.QDoubleValidator)

        # Ranges
        assert widget.txtMinAmplitude.text() == "0"
        assert widget.txtMaxAmplitude.text() == "100"
        assert isinstance(widget.slider, QtWidgets.QSlider)

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnReset(self, widget):
        '''Check the dialog reset function'''
        # Set some controls to non-default state
        widget.cbColorMap.setCurrentIndex(20)
        widget.chkReverse.setChecked(True)
        widget.txtMinAmplitude.setText("20.0")

        # Reset the widget state
        widget.onReset()

        # Assure things went back to default
        assert widget.cbColorMap.currentIndex() == 20
        assert not widget.chkReverse.isChecked()
        assert widget.txtMinAmplitude.text() == "0"

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnApply(self, widget):
        '''Check the dialog apply function'''
        # Set some controls to non-default state
        widget.show()
        widget.cbColorMap.setCurrentIndex(20) # PuRd_r
        widget.chkReverse.setChecked(True)
        widget.txtMinAmplitude.setText("20.0")

        spy_apply = QtSignalSpy(widget, widget.apply_signal)
        # Reset the widget state
        widget.onApply()

        # Assure the widget is still up and the signal was sent.
        assert widget.isVisible()
        assert spy_apply.count() == 1
        assert 'PuRd_r' in spy_apply.called()[0]['args'][1]

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testInitMapCombobox(self, widget):
        '''Test the combo box initializer'''
        # Set a color map from the direct list
        widget._cmap = "gnuplot"
        widget.initMapCombobox()

        # Check the combobox
        assert widget.cbColorMap.currentIndex() == 55
        assert not widget.chkReverse.isChecked()

        # Set a reversed value
        widget._cmap = "hot_r"
        widget.initMapCombobox()
        # Check the combobox
        assert widget.cbColorMap.currentIndex() == 56
        assert widget.chkReverse.isChecked()

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testInitRangeSlider(self, widget):
        '''Test the range slider initializer'''
        # Set a color map from the direct list
        widget._cmap = "gnuplot"
        widget.initRangeSlider()

        # Check the values
        assert widget.slider.minimum() == 0
        assert widget.slider.maximum() == 100
        assert widget.slider.orientation() == 1

        # Emit new low value
        widget.slider.lowValueChanged.emit(5)
        # Assure the widget received changes
        assert widget.txtMinAmplitude.text() == "5"

        # Emit new high value
        widget.slider.highValueChanged.emit(45)
        # Assure the widget received changes
        assert widget.txtMaxAmplitude.text() == "45"

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnMapIndexChange(self, widget, mocker):
        '''Test the response to the combo box index change'''

        mocker.patch.object(widget.canvas, 'draw')
        mocker.patch.object(mpl.colorbar, 'ColorbarBase')

        # simulate index change
        widget.cbColorMap.setCurrentIndex(1)

        # Check that draw() got called
        assert widget.canvas.draw.called
        assert mpl.colorbar.ColorbarBase.called

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnColorMapReversed(self, widget, mocker):
        '''Test reversing the color map functionality'''
        # Check the defaults
        assert widget._cmap == "jet"
        mocker.patch.object(widget.cbColorMap, 'addItems')

        # Reverse the choice
        widget.onColorMapReversed(True)

        # check the behaviour
        assert widget._cmap == "jet_r"
        assert widget.cbColorMap.addItems.called

    @pytest.mark.skip(reason="2022-09 already broken - causes segfault")
    def testOnAmplitudeChange(self, widget, mocker):
        '''Check the callback method for responding to changes in textboxes'''
        mocker.patch.object(widget.canvas, 'draw')
        mocker.patch.object(mpl.colors, 'Normalize')
        mocker.patch.object(mpl.colorbar, 'ColorbarBase')

        widget.vmin = 0.0
        widget.vmax = 100.0

        # good values in fields
        widget.txtMinAmplitude.setText("1.0")
        widget.txtMaxAmplitude.setText("10.0")

        widget.onAmplitudeChange()

        # Check the arguments to Normalize
        mpl.colors.Normalize.assert_called_with(vmin=1.0, vmax=10.0)
        assert widget.canvas.draw.called

        # Bad values in fields
        widget.txtMinAmplitude.setText("cake")
        widget.txtMaxAmplitude.setText("more cake")

        widget.onAmplitudeChange()

        # Check the arguments to Normalize - should be defaults
        mpl.colors.Normalize.assert_called_with(vmin=0.0, vmax=100.0)
        assert widget.canvas.draw.called
