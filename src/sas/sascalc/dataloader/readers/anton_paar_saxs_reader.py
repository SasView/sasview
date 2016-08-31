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

    def __init__(self):
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
        self.__init__()
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
                xml_intermediate = self.raw_data[self.upper:]
                xml = ''.join(xml_intermediate)
                self.set_xml_file(xml)
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
        self.detector.distance = float(line4[1])
        self.current_dataset.source.radiation = "x-ray"
        self.current_dataset.source.name = "Anton Paar SAXSess Instrument"
        self.current_dataset.source.wavelength = float(line4[4])
        normal = line4[3]
        for i in range(self.lower, self.upper):
            data = self.raw_data[i].split()
            x_val = [float(data[0])]
            y_val = [float(data[1])]
            dy_val = [float(data[2])]
            self.current_dataset.x = np.append(self.current_dataset.x, x_val)
            self.current_dataset.y = np.append(self.current_dataset.y, y_val)
            self.current_dataset.dy = np.append(self.current_dataset.dy, dy_val)
        self.current_dataset.xaxis("Q (%s)" % (q_unit), q_unit)
        self.current_dataset.yaxis("Intensity (%s)" % (i_unit), i_unit)
        self.current_dataset.detector.append(self.detector)
        self.output.append(self.current_dataset)