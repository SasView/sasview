"""
    CanSAS 2D data reader for reading HDF5 formatted CanSAS files.
"""

import h5py
import numpy as np
import re
import os
import sys

from sas.sascalc.dataloader.data_info import plottable_1D, plottable_2D, Data1D, Data2D, Sample, Source
from sas.sascalc.dataloader.data_info import Process, Aperture, Collimation, TransmissionSpectrum, Detector


class Reader():
    """
    A class for reading in CanSAS v2.0 data files. The existing iteration opens Mantid generated HDF5 formatted files
    with file extension .h5/.H5. Any number of data sets may be present within the file and any dimensionality of data
    may be used. Currently 1D and 2D SAS data sets are supported, but future implementations will include 1D and 2D
    SESANS data. This class assumes a single data set for each sasentry.

    :Dependencies:
        The CanSAS HDF5 reader requires h5py v2.5.0 or later.
    """

    ## CanSAS version
    cansas_version = 2.0
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
    type_name = "CanSAS 2.0"
    ## Wildcards
    type = ["CanSAS 2.0 HDF5 Files (*.h5)|*.h5"]
    ## List of allowed extensions
    ext = ['.h5', '.H5']
    ## Flag to bypass extension check
    allow_all = False
    ## List of files to return
    output = None

    def __init__(self):
        """
        Create the reader object and define initial states for class variables
        """
        self.current_dataset = None
        self.datasets = []
        self.raw_data = None
        self.errors = set()
        self.logging = []
        self.parent_list = []
        self.output = []
        self.detector = Detector()
        self.collimation = Collimation()
        self.aperture = Aperture()
        self.process = Process()
        self.sample = Sample()
        self.source = Source()
        self.trans_spectrum  = TransmissionSpectrum()

    def read(self, filename):
        """
        This is the general read method that all SasView data_loaders must have.

        :param filename: A path for an HDF5 formatted CanSAS 2D data file.
        :return: List of Data1D/2D objects or a list of errors.
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
                self.raw_data = h5py.File(filename, 'r')
                ## Read in all child elements of top level SASroot
                self.read_children(self.raw_data)
                ## Add the last data set to the list of outputs
                self.add_data_set()
        ## Return data set(s)
        return self.output

    def read_children(self, data, parent=u'SASroot'):
        """
        A recursive method for stepping through the hierarchical data file.

        :param data: h5py Group object of any kind
        :param parent: h5py Group parent name
        :return: None
        """

        ## Create regex for base sasentry and for parent
        parent_prog = re.compile(parent)

        ## Loop through each element of the parent and process accordingly
        for key in data.keys():
            ## Get all information for the current key
            value = data.get(key)
            attr_keys = value.attrs.keys()
            attr_values = value.attrs.values()
            if value.attrs.get(u'canSAS_class') is not None:
                class_name = value.attrs.get(u'canSAS_class')
            else:
                class_name = value.attrs.get(u'NX_class')
            if class_name is not None:
                class_prog = re.compile(class_name)
            else:
                class_prog = re.compile(value.name)

            if isinstance(value, h5py.Group):
                ##TODO: Rework this for multiple SASdata objects within a single SASentry to allow for both 1D and 2D
                ##TODO:     data within the same SASentry - One 1D and one 2D data object for all SASdata sets?
                ## If this is a new sasentry, store the current data set and create a fresh Data1D/2D object
                if class_prog.match(u'SASentry'):
                    self.add_data_set(key)
                ## Recursion step to access data within the group
                self.read_children(value, class_name)
                self.add_intermediate(class_name)

            elif isinstance(value, h5py.Dataset):
                ## If this is a dataset, store the data appropriately
                data_set = data[key][:]

                for data_point in data_set:
                    ## Top Level Meta Data
                    unit = self._get_unit(value)
                    if key == u'definition':
                        self.current_dataset.meta_data['reader'] = data_point
                    elif key == u'run':
                        self.current_dataset.run.append(data_point)
                    elif key == u'title':
                        self.current_dataset.title = data_point
                    elif key == u'SASnote':
                        self.current_dataset.notes.append(data_point)

                    ## I and Q Data
                    elif key == u'I':
                        if type(self.current_dataset) is Data2D:
                            self.current_dataset.data = np.append(self.current_dataset.data, data_point)
                            self.current_dataset.zaxis("Intensity", unit)
                        else:
                            self.current_dataset.y = np.append(self.current_dataset.y, data_point)
                            self.current_dataset.yaxis("Intensity", unit)
                    elif key == u'Idev':
                        if type(self.current_dataset) is Data2D:
                            self.current_dataset.err_data = np.append(self.current_dataset.err_data, data_point)
                        else:
                            self.current_dataset.dy = np.append(self.current_dataset.dy, data_point)
                    elif key == u'Q':
                        self.current_dataset.xaxis("Q", unit)
                        if type(self.current_dataset) is Data2D:
                            self.current_dataset.q = np.append(self.current_dataset.q, data_point)
                        else:
                            self.current_dataset.x = np.append(self.current_dataset.x, data_point)
                    elif key == u'Qy':
                        self.current_dataset.yaxis("Q_y", unit)
                        self.current_dataset.qy_data = np.append(self.current_dataset.qy_data, data_point)
                    elif key == u'Qydev':
                        self.current_dataset.dqy_data = np.append(self.current_dataset.dqy_data, data_point)
                    elif key == u'Qx':
                        self.current_dataset.xaxis("Q_x", unit)
                        self.current_dataset.qx_data = np.append(self.current_dataset.qx_data, data_point)
                    elif key == u'Qxdev':
                        self.current_dataset.dqx_data = np.append(self.current_dataset.dqx_data, data_point)
                    elif key == u'Mask':
                        self.current_dataset.mask = np.append(self.current_dataset.mask, data_point)

                    ## Sample Information
                    elif key == u'Title' and parent == u'SASsample':
                        self.sample.name = data_point
                    elif key == u'thickness' and parent == u'SASsample':
                        self.sample.thickness = data_point
                    elif key == u'temperature' and parent == u'SASsample':
                        self.sample.temperature = data_point

                    ## Instrumental Information
                    elif key == u'name' and parent == u'SASinstrument':
                        self.current_dataset.instrument = data_point
                    elif key == u'name' and parent == u'SASdetector':
                        self.detector.name = data_point
                    elif key == u'SDD' and parent == u'SASdetector':
                        self.detector.distance = data_point
                        self.detector.distance_unit = unit
                    elif key == u'SSD' and parent == u'SAScollimation':
                        self.collimation.length = data_point
                        self.collimation.length_unit = unit
                    elif key == u'name' and parent == u'SAScollimation':
                        self.collimation.name = data_point

                    ## Process Information
                    elif key == u'name' and parent == u'SASprocess':
                        self.process.name = data_point
                    elif key == u'Title' and parent == u'SASprocess':
                        self.process.name = data_point
                    elif key == u'description' and parent == u'SASprocess':
                        self.process.description = data_point
                    elif key == u'date' and parent == u'SASprocess':
                        self.process.date = data_point
                    elif parent == u'SASprocess':
                        self.process.notes.append(data_point)

                    ## Transmission Spectrum
                    elif key == u'T' and parent == u'SAStransmission_spectrum':
                        self.trans_spectrum.transmission.append(data_point)
                    elif key == u'Tdev' and parent == u'SAStransmission_spectrum':
                        self.trans_spectrum.transmission_deviation.append(data_point)
                    elif key == u'lambda' and parent == u'SAStransmission_spectrum':
                        self.trans_spectrum.wavelength.append(data_point)

                    ## Other Information
                    elif key == u'wavelength' and parent == u'SASdata':
                        self.source.wavelength = data_point
                        self.source.wavelength.unit = unit
                    elif key == u'radiation' and parent == u'SASsource':
                        self.source.radiation = data_point
                    elif key == u'transmission' and parent == u'SASdata':
                        self.sample.transmission = data_point

                    ## Everything else goes in meta_data
                    else:
                        new_key = self._create_unique_key(self.current_dataset.meta_data, key)
                        self.current_dataset.meta_data[new_key] = data_point

            else:
                ## I don't know if this reachable code
                self.errors.add("ShouldNeverHappenException")

    def add_intermediate(self, parent):
        """
        This method stores any intermediate objects within the final data set after fully reading the set.

        :param parent: The NXclass name for the h5py Group object that just finished being processed
        :return:
        """

        if parent == u'SASprocess':
            self.current_dataset.process.append(self.process)
            self.process = Process()
        elif parent == u'SASdetector':
            self.current_dataset.detector.append(self.detector)
            self.detector = Detector()
        elif parent == u'SAStransmission_spectrum':
            self.current_dataset.trans_spectrum.append(self.trans_spectrum)
            self.trans_spectrum = TransmissionSpectrum()
        elif parent == u'SASsource':
            self.current_dataset.source = self.source
            self.source = Source()
        elif parent == u'SASsample':
            self.current_dataset.sample = self.sample
            self.sample = Sample()
        elif parent == u'SAScollimation':
            self.current_dataset.collimation.append(self.collimation)
            self.collimation = Collimation()
        elif parent == u'SASaperture':
            self.collimation.aperture.append(self.aperture)
            self.aperture = Aperture()

    def final_data_cleanup(self):
        """
        Does some final cleanup and formatting on self.current_dataset
        """

        ## Type cast data arrays to float64 and find min/max as appropriate
        if type(self.current_dataset) is Data2D:
            self.current_dataset.data = np.delete(self.current_dataset.data, [0])
            self.current_dataset.data = self.current_dataset.data.astype(np.float64)
            self.current_dataset.err_data = np.delete(self.current_dataset.err_data, [0])
            self.current_dataset.err_data = self.current_dataset.err_data.astype(np.float64)
            self.current_dataset.mask = np.delete(self.current_dataset.mask, [0])
            if self.current_dataset.qx_data is not None:
                self.current_dataset.qx_data = np.delete(self.current_dataset.qx_data, [0])
                self.current_dataset.xmin = np.min(self.current_dataset.qx_data)
                self.current_dataset.xmax = np.max(self.current_dataset.qx_data)
                self.current_dataset.qx_data = self.current_dataset.qx_data.astype(np.float64)
            if self.current_dataset.dqx_data is not None:
                self.current_dataset.dqx_data = np.delete(self.current_dataset.dqx_data, [0])
                self.current_dataset.dqx_data = self.current_dataset.dqx_data.astype(np.float64)
            if self.current_dataset.qy_data is not None:
                self.current_dataset.qy_data = np.delete(self.current_dataset.qy_data, [0])
                self.current_dataset.ymin = np.min(self.current_dataset.qy_data)
                self.current_dataset.ymax = np.max(self.current_dataset.qy_data)
                self.current_dataset.qy_data = self.current_dataset.qy_data.astype(np.float64)
            if self.current_dataset.dqy_data is not None:
                self.current_dataset.dqy_data = np.delete(self.current_dataset.dqy_data, [0])
                self.current_dataset.dqy_data = self.current_dataset.dqy_data.astype(np.float64)
            if self.current_dataset.q_data is not None:
                self.current_dataset.q_data = np.delete(self.current_dataset.q_data, [0])
                self.current_dataset.q_data = self.current_dataset.q_data.astype(np.float64)
            zeros = np.ones(self.current_dataset.data.size, dtype=bool)
            try:
                for i in range (0, self.current_dataset.mask.size - 1):
                    zeros[i] = self.current_dataset.mask[i]
            except:
                self.errors.add(sys.exc_value)
            self.current_dataset.mask = zeros

            ## Calculate the actual Q matrix
            try:
                if self.current_dataset.q_data.size <= 1:
                    self.current_dataset.q_data = np.sqrt(self.current_dataset.qx_data * self.current_dataset.qx_data +
                            self.current_dataset.qy_data * self.current_dataset.qy_data)
            except:
                self.current_dataset.q_data = None

        elif type(self.current_dataset) is Data1D:
            if self.current_dataset.x is not None:
                self.current_dataset.x = np.delete(self.current_dataset.x, [0])
                self.current_dataset.x = self.current_dataset.x.astype(np.float64)
                self.current_dataset.xmin = np.min(self.current_dataset.x)
                self.current_dataset.xmax = np.max(self.current_dataset.x)
            if self.current_dataset.y is not None:
                self.current_dataset.y = np.delete(self.current_dataset.y, [0])
                self.current_dataset.y = self.current_dataset.y.astype(np.float64)
                self.current_dataset.ymin = np.min(self.current_dataset.y)
                self.current_dataset.ymax = np.max(self.current_dataset.y)
            if self.current_dataset.dx is not None:
                self.current_dataset.dx = np.delete(self.current_dataset.dx, [0])
                self.current_dataset.dx = self.current_dataset.dx.astype(np.float64)
            if self.current_dataset.dxl is not None:
                self.current_dataset.dxl = np.delete(self.current_dataset.dxl, [0])
                self.current_dataset.dxl = self.current_dataset.dxl.astype(np.float64)
            if self.current_dataset.dxw is not None:
                self.current_dataset.dxw = np.delete(self.current_dataset.dxw, [0])
                self.current_dataset.dxw = self.current_dataset.dxw.astype(np.float64)
            if self.current_dataset.dy is not None:
                self.current_dataset.dy = np.delete(self.current_dataset.dy, [0])
                self.current_dataset.dy =self.current_dataset.dy.astype(np.float64)

        if len(self.current_dataset.trans_spectrum) is not 0:
            spectrum_list = []
            for spectrum in self.current_dataset.trans_spectrum:
                spectrum.transmission = np.delete(spectrum.transmission, [0])
                spectrum.transmission = spectrum.transmission.astype(np.float64)
                spectrum.transmission_deviation = np.delete(spectrum.transmission_deviation, [0])
                spectrum.transmission_deviation = spectrum.transmission_deviation.astype(np.float64)
                spectrum.wavelength = np.delete(spectrum.wavelength, [0])
                spectrum.wavelength = spectrum.wavelength.astype(np.float64)
                spectrum_list.append(spectrum)
            self.current_dataset.trans_spectrum = spectrum_list

        else:
            self.errors.add("ShouldNeverHappenException")

        ## Append intermediate objects to data
        self.current_dataset.sample = self.sample
        self.current_dataset.source = self.source
        self.current_dataset.collimation.append(self.collimation)

        ## Append errors to dataset and reset class errors
        self.current_dataset.errors = self.errors
        self.errors.clear()

    def add_data_set(self, key=""):
        """
        Adds the current_dataset to the list of outputs after preforming final processing on the data and then calls a
        private method to generate a new data set.

        :param key: NeXus group name for current tree level
        :return: None
        """
        if self.current_dataset is not None:
            self.final_data_cleanup()
            self.output.append(self.current_dataset)
        self._initialize_new_data_set(key)

    def _initialize_new_data_set(self, key=""):
        """
        A private class method to generate a new 1D or 2D data object based on the type of data within the set.
        Outside methods should call add_data_set() to be sure any existing data is stored properly.

        :param key: NeXus group name for current tree level
        :return: None
        """
        entry = self._find_intermediate(key, "sasentry*")
        data = entry.get("sasdata")
        if data.get("Qx") is not None:
            self.current_dataset = Data2D()
        else:
            x = np.array(0)
            y = np.array(0)
            self.current_dataset = Data1D(x, y)
        self.current_dataset.filename = self.raw_data.filename

    def _find_intermediate(self, key="", basename=""):
        """
        A private class used to find an entry by either using a direct key or knowing the approximate basename.

        :param key: Exact keyname of an entry
        :param basename: Approximate name of an entry
        :return:
        """
        entry = []
        if key is not "":
            entry = self.raw_data.get(key)
        else:
            key_prog = re.compile(basename)
            for key in self.raw_data.keys():
                if (key_prog.match(key)):
                    entry = self.raw_data.get(key)
                    break
        return entry

    def _create_unique_key(self, dictionary, name, numb=0):
        """
        Create a unique key value for any dictionary to prevent overwriting
        Recurses until a unique key value is found.

        :param dictionary: A dictionary with any number of entries
        :param name: The index of the item to be added to dictionary
        :param numb: The number to be appended to the name, starts at 0
        """
        if dictionary.get(name) is not None:
            numb += 1
            name = name.split("_")[0]
            name += "_{0}".format(numb)
            name = self._create_unique_key(dictionary, name, numb)
        return name

    def _get_unit(self, value):
        """
        Find the unit for a particular value within the h5py dictionary

        :param value: attribute dictionary for a particular value set
        :return:
        """
        unit = value.attrs.get(u'units')
        if unit == None:
            unit = value.attrs.get(u'unit')

        ## Convert the unit formats
        if unit == "1/A":
            unit = "A^{-1}"
        elif unit == "1/cm":
            unit = "cm^{-1}"

        return unit