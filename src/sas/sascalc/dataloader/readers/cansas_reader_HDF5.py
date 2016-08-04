"""
    CanSAS 2D data reader for reading HDF5 formatted CanSAS files.
"""

import h5py
import numpy as np
import re
import os
import sys

from sas.sascalc.dataloader.data_info import plottable_1D, plottable_2D, Data1D, Data2D, DataInfo, Process, Aperture
from sas.sascalc.dataloader.data_info import Collimation, TransmissionSpectrum, Detector
from sas.sascalc.dataloader.data_info import combine_data_info_with_plottable



class Reader():
    """
    A class for reading in CanSAS v2.0 data files. The existing iteration opens Mantid generated HDF5 formatted files
    with file extension .h5/.H5. Any number of data sets may be present within the file and any dimensionality of data
    may be used. Currently 1D and 2D SAS data sets are supported, but future implementations will include 1D and 2D
    SESANS data.

    Any number of SASdata sets may be present in a SASentry and the data within can be either 1D I(Q) or 2D I(Qx, Qy).

    :Dependencies:
        The CanSAS HDF5 reader requires h5py => v2.5.0 or later.
    """

    ## CanSAS version
    cansas_version = 2.0
    ## Logged warnings or messages
    logging = None
    ## List of errors for the current data set
    errors = None
    ## Raw file contents to be processed
    raw_data = None
    ## Data info currently being read in
    current_datainfo = None
    ## SASdata set currently being read in
    current_dataset = None
    ## List of plottable1D objects that should be linked to the current_datainfo
    data1d = None
    ## List of plottable2D objects that should be linked to the current_datainfo
    data2d = None
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

    def read(self, filename):
        """
        This is the general read method that all SasView data_loaders must have.

        :param filename: A path for an HDF5 formatted CanSAS 2D data file.
        :return: List of Data1D/2D objects and/or a list of errors.
        """

        ## Reinitialize the class when loading a new data file to reset all class variables
        self.reset_class_variables()
        ## Check that the file exists
        if os.path.isfile(filename):
            basename = os.path.basename(filename)
            _, extension = os.path.splitext(basename)
            # If the file type is not allowed, return empty list
            if extension in self.ext or self.allow_all:
                ## Load the data file
                self.raw_data = h5py.File(filename, 'r')
                ## Read in all child elements of top level SASroot
                self.read_children(self.raw_data, [])
                ## Add the last data set to the list of outputs
                self.add_data_set()
        ## Return data set(s)
        return self.output

    def reset_class_variables(self):
        """
        Create the reader object and define initial states for class variables
        """
        self.current_datainfo = None
        self.current_dataset = None
        self.data1d = []
        self.data2d = []
        self.raw_data = None
        self.errors = set()
        self.logging = []
        self.output = []
        self.parent_class = u''
        self.detector = Detector()
        self.collimation = Collimation()
        self.aperture = Aperture()
        self.process = Process()
        self.trans_spectrum = TransmissionSpectrum()

    def read_children(self, data, parent_list):
        """
        A recursive method for stepping through the hierarchical data file.

        :param data: h5py Group object of any kind
        :param parent: h5py Group parent name
        """

        ## Loop through each element of the parent and process accordingly
        for key in data.keys():
            ## Get all information for the current key
            value = data.get(key)
            if value.attrs.get(u'canSAS_class') is not None:
                class_name = value.attrs.get(u'canSAS_class')
            else:
                class_name = value.attrs.get(u'NX_class')
            if class_name is not None:
                class_prog = re.compile(class_name)
            else:
                class_prog = re.compile(value.name)

            if isinstance(value, h5py.Group):
                self.parent_class = class_name
                parent_list.append(key)
                ## If this is a new sasentry, store the current data sets and create a fresh Data1D/2D object
                if class_prog.match(u'SASentry'):
                    self.add_data_set(key)
                elif class_prog.match(u'SASdata'):
                    self._initialize_new_data_set(parent_list)
                ## Recursion step to access data within the group
                self.read_children(value, parent_list)
                self.add_intermediate()
                parent_list.remove(key)

            elif isinstance(value, h5py.Dataset):
                ## If this is a dataset, store the data appropriately
                data_set = data[key][:]

                for data_point in data_set:
                    ## Top Level Meta Data
                    unit = self._get_unit(value)
                    if key == u'definition':
                        self.current_datainfo.meta_data['reader'] = data_point
                    elif key == u'run':
                        self.current_datainfo.run.append(data_point)
                    elif key == u'title':
                        self.current_datainfo.title = data_point
                    elif key == u'SASnote':
                        self.current_datainfo.notes.append(data_point)

                    ## I and Q Data
                    elif key == u'I':
                        if type(self.current_dataset) is plottable_2D:
                            self.current_dataset.data = np.append(self.current_dataset.data, data_point)
                            self.current_dataset.zaxis("Intensity", unit)
                        else:
                            self.current_dataset.y = np.append(self.current_dataset.y, data_point)
                            self.current_dataset.yaxis("Intensity", unit)
                    elif key == u'Idev':
                        if type(self.current_dataset) is plottable_2D:
                            self.current_dataset.err_data = np.append(self.current_dataset.err_data, data_point)
                        else:
                            self.current_dataset.dy = np.append(self.current_dataset.dy, data_point)
                    elif key == u'Q':
                        self.current_dataset.xaxis("Q", unit)
                        if type(self.current_dataset) is plottable_2D:
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
                    elif key == u'Title' and self.parent_class == u'SASsample':
                        self.current_datainfo.sample.name = data_point
                    elif key == u'thickness' and self.parent_class == u'SASsample':
                        self.current_datainfo.sample.thickness = data_point
                    elif key == u'temperature' and self.parent_class == u'SASsample':
                        self.current_datainfo.sample.temperature = data_point

                    ## Instrumental Information
                    elif key == u'name' and self.parent_class == u'SASinstrument':
                        self.current_datainfo.instrument = data_point
                    elif key == u'name' and self.parent_class == u'SASdetector':
                        self.detector.name = data_point
                    elif key == u'SDD' and self.parent_class == u'SASdetector':
                        self.detector.distance = float(data_point)
                        self.detector.distance_unit = unit
                    elif key == u'SSD' and self.parent_class == u'SAScollimation':
                        self.collimation.length = data_point
                        self.collimation.length_unit = unit
                    elif key == u'name' and self.parent_class == u'SAScollimation':
                        self.collimation.name = data_point

                    ## Process Information
                    elif key == u'name' and self.parent_class == u'SASprocess':
                        self.process.name = data_point
                    elif key == u'Title' and self.parent_class == u'SASprocess':
                        self.process.name = data_point
                    elif key == u'description' and self.parent_class == u'SASprocess':
                        self.process.description = data_point
                    elif key == u'date' and self.parent_class == u'SASprocess':
                        self.process.date = data_point
                    elif self.parent_class == u'SASprocess':
                        self.process.notes.append(data_point)

                    ## Transmission Spectrum
                    elif key == u'T' and self.parent_class == u'SAStransmission_spectrum':
                        self.trans_spectrum.transmission.append(data_point)
                    elif key == u'Tdev' and self.parent_class == u'SAStransmission_spectrum':
                        self.trans_spectrum.transmission_deviation.append(data_point)
                    elif key == u'lambda' and self.parent_class == u'SAStransmission_spectrum':
                        self.trans_spectrum.wavelength.append(data_point)

                    ## Other Information
                    elif key == u'wavelength' and self.parent_class == u'SASdata':
                        self.current_datainfo.source.wavelength = data_point
                        self.current_datainfo.source.wavelength.unit = unit
                    elif key == u'radiation' and self.parent_class == u'SASsource':
                        self.current_datainfo.source.radiation = data_point
                    elif key == u'transmission' and self.parent_class == u'SASdata':
                        self.current_datainfo.sample.transmission = data_point

                    ## Everything else goes in meta_data
                    else:
                        new_key = self._create_unique_key(self.current_datainfo.meta_data, key)
                        self.current_datainfo.meta_data[new_key] = data_point

            else:
                ## I don't know if this reachable code
                self.errors.add("ShouldNeverHappenException")

    def add_intermediate(self):
        """
        This method stores any intermediate objects within the final data set after fully reading the set.

        :param parent: The NXclass name for the h5py Group object that just finished being processed
        """

        if self.parent_class == u'SASprocess':
            self.current_datainfo.process.append(self.process)
            self.process = Process()
        elif self.parent_class == u'SASdetector':
            self.current_datainfo.detector.append(self.detector)
            self.detector = Detector()
        elif self.parent_class == u'SAStransmission_spectrum':
            self.current_datainfo.trans_spectrum.append(self.trans_spectrum)
            self.trans_spectrum = TransmissionSpectrum()
        elif self.parent_class == u'SAScollimation':
            self.current_datainfo.collimation.append(self.collimation)
            self.collimation = Collimation()
        elif self.parent_class == u'SASaperture':
            self.collimation.aperture.append(self.aperture)
            self.aperture = Aperture()
        elif self.parent_class == u'SASdata':
            if type(self.current_dataset) is plottable_2D:
                self.data2d.append(self.current_dataset)
            elif type(self.current_dataset) is plottable_1D:
                self.data1d.append(self.current_dataset)

    def final_data_cleanup(self):
        """
        Does some final cleanup and formatting on self.current_datainfo and all data1D and data2D objects and then
        combines the data and info into Data1D and Data2D objects
        """

        ## Type cast data arrays to float64
        if len(self.current_datainfo.trans_spectrum) > 0:
            spectrum_list = []
            for spectrum in self.current_datainfo.trans_spectrum:
                spectrum.transmission = np.delete(spectrum.transmission, [0])
                spectrum.transmission = spectrum.transmission.astype(np.float64)
                spectrum.transmission_deviation = np.delete(spectrum.transmission_deviation, [0])
                spectrum.transmission_deviation = spectrum.transmission_deviation.astype(np.float64)
                spectrum.wavelength = np.delete(spectrum.wavelength, [0])
                spectrum.wavelength = spectrum.wavelength.astype(np.float64)
                if len(spectrum.transmission) > 0:
                    spectrum_list.append(spectrum)
            self.current_datainfo.trans_spectrum = spectrum_list

        ## Append errors to dataset and reset class errors
        self.current_datainfo.errors = self.errors
        self.errors.clear()

        ## Combine all plottables with datainfo and append each to output
        ## Type cast data arrays to float64 and find min/max as appropriate
        for dataset in self.data2d:
            dataset.data = np.delete(dataset.data, [0])
            dataset.data = dataset.data.astype(np.float64)
            dataset.err_data = np.delete(dataset.err_data, [0])
            dataset.err_data = dataset.err_data.astype(np.float64)
            dataset.mask = np.delete(dataset.mask, [0])
            if dataset.qx_data is not None:
                dataset.qx_data = np.delete(dataset.qx_data, [0])
                dataset.xmin = np.min(dataset.qx_data)
                dataset.xmax = np.max(dataset.qx_data)
                dataset.qx_data = dataset.qx_data.astype(np.float64)
            if dataset.dqx_data is not None:
                dataset.dqx_data = np.delete(dataset.dqx_data, [0])
                dataset.dqx_data = dataset.dqx_data.astype(np.float64)
            if dataset.qy_data is not None:
                dataset.qy_data = np.delete(dataset.qy_data, [0])
                dataset.ymin = np.min(dataset.qy_data)
                dataset.ymax = np.max(dataset.qy_data)
                dataset.qy_data = dataset.qy_data.astype(np.float64)
            if dataset.dqy_data is not None:
                dataset.dqy_data = np.delete(dataset.dqy_data, [0])
                dataset.dqy_data = dataset.dqy_data.astype(np.float64)
            if dataset.q_data is not None:
                dataset.q_data = np.delete(dataset.q_data, [0])
                dataset.q_data = dataset.q_data.astype(np.float64)
            zeros = np.ones(dataset.data.size, dtype=bool)
            try:
                for i in range (0, dataset.mask.size - 1):
                    zeros[i] = dataset.mask[i]
            except:
                self.errors.add(sys.exc_value)
            dataset.mask = zeros
            ## Calculate the actual Q matrix
            try:
                if dataset.q_data.size <= 1:
                    dataset.q_data = np.sqrt(dataset.qx_data * dataset.qx_data + dataset.qy_data * dataset.qy_data)
            except:
                dataset.q_data = None
            final_dataset = combine_data_info_with_plottable(dataset, self.current_datainfo)
            self.output.append(final_dataset)

        for dataset in self.data1d:
            if dataset.x is not None:
                dataset.x = np.delete(dataset.x, [0])
                dataset.x = dataset.x.astype(np.float64)
                dataset.xmin = np.min(dataset.x)
                dataset.xmax = np.max(dataset.x)
            if dataset.y is not None:
                dataset.y = np.delete(dataset.y, [0])
                dataset.y = dataset.y.astype(np.float64)
                dataset.ymin = np.min(dataset.y)
                dataset.ymax = np.max(dataset.y)
            if dataset.dx is not None:
                dataset.dx = np.delete(dataset.dx, [0])
                dataset.dx = dataset.dx.astype(np.float64)
            if dataset.dxl is not None:
                dataset.dxl = np.delete(dataset.dxl, [0])
                dataset.dxl = dataset.dxl.astype(np.float64)
            if dataset.dxw is not None:
                dataset.dxw = np.delete(dataset.dxw, [0])
                dataset.dxw = dataset.dxw.astype(np.float64)
            if dataset.dy is not None:
                dataset.dy = np.delete(dataset.dy, [0])
                dataset.dy = dataset.dy.astype(np.float64)
            final_dataset = combine_data_info_with_plottable(dataset, self.current_datainfo)
            self.output.append(final_dataset)

    def add_data_set(self, key=""):
        """
        Adds the current_dataset to the list of outputs after preforming final processing on the data and then calls a
        private method to generate a new data set.

        :param key: NeXus group name for current tree level
        """

        if self.current_datainfo and self.current_dataset:
            self.final_data_cleanup()
        self.data1d = []
        self.data2d = []
        self.current_datainfo = DataInfo()

    def _initialize_new_data_set(self, parent_list = None):
        """
        A private class method to generate a new 1D or 2D data object based on the type of data within the set.
        Outside methods should call add_data_set() to be sure any existing data is stored properly.

        :param parent_list: List of names of parent elements
        """

        if parent_list is None:
            parent_list = []
        if self._find_intermediate(parent_list, "Qx"):
            self.current_dataset = plottable_2D()
        else:
            x = np.array(0)
            y = np.array(0)
            self.current_dataset = plottable_1D(x, y)
        self.current_datainfo.filename = self.raw_data.filename

    def _find_intermediate(self, parent_list, basename=""):
        """
        A private class used to find an entry by either using a direct key or knowing the approximate basename.

        :param parent_list: List of parents to the current level in the HDF5 file
        :param basename: Approximate name of an entry to search for
        :return:
        """

        entry = False
        key_prog = re.compile(basename)
        top = self.raw_data
        for parent in parent_list:
            top = top.get(parent)
        for key in top.keys():
            if (key_prog.match(key)):
                entry = True
                break
        return entry

    def _create_unique_key(self, dictionary, name, numb=0):
        """
        Create a unique key value for any dictionary to prevent overwriting
        Recurses until a unique key value is found.

        :param dictionary: A dictionary with any number of entries
        :param name: The index of the item to be added to dictionary
        :param numb: The number to be appended to the name, starts at 0
        :return: The new name for the dictionary entry
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
        :return: unit for the value passed to the method
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