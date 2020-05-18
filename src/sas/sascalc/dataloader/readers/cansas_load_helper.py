import datetime
import numpy as np

from ..data_info import plottable_1D, plottable_2D, set_loaded_units


class CansasLoaderHelper:

    def __init__(self, parent):
        self.parent = parent
        self.tagname_switcher = {
            "Run": self.process_run,
            "Title": self.process_title,
            "SASnote": self.process_note,
        }
        self.parent_class_switcher = {
            "SASdata": self.process_data,
            "SASsample": self.process_sample,
            "SASinstrument": self.process_instrument,
            "SASdetector": self.process_detector,
            "SAScollimation": self.process_collimation,
            "Tdata": self.process_transmission_spectrum,
            "SASprocess": self.process_process,
            "SASsource": self.process_source,
        }
        self.names_switcher = {
            "SASdata": self.process_data,
            "SASsample": self.process_sample,
            "SASdetector": self.process_detector,
            "SAScollimation": self.process_collimation,
            "SASsource": self.process_source,
        }
        self.data_switcher = {
            'I': self.process_i,
            'Q': self.process_q,
            'Qx': self.process_qx,
            'Qy': self.process_qy,
            'Idev': self.process_i_dev,
            'Qdev': self.process_q_dev,
            'Qxdev': self.process_qx_dev,
            'Qydev': self.process_qy_dev,
            'dQw': self.process_dqw,
            'dQl': self.process_dql,
            'Mask': self.process_mask,
            'Qmean': self.call_pass,
            'Shadowfactor': self.call_pass,
            'Sesans': self.process_sesans,
            'yacceptance': self.process_y_acceptance,
            'zacceptance': self.process_z_acceptance,
        }
        self.sample_switcher = {
            'ID': self.process_sample_id,
            'Title': self.process_sample_title,
            'thickness': self.process_sample_thickness,
            'transmission': self.process_sample_transmission,
            'temperature': self.process_temperature,
            'details': self.process_sample_details,
            'x': self.process_sample_pos_x,
            'y': self.process_sample_pos_y,
            'z': self.process_sample_pos_z,
            'roll': self.process_sample_pos_roll,
            'pitch': self.process_sample_pos_pitch,
            'yaw': self.process_sample_pos_yaw,
        }
        self.source_switcher = {
            'wavelength': self.process_wavelength,
            'wavelength_min': self.process_wavelength_min,
            'wavelength_max': self.process_wavelength_max,
            'wavelength_spread': self.process_wavelength_spread,
            'x': self.process_beam_size_x,
            'y': self.process_beam_size_y,
            'z': self.process_beam_size_z,
            'radiation': self.process_radiation,
            'beam_shape': self.process_beam_shape,
        }
        self.detector_switcher = {
            'name': self.process_detector_name,
            'SDD': self.process_sdd,
            'slit_length': self.process_slit_length,
            'x': self.process_detector_x,
            'y': self.process_detector_y,
            'z': self.process_detector_z,
            'roll': self.process_detector_roll,
            'pitch': self.process_detector_pitch,
            'yaw': self.process_detector_yaw,
        }
        self.collimation_switcher = {
            'name': self.process_collimation_name,
            'length': self.process_collimation_length,
            'distance': self.process_aperture_distance,
            'x': self.process_aperture_x,
            'y': self.process_aperture_y,
            'z': self.process_aperture_z,
        }
        self.trans_spectra_switcher = {
            'T': self.process_t,
            'Tdev': self.process_t_dev,
            'Lambda': self.process_lambda,
        }
        self.process_switcher = {
            'name': self.process_process_name,
            'description': self.process_desciption,
            'date': self.process_date,
            'SASprocessnote': self.process_process_note,
            'term': self.process_term,
        }

    def process_meta_data(self, params):
        tagname = params.get('tagname', '')
        data_point = params.get('data_point', '')
        key = self.parent._create_unique_key(
            self.parent.current_datainfo.meta_data, tagname)
        self.parent.current_datainfo.meta_data[key] = data_point

    def process_run(self, params):
        data_point = params.get('data_point', '')
        name = params.get('name', '')
        self.parent.current_datainfo.run_name[data_point] = name
        self.parent.current_datainfo.run.append(data_point)

    def process_title(self, params):
        data_point = params.get('data_point', '')
        self.parent.current_datainfo.title = data_point

    def process_note(self, params):
        data_point = params.get('data_point', '')
        self.parent.current_datainfo.notes.append(data_point)

    def process_i(self, params):
        data_point = params.get('data_point', '')
        unit = params.get('unit', '')
        if isinstance(self.parent.current_dataset, plottable_1D):
            set_loaded_units(self.parent.current_dataset, "y", unit)
            self.parent.current_dataset.y = np.append(
                self.parent.current_dataset.y, float(data_point))
        elif isinstance(self.parent.current_dataset, plottable_2D):
            set_loaded_units(self.parent.current_dataset, "z", unit)
            self.parent.current_dataset.data = np.fromstring(
                data_point, dtype=float, sep=",")

    def process_q(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        set_loaded_units(self.parent.current_dataset, "x", unit)
        self.parent.current_dataset.x = np.append(self.parent.current_dataset.x,
                                                  data_point)

    def process_qx(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        set_loaded_units(self.parent.current_dataset, "x", unit)
        self.parent.current_dataset.qx_data = np.fromstring(
            data_point, dtype=float, sep=",")

    def process_qy(self, params):
        data_point = params.get('data_point', '')
        unit = params.get('unit', '')
        set_loaded_units(self.parent.current_dataset, "y", unit)
        self.parent.current_dataset.qy_data = np.fromstring(
            data_point, dtype=float, sep=",")

    def process_i_dev(self, params):
        data_point = params.get('data_point', '')
        unit = params.get('unit', '')
        if isinstance(self.parent.current_dataset, plottable_1D):
            self.parent.current_dataset.dy = np.append(
                self.parent.current_dataset.dy, float(data_point))
        elif isinstance(self.parent.current_dataset, plottable_2D):
            self.parent.current_dataset.err_data = np.fromstring(
                data_point, dtype=float, sep=",")

    def process_q_dev(self, params):
        data_point = float(params.get('data_point', ''))
        self.parent.current_dataset.dx = np.append(self.parent.current_dataset.dx,
                                           data_point)

    def process_qx_dev(self, params):
        data_point = params.get('data_point', '')
        self.parent.current_dataset.dqx_data = np.fromstring(
            data_point, dtype=float, sep=",")

    def process_qy_dev(self, params):
        data_point = params.get('data_point', '')
        self.parent.current_dataset.dqy_data = np.fromstring(
            data_point, dtype=float, sep=",")

    def process_dqw(self, params):
        data_point = float(params.get('data_point', ''))
        self.parent.current_dataset.dxw = np.append(self.parent.current_dataset.dxw,
                                            data_point)

    def process_dql(self, params):
        data_point = float(params.get('data_point', ''))
        self.parent.current_dataset.dxl = np.append(self.parent.current_dataset.dxl,
                                            data_point)

    def process_mask(self, params):
        data_point = params.get('data_point', '')
        inter = [item == "1" for item in data_point.split(",")]
        self.parent.current_dataset.mask = np.asarray(inter, dtype=bool)

    def process_sesans(self, params):
        data_point = params.get('data_point', '')
        self.parent.current_datainfo.isSesans = bool(data_point)

    def process_y_acceptance(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.sample.yacceptance = (data_point, unit)
        set_loaded_units(self.parent.current_dataset, "x", unit)

    def process_z_acceptance(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.sample.zacceptance = (data_point, unit)
        set_loaded_units(self.parent.current_dataset, "y", unit)

    def call_pass(self, params):
        pass

    def process_data(self, params):
        tag = params.get('tagname', '')
        handler = self.data_switcher.get(tag, '')
        if callable(handler):
            handler(params)
        else:
            self.process_meta_data(params)

    def process_sample_id(self, params):
        data_point = params.get('data_point', '')
        self.parent.current_datainfo.sample.ID = data_point

    def process_sample_title(self, params):
        data_point = params.get('data_point', '')
        self.parent.current_datainfo.sample.name = data_point

    def process_sample_transmission(self, params):
        data_point = float(params.get('data_point', ''))
        self.parent.current_datainfo.sample.transmission = data_point

    def process_sample_details(self, params):
        data_point = params.get('data_point', '')
        self.parent.current_datainfo.sample.details.append(data_point)

    def process_sample_thickness(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.sample.thickness = data_point
        self.parent.current_datainfo.sample.thickness_unit = unit

    def process_temperature(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.sample.temperature = data_point
        self.parent.current_datainfo.sample.temperature_unit = unit

    def process_sample_pos_roll(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.sample.orientation.x = data_point
        self.parent.current_datainfo.sample.orientation_unit = unit

    def process_sample_pos_pitch(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.sample.orientation.y = data_point
        self.parent.current_datainfo.sample.orientation_unit = unit

    def process_sample_pos_yaw(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.sample.orientation.z = data_point
        self.parent.current_datainfo.sample.orientation_unit = unit

    def process_sample_pos_x(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.sample.position.x = data_point
        self.parent.current_datainfo.sample.position_unit = unit

    def process_sample_pos_y(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.sample.position.y = data_point
        self.parent.current_datainfo.sample.position_unit = unit

    def process_sample_pos_z(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.sample.position.z = data_point
        self.parent.current_datainfo.sample.position_unit = unit

    def process_sample(self, params):
        tagname = params.get('tagname', '')
        handler = self.sample_switcher.get(tagname, '')
        if callable(handler):
            handler(params)
        else:
            self.process_meta_data(params)

    def process_instrument(self, params):
        if params.get('tagname', '') == 'name':
            self.parent.current_datainfo.instrument = params.get('data_point', '')
        else:
            self.process_meta_data(params)

    def process_detector_name(self, params):
        data_point = params.get('data_point', '')
        self.parent.detector.name = data_point

    def process_sdd(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.detector.distance = data_point
        self.parent.detector.distance_unit = unit

    def process_slit_length(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.detector.slit_length = data_point
        self.parent.detector.slit_length_unit = unit

    def process_detector_x(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        if self.parent.parent_class == 'offset':
            self.parent.detector.offset.x = data_point
            self.parent.detector.offset_unit = unit
        elif self.parent.parent_class == 'beam_center':
            self.parent.detector.beam_center.x = data_point
            self.parent.detector.beam_center_unit = unit
        elif self.parent.parent_class == 'pixel_size':
            self.parent.detector.pixel_size.x = data_point
            self.parent.detector.pixel_size_unit = unit

    def process_detector_y(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        if self.parent.parent_class == 'offset':
            self.parent.detector.offset.y = data_point
            self.parent.detector.offset_unit = unit
        elif self.parent.parent_class == 'beam_center':
            self.parent.detector.beam_center.y = data_point
            self.parent.detector.beam_center_unit = unit
        elif self.parent.parent_class == 'pixel_size':
            self.parent.detector.pixel_size.y = data_point
            self.parent.detector.pixel_size_unit = unit

    def process_detector_z(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        if self.parent.parent_class == 'offset':
            self.parent.detector.offset.z = data_point
            self.parent.detector.offset_unit = unit
        elif self.parent.parent_class == 'beam_center':
            self.parent.detector.beam_center.z = data_point
            self.parent.detector.beam_center_unit = unit
        elif self.parent.parent_class == 'pixel_size':
            self.parent.detector.pixel_size.z = data_point
            self.parent.detector.pixel_size_unit = unit

    def process_detector_roll(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.detector.orientation.x = data_point
        self.parent.detector.orientation_unit = unit

    def process_detector_pitch(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.detector.orientation.y = data_point
        self.parent.detector.orientation_unit = unit

    def process_detector_yaw(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.detector.orientation.z = data_point
        self.parent.detector.orientation_unit = unit

    def process_detector(self, params):
        tagname = params.get('tagname', '')
        handler = self.detector_switcher.get(tagname, '')
        if callable(handler):
            handler(params)
        else:
            self.process_meta_data(params)

    def process_collimation_name(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.collimation.name = data_point

    def process_collimation_length(self, params):
        data_point = params.get('data_point', '')
        unit = params.get('unit', '')
        self.parent.collimation.length = data_point
        self.parent.collimation.length_unit = unit

    def process_aperture_distance(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.aperture.distance = data_point
        self.parent.aperture.distance_unit = unit

    def process_aperture_x(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.aperture.size.x = data_point
        self.parent.collimation.size_unit = unit

    def process_aperture_y(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.aperture.size.y = data_point
        self.parent.collimation.size_unit = unit

    def process_aperture_z(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.aperture.size.z = data_point
        self.parent.collimation.size_unit = unit

    def process_collimation(self, params):
        tagname = params.get('tagname', '')
        handler = self.collimation_switcher.get(tagname, '')
        if callable(handler):
            handler(params)
        else:
            self.process_meta_data(params)

    def process_process_name(self, params):
        data_point = params.get('data_point', '')
        self.parent.process.name = data_point

    def process_desciption(self, params):
        data_point = params.get('data_point', '')
        self.parent.process.description = data_point

    def process_date(self, params):
        data_point = params.get('data_point', '')
        try:
            self.parent.process.date = datetime.datetime.fromtimestamp(
                data_point)
        except Exception as e:
            self.parent.process.date = data_point

    def process_process_note(self, params):
        data_point = params.get('data_point', '')
        self.parent.process.notes.append(data_point)

    def process_term(self, params):
        data_point = params.get('data_point', '')
        unit = params.get('unit', '')
        name = params.get('name', '')
        dic = {"name": name, "value": data_point, "unit": unit}
        self.parent.process.term.append(dic)

    def process_process(self, params):
        tagname = params.get('tagname', '')
        handler = self.process_switcher.get(tagname, '')
        if callable(handler):
            handler(params)
        else:
            self.process_meta_data(params)

    def process_t(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.transspectrum.transmission = np.append(
            self.parent.transspectrum.transmission, data_point)
        self.parent.transspectrum.transmission_unit = unit

    def process_t_dev(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.transspectrum.transmission_deviation = np.append(
            self.parent.transspectrum.transmission_deviation, data_point)
        self.parent.transspectrum.transmission_deviation_unit = unit

    def process_lambda(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.transspectrum.wavelength = np.append(
            self.parent.transspectrum.wavelength, data_point)
        self.parent.transspectrum.wavelength_unit = unit

    def process_transmission_spectrum(self, params):
        tag = params.get('tagname', '')
        handler = self.trans_spectra_switcher.get(tag, '')
        if callable(handler):
            handler(params)
        else:
            self.process_meta_data(params)

    def process_wavelength(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.source.wavelength = data_point
        self.parent.current_datainfo.source.wavelength_unit = unit

    def process_wavelength_min(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.source.wavelength_min = data_point
        self.parent.current_datainfo.source.wavelength_min_unit = unit

    def process_wavelength_max(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.source.wavelength_max = data_point
        self.parent.current_datainfo.source.wavelength_max_unit = unit

    def process_wavelength_spread(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.source.wavelength_spread = data_point
        self.parent.current_datainfo.source.wavelength_spread_unit = unit

    def process_beam_size_x(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.source.beam_size.x = data_point
        self.parent.current_datainfo.source.beam_size_unit = unit

    def process_beam_size_y(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.source.beam_size.y = data_point
        self.parent.current_datainfo.source.beam_size_unit = unit

    def process_beam_size_z(self, params):
        data_point = float(params.get('data_point', ''))
        unit = params.get('unit', '')
        self.parent.current_datainfo.source.beam_size.z = data_point
        self.parent.current_datainfo.source.beam_size_unit = unit

    def process_radiation(self, params):
        data_point = params.get('data_point', '')
        self.parent.current_datainfo.source.radiation = data_point

    def process_beam_shape(self, params):
        data_point = params.get('data_point', '')
        self.parent.current_datainfo.source.beam_shape = data_point

    def process_source(self, params):
        tag = params.get('tagname', '')
        handler = self.source_switcher.get(tag, '')
        if callable(handler):
            handler(params)
        else:
            self.process_meta_data(params)