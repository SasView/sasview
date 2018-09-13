"""
    CanSAS 2D data reader for reading HDF5 formatted CanSAS files.
"""

import h5py
import numpy as np
import re
import os
import sys

from ..data_info import plottable_1D, plottable_2D,\
    Data1D, Data2D, DataInfo, Process, Aperture, Collimation, \
    TransmissionSpectrum, Detector
from ..loader_exceptions import FileContentsException, DefaultReaderException
from ..file_reader_base_class import FileReader, decode


def h5attr(node, key, default=None):
    return decode(node.attrs.get(key, default))


class Reader(FileReader):
    """
    A class for reading in CanSAS v2.0 data files. The existing iteration opens
    Mantid generated HDF5 formatted files with file extension .h5/.H5. Any
    number of data sets may be present within the file and any dimensionality
    of data may be used. Currently 1D and 2D SAS data sets are supported, but
    future implementations will include 1D and 2D SESANS data.

    Any number of SASdata sets may be present in a SASentry and the data within
    can be either 1D I(Q) or 2D I(Qx, Qy).

    Also supports reading NXcanSAS formatted HDF5 files

    :Dependencies:
        The CanSAS HDF5 reader requires h5py => v2.5.0 or later.
    """

    # CanSAS version
    cansas_version = 2.0
    # Data type name
    type_name = "NXcanSAS"
    # Wildcards
    type = ["NXcanSAS HDF5 Files (*.h5)|*.h5|"]
    # List of allowed extensions
    ext = ['.h5', '.H5']
    # Flag to bypass extension check
    allow_all = True

    def get_file_contents(self):
        """
        This is the general read method that all SasView data_loaders must have.

        :param filename: A path for an HDF5 formatted CanSAS 2D data file.
        :return: List of Data1D/2D objects and/or a list of errors.
        """
        # Reinitialize when loading a new data file to reset all class variables
        self.reset_state()

        filename = self.f_open.name
        self.f_open.close() # IO handled by h5py

        # Check that the file exists
        if os.path.isfile(filename):
            basename = os.path.basename(filename)
            _, extension = os.path.splitext(basename)
            # If the file type is not allowed, return empty list
            if extension in self.ext or self.allow_all:
                # Load the data file
                try:
                    self.raw_data = h5py.File(filename, 'r')
                except Exception as e:
                    if extension not in self.ext:
                        msg = "NXcanSAS Reader could not load file {}".format(
                            basename + extension)
                        raise DefaultReaderException(msg)
                    raise FileContentsException(e.message)
                try:
                    # Read in all child elements of top level SASroot
                    self.read_children(self.raw_data, [])
                    # Add the last data set to the list of outputs
                    self.add_data_set()
                except Exception as exc:
                    raise FileContentsException(exc.message)
                finally:
                    # Close the data file
                    self.raw_data.close()

                for data_set in self.output:
                    if isinstance(data_set, Data1D):
                        if data_set.x.size < 5:
                            exception = FileContentsException(
                                "Fewer than 5 data points found.")
                            data_set.errors.append(exception)

    def reset_state(self):
        """
        Create the reader object and define initial states for class variables
        """
        super(Reader, self).reset_state()
        self.data1d = []
        self.data2d = []
        self.raw_data = None
        self.errors = set()
        self.logging = []
        self.q_name = []
        self.mask_name = u''
        self.i_name = u''
        self.i_node = u''
        self.q_uncertainties = None
        self.q_resolutions = None
        self.i_uncertainties = u''
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

        # Loop through each element of the parent and process accordingly
        for key in data.keys():
            # Get all information for the current key
            value = data.get(key)
            class_name = h5attr(value, u'canSAS_class')
            if isinstance(class_name, (list, tuple, np.ndarray)):
                class_name = class_name[0]
            if class_name is None:
                class_name = h5attr(value, u'NX_class')
            if class_name is not None:
                class_prog = re.compile(class_name)
            else:
                class_prog = re.compile(value.name)

            if isinstance(value, h5py.Group):
                # Set parent class before recursion
                last_parent_class = self.parent_class
                self.parent_class = class_name
                parent_list.append(key)
                # If a new sasentry, store the current data sets and create
                # a fresh Data1D/2D object
                if class_prog.match(u'SASentry'):
                    self.add_data_set(key)
                elif class_prog.match(u'SASdata'):
                    self._initialize_new_data_set(value)
                    self._find_data_attributes(value)
                # Recursion step to access data within the group
                self.read_children(value, parent_list)
                self.add_intermediate()
                # Reset parent class when returning from recursive method
                self.parent_class = last_parent_class
                parent_list.remove(key)

            elif isinstance(value, h5py.Dataset):
                # If this is a dataset, store the data appropriately
                data_set = value.value
                unit = self._get_unit(value)

                for data_point in data_set:
                    if isinstance(data_point, np.ndarray):
                        if data_point.dtype.char == 'S':
                            data_point = decode(bytes(data_point))
                    else:
                        data_point = decode(data_point)
                    # Top Level Meta Data
                    if key == u'definition':
                        self.current_datainfo.meta_data['reader'] = data_point
                    # Run
                    elif key == u'run':
                        self.current_datainfo.run.append(data_point)
                        try:
                            run_name = h5attr(value, 'name')
                            run_dict = {data_point: run_name}
                            self.current_datainfo.run_name = run_dict
                        except Exception:
                            pass
                    # Title
                    elif key == u'title':
                        self.current_datainfo.title = data_point
                    # Note
                    elif key == u'SASnote':
                        self.current_datainfo.notes.append(data_point)
                    # Sample Information
                    elif self.parent_class == u'SASsample':
                        self.process_sample(data_point, key)
                    # Instrumental Information
                    elif (key == u'name'
                          and self.parent_class == u'SASinstrument'):
                        self.current_datainfo.instrument = data_point
                    # Detector
                    elif self.parent_class == u'SASdetector':
                        self.process_detector(data_point, key, unit)
                    # Collimation
                    elif self.parent_class == u'SAScollimation':
                        self.process_collimation(data_point, key, unit)
                    # Aperture
                    elif self.parent_class == u'SASaperture':
                        self.process_aperture(data_point, key)
                    # Process Information
                    elif self.parent_class == u'SASprocess': # CanSAS 2.0
                        self.process_process(data_point, key)
                    # Source
                    elif self.parent_class == u'SASsource':
                        self.process_source(data_point, key, unit)
                    # Everything else goes in meta_data
                    elif self.parent_class == u'SASdata':
                        if isinstance(self.current_dataset, plottable_2D):
                            self.process_2d_data_object(data_set, key, unit)
                        else:
                            self.process_1d_data_object(data_set, key, unit)

                        break
                    elif self.parent_class == u'SAStransmission_spectrum':
                        self.process_trans_spectrum(data_set, key)
                        break
                    else:
                        new_key = self._create_unique_key(
                            self.current_datainfo.meta_data, key)
                        self.current_datainfo.meta_data[new_key] = data_point

            else:
                # I don't know if this reachable code
                self.errors.add("ShouldNeverHappenException")

    def process_1d_data_object(self, data_set, key, unit):
        """
        SASdata processor method for 1d data items
        :param data_set: data from HDF5 file
        :param key: canSAS_class attribute
        :param unit: unit attribute
        """
        if key == self.i_name:
            self.current_dataset.y = data_set.flatten()
            self.current_dataset.yaxis("Intensity", unit)
        elif key == self.i_uncertainties:
            self.current_dataset.dy = data_set.flatten()
        elif key in self.q_name:
            self.current_dataset.xaxis("Q", unit)
            self.current_dataset.x = data_set.flatten()
        elif key in self.q_uncertainties or key in self.q_resolutions:
            if (len(self.q_resolutions) > 1
                    and np.where(self.q_resolutions == key)[0] == 0):
                self.current_dataset.dxw = data_set.flatten()
            elif (len(self.q_resolutions) > 1
                  and np.where(self.q_resolutions == key)[0] == 1):
                self.current_dataset.dxl = data_set.flatten()
            else:
                self.current_dataset.dx = data_set.flatten()
        elif key == self.mask_name:
            self.current_dataset.mask = data_set.flatten()
        elif key == u'wavelength':
            self.current_datainfo.source.wavelength = data_set[0]
            self.current_datainfo.source.wavelength_unit = unit

    def process_2d_data_object(self, data_set, key, unit):
        if key == self.i_name:
            self.current_dataset.data = data_set
            self.current_dataset.zaxis("Intensity", unit)
        elif key == self.i_uncertainties:
            self.current_dataset.err_data = data_set.flatten()
        elif key in self.q_name:
            self.current_dataset.xaxis("Q_x", unit)
            self.current_dataset.yaxis("Q_y", unit)
            if self.q_name[0] == self.q_name[1]:
                # All q data in a single array
                self.current_dataset.qx_data = data_set[0]
                self.current_dataset.qy_data = data_set[1]
            elif self.q_name.index(key) == 0:
                self.current_dataset.qx_data = data_set
            elif self.q_name.index(key) == 1:
                self.current_dataset.qy_data = data_set
        elif key in self.q_uncertainties or key in self.q_resolutions:
            if ((self.q_uncertainties[0] == self.q_uncertainties[1]) or
                    (self.q_resolutions[0] == self.q_resolutions[1])):
                # All q data in a single array
                self.current_dataset.dqx_data = data_set[0].flatten()
                self.current_dataset.dqy_data = data_set[1].flatten()
            elif (self.q_uncertainties.index(key) == 0 or
                  self.q_resolutions.index(key) == 0):
                self.current_dataset.dqx_data = data_set.flatten()
            elif (self.q_uncertainties.index(key) == 1 or
                  self.q_resolutions.index(key) == 1):
                self.current_dataset.dqy_data = data_set.flatten()
                self.current_dataset.yaxis("Q_y", unit)
        elif key == self.mask_name:
            self.current_dataset.mask = data_set.flatten()
        elif key == u'Qy':
            self.current_dataset.yaxis("Q_y", unit)
            self.current_dataset.qy_data = data_set.flatten()
        elif key == u'Qydev':
            self.current_dataset.dqy_data = data_set.flatten()
        elif key == u'Qx':
            self.current_dataset.xaxis("Q_x", unit)
            self.current_dataset.qx_data = data_set.flatten()
        elif key == u'Qxdev':
            self.current_dataset.dqx_data = data_set.flatten()

    def process_trans_spectrum(self, data_set, key):
        """
        SAStransmission_spectrum processor
        :param data_set: data from HDF5 file
        :param key: canSAS_class attribute
        """
        if key == u'T':
            self.trans_spectrum.transmission = data_set.flatten()
        elif key == u'Tdev':
            self.trans_spectrum.transmission_deviation = data_set.flatten()
        elif key == u'lambda':
            self.trans_spectrum.wavelength = data_set.flatten()

    def process_sample(self, data_point, key):
        """
        SASsample processor
        :param data_point: Single point from an HDF5 data file
        :param key: class name data_point was taken from
        """
        if key == u'Title':
            self.current_datainfo.sample.name = data_point
        elif key == u'name':
            self.current_datainfo.sample.name = data_point
        elif key == u'ID':
            self.current_datainfo.sample.name = data_point
        elif key == u'thickness':
            self.current_datainfo.sample.thickness = data_point
        elif key == u'temperature':
            self.current_datainfo.sample.temperature = data_point
        elif key == u'transmission':
            self.current_datainfo.sample.transmission = data_point
        elif key == u'x_position':
            self.current_datainfo.sample.position.x = data_point
        elif key == u'y_position':
            self.current_datainfo.sample.position.y = data_point
        elif key == u'pitch':
            self.current_datainfo.sample.orientation.x = data_point
        elif key == u'yaw':
            self.current_datainfo.sample.orientation.y = data_point
        elif key == u'roll':
            self.current_datainfo.sample.orientation.z = data_point
        elif key == u'details':
            self.current_datainfo.sample.details.append(data_point)

    def process_detector(self, data_point, key, unit):
        """
        SASdetector processor
        :param data_point: Single point from an HDF5 data file
        :param key: class name data_point was taken from
        :param unit: unit attribute from data set
        """
        if key == u'name':
            self.detector.name = data_point
        elif key == u'SDD':
            self.detector.distance = float(data_point)
            self.detector.distance_unit = unit
        elif key == u'slit_length':
            self.detector.slit_length = float(data_point)
            self.detector.slit_length_unit = unit
        elif key == u'x_position':
            self.detector.offset.x = float(data_point)
            self.detector.offset_unit = unit
        elif key == u'y_position':
            self.detector.offset.y = float(data_point)
            self.detector.offset_unit = unit
        elif key == u'pitch':
            self.detector.orientation.x = float(data_point)
            self.detector.orientation_unit = unit
        elif key == u'roll':
            self.detector.orientation.z = float(data_point)
            self.detector.orientation_unit = unit
        elif key == u'yaw':
            self.detector.orientation.y = float(data_point)
            self.detector.orientation_unit = unit
        elif key == u'beam_center_x':
            self.detector.beam_center.x = float(data_point)
            self.detector.beam_center_unit = unit
        elif key == u'beam_center_y':
            self.detector.beam_center.y = float(data_point)
            self.detector.beam_center_unit = unit
        elif key == u'x_pixel_size':
            self.detector.pixel_size.x = float(data_point)
            self.detector.pixel_size_unit = unit
        elif key == u'y_pixel_size':
            self.detector.pixel_size.y = float(data_point)
            self.detector.pixel_size_unit = unit

    def process_collimation(self, data_point, key, unit):
        """
        SAScollimation processor
        :param data_point: Single point from an HDF5 data file
        :param key: class name data_point was taken from
        :param unit: unit attribute from data set
        """
        if key == u'distance':
            self.collimation.length = data_point
            self.collimation.length_unit = unit
        elif key == u'name':
            self.collimation.name = data_point

    def process_aperture(self, data_point, key):
        """
        SASaperture processor
        :param data_point: Single point from an HDF5 data file
        :param key: class name data_point was taken from
        """
        if key == u'shape':
            self.aperture.shape = data_point
        elif key == u'x_gap':
            self.aperture.size.x = data_point
        elif key == u'y_gap':
            self.aperture.size.y = data_point

    def process_source(self, data_point, key, unit):
        """
        SASsource processor
        :param data_point: Single point from an HDF5 data file
        :param key: class name data_point was taken from
        :param unit: unit attribute from data set
        """
        if key == u'incident_wavelength':
            self.current_datainfo.source.wavelength = data_point
            self.current_datainfo.source.wavelength_unit = unit
        elif key == u'wavelength_max':
            self.current_datainfo.source.wavelength_max = data_point
            self.current_datainfo.source.wavelength_max_unit = unit
        elif key == u'wavelength_min':
            self.current_datainfo.source.wavelength_min = data_point
            self.current_datainfo.source.wavelength_min_unit = unit
        elif key == u'incident_wavelength_spread':
            self.current_datainfo.source.wavelength_spread = data_point
            self.current_datainfo.source.wavelength_spread_unit = unit
        elif key == u'beam_size_x':
            self.current_datainfo.source.beam_size.x = data_point
            self.current_datainfo.source.beam_size_unit = unit
        elif key == u'beam_size_y':
            self.current_datainfo.source.beam_size.y = data_point
            self.current_datainfo.source.beam_size_unit = unit
        elif key == u'beam_shape':
            self.current_datainfo.source.beam_shape = data_point
        elif key == u'radiation':
            self.current_datainfo.source.radiation = data_point

    def process_process(self, data_point, key):
        """
        SASprocess processor
        :param data_point: Single point from an HDF5 data file
        :param key: class name data_point was taken from
        """
        term_match = re.compile(u'^term[0-9]+$')
        if key == u'Title':  # CanSAS 2.0
            self.process.name = data_point
        elif key == u'name':  # NXcanSAS
            self.process.name = data_point
        elif key == u'description':
            self.process.description = data_point
        elif key == u'date':
            self.process.date = data_point
        elif term_match.match(key):
            self.process.term.append(data_point)
        else:
            self.process.notes.append(data_point)

    def add_intermediate(self):
        """
        This method stores any intermediate objects within the final data set
        after fully reading the set.

        :param parent: The NXclass name for the h5py Group object that just
                       finished being processed
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
            if isinstance(self.current_dataset, plottable_2D):
                self.data2d.append(self.current_dataset)
            elif isinstance(self.current_dataset, plottable_1D):
                self.data1d.append(self.current_dataset)

    def final_data_cleanup(self):
        """
        Does some final cleanup and formatting on self.current_datainfo and
        all data1D and data2D objects and then combines the data and info into
        Data1D and Data2D objects
        """
        # Type cast data arrays to float64
        if len(self.current_datainfo.trans_spectrum) > 0:
            spectrum_list = []
            for spectrum in self.current_datainfo.trans_spectrum:
                spectrum.transmission = spectrum.transmission.astype(np.float64)
                spectrum.transmission_deviation = \
                    spectrum.transmission_deviation.astype(np.float64)
                spectrum.wavelength = spectrum.wavelength.astype(np.float64)
                if len(spectrum.transmission) > 0:
                    spectrum_list.append(spectrum)
            self.current_datainfo.trans_spectrum = spectrum_list

        # Append errors to dataset and reset class errors
        self.current_datainfo.errors = self.errors
        self.errors.clear()

        # Combine all plottables with datainfo and append each to output
        # Type cast data arrays to float64 and find min/max as appropriate
        for dataset in self.data2d:
            zeros = np.ones(dataset.data.size, dtype=bool)
            try:
                for i in range(0, dataset.mask.size - 1):
                    zeros[i] = dataset.mask[i]
            except:
                self.errors.add(sys.exc_value)
            dataset.mask = zeros
            # Calculate the actual Q matrix
            try:
                if dataset.q_data.size <= 1:
                    dataset.q_data = np.sqrt(dataset.qx_data
                                             * dataset.qx_data
                                             + dataset.qy_data
                                             * dataset.qy_data)
            except:
                dataset.q_data = None

            if dataset.data.ndim == 2:
                (n_rows, n_cols) = dataset.data.shape
                flat_qy = dataset.qy_data[0::n_cols].flatten()
                if flat_qy[0] == flat_qy[1]:
                    flat_qy = np.transpose(dataset.qy_data)[0::n_cols].flatten()
                dataset.y_bins = np.unique(flat_qy)
                flat_qx = dataset.qx_data[0::n_rows].flatten()
                if flat_qx[0] == flat_qx[1]:
                    flat_qx = np.transpose(dataset.qx_data)[0::n_rows].flatten()
                dataset.x_bins = np.unique(flat_qx)
                dataset.data = dataset.data.flatten()
                dataset.qx_data = dataset.qx_data.flatten()
                dataset.qy_data = dataset.qy_data.flatten()
            self.current_dataset = dataset
            self.send_to_output()

        for dataset in self.data1d:
            self.current_dataset = dataset
            self.send_to_output()

    def add_data_set(self, key=""):
        """
        Adds the current_dataset to the list of outputs after preforming final
        processing on the data and then calls a private method to generate a
        new data set.

        :param key: NeXus group name for current tree level
        """

        if self.current_datainfo and self.current_dataset:
            self.final_data_cleanup()
        self.data1d = []
        self.data2d = []
        self.current_datainfo = DataInfo()

    def _initialize_new_data_set(self, value=None):
        """
        A private class method to generate a new 1D or 2D data object based on
        the type of data within the set. Outside methods should call
        add_data_set() to be sure any existing data is stored properly.

        :param parent_list: List of names of parent elements
        """
        if self._is2d(value):
            self.current_dataset = plottable_2D()
        else:
            x = np.array(0)
            y = np.array(0)
            self.current_dataset = plottable_1D(x, y)
        self.current_datainfo.filename = self.raw_data.filename
        self.mask_name = ""
        self.i_name = ""
        self.i_node = ""
        self.q_name = []
        self.q_uncertainties = []
        self.q_resolutions = []
        self.i_uncertainties = ""

    @staticmethod
    def check_is_list_or_array(iterable):
        try:
            iter(iterable)
            if (not isinstance(iterable, np.ndarray) and not isinstance(
                    iterable, list)) or (isinstance(iterable, str) or
                                         isinstance(iterable, unicode)):
                raise TypeError
        except TypeError:
            iterable = iterable.split(",")
        return iterable

    def _find_data_attributes(self, value):
        """
        A class to find the indices for Q, the name of the Qdev and Idev, and
        the name of the mask.
        :param value: SASdata/NXdata HDF5 Group
        """
        attrs = value.attrs
        signal = attrs.get("signal", "I")
        i_axes = attrs.get("I_axes", ["Q"])
        q_indices = attrs.get("Q_indices", [0])
        q_indices = map(int, self.check_is_list_or_array(q_indices))
        i_axes = self.check_is_list_or_array(i_axes)
        keys = value.keys()
        self.mask_name = attrs.get("mask")
        for val in q_indices:
            self.q_name.append(i_axes[val])
        self.i_name = signal
        self.i_node = value.get(self.i_name)
        for item in self.q_name:
            if item in keys:
                q_vals = value.get(item)
                if q_vals.attrs.get("uncertainties") is not None:
                    self.q_uncertainties = q_vals.attrs.get("uncertainties")
                elif q_vals.attrs.get("uncertainty") is not None:
                    self.q_uncertainties = q_vals.attrs.get("uncertainty")
                if isinstance(self.q_uncertainties, str) is not None:
                    self.q_uncertainties = [self.q_uncertainties]
                if q_vals.attrs.get("resolutions") is not None:
                    self.q_resolutions = q_vals.attrs.get("resolutions")
                if isinstance(self.q_resolutions, str):
                    self.q_resolutions = self.q_resolutions.split(",")
        if self.i_name in keys:
            i_vals = value.get(self.i_name)
            self.i_uncertainties = i_vals.attrs.get("uncertainties")
            if self.i_uncertainties is None:
                self.i_uncertainties = i_vals.attrs.get("uncertainty")

    def _is2d(self, value, basename="I"):
        """
        A private class to determine if the data set is 1d or 2d.

        :param parent_list: List of parents nodes in the HDF5 file
        :param basename: Approximate name of an entry to search for
        :return: True if 2D, otherwise false
        """

        vals = value.get(basename)
        return (vals is not None and vals.shape is not None
                and len(vals.shape) != 1)

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
        unit = h5attr(value, u'units')
        if unit is None:
            unit = h5attr(value, u'unit')
        return unit
