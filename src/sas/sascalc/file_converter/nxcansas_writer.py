"""
    NXcanSAS 1/2D data reader for writing HDF5 formatted NXcanSAS files.
"""

import h5py
import numpy as np

from sas.sascalc.dataloader.data_info import Data1D, Data2D

PROBES = ['neutron', 'x-ray', 'muon', 'electron', 'ultraviolet',
          'visible light', 'positron', 'proton']
TYPES = ['Spallation Neutron Source', 'UV Plasma Source', 'Free-Electron Laser',
         'Reactor Neutron Source', 'Synchrotron X-ray Source', 'UV Laser',
         'Pulsed Muon Source', 'Pulsed Reactor Neutron Source', 'Ion Source',
         'Rotating Anode X-ray', 'Optical Laser', 'Fixed Tube X-ray']


class NXcanSASWriter:
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
            if isinstance(string, np.ndarray):
                return string
            elif not isinstance(string, str):
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
            """
            Write a vector to an h5 entry

            :param entry: The H5Py entry to write to
            :param vector: The Vector to write
            :param names: What to call the x,y and z components of the vector
                when writing to the H5Py entry
            :param units: The units of the vector (optional)
            :param write_fn: A function to convert the value to the required
                format and write it to the H5Py entry, of the form
                f(entry, value, name) (optional)
            """
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

        valid_data = all([isinstance(d, (Data1D, Data2D)) for d in dataset])
        if not valid_data:
            raise ValueError("All entries of dataset must be Data1D or Data2D"
                             "objects")

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
        sasentry.attrs['version'] = '1.1'

        for i, data_obj in enumerate(dataset):
            data_entry = sasentry.create_group("sasdata{0:0=2d}".format(i+1))
            data_entry.attrs['canSAS_class'] = 'SASdata'
            if isinstance(data_obj, Data1D):
                self._write_1d_data(data_obj, data_entry)
            elif isinstance(data_obj, Data2D):
                self._write_2d_data(data_obj, data_entry)

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
        # NXcanSAS doesn't save information about pitch, only roll
        # and yaw. The _write_h5_vector method writes vector.y, but we
        # need to write vector.z for yaw
        data_info.sample.orientation.y = data_info.sample.orientation.z
        _write_h5_vector(sample_entry, data_info.sample.orientation,
            names=['polar_angle', 'azimuthal_angle'])
        if data_info.sample.details is not None\
            and data_info.sample.details != []:
            details = None
            if len(data_info.sample.details) > 1:
                details = [np.string_(d) for d in data_info.sample.details]
                details = np.array(details)
            elif data_info.sample.details != []:
                details = _h5_string(data_info.sample.details[0])
            if details is not None:
                sample_entry.create_dataset('details', data=details)

        # Instrument metadata
        instrument_entry = sasentry.create_group('sasinstrument')
        instrument_entry.attrs['canSAS_class'] = 'SASinstrument'
        instrument_entry['name'] = _h5_string(data_info.instrument)

        # Source metadata
        source_entry = instrument_entry.create_group('sassource')
        source_entry.attrs['canSAS_class'] = 'SASsource'
        if data_info.source.radiation is not None:
            if data_info.source.radiation in PROBES:
                source_entry['probe'] = _h5_string(data_info.source.radiation)
            elif data_info.source.radiation in TYPES:
                source_entry['type'] = _h5_string(data_info.source.radiation)
            else:
                # Should not get here, but we shouldn't throw info out either
                source_entry['notes'] = _h5_string(data_info.source.radiation)
        if data_info.source.type is not None:
            source_entry['type'] = _h5_string(data_info.source.type)
        if data_info.source.probe is not None:
            source_entry['probe'] = _h5_string(data_info.source.probe)
        if data_info.source.beam_shape is not None:
            source_entry['beam_shape'] = _h5_string(data_info.source.beam_shape)
        wavelength_keys = { 'wavelength': 'incident_wavelength',
            'wavelength_min':'wavelength_min',
            'wavelength_max': 'wavelength_max',
            'wavelength_spread': 'incident_wavelength_spread' }
        for sasname, nxname in wavelength_keys.items():
            value = getattr(data_info.source, sasname)
            units = getattr(data_info.source, sasname + '_unit')
            if value is not None:
                source_entry[nxname] = _h5_float(value)
                source_entry[nxname].attrs['units'] = units
        _write_h5_vector(source_entry, data_info.source.beam_size,
            names=['beam_size_x', 'beam_size_y'],
            units=data_info.source.beam_size_unit, write_fn=_write_h5_float)

        # Collimation metadata
        if len(data_info.collimation) > 0:
            for i, coll_info in enumerate(data_info.collimation):
                collimation_entry = instrument_entry.create_group(
                    'sascollimation{0:0=2d}'.format(i + 1))
                collimation_entry.attrs['canSAS_class'] = 'SAScollimation'
                if coll_info.length is not None:
                    _write_h5_float(collimation_entry, coll_info.length, 'SDD')
                    collimation_entry['SDD'].attrs['units'] =\
                        coll_info.length_unit
                if coll_info.name is not None:
                    collimation_entry['name'] = _h5_string(coll_info.name)
        else:
            # Create a blank one - at least 1 collimation required by format
            instrument_entry.create_group('sascollimation01')

        # Detector metadata
        if len(data_info.detector) > 0:
            i = 1
            for i, det_info in enumerate(data_info.detector):
                detector_entry = instrument_entry.create_group(
                    'sasdetector{0:0=2d}'.format(i + 1))
                detector_entry.attrs['canSAS_class'] = 'SASdetector'
                if det_info.distance is not None:
                    _write_h5_float(detector_entry, det_info.distance, 'SDD')
                    detector_entry['SDD'].attrs['units'] =\
                        det_info.distance_unit
                if det_info.name is not None:
                    detector_entry['name'] = _h5_string(det_info.name)
                else:
                    detector_entry['name'] = _h5_string('')
                if det_info.slit_length is not None:
                    _write_h5_float(detector_entry, det_info.slit_length,
                                    'slit_length')
                    detector_entry['slit_length'].attrs['units'] =\
                        det_info.slit_length_unit
                _write_h5_vector(detector_entry, det_info.offset)
                # NXcanSAS doesn't save information about pitch, only roll
                # and yaw. The _write_h5_vector method writes vector.y, but we
                # need to write vector.z for yaw
                det_info.orientation.y = det_info.orientation.z
                _write_h5_vector(detector_entry, det_info.orientation,
                    names=['polar_angle', 'azimuthal_angle'])
                _write_h5_vector(detector_entry, det_info.beam_center,
                    names=['beam_center_x', 'beam_center_y'],
                    write_fn=_write_h5_float, units=det_info.beam_center_unit)
                _write_h5_vector(detector_entry, det_info.pixel_size,
                    names=['x_pixel_size', 'y_pixel_size'],
                    write_fn=_write_h5_float, units=det_info.pixel_size_unit)
        else:
            # Create a blank one - at least 1 detector required by format
            detector_entry = instrument_entry.create_group('sasdetector01')
            detector_entry.attrs['canSAS_class'] = 'SASdetector'
            detector_entry.attrs['name'] = ''

        # Process meta data
        for i, process in enumerate(data_info.process):
            process_entry = sasentry.create_group('sasprocess{0:0=2d}'.format(
                i + 1))
            process_entry.attrs['canSAS_class'] = 'SASprocess'
            if process.name:
                name = _h5_string(process.name)
                process_entry.create_dataset('name', data=name)
            if process.date:
                date = _h5_string(process.date)
                process_entry.create_dataset('date', data=date)
            if process.description:
                desc = _h5_string(process.description)
                process_entry.create_dataset('description', data=desc)
            for j, term in enumerate(process.term):
                # Don't save empty terms
                if term:
                    h5_term = _h5_string(term)
                    process_entry.create_dataset('term{0:0=2d}'.format(
                        j + 1), data=h5_term)
            for j, note in enumerate(process.notes):
                # Don't save empty notes
                if note:
                    h5_note = _h5_string(note)
                    process_entry.create_dataset('note{0:0=2d}'.format(
                        j + 1), data=h5_note)

        # Transmission Spectrum
        for i, trans in enumerate(data_info.trans_spectrum):
            trans_entry = sasentry.create_group(
                'sastransmission_spectrum{0:0=2d}'.format(i + 1))
            trans_entry.attrs['canSAS_class'] = 'SAStransmission_spectrum'
            trans_entry.attrs['signal'] = 'T'
            trans_entry.attrs['T_axes'] = 'T'
            trans_entry.attrs['name'] = trans.name
            # Timestamp can be a string or a date-like object. Only write if set
            if trans.timestamp:
                trans_entry.attrs['timestamp'] = trans.timestamp
            transmission = trans_entry.create_dataset('T',
                                                      data=trans.transmission)
            transmission.attrs['unertainties'] = 'Tdev'
            trans_entry.create_dataset('Tdev',
                                       data=trans.transmission_deviation)
            trans_entry.create_dataset('lambda', data=trans.wavelength)

        if np.isscalar(data_info.notes) and data_info.notes:
            # Handle scalars that aren't empty arrays, None, '', etc.
            notes = [np.string_(data_info.notes)]
        elif len(data_info.notes) > 1:
            # Handle iterables that aren't empty
            notes = [np.string_(n) for n in data_info.notes]
        else:
            # Notes are required in NXcanSAS format
            notes = [np.string_('')]
        if notes is not None:
            for i, note in enumerate(notes):
                note_entry = sasentry.create_group('sasnote{0}'.format(i))
                note_entry.attrs['canSAS_class'] = 'SASnote'
                note_entry.create_dataset('SASnote', data=note)

        f.close()

    def _write_1d_data(self, data_obj, data_entry):
        """
        Writes the contents of a Data1D object to a SASdata h5py Group

        :param data_obj: A Data1D object to write to the file
        :param data_entry: A h5py Group object representing the SASdata
        """
        data_entry.attrs['signal'] = 'I'
        data_entry.attrs['I_axes'] = 'Q'
        data_entry.attrs['Q_indices'] = [0]
        q_entry = data_entry.create_dataset('Q', data=data_obj.x)
        q_entry.attrs['units'] = data_obj.x_unit
        i_entry = data_entry.create_dataset('I', data=data_obj.y)
        i_entry.attrs['units'] = data_obj.y_unit
        if data_obj.dy is not None:
            i_entry.attrs['uncertainties'] = 'Idev'
            i_dev_entry = data_entry.create_dataset('Idev', data=data_obj.dy)
            i_dev_entry.attrs['units'] = data_obj.y_unit
        if data_obj.dx is not None:
            q_entry.attrs['resolutions'] = 'dQ'
            dq_entry = data_entry.create_dataset('dQ', data=data_obj.dx)
            dq_entry.attrs['units'] = data_obj.x_unit
        elif data_obj.dxl is not None:
            q_entry.attrs['resolutions'] = ['dQl','dQw']
            dql_entry = data_entry.create_dataset('dQl', data=data_obj.dxl)
            dql_entry.attrs['units'] = data_obj.x_unit
            dqw_entry = data_entry.create_dataset('dQw', data=data_obj.dxw)
            dqw_entry.attrs['units'] = data_obj.x_unit

    def _write_2d_data(self, data, data_entry):
        """
        Writes the contents of a Data2D object to a SASdata h5py Group

        :param data: A Data2D object to write to the file
        :param data_entry: A h5py Group object representing the SASdata
        """
        data_entry.attrs['signal'] = 'I'
        data_entry.attrs['I_axes'] = 'Qx,Qy'
        data_entry.attrs['Q_indices'] = [0,1]

        (n_rows, n_cols) = (len(data.y_bins), len(data.x_bins))

        if (n_rows == 0 and n_cols == 0) or (n_cols*n_rows != data.data.size):
            # Calculate rows and columns, assuming detector is square
            # Same logic as used in PlotPanel.py _get_bins
            n_cols = int(np.floor(np.sqrt(len(data.qy_data))))
            n_rows = int(np.floor(len(data.qy_data) / n_cols))

            if n_rows * n_cols != len(data.qy_data):
                raise ValueError("Unable to calculate dimensions of 2D data")

        intensity = np.reshape(data.data, (n_rows, n_cols))
        qx = np.reshape(data.qx_data, (n_rows, n_cols))
        qy = np.reshape(data.qy_data, (n_rows, n_cols))

        i_entry = data_entry.create_dataset('I', data=intensity)
        i_entry.attrs['units'] = data.I_unit
        qx_entry = data_entry.create_dataset('Qx', data=qx)
        qx_entry.attrs['units'] = data.Q_unit
        qy_entry = data_entry.create_dataset('Qy', data=qy)
        qy_entry.attrs['units'] = data.Q_unit
        if (data.err_data is not None
                and not all(v is None for v in data.err_data)):
            d_i = np.reshape(data.err_data, (n_rows, n_cols))
            i_entry.attrs['uncertainties'] = 'Idev'
            i_dev_entry = data_entry.create_dataset('Idev', data=d_i)
            i_dev_entry.attrs['units'] = data.I_unit
        if (data.dqx_data is not None
                and not all(v is None for v in data.dqx_data)):
            qx_entry.attrs['resolutions'] = 'dQx'
            dqx_entry = data_entry.create_dataset('dQx', data=data.dqx_data)
            dqx_entry.attrs['units'] = data.Q_unit
        if (data.dqy_data is not None
                and not all(v is None for v in data.dqy_data)):
            qy_entry.attrs['resolutions'] = 'dQy'
            dqy_entry = data_entry.create_dataset('dQy', data=data.dqy_data)
            dqy_entry.attrs['units'] = data.Q_unit
        if data.mask is not None and not all(v is None for v in data.mask):
            data_entry.attrs['mask'] = "mask"
            mask = np.invert(np.asarray(data.mask, dtype=bool))
            data_entry.create_dataset('mask', data=mask)
