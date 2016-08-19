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

        def _h5_float(x):
            if not (isinstance(x, list)):
                x = [x]
            return np.array(x, dtype=np.float32)

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
        sample_entry = sasentry.create_group('sassample')
        sample_entry.attrs['canSAS_class'] = 'SASsample'
        sample_entry['name'] = _h5_string(data_info.sample.name)
        sample_attrs = ['thickness', 'temperature']
        for key in sample_attrs:
            if getattr(data_info.sample, key) is not None:
                sample_entry.create_dataset(key,
                    data=np.array([getattr(data_info.sample, key)]))

        instrument_entry = sasentry.create_group('sasinstrument')
        instrument_entry.attrs['canSAS_class'] = 'SASinstrument'
        instrument_entry['name'] = _h5_string(data_info.instrument)

        source_entry = instrument_entry.create_group('sassource')
        source_entry.attrs['canSAS_class'] = 'SASsource'
        if data_info.source.radiation is None:
            source_entry['radiation'] = _h5_string('neutron')
        else:
            source_entry['radiation'] = _h5_string(data_info.source.radiation)

        if len(data_info.collimation) > 0:
            i = 1
            for coll_info in data_info.collimation:
                collimation_entry = instrument_entry.create_group(
                    'sascollimation{0:0=2d}'.format(i))
                collimation_entry.attrs['canSAS_class'] = 'SAScollimation'
                if coll_info.length is not None:
                    collimation_entry['SDD'] = _h5_float(coll_info.length)
                    collimation_entry['SDD'].attrs['units'] = coll_info.length_unit
                if coll_info.name is not None:
                    collimation_entry['name'] = _h5_string(coll_info.name)
        else:
            collimation_entry = instrument_entry.create_group('sascollimation01')

        if len(data_info.detector) > 0:
            i = 1
            for det_info in data_info.detector:
                detector_entry = instrument_entry.create_group(
                    'sasdetector{0:0=2d}'.format(i))
                detector_entry.attrs['canSAS_class'] = 'SASdetector'
                if det_info.distance is not None:
                    detector_entry['SDD'] = _h5_float(det_info.distance)
                    detector_entry['SDD'].attrs['units'] = det_info.distance_unit
                if det_info.name is not None:
                    detector_entry['name'] = _h5_string(det_info.name)
                else:
                    detector_entry['name'] = _h5_string('')
                i += 1
        else:
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
        data_entry.create_dataset('Q', data=data_obj.x)
        data_entry.create_dataset('I', data=data_obj.y)
        data_entry.create_dataset('Idev', data=data_obj.dy)

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
