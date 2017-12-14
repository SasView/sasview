"""
This object is a small tool to allow user to quickly
determine the variance in q  from the
instrumental parameters.
"""
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from twisted.internet import threads
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterData import Data2D
from sas.qtgui.Plotting.Plotter2D import Plotter2DWidget
from sas.sascalc.calculator.resolution_calculator import ResolutionCalculator
import matplotlib.patches as patches

import numpy
import sys
import logging
import os
import re

from .UI.ResolutionCalculatorPanelUI import Ui_ResolutionCalculatorPanel

_SOURCE_MASS = {'Alpha': 6.64465620E-24,
                'Deuteron': 3.34358320E-24,
                'Neutron': 1.67492729E-24,
                'Photon': 0.0,
                'Proton': 1.67262137E-24,
                'Triton': 5.00826667E-24}

BG_WHITE = "background-color: rgb(255, 255, 255);"
BG_RED = "background-color: rgb(244, 170, 164);"


class ResolutionCalculatorPanel(QtWidgets.QDialog, Ui_ResolutionCalculatorPanel):
    """
    compute resolution in 2D
    """
    def __init__(self, parent=None):
        super(ResolutionCalculatorPanel, self).__init__()
        self.setupUi(self)
        self.manager = parent

        # New font to display angstrom symbol
        new_font = 'font-family: -apple-system, "Helvetica Neue", "Ubuntu";'
        self.lblUnitWavelength.setStyleSheet(new_font)
        self.lblUnitQx.setStyleSheet(new_font)
        self.lblUnitQy.setStyleSheet(new_font)
        self.lblUnitSigmax.setStyleSheet(new_font)
        self.lblUnitSigmay.setStyleSheet(new_font)
        self.lblUnitSigmalamd.setStyleSheet(new_font)
        self.lblUnit1DSigma.setStyleSheet(new_font)

        # by default Spectrum label and cbCustomSpectrum are not visible
        self.cbCustomSpectrum.setVisible(False)
        self.lblSpectrum.setVisible(False)
        # self.onReset()

        # change index of comboboxes
        self.cbWaveColor.currentIndexChanged.connect(self.onSelectWaveColor)
        self.cbCustomSpectrum.currentIndexChanged.connect(self.onSelectCustomSpectrum)

        # push buttons
        self.cmdClose.clicked.connect(self.accept)
        self.cmdHelp.clicked.connect(self.onHelp)
        self.cmdCompute.clicked.connect(self.onCompute)
        self.cmdReset.clicked.connect(self.onReset)

        # input defaults
        self.qx = []
        self.qy = []
        # dQ defaults
        self.sigma_r = None
        self.sigma_phi = None
        self.sigma_1d = None

        # number of bins for wavelength and wavelength spread
        self.num_wave = 10
        self.spectrum_dic = {}

        # dQ 2d image
        self.image = None
        # Source selection dic
        self.source_mass = _SOURCE_MASS
        # detector coordinate of estimation of sigmas
        self.det_coordinate = 'cartesian'

        self.resolution = ResolutionCalculator()
        self.spectrum_dic['Add new'] = ''
        self.spectrum_dic['Flat'] = self.resolution.get_default_spectrum()
        self.resolution.set_spectrum(self.spectrum_dic['Flat'])

        # validators
        self.txtWavelength.editingFinished.connect(self.checkWavelength)
        self.txtWavelengthSpread.editingFinished.connect(self.checkWavelengthSpread)

        self.txtDetectorPixSize.editingFinished.connect(self.checkPixels)
        self.txtDetectorSize.editingFinished.connect(self.checkPixels)

        self.txtSourceApertureSize.editingFinished.connect(self.checkAperture)
        self.txtSampleApertureSize.editingFinished.connect(self.checkAperture)

        self.txtQx.editingFinished.connect(self.checkQx_y)
        self.txtQy.editingFinished.connect(self.checkQx_y)

        # double validator
        self.txtSource2SampleDistance.setValidator(GuiUtils.DoubleValidator())
        self.txtSample2DetectorDistance.setValidator(GuiUtils.DoubleValidator())
        self.txtSampleOffset.setValidator(GuiUtils.DoubleValidator())

        # call compute to calculate with default values
        self.createTemplate2DPlot()
        #self.onCompute()

    # #################################
    # Validators: red background in line edits when wrong input
    # and display of info logging message
    # #################################

    def checkWavelength(self):
        """ Validator for Wavelength
         if TOF, wavelength = min - max else only one number """
        text_edit = self.txtWavelength  # self.sender()
        if text_edit.isModified():
            text_edit.setStyleSheet(BG_WHITE)
            input_string = str(text_edit.text())
            if self.cbWaveColor.currentText() != 'TOF':
                input_wavelength = re.match('\d+\.?\d*', input_string)
                if input_wavelength is None:
                    text_edit.setStyleSheet(BG_RED)
                    self.cmdCompute.setEnabled(False)
                    logging.info('Wavelength has to be a number.')
                else:
                    text_edit.setStyleSheet(BG_WHITE)
                    self.cmdCompute.setEnabled(True)
            else:
                interval_wavelength = re.match('^\d+\.?\d*\s*-\s*\d+\.?\d*$',
                                               input_string)

                if interval_wavelength is None:
                    text_edit.setStyleSheet(BG_RED)
                    self.cmdCompute.setEnabled(False)
                    logging.info("Wavelength's input has to be an interval: "
                                 "min - max.")
                else:
                    # check on min < max
                    [wavelength_min, wavelength_max] = \
                        re.findall('\d+\.?\d*', interval_wavelength.group())

                    if float(wavelength_min) >= float(wavelength_max):
                        text_edit.setStyleSheet(BG_RED)
                        self.cmdCompute.setEnabled(False)
                        logging.info("Wavelength: min must be smaller than max.")

                    else:
                        text_edit.setStyleSheet(BG_WHITE)
                        self.cmdCompute.setEnabled(True)

    def checkWavelengthSpread(self):
        """ Validator for WavelengthSpread
         Input can be a 'number or min - max (; Number of bins)' """
        text_edit = self.sender()

        if text_edit.isModified():
            text_edit.setStyleSheet(BG_WHITE)
            if self.cbWaveColor.currentText() != 'TOF':
                pattern = '^\d+\.?\d*(|;\s*\d+)$'
                input_string = str(text_edit.text())
                wavelength_spread_input = re.match(pattern, input_string)

                if wavelength_spread_input is None:
                    text_edit.setStyleSheet(BG_RED)
                    self.cmdCompute.setEnabled(False)
                    logging.info('Wavelength spread has to be specified: '
                                 'single value or value; integer number of bins.')

                else:
                    split_input = wavelength_spread_input.group().split(';')
                    self.num_wave = split_input[1] if len(split_input) > 1 else 10
                    text_edit.setStyleSheet(BG_WHITE)
                    self.cmdCompute.setEnabled(True)
            else:
                pattern = '^\d+\.?\d*\s*-\s*\d+\.?\d*(|;\s*\d+)$'
                input_string = str(text_edit.text())
                wavelength_spread_input = re.match(pattern, input_string)

                if wavelength_spread_input is None:
                    text_edit.setStyleSheet(BG_RED)
                    self.cmdCompute.setEnabled(False)
                    logging.info("Wavelength spread has to be specified: "
                                 "doublet separated by '-' with optional "
                                 "number of bins (given after ';'). "
                                 "For example, 0.1 - 0.1 (; 20).")

                else:
                    split_input = wavelength_spread_input.group().split(';')
                    self.num_wave = split_input[1] if len(
                        split_input) > 1 else 10
                    text_edit.setStyleSheet(BG_WHITE)
                    self.cmdCompute.setEnabled(True)

    def checkPixels(self):
        """ Validator for detector pixel size and number """
        text_edit = self.sender()

        if text_edit.isModified():
            text_edit.setStyleSheet(BG_WHITE)
            pattern = '^\d+\.?\d*,\s*\d+\.?\d*$'
            input_string = str(text_edit.text())
            pixels_input = re.match(pattern, input_string)

            if pixels_input is None:
                text_edit.setStyleSheet(BG_RED)
                self.cmdCompute.setEnabled(False)
                logging.info('The input for the detector should contain 2 '
                             'values separated by a comma.')

            else:
                text_edit.setStyleSheet(BG_WHITE)
                self.cmdCompute.setEnabled(True)

    def checkQx_y(self):
        """ Validator for qx and qy inputs """
        Q_modified = [self.txtQx.isModified(), self.txtQy.isModified()]
        if any(Q_modified):
            pattern = '^-?\d+\.?\d*(,\s*-?\d+\.?\d*)*$'
            text_edit = self.txtQx if Q_modified[0] else self.txtQy
            input_string = str(text_edit.text())
            q_input = re.match(pattern, input_string)
            if q_input is None:
                text_edit.setStyleSheet(BG_RED)
                self.cmdCompute.setEnabled(False)
                logging.info('Qx and Qy should contain one or more comma-separated numbers.')
            else:
                text_edit.setStyleSheet(BG_WHITE)
                self.cmdCompute.setEnabled(True)
                qx = str(self.txtQx.text()).split(',')
                qy = str(self.txtQy.text()).split(',')

                if len(qx) == 1 and len(qy) > 1:
                    fill_qx = ', '.join([qx[0]] * len(qy))
                    self.txtQx.setText(fill_qx)

                elif len(qy) == 1 and len(qx) > 1:
                    fill_qy = ', '.join([qy[0]] * len(qx))
                    self.txtQy.setText(fill_qy)

                elif len(qx) != len(qy):
                    text_edit.setStyleSheet(BG_RED)
                    self.cmdCompute.setEnabled(False)
                    logging.info(
                        'Qx and Qy should have the same number of elements.')

                else:
                    text_edit.setStyleSheet(BG_WHITE)
                    self.cmdCompute.setEnabled(True)

    def checkAperture(self):
        """ Validator for Sample and Source apertures"""
        text_edit = self.sender()

        if text_edit.isModified():
            text_edit.setStyleSheet(BG_WHITE)
            input_string = str(text_edit.text())
            pattern = '^\d+\.?\d*(|,\s*\d+)$'
            aperture_input = re.match(pattern, input_string)

            if aperture_input is None:
                text_edit.setStyleSheet(BG_RED)
                self.cmdCompute.setEnabled(False)
                logging.info('A circular aperture is defined by a single '
                             'value (diameter). A rectangular aperture is '
                             'defined by 2 values separated by a comma.')

            else:
                text_edit.setStyleSheet(BG_WHITE)
                self.cmdCompute.setEnabled(True)

    # #################################
    # Slots associated with signals from comboboxes
    # #################################

    def onSelectWaveColor(self):
        """ Modify layout of GUI when TOF selected: add elements
        and modify default entry of Wavelength """
        list_wdata = self.resolution.get_wave_list()
        min_lambda = min(list_wdata[0])

        min_wspread = min(list_wdata[1])
        max_wspread = max(list_wdata[1])

        if self.cbWaveColor.currentText() == 'TOF':
            self.cbCustomSpectrum.setVisible(True)
            self.lblSpectrum.setVisible(True)
            # Get information about wavelength and spread

            if len(list_wdata[0]) < 2:
                max_lambda = 2 * min_lambda
            else:
                max_lambda = max(list_wdata[0])
            self.txtWavelength.setText('{} - {}'.format(min_lambda, max_lambda))
            self.txtWavelengthSpread.setText('{} - {}'.format(min_wspread,
                                                    max_wspread))

        else:
            self.cbCustomSpectrum.setVisible(False)
            self.lblSpectrum.setVisible(False)
            # modify Wavelength line edit only if set for TOF (2 elements)

            if len(self.txtWavelength.text().split('-')) >= 2:
                self.txtWavelength.setText(str(min_lambda))
                self.txtWavelengthSpread.setText(str(min_wspread))

    def onSelectCustomSpectrum(self):
        """ On Spectrum Combobox event"""
        if self.cbCustomSpectrum.currentText() == 'Add New':
            datafile = QtWidgets.QFileDialog.getOpenFileName(
                self, "Choose a spectral distribution file","",
                "All files (*.*)", None,
                QtWidgets.QFileDialog.DontUseNativeDialog)[0]

            if datafile is None or str(datafile) == '':
                logging.info("No spectral distribution data chosen.")
                self.cbCustomSpectrum.setCurrentIndex(0)
                self.resolution.set_spectrum(self.spectrum_dic['Flat'])
                return

            try:
                basename = os.path.basename(datafile)
                if basename not in list(self.spectrum_dic.keys()):
                    self.cbCustomSpectrum.addItem(basename)

                input_f = open(datafile, 'r')
                buff = input_f.read()
                lines = buff.split('\n')

                wavelength = []
                intensity = []

                for line in lines:
                    toks = line.split()
                    try:
                        wave = float(toks[0])
                        intens = float(toks[1])
                        wavelength.append(wave)
                        intensity.append(intens)
                    except:
                        logging.info('Could not extract values from file')
            except:
                raise

            self.spectrum_dic[basename] = [wavelength, intensity]
            self.resolution.set_spectrum(self.spectrum_dic[basename])
        return

    # #################################
    # Slots associated with signals from push buttons
    # #################################

    def onHelp(self):
        """
        Bring up the Resolution Calculator Documentation whenever
        the HELP button is clicked.
        Calls Documentation Window with the path of the location within the
        documentation tree (after /doc/ ....".
        """
        location = "/user/sasgui/perspectives/calculator/resolution_calculator_help.html"
        self.manager.showHelp(location)

    def onReset(self):
        # by default Spectrum label and cbCustomSpectrum are not visible
        self.cbCustomSpectrum.setVisible(False)
        self.lblSpectrum.setVisible(False)
        # Comboboxes
        self.cbCustomSpectrum.setCurrentIndex([self.cbCustomSpectrum.itemText(i)
                                               for i in range(self.cbCustomSpectrum.count())].index('Flat'))
        self.cbSource.setCurrentIndex([self.cbSource.itemText(i) for i in
                                       range(self.cbSource.count())].index('Neutron'))
        self.cbWaveColor.setCurrentIndex([self.cbWaveColor.itemText(i) for i
                                          in range(self.cbWaveColor.count())].index('Monochromatic'))
        # LineEdits
        self.txtDetectorPixSize.setText('0.5, 0.5')
        self.txtDetectorSize.setText('128, 128')
        self.txtSample2DetectorDistance.setText('1000')
        self.txtSampleApertureSize.setText('1.27')
        self.txtSampleOffset.setText('0')
        self.txtSource2SampleDistance.setText('1627')
        self.txtSourceApertureSize.setText('3.81')
        self.txtWavelength.setText('6.0')
        self.txtWavelengthSpread.setText('0.125')
        self.txtQx.setText('0.0')
        self.txtQy.setText('0.0')
        self.txt1DSigma.setText('0.0008289')
        self.txtSigma_x.setText('0.0008288')
        self.txtSigma_y.setText('0.0008288')
        self.txtSigma_lamd.setText('3.168e-05')

        self.image = None
        self.source_mass = _SOURCE_MASS
        self.det_coordinate = 'cartesian'
        self.num_wave = 10
        self.spectrum_dic = {}
        self.spectrum_dic['Add new'] = ''
        self.spectrum_dic['Flat'] = self.resolution.get_default_spectrum()
        self.resolution.set_spectrum(self.spectrum_dic['Flat'])
        # Reset plot
        self.onCompute()

    # TODO Keep legacy validators??
    def onCompute(self):
        """
        Execute the computation of resolution
        """
        # Q min max list default
        qx_min = []
        qx_max = []
        qy_min = []
        qy_max = []
        # possible max qrange
        self.resolution.qxmin_limit = 0
        self.resolution.qxmax_limit = 0
        self.resolution.qymin_limit = 0
        self.resolution.qymax_limit = 0

        try:
            # Get all the values to compute
            wavelength = self._str2longlist(self.txtWavelength.text())

            source = self.cbSource.currentText()
            mass = self.source_mass[str(source)]
            self.resolution.set_neutron_mass(float(mass))

            wavelength_spread = self._str2longlist(\
                        self.txtWavelengthSpread.text().split(';')[0])
            # Validate the wave inputs
            wave_input = self._validate_q_input(wavelength, wavelength_spread)
            if wave_input is not None:
                wavelength, wavelength_spread = wave_input

            self.resolution.set_wave(wavelength)
            self.resolution.set_wave_spread(wavelength_spread)

            # use legacy validator for correct input assignment

            source_aperture_size = self.txtSourceApertureSize.text()
            source_aperture_size = self._str2longlist(source_aperture_size)
            self.resolution.set_source_aperture_size(source_aperture_size)

            sample_aperture_size = self.txtSampleApertureSize.text()
            sample_aperture_size = self._string2list(sample_aperture_size)
            self.resolution.set_sample_aperture_size(sample_aperture_size)

            source2sample_distance = self.txtSource2SampleDistance.text()
            source2sample_distance = self._string2list(source2sample_distance)
            self.resolution.set_source2sample_distance(source2sample_distance)

            sample2sample_distance = self.txtSampleOffset.text()
            sample2sample_distance = self._string2list(sample2sample_distance)
            self.resolution.set_sample2sample_distance(sample2sample_distance)

            sample2detector_distance = self.txtSample2DetectorDistance.text()
            sample2detector_distance = self._string2list(
                sample2detector_distance)
            self.resolution.set_sample2detector_distance(
                sample2detector_distance)

            detector_size = self.txtDetectorSize.text()
            detector_size = self._string2list(detector_size)
            self.resolution.set_detector_size(detector_size)

            detector_pix_size = self.txtDetectorPixSize.text()
            detector_pix_size = self._string2list(detector_pix_size)
            self.resolution.set_detector_pix_size(detector_pix_size)

            self.qx = self._string2inputlist(self.txtQx.text())
            self.qy = self._string2inputlist(self.txtQy.text())

            # Find min max of qs
            xmin = min(self.qx)
            xmax = max(self.qx)
            ymin = min(self.qy)
            ymax = max(self.qy)
            if not self._validate_q_input(self.qx, self.qy):
                raise ValueError("Invalid Q input")
        except:
            msg = "An error occurred during the resolution computation."
            msg += "Please check your inputs..."
            logging.warning(msg)
            return

        # Validate the q inputs
        q_input = self._validate_q_input(self.qx, self.qy)
        if q_input is not None:
            self.qx, self.qy = q_input

        # Make list of q min max for mapping
        for i in range(len(self.qx)):
            qx_min.append(xmin)
            qx_max.append(xmax)
        for i in range(len(self.qy)):
            qy_min.append(ymin)
            qy_max.append(ymax)

        # Compute the resolution
        if self.image is not None:
            self.resolution.reset_image()

        # Compute and get the image plot
        try:
            cal_res = threads.deferToThread(self.map_wrapper,
                                            self.calc_func,
                                            self.qx,
                                            self.qy,
                                            qx_min,
                                            qx_max,
                                            qy_min, qy_max)

            cal_res.addCallback(self.complete)
            cal_res.addErrback(self.calculateFailed)

            # logging.info("Computation is in progress...")
            self.cmdCompute.setText('Wait...')
            self.cmdCompute.setEnabled(False)
        except:
            raise

    def calculateFailed(self, reason):
        print("calculateFailed Failed with:\n", reason)
        pass

    def complete(self, image):
        """
        Complete computation
        """
        self.image = image

        # Get and format the sigmas
        sigma_r = self.formatNumber(self.resolution.sigma_1)
        sigma_phi = self.formatNumber(self.resolution.sigma_2)
        sigma_lamd = self.formatNumber(self.resolution.sigma_lamd)
        sigma_1d = self.formatNumber(self.resolution.sigma_1d)

        # Set output values
        self.txtSigma_x.setText(str(sigma_r))
        self.txtSigma_y.setText(str(sigma_phi))
        self.txtSigma_lamd.setText(str(sigma_lamd))
        self.txt1DSigma.setText(str(sigma_1d))

        self.cmdCompute.setText('Compute')
        self.cmdCompute.setEnabled(True)

        self.new2DPlot()

        return

    def map_wrapper(self, func, qx, qy, qx_min, qx_max, qy_min, qy_max):
        """
        Prepare the Mapping for the computation
        : params qx, qy, qx_min, qx_max, qy_min, qy_max:
        : return: image (numpy array)
        """
        image = list(map(func, qx, qy,
                    qx_min, qx_max,
                    qy_min, qy_max))[0]

        return image

    def calc_func(self, qx, qy, qx_min, qx_max, qy_min, qy_max):
        """
        Perform the calculation for a given set of Q values.
        : return: image (numpy array)
        """
        try:
            qx_value = float(qx)
            qy_value = float(qy)
        except :
            raise ValueError

        # calculate 2D resolution distribution image
        image = self.resolution.compute_and_plot(qx_value, qy_value,
                                                 qx_min, qx_max, qy_min,
                                                 qy_max,
                                                 self.det_coordinate)
        return image

    # #################################
    # Legacy validators
    # #################################
    def _string2list(self, input_string):
        """
        Change NNN, NNN to list,ie. [NNN, NNN] where NNN is a number
        """
        new_numbers_list = []
        # check the number of floats
        try:
            strg = float(input_string)
            new_numbers_list.append(strg)
        except:
            string_split = input_string.split(',')
            if len(string_split) == 1 or len(string_split) == 2:
                new_numbers_list = [float(item) for item in string_split]
            else:
                msg = "The numbers must be one or two (separated by ',')"
                logging.info(msg)
                raise RuntimeError(msg)

        return new_numbers_list

    def _string2inputlist(self, input_string):
        """
        Change NNN, NNN,... to list,ie. [NNN, NNN,...] where NNN is a number
        : return new_list: string like list
        """
        new_list = []
        string_split = input_string.split(',')
        try:
            new_list = [float(t) for t in string_split]
        except:
            logging.error(sys.exc_info()[1])
        return new_list

    def _str2longlist(self, input_string):
        """
          Change NNN, NNN,... to list, NNN - NNN ; NNN to list, or float to list
          : return new_string: string like list
          """
        try:
            # is float
            out = [float(input_string)]
            return out
        except:
            if self.cbWaveColor.currentText() == 'Monochromatic':
                logging.warning("Wrong format of inputs.")
            else:
                try:
                    # has a '-'
                    if input_string.count('-') > 0:
                        value = input_string.split('-')
                        if value[1].count(';') > 0:
                            # has a ';'
                            last_list = value[1].split(';')
                            num = numpy.ceil(float(last_list[1]))
                            max_value = float(last_list[0])
                            self.num_wave = num
                        else:
                            # default num
                            num = self.num_wave
                            max_value = float(value[1])
                        min_value = float(value[0])
                        # make a list
                        bin_size = numpy.fabs(max_value - min_value) / (num - 1)
                        out = [min_value + bin_size * bnum for bnum in
                               range(num)]
                        return out
                    if input_string.count(',') > 0:
                        out = self._string2inputlist(input_string)
                        return out
                except:
                    logging.error(sys.exc_info()[1])

    def _validate_q_input(self, qx, qy):
        """
        Check if q inputs are valid
        : params qx:  qx as a list
        : params qy:  qy as a list
        : return: True/False
        """
        # check qualifications
        if qx.__class__.__name__ != 'list':
            return None
        if qy.__class__.__name__ != 'list':
            return None
        if len(qx) < 1:
            return None
        if len(qy) < 1:
            return None
        # allow one input
        if len(qx) == 1 and len(qy) > 1:
            qx = [qx[0] for ind in range(len(qy))]

        if len(qy) == 1 and len(qx) > 1:
            qy = [qy[0] for ind in range(len(qx))]
        # check length
        if len(qx) != len(qy):
            return None
        if qx is None or qy is None:
            return None
        return qx, qy

    def formatNumber(self, value=None):
        """
        Return a float in a standardized, human-readable formatted string
        """
        try:
            value = float(value)
        except:
            output = None
            return output

        output = "%-7.4g" % value
        return output.lstrip().rstrip()

    # #################################
    # Plot
    # #################################

    def createTemplate2DPlot(self):
        """
        Create a template for 2D data
        """
        self.plotter = Plotter2DWidget(self, quickplot=True)
        self.plotter.scale = 'linear'
        self.plotter.cmap = None
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.graphicsView.setLayout(layout)
        layout.addWidget(self.plotter)

    def new2DPlot(self):
        """
        Create a new 2D data instance based on computing results
        """
        qx_min, qx_max, qy_min, qy_max = self.resolution.get_detector_qrange()

        dx_size = (qx_max - qx_min) / (1000 - 1)
        dy_size = (qy_max - qy_min) / (1000 - 1)
        x_val = numpy.arange(qx_min, qx_max, dx_size)
        y_val = numpy.arange(qy_max, qy_min, -dy_size)

        if len(self.plotter.ax.patches):
            self.plotter.ax.patches[0].remove()

        self.drawLines()

        self.plotter.data = Data2D(image=self.image,
                      qx_data=x_val,
                      qy_data=y_val,
                      xmin=qx_min, xmax=qx_max,
                      ymin=qy_min, ymax=qy_max)

        self.plotter.plot()
        self.plotter.show()
        self.plotter.update()

    def drawLines(self):
        """
        Draw lines in image if applicable
        """
        wave_list, _ = self.resolution.get_wave_list()
        if len(wave_list) > 1 and wave_list[-1] == max(wave_list):
            color = 'g'
            # draw a green rectangle(limit for the longest wavelength
            # to be involved) for tof inputs
            # Get the params from resolution
            # plotting range for largest wavelength
            qx_min = self.resolution.qx_min
            qx_max = self.resolution.qx_max
            qy_min = self.resolution.qy_min
            qy_max = self.resolution.qy_max
            # detector range
            detector_qx_min = self.resolution.detector_qx_min
            detector_qx_max = self.resolution.detector_qx_max
            detector_qy_min = self.resolution.detector_qy_min
            detector_qy_max = self.resolution.detector_qy_max

            rect = patches.Rectangle((detector_qx_min + 0.0002,
                                      detector_qy_min + 0.0002),
                                     detector_qx_max - detector_qx_min,
                                     detector_qy_max - detector_qy_min,
                                     linewidth=2,
                                     edgecolor=color, facecolor='none')
            self.plotter.ax.add_patch(rect)
        else:
            qx_min, qx_max, qy_min, qy_max = self.resolution.get_detector_qrange()
            # detector range
            detector_qx_min = self.resolution.qxmin_limit
            detector_qx_max = self.resolution.qxmax_limit
            detector_qy_min = self.resolution.qymin_limit
            detector_qy_max = self.resolution.qymax_limit

            xmin = min(self.qx)
            xmax = max(self.qx)
            ymin = min(self.qy)
            ymax = max(self.qy)

            if xmin < detector_qx_min or xmax > detector_qx_max or \
                            ymin < detector_qy_min or ymax > detector_qy_max:
                # message
                msg = 'At least one q value located out side of\n'
                msg += " the detector range (%s < qx < %s, %s < qy < %s),\n" % \
                       (self.formatNumber(detector_qx_min),
                        self.formatNumber(detector_qx_max),
                        self.formatNumber(detector_qy_min),
                        self.formatNumber(detector_qy_max))
                msg += " is ignored in computation.\n"

                logging.warning(msg)

        # Draw zero axis lines.
        if qy_min < 0 <= qy_max:
            self.plotter.ax.axhline(linewidth=1)

        if qx_min < 0 <= qx_max:
            self.plotter.ax.axvline(linewidth=1)
