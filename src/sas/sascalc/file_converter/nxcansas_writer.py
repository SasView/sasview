"""
    NXcanSAS 1/2D data reader for writing HDF5 formatted NXcanSAS files.
"""

import h5py
import numpy as np
import re
import os

from sas.sascalc.dataloader.readers.cansas_reader_HDF5 import Reader as Cansas2Reader
from sas.sascalc.dataloader.data_info import Data1D, Data2D

class NXcanSASWriter(Cansas2Reader):
    """
    A class for writing in NXcanSAS data files. Any number of data sets may be
    written to the file. Currently 1D and 2D SAS data sets are supported

    NXcanSAS spec: http://download.nexusformat.org/sphinx/classes/contributed_definitions/NXcanSAS.html

    :Dependencies:
        The NXcanSAS writer requires h5py => v2.5.0 or later.
    """

    def write(self, dataset, filename):
        """
        Write an array of Data1d or Data2D objects to an NXcanSAS file, as
        one SASEntry with multiple SASData elements. The metadata of the first
        elememt in the array will be written as the SASentry metadata
        (detector, instrument, sample, etc).

        :param dataset: A list of Data1D or Data2D objects to write
        :param filename: Where to write the NXcanSAS file
        """

        def _h5_string(string):
            """
            Convert a string to a numpy string in a numpy array. This way it is
            written to the HDF5 file as a fixed length ASCII string and is
            compatible with the Reader read() method.
            """
            if not isinstance(string, str):
                string = str(string)

            return np.array([np.string_(string)])

        def _write_h5_string(entry, value, key):
            entry[key] = _h5_string(value)


        def _h5_float(x):
            if not (isinstance(x, list)):
                x = [x]
            return np.array(x, dtype=np.float32)

        def _write_h5_float(entry, value, key):
            entry.create_dataset(key, data=_h5_float(value))

        def _write_h5_vector(entry, vector, names=['x_position', 'y_position'],
            units=None, write_fn=_write_h5_string):
            if len(names) < 2:
                raise ValueError("Length of names must be >= 2.")

            if vector.x is not None:
                write_fn(entry, vector.x, names[0])
                if units is not None:
                    entry[names[0]].attrs['units'] = units
            if vector.y is not None:
                write_fn(entry, vector.y, names[1])
                if units is not None:
                    entry[names[1]].attrs['units'] = units
            if len(names) == 3 and vector.z is not None:
                write_fn(entry, vector.z, names[2])
                if units is not None:
                    entry[names[2]].attrs['units'] = units

        valid_data = all([issubclass(d.__class__, (Data1D, Data2D)) for d in dataset])
        if not valid_data:
            raise ValueError("All entries of dataset must be Data1D or Data2D objects")

        # Get run name and number from first Data object
        data_info = dataset[0]
        run_number = ''
        run_name = ''
        if len(data_info.run) > 0:
            run_number = data_info.run[0]
            if len(data_info.run_name) > 0:
                run_name = data_info.run_name[run_number]

        f = h5py.File(filename, 'w')
        sasentry = f.create_group('sasentry01')
        sasentry['definition'] = _h5_string('NXcanSAS')
        sasentry['run'] = _h5_string(run_number)
        sasentry['run'].attrs['name'] = run_name
        sasentry['title'] = _h5_string(data_info.title)
        sasentry.attrs['canSAS_class'] = 'SASentry'
        sasentry.attrs['version'] = '1.0'

        i = 1

        for data_obj in dataset:
            data_entry = sasentry.create_group("sasdata{0:0=2d}".format(i))
            data_entry.attrs['canSAS_class'] = 'SASdata'
            if isinstance(data_obj, Data1D):
                self._write_1d_data(data_obj, data_entry)
            elif isinstance(data_obj, Data2D):
                self._write_2d_data(data_obj, data_entry)
            i += 1

        data_info = dataset[0]
        # Sample metadata
        sample_entry = sasentry.create_group('sassample')
        sample_entry.attrs['canSAS_class'] = 'SASsample'
        sample_entry['ID'] = _h5_string(data_info.sample.name)
        sample_attrs = ['thickness', 'temperature', 'transmission']
        for key in sample_attrs:
            if getattr(data_info.sample, key) is not None:
                sample_entry.create_dataset(key,
                    data=_h5_float(getattr(data_info.sample, key)))
        _write_h5_vector(sample_entry, data_info.sample.position)
        _write_h5_vector(sample_entry, data_info.sample.orientation,
            names=['polar_angle', 'azimuthal_angle'])

        # Instrumment metadata
        instrument_entry = sasentry.create_group('sasinstrument')
        instrument_entry.attrs['canSAS_class'] = 'SASinstrument'
        instrument_entry['name'] = _h5_string(data_info.instrument)

        # Source metadata
        source_entry = instrument_entry.create_group('sassource')
        source_entry.attrs['canSAS_class'] = 'SASsource'
        if data_info.source.radiation is None:
            source_entry['radiation'] = _h5_string('neutron')
        else:
            source_entry['radiation'] = _h5_string(data_info.source.radiation)

        # Collimation metadata
        if len(data_info.collimation) > 0:
            i = 1
            for coll_info in data_info.collimation:
                collimation_entry = instrument_entry.create_group(
                    'sascollimation{0:0=2d}'.format(i))
                collimation_entry.attrs['canSAS_class'] = 'SAScollimation'
                if coll_info.length is not None:
                    _write_h5_float(collimation_entry, coll_info.length, 'SDD')
                    collimation_entry['SDD'].attrs['units'] = coll_info.length_unit
                if coll_info.name is not None:
                    collimation_entry['name'] = _h5_string(coll_info.name)
        else:
            # Create a blank one - at least 1 set of collimation metadata
            # required by format
            collimation_entry = instrument_entry.create_group('sascollimation01')

        # Detector metadata
        if len(data_info.detector) > 0:
            i = 1
            for det_info in data_info.detector:
                detector_entry = instrument_entry.create_group(
                    'sasdetector{0:0=2d}'.format(i))
                detector_entry.attrs['canSAS_class'] = 'SASdetector'
                if det_info.distance is not None:
                    _write_h5_float(detector_entry, det_info.distance, 'SDD')
                    detector_entry['SDD'].attrs['units'] = det_info.distance_unit
                if det_info.name is not None:
                    detector_entry['name'] = _h5_string(det_info.name)
                else:
                    detector_entry['name'] = _h5_string('')
                if det_info.slit_length is not None:
                    _write_h5_float(detector_entry, det_info.slit_length, 'slit_length')
                    detector_entry['slit_length'].attrs['units'] = det_info.slit_length_unit
                _write_h5_vector(detector_entry, det_info.offset)
                _write_h5_vector(detector_entry, det_info.orientation,
                    names=['polar_angle', 'azimuthal_angle'])
                _write_h5_vector(detector_entry, det_info.beam_center,
                    names=['beam_center_x', 'beam_center_y'],
                    write_fn=_write_h5_float, units=det_info.beam_center_unit)
                _write_h5_vector(detector_entry, det_info.pixel_size,
                    names=['x_pixel_size', 'y_pixel_size'],
                    write_fn=_write_h5_float, units=det_info.pixel_size_unit)

                i += 1
        else:
            # Create a blank one - at least 1 detector required by format
            detector_entry = instrument_entry.create_group('sasdetector01')
            detector_entry.attrs['canSAS_class'] = 'SASdetector'
            detector_entry.attrs['name'] = ''

        # TODO: implement writing SASnote
        i = 1
        note_entry = sasentry.create_group('sasnote{0:0=2d}'.format(i))
        note_entry.attrs['canSAS_class'] = 'SASnote'

        f.close()

    def _write_1d_data(self, data_obj, data_entry):
        """
        Writes the contents of a Data1D object to a SASdata h5py Group

        :param data_obj: A Data1D object to write to the file
        :param data_entry: A h5py Group object representing the SASdata
        """
        data_entry.attrs['signal'] = 'I'
        data_entry.attrs['I_axes'] = 'Q'
        data_entry.attrs['I_uncertainties'] = 'Idev'
        data_entry.attrs['Q_indicies'] = 0

        dI = data_obj.dy
        if dI is None:
            dI = np.zeros((data_obj.y.shape))

        data_entry.create_dataset('Q', data=data_obj.x)
        data_entry.create_dataset('I', data=data_obj.y)
        data_entry.create_dataset('Idev', data=dI)

    def _write_2d_data(self, data, data_entry):
        """
        Writes the contents of a Data2D object to a SASdata h5py Group

        :param data: A Data2D object to write to the file
        :param data_entry: A h5py Group object representing the SASdata
        """
        data_entry.attrs['signal'] = 'I'
        data_entry.attrs['I_axes'] = 'Q,Q'
        data_entry.attrs['I_uncertainties'] = 'Idev'
        data_entry.attrs['Q_indicies'] = [0,1]

        (n_rows, n_cols) = (len(data.y_bins), len(data.x_bins))

        if n_rows == 0 and n_cols == 0:
            # Calculate rows and columns, assuming detector is square
            # Same logic as used in PlotPanel.py _get_bins
            n_cols = int(np.floor(np.sqrt(len(data.qy_data))))
            n_rows = int(np.floor(len(data.qy_data) / n_cols))

            if n_rows * n_cols != len(data.qy_data):
                raise ValueError("Unable to calculate dimensions of 2D data")

        I = np.reshape(data.data, (n_rows, n_cols))
        dI = np.zeros((n_rows, n_cols))
        if not all(data.err_data == [None]):
            dI = np.reshape(data.err_data, (n_rows, n_cols))
        qx =  np.reshape(data.qx_data, (n_rows, n_cols))
        qy = np.reshape(data.qy_data, (n_rows, n_cols))

        I_entry = data_entry.create_dataset('I', data=I)
        I_entry.attrs['units'] = data.I_unit
        Qx_entry = data_entry.create_dataset('Qx', data=qx)
        Qx_entry.attrs['units'] = data.Q_unit
        Qy_entry = data_entry.create_dataset('Qy', data=qy)
        Qy_entry.attrs['units'] = data.Q_unit
        Idev_entry = data_entry.create_dataset('Idev', data=dI)
        Idev_entry.attrs['units'] = data.I_unit
