"""
    CanSAS 2D data reader for reading HDF5 formatted CanSAS files.
"""

import numpy as np
import re
import os
import sys

from sas.sascalc.dataloader.readers.xml_reader import XMLreader
from sas.sascalc.dataloader.data_info import plottable_1D, Data1D, DataInfo, Sample, Source
from sas.sascalc.dataloader.data_info import Process, Aperture, Collimation, TransmissionSpectrum, Detector
from sas.sascalc.dataloader.loader_exceptions import FileContentsException, DataReaderException

class Reader(XMLreader):
    """
    A class for reading in Anton Paar .pdh files
    """

    ## Logged warnings or messages
    logging = None
    ## List of errors for the current data set
    errors = None
    ## Raw file contents to be processed
    raw_data = None
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

    def reset_state(self):
        self.current_dataset = plottable_1D(np.empty(0), np.empty(0), np.empty(0), np.empty(0))
        self.current_datainfo = DataInfo()
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

    def get_file_contents(self):
        """
            This is the general read method that all SasView data_loaders must have.

            :param filename: A path for an XML formatted Anton Paar SAXSess data file.
            :return: List of Data1D objects or a list of errors.
            """

        ## Reinitialize the class when loading a new data file to reset all class variables
        self.reset_state()
        buff = self.readall()
        self.raw_data = buff.splitlines()
        self.read_data()

    def read_data(self):
        correctly_loaded = True
        error_message = ""

        q_unit = "1/nm"
        i_unit = "1/um^2"
        try:
            self.current_datainfo.title = self.raw_data[0]
            self.current_datainfo.meta_data["Keywords"] = self.raw_data[1]
            line3 = self.raw_data[2].split()
            line4 = self.raw_data[3].split()
            line5 = self.raw_data[4].split()
            self.data_points = int(line3[0])
            self.lower = 5
            self.upper = self.lower + self.data_points
            self.source.radiation = 'x-ray'
            normal = float(line4[3])
            self.current_datainfo.source.radiation = "x-ray"
            self.current_datainfo.source.name = "Anton Paar SAXSess Instrument"
            self.current_datainfo.source.wavelength = float(line4[4])
            xvals = []
            yvals = []
            dyvals = []
            for i in range(self.lower, self.upper):
                index = i - self.lower
                data = self.raw_data[i].split()
                xvals.insert(index, normal * float(data[0]))
                yvals.insert(index, normal * float(data[1]))
                dyvals.insert(index, normal * float(data[2]))
        except Exception as e:
            error_message = "Couldn't load {}.\n".format(self.f_open.name)
            error_message += e.message
            raise FileContentsException(error_message)
        self.current_dataset.x = np.append(self.current_dataset.x, xvals)
        self.current_dataset.y = np.append(self.current_dataset.y, yvals)
        self.current_dataset.dy = np.append(self.current_dataset.dy, dyvals)
        if self.data_points != self.current_dataset.x.size:
            error_message += "Not all data points could be loaded.\n"
            correctly_loaded = False
        if self.current_dataset.x.size != self.current_dataset.y.size:
            error_message += "The x and y data sets are not the same size.\n"
            correctly_loaded = False
        if self.current_dataset.y.size != self.current_dataset.dy.size:
            error_message += "The y and dy datasets are not the same size.\n"
            correctly_loaded = False

        self.current_dataset.xaxis("Q", q_unit)
        self.current_dataset.yaxis("Intensity", i_unit)
        xml_intermediate = self.raw_data[self.upper:]
        xml = ''.join(xml_intermediate)
        try:
            self.set_xml_string(xml)
            dom = self.xmlroot.xpath('/fileinfo')
            self._parse_child(dom)
        except Exception as e:
            # Data loaded but XML metadata has an error
            error_message += "Data points have been loaded but there was an "
            error_message += "error reading XML metadata: " + e.message
            correctly_loaded = False
        self.send_to_output()
        if not correctly_loaded:
            raise DataReaderException(error_message)

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
                    self.current_datainfo.detector.append(self.detector)
                    self.detector = Detector()
            else:
                if key == "value":
                    if parent == "Wavelength":
                        self.current_datainfo.source.wavelength = value
                    elif parent == "SampleDetector":
                        self.detector.distance = value
                    elif parent == "Temperature":
                        self.current_datainfo.sample.temperature = value
                    elif parent == "CounterSlitLength":
                        self.detector.slit_length = value
                elif key == "unit":
                    value = value.replace("_", "")
                    if parent == "Wavelength":
                        self.current_datainfo.source.wavelength_unit = value
                    elif parent == "SampleDetector":
                        self.detector.distance_unit = value
                    elif parent == "X":
                        self.current_dataset.xaxis(self.current_dataset._xaxis, value)
                    elif parent == "Y":
                        self.current_dataset.yaxis(self.current_dataset._yaxis, value)
                    elif parent == "Temperature":
                        self.current_datainfo.sample.temperature_unit = value
                    elif parent == "CounterSlitLength":
                        self.detector.slit_length_unit = value
                elif key == "quantity":
                    if parent == "X":
                        self.current_dataset.xaxis(value, self.current_dataset._xunit)
                    elif parent == "Y":
                        self.current_dataset.yaxis(value, self.current_dataset._yunit)
