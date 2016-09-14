"""
    CanSAS 2D data reader for reading HDF5 formatted CanSAS files.
"""

import numpy as np
import re
import os
import sys

from sas.sascalc.dataloader.readers.xml_reader import XMLreader
from sas.sascalc.dataloader.data_info import plottable_1D, Data1D, Sample, Source
from sas.sascalc.dataloader.data_info import Process, Aperture, Collimation, TransmissionSpectrum, Detector


class Reader(XMLreader):
    """
    A class for reading in CanSAS v2.0 data files. The existing iteration opens Mantid generated HDF5 formatted files
    with file extension .h5/.H5. Any number of data sets may be present within the file and any dimensionality of data
    may be used. Currently 1D and 2D SAS data sets are supported, but future implementations will include 1D and 2D
    SESANS data. This class assumes a single data set for each sasentry.

    :Dependencies:
        The CanSAS HDF5 reader requires h5py v2.5.0 or later.
    """

    ## Logged warnings or messages
    logging = None
    ## List of errors for the current data set
    errors = None
    ## Raw file contents to be processed
    raw_data = None
    ## Data set being modified
    current_dataset = None
    ## For recursion and saving purposes, remember parent objects
    parent_list = None
    ## Data type name
    type_name = "Anton Paar SAXSess"
    ## Wildcards
    type = ["Anton Paar SAXSess Files (*.pdh)|*.pdh"]
    ## List of allowed extensions
    ext = ['.pdh', '.PDH']
    ## Flag to bypass extension check
    allow_all = False
    ## List of files to return
    output = None

    def reset_state(self):
        self.current_dataset = Data1D(np.empty(0), np.empty(0),
                                            np.empty(0), np.empty(0))
        self.datasets = []
        self.raw_data = None
        self.errors = set()
        self.logging = []
        self.output = []
        self.detector = Detector()
        self.collimation = Collimation()
        self.aperture = Aperture()
        self.process = Process()
        self.source = Source()
        self.sample = Sample()
        self.trans_spectrum = TransmissionSpectrum()
        self.upper = 5
        self.lower = 5

    def read(self, filename):
        """
            This is the general read method that all SasView data_loaders must have.

            :param filename: A path for an XML formatted Anton Paar SAXSess data file.
            :return: List of Data1D objects or a list of errors.
            """

        ## Reinitialize the class when loading a new data file to reset all class variables
        self.reset_state()
        ## Check that the file exists
        if os.path.isfile(filename):
            basename = os.path.basename(filename)
            _, extension = os.path.splitext(basename)
            # If the file type is not allowed, return empty list
            if extension in self.ext or self.allow_all:
                ## Load the data file
                input_f = open(filename, 'r')
                buff = input_f.read()
                self.raw_data = buff.splitlines()
                self.read_data()
        return self.output

    def read_data(self):
        q_unit = "1/nm"
        i_unit = "1/um^2"
        self.current_dataset.title = self.raw_data[0]
        self.current_dataset.meta_data["Keywords"] = self.raw_data[1]
        line3 = self.raw_data[2].split()
        line4 = self.raw_data[3].split()
        line5 = self.raw_data[4].split()
        self.data_points = int(line3[0])
        self.lower = 5
        self.upper = self.lower + self.data_points
        self.source.radiation = 'x-ray'
        normal = float(line4[3])
        self.current_dataset.source.radiation = "x-ray"
        self.current_dataset.source.name = "Anton Paar SAXSess Instrument"
        self.current_dataset.source.wavelength = float(line4[4])
        xvals = []
        yvals = []
        dyvals = []
        for i in range(self.lower, self.upper):
            index = i - self.lower
            data = self.raw_data[i].split()
            xvals.insert(index, normal * float(data[0]))
            yvals.insert(index, normal * float(data[1]))
            dyvals.insert(index, normal * float(data[2]))
        self.current_dataset.x = np.append(self.current_dataset.x, xvals)
        self.current_dataset.y = np.append(self.current_dataset.y, yvals)
        self.current_dataset.dy = np.append(self.current_dataset.dy, dyvals)
        if self.data_points != self.current_dataset.x.size:
            self.errors.add("Not all data was loaded properly.")
        if self.current_dataset.dx.size != self.current_dataset.x.size:
            dxvals = np.zeros(self.current_dataset.x.size)
            self.current_dataset.dx = dxvals
        if self.current_dataset.x.size != self.current_dataset.y.size:
            self.errors.add("The x and y data sets are not the same size.")
        if self.current_dataset.y.size != self.current_dataset.dy.size:
            self.errors.add("The y and dy datasets are not the same size.")
        self.current_dataset.errors = self.errors
        self.current_dataset.xaxis("Q", q_unit)
        self.current_dataset.yaxis("Intensity", i_unit)
        xml_intermediate = self.raw_data[self.upper:]
        xml = ''.join(xml_intermediate)
        self.set_xml_string(xml)
        dom = self.xmlroot.xpath('/fileinfo')
        self._parse_child(dom)
        self.output.append(self.current_dataset)

    def _parse_child(self, dom, parent=''):
        """
        Recursive method for stepping through the embedded XML
        :param dom: XML node with or without children
        """
        for node in dom:
            tagname = node.tag
            value = node.text
            attr = node.attrib
            key = attr.get("key", '')
            if len(node.getchildren()) > 1:
                self._parse_child(node, key)
                if key == "SampleDetector":
                    self.current_dataset.detector.append(self.detector)
                    self.detector = Detector()
            else:
                if key == "value":
                    if parent == "Wavelength":
                        self.current_dataset.source.wavelength = value
                    elif parent == "SampleDetector":
                        self.detector.distance = value
                    elif parent == "Temperature":
                        self.current_dataset.sample.temperature = value
                    elif parent == "CounterSlitLength":
                        self.detector.slit_length = value
                elif key == "unit":
                    value = value.replace("_", "")
                    if parent == "Wavelength":
                        self.current_dataset.source.wavelength_unit = value
                    elif parent == "SampleDetector":
                        self.detector.distance_unit = value
                    elif parent == "X":
                        self.current_dataset.xaxis(self.current_dataset._xaxis, value)
                    elif parent == "Y":
                        self.current_dataset.yaxis(self.current_dataset._yaxis, value)
                    elif parent == "Temperature":
                        self.current_dataset.sample.temperature_unit = value
                    elif parent == "CounterSlitLength":
                        self.detector.slit_length_unit = value
                elif key == "quantity":
                    if parent == "X":
                        self.current_dataset.xaxis(value, self.current_dataset._xunit)
                    elif parent == "Y":
                        self.current_dataset.yaxis(value, self.current_dataset._yunit)
