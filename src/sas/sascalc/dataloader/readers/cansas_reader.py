import logging
import os
import sys
import datetime
import inspect

import numpy as np

# The following 2 imports *ARE* used. Do not remove either.
import xml.dom.minidom
from xml.dom.minidom import parseString

from lxml import etree

from sas.sascalc.data_util.nxsunit import Converter

# For saving individual sections of data
from ..data_info import Data1D, Data2D, DataInfo, plottable_1D, plottable_2D, \
    Collimation, TransmissionSpectrum, Detector, Process, Aperture,\
    set_loaded_units
from ..loader_exceptions import FileContentsException, DefaultReaderException, \
    DataReaderException
from . import xml_reader
from .xml_reader import XMLreader
from .cansas_constants import CansasConstants

logger = logging.getLogger(__name__)

PREPROCESS = "xmlpreprocess"
ENCODING = "encoding"
RUN_NAME_DEFAULT = "None"
INVALID_SCHEMA_PATH_1_1 = "{0}/sas/sascalc/dataloader/readers/schema/cansas1d_invalid_v1_1.xsd"
INVALID_SCHEMA_PATH_1_0 = "{0}/sas/sascalc/dataloader/readers/schema/cansas1d_invalid_v1_0.xsd"
INVALID_XML = "\n\nThe loaded xml file, {0} does not fully meet the CanSAS v1.x specification. SasView loaded " + \
              "as much of the data as possible.\n\n"

CONSTANTS = CansasConstants()
CANSAS_FORMAT = CONSTANTS.format
CANSAS_NS = CONSTANTS.names
ALLOW_ALL = True


class Reader(XMLreader):
    cansas_version = "1.1"
    base_ns = "{cansas1d/1.1}"
    cansas_defaults = None
    type_name = "canSAS"
    invalid = True
    frm = ""
    # Log messages and errors
    logging = None
    errors = set()
    # Namespace hierarchy for current xml_file object
    names = None
    ns_list = None
    # Temporary storage location for loading multiple data sets in a single file
    current_data1d = None
    data = None
    # Wildcards
    type = ["XML files (*.xml)|*.xml", "SasView Save Files (*.svs)|*.svs"]
    # List of allowed extensions
    ext = ['.xml', '.svs']
    # Flag to bypass extension check
    allow_all = True

    def reset_state(self):
        """
        Resets the class state to a base case when loading a new data file so previous
        data files do not appear a second time
        """
        super(Reader, self).reset_state()
        self.data = []
        self.process = Process()
        self.transspectrum = TransmissionSpectrum()
        self.aperture = Aperture()
        self.collimation = Collimation()
        self.detector = Detector()
        self.names = []
        self.cansas_defaults = {}
        self.ns_list = None
        self.logging = []
        self.encoding = None

    def get_file_contents(self):
        # Reset everything since we're loading a new file
        self.reset_state()
        self.invalid = True
        xml_file = self.f_open.name
        try:
            is_valid_cansas = self.load_file_and_schema(xml_file, '')
        except FileContentsException as fc_exc:
            msg = "CanSAS Reader could not load {}".format(xml_file)
            if self.extension not in self.ext:
                # If the file has no associated loader
                raise DefaultReaderException(msg)
            raise FileContentsException(msg)
        try:
            # Parse each SASentry
            entry_list = self.xmlroot.xpath(
                '/ns:SASroot/ns:SASentry',
                namespaces={'ns': self.cansas_defaults.get("ns")})
            self.set_processing_instructions()
            for entry in entry_list:
                self._parse_entry(entry)
                if not is_valid_cansas:
                    # Set schema back to default canSAS XML for comparison
                    self.set_default_schema()
                    invalid_xml = self.find_invalid_xml()
                    if invalid_xml:
                        basename, _ = os.path.splitext(
                            os.path.basename(self.f_open.name))
                        bad_xml = INVALID_XML.format(basename + self.extension)
                        bad_xml += invalid_xml
                        self.current_datainfo.errors.append(bad_xml)
                self.data_cleanup()
        except Exception as e:
            # Convert all other exceptions to FileContentsExceptions
            raise FileContentsException(str(e))

    def load_file_and_schema(self, xml_file, schema_path=""):
        # Try and parse the XML file
        try:
            self.set_xml_file(xml_file)
        except etree.XMLSyntaxError: # File isn't valid XML so can't be loaded
            msg = "SasView cannot load {}.\nInvalid XML syntax".format(xml_file)
            raise FileContentsException(msg)

        self.cansas_version = self.xmlroot.get("version", "1.1")
        self.cansas_defaults = CANSAS_NS.get(self.cansas_version, "1.1")

        if schema_path == "":
            self.set_default_schema()
        is_valid = self.is_cansas(self.extension)
        return is_valid

    def is_cansas(self, ext="xml"):
        """
        Checks to see if the XML file is a CanSAS file

        :param ext: The file extension of the data file
        :raises FileContentsException: Raised if XML file isn't valid CanSAS
        """
        if self.validate_xml():
            name = "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"
            value = self.xmlroot.get(name)
            # Check schema CanSAS version matches file CanSAS version
            if CANSAS_NS.get(self.cansas_version).get("ns") == value.rsplit(" ")[0]:
                return None
        if ext == "svs":
            # Skip check if saved file
            return None
        # File doesn't meet schema - try loading with a less strict schema
        base_name = xml_reader.__file__
        base_name = base_name.replace("\\", "/")
        base = base_name.split("/sas/")[0]
        if self.cansas_version == "1.1":
            invalid_schema = INVALID_SCHEMA_PATH_1_1.format(
                base, self.cansas_defaults.get("schema"))
        else:
            invalid_schema = INVALID_SCHEMA_PATH_1_0.format(
                base, self.cansas_defaults.get("schema"))
        self.set_schema(invalid_schema)
        if self.validate_xml():
            return False
        # If we get to this point then file isn't valid CanSAS
        raise FileContentsException("The file is not valid CanSAS")

    def set_default_schema(self):
        base_name = xml_reader.__file__
        base_name = base_name.replace("\\", "/")
        base = base_name.split("/sas/")[0]
        schema_path = "{}/sas/sascalc/dataloader/readers/schema/{}".format(
            base, self.cansas_defaults.get("schema").replace("\\", "/")
        )
        self.set_schema(schema_path)

    def _parse_entry(self, dom, recurse=False):
        if not self._is_call_local() and not recurse:
            self.reset_state()
        if not recurse:
            self.current_datainfo = DataInfo()
            # Raises FileContentsException if file doesn't meet CanSAS schema
            self.invalid = False
            # Look for a SASentry
            self.data = []
            self.parent_class = "SASentry"
            self.names.append("SASentry")
            self.current_datainfo.meta_data["loader"] = "CanSAS XML 1D"
            self.current_datainfo.meta_data[
                PREPROCESS] = self.processing_instructions
        if self._is_call_local() and not recurse:
            basename, _ = os.path.splitext(os.path.basename(self.f_open.name))
            self.current_datainfo.filename = basename + self.extension
        # Create an empty dataset if no data has been passed to the reader
        if self.current_dataset is None:
            self._initialize_new_data_set(dom)
        self.base_ns = "{" + CANSAS_NS.get(self.cansas_version).get("ns") + "}"

        # Loop through each child in the parent element
        for node in dom:
            attr = node.attrib
            name = attr.get("name", "")
            type = attr.get("type", "")
            # Get the element name and set the current names level
            tagname = node.tag.replace(self.base_ns, "")
            tagname_original = tagname
            # Skip this iteration when loading in save state information
            if tagname in ["fitting_plug_in", "pr_inversion", "invariant",
                           "corfunc"]:
                continue
            # Get where to store content
            self.names.append(tagname_original)
            self.ns_list = CONSTANTS.iterate_namespace(self.names)
            # If the element is a child element, recurse
            if len(node.getchildren()) > 0:
                self.parent_class = tagname_original
                if tagname == 'SASdata':
                    self._initialize_new_data_set(node)
                    if isinstance(self.current_dataset, plottable_2D):
                        x_bins = attr.get("x_bins", "")
                        y_bins = attr.get("y_bins", "")
                        if x_bins is not "" and y_bins is not "":
                            self.current_dataset.shape = (x_bins, y_bins)
                        else:
                            self.current_dataset.shape = ()
                # Recurse to access data within the group
                self._parse_entry(node, recurse=True)
                if tagname == "SASsample":
                    self.current_datainfo.sample.name = name
                elif tagname == "beam_size":
                    self.current_datainfo.source.beam_size_name = name
                elif tagname == "SAScollimation":
                    self.collimation.name = name
                elif tagname == "aperture":
                    self.aperture.name = name
                    self.aperture.type = type
                self._add_intermediate()
            else:
                if isinstance(self.current_dataset, plottable_2D):
                    data_point = node.text
                    unit = attr.get('unit', '')
                else:
                    data_point, unit = self._get_node_value(node, tagname)
                if not unit:
                    unit = attr.get('unit', '')

                # Psuedo-switch statement for faster processing of data
                tagname_switcher = {
                    "Run": self.process_run,
                    "Title": self.process_title,
                    "SASnote": self.process_note,
                }
                parent_class_switcher = {
                    "SASdata": self.process_data,
                    "SASsample": self.process_sample,
                    "SASinstrument": self.process_instrument,
                    "SASdetector": self.process_detector,
                    "SAScollimation": self.process_collimation,
                    "Tdata": self.process_transmission_spectrum,
                    "SASprocess": self.process_process,
                    "SASsource": self.process_source,
                }
                names_switcher = {
                    "SASdata": self.process_data,
                    "SASsample": self.process_sample,
                    "SASdetector": self.process_detector,
                    "SAScollimation": self.process_collimation,
                    "SASsource": self.process_source,
                }
                use_tag = tagname_switcher.get(tagname, '')
                use_parent = parent_class_switcher.get(self.parent_class, '')
                params = {
                    'tagname': tagname,
                    'data_point': data_point,
                    'unit': unit,
                    'name': name,
                }
                if callable(use_tag):
                    use_tag(params)
                elif callable(use_parent):
                    use_parent(params)
                else:
                    # The elusive for/else statement...
                    for item in self.names:
                        name = names_switcher.get(item, '')
                        if callable(name):
                            name(params)
                            break
                    else:
                        # Send to meta data if no other known location
                        self.process_meta_data(params)

            self.names.remove(tagname_original)
            length = 0 if len(self.names) < 1 else len(self.names) - 1
            self.parent_class = self.names[length]
        if not self._is_call_local() and not recurse:
            self.frm = ""
            self.current_datainfo.errors = set()
            for error in self.errors:
                self.current_datainfo.errors.add(error)
            self.data_cleanup()
            self.sort_data()
            self.reset_data_list()
            return self.output[0], None

    def process_meta_data(self, params):
        tagname = params.get('tagname', '')
        data_point = params.get('data_point', '')
        key = self._create_unique_key(self.current_datainfo.meta_data, tagname)
        self.current_datainfo.meta_data[key] = data_point

    def process_run(self, params):
        data_point = params.get('data_point', '')
        name = params.get('name', '')
        self.current_datainfo.run_name[data_point] = name
        self.current_datainfo.run.append(data_point)

    def process_title(self, params):
        data_point = params.get('data_point', '')
        self.current_datainfo.title = data_point

    def process_note(self, params):
        data_point = params.get('data_point', '')
        self.current_datainfo.notes.append(data_point)

    def process_data(self, params):
        def process_i(obj):
            if isinstance(obj.current_dataset, plottable_1D):
                set_loaded_units(obj.current_dataset, "y", unit)
                obj.current_dataset.y = np.append(obj.current_dataset.y,
                                                  data_point)
            elif isinstance(obj.current_dataset, plottable_2D):
                set_loaded_units(obj.current_dataset, "z", unit)
                obj.current_dataset.data = np.fromstring(
                    data_point, dtype=float, sep=",")

        def process_q(obj):
            set_loaded_units(obj.current_dataset, "x", unit)
            obj.current_dataset.x = np.append(obj.current_dataset.x, data_point)

        def process_qx(obj):
            set_loaded_units(obj.current_dataset, "x", unit)
            obj.current_dataset.qx_data = np.fromstring(
                data_point, dtype=float, sep=",")

        def process_qy(obj):
            set_loaded_units(obj.current_dataset, "y", unit)
            obj.current_dataset.qy_data = np.fromstring(
                data_point, dtype=float, sep=",")

        def process_i_dev(obj):
            if isinstance(obj.current_dataset, plottable_1D):
                obj.current_dataset.dy = np.append(obj.current_dataset.dy,
                                                   data_point)
            elif isinstance(obj.current_dataset, plottable_2D):
                obj.current_dataset.err_data = np.fromstring(
                    data_point, dtype=float, sep=",")

        def process_q_dev(obj):
            obj.current_dataset.dx = np.append(obj.current_dataset.dx,
                                               data_point)

        def process_qx_dev(obj):
            obj.current_dataset.dqx_data = np.fromstring(
                data_point, dtype=float, sep=",")

        def process_qy_dev(obj):
            obj.current_dataset.dqy_data = np.fromstring(
                data_point, dtype=float, sep=",")

        def process_dqw(obj):
            obj.current_dataset.dxw = np.append(obj.current_dataset.dxw,
                                                data_point)

        def process_dql(obj):
            obj.current_dataset.dxl = np.append(obj.current_dataset.dxl,
                                                data_point)

        def process_mask(obj):
            inter = [item == "1" for item in data_point.split(",")]
            obj.current_dataset.mask = np.asarray(inter, dtype=bool)

        def process_sesans(obj):
            obj.current_datainfo.isSesans = bool(data_point)

        def process_y_acceptance(obj):
            obj.current_datainfo.sample.yacceptance = (data_point, unit)
            set_loaded_units(obj.current_dataset, "x", unit)

        def process_z_acceptance(obj):
            obj.current_datainfo.sample.zacceptance = (data_point, unit)
            set_loaded_units(obj.current_dataset, "y", unit)

        def call_pass(obj):
            pass

        tag = params.get('tagname', '')
        data_point = params.get('data_point', '')
        unit = params.get('unit', '')
        process_switcher = {
            'I': process_i,
            'Q': process_q,
            'Qx': process_qx,
            'Qy': process_qy,
            'Idev': process_i_dev,
            'Qdev': process_q_dev,
            'Qxdev': process_qx_dev,
            'Qydev': process_qy_dev,
            'dQw': process_dqw,
            'dQl': process_dql,
            'Mask': process_mask,
            'Qmean': call_pass,
            'Shadowfactor': call_pass,
            'Sesans': process_sesans,
            'yacceptance': process_y_acceptance,
            'zacceptance': process_z_acceptance,
        }
        handler = process_switcher.get(tag, '')
        if callable(handler):
            handler(self)
        else:
            self.process_meta_data(params)

    def process_sample(self, params):
        def process_id(obj):
            obj.current_datainfo.sample.ID = data_point

        def process_title(obj):
            obj.current_datainfo.sample.name = data_point

        def process_transmission(obj):
            obj.current_datainfo.sample.transmission = data_point

        def process_details(obj):
            obj.current_datainfo.sample.details.append(data_point)

        def process_thickness(obj):
            obj.current_datainfo.sample.thickness = data_point
            obj.current_datainfo.sample.thickness_unit = unit

        def process_temperature(obj):
            obj.current_datainfo.sample.temperature = data_point
            obj.current_datainfo.sample.temperature_unit = unit

        def process_roll(obj):
            obj.current_datainfo.sample.orientation.x = data_point
            obj.current_datainfo.sample.orientation_unit = unit

        def process_pitch(obj):
            obj.current_datainfo.sample.orientation.y = data_point
            obj.current_datainfo.sample.orientation_unit = unit

        def process_yaw(obj):
            obj.current_datainfo.sample.orientation.z = data_point
            obj.current_datainfo.sample.orientation_unit = unit

        def process_x(obj):
            obj.current_datainfo.sample.position.x = data_point
            obj.current_datainfo.sample.position_unit = unit

        def process_y(obj):
            obj.current_datainfo.sample.position.y = data_point
            obj.current_datainfo.sample.position_unit = unit

        def process_z(obj):
            obj.current_datainfo.sample.position.z = data_point
            obj.current_datainfo.sample.position_unit = unit

        tagname = params.get('tagname', '')
        data_point = params.get('data_point', '')
        unit = params.get('unit', '')
        process_switcher = {
            'ID': process_id,
            'Title': process_title,
            'thickness': process_thickness,
            'transmission': process_transmission,
            'temperature': process_temperature,
            'details': process_details,
            'x': process_x,
            'y': process_y,
            'z': process_z,
            'roll': process_roll,
            'pitch': process_pitch,
            'yaw': process_yaw,
        }
        handler = process_switcher.get(tagname, '')
        if callable(handler):
            handler(self)
        else:
            self.process_meta_data(params)

    def process_instrument(self, params):
        if params.get('tagname', '') == 'name':
            self.current_datainfo.instrument = params.get('data_point', '')
        else:
            self.process_meta_data(params)

    def process_detector(self, params):
        def process_name(obj):
            obj.detector.name = data_point

        def process_sdd(obj):
            obj.detector.distance = data_point
            obj.detector.distance_unit = unit

        def process_slit_length(obj):
            obj.detector.slit_length = data_point
            obj.detector.slit_length_unit = unit

        def process_x(obj):
            if obj.parent_class == 'offset':
                obj.detector.offset.x = data_point
                obj.detector.offset_unit = unit
            elif obj.parent_class == 'beam_center':
                obj.detector.beam_center.x = data_point
                obj.detector.beam_center_unit = unit
            elif obj.parent_class == 'pixel_size':
                obj.detector.pixel_size.x = data_point
                obj.detector.pixel_size_unit = unit

        def process_y(obj):
            if obj.parent_class == 'offset':
                obj.detector.offset.y = data_point
                obj.detector.offset_unit = unit
            elif obj.parent_class == 'beam_center':
                obj.detector.beam_center.y = data_point
                obj.detector.beam_center_unit = unit
            elif obj.parent_class == 'pixel_size':
                obj.detector.pixel_size.y = data_point
                obj.detector.pixel_size_unit = unit

        def process_z(obj):
            if obj.parent_class == 'offset':
                obj.detector.offset.z = data_point
                obj.detector.offset_unit = unit
            elif obj.parent_class == 'beam_center':
                obj.detector.beam_center.z = data_point
                obj.detector.beam_center_unit = unit
            elif obj.parent_class == 'pixel_size':
                obj.detector.pixel_size.z = data_point
                obj.detector.pixel_size_unit = unit

        def process_roll(obj):
            obj.detector.orientation.x = data_point
            obj.detector.orientation_unit = unit

        def process_pitch(obj):
            obj.detector.orientation.y = data_point
            obj.detector.orientation_unit = unit

        def process_yaw(obj):
            obj.detector.orientation.z = data_point
            obj.detector.orientation_unit = unit

        tagname = params.get('tagname', '')
        data_point = params.get('data_point', '')
        unit = params.get('unit', '')
        process_switcher = {
            'name': process_name,
            'SDD': process_sdd,
            'slit_length': process_slit_length,
            'x': process_x,
            'y': process_y,
            'z': process_z,
            'roll': process_roll,
            'pitch': process_pitch,
            'yaw': process_yaw,
        }
        handler = process_switcher.get(tagname, '')
        if callable(handler):
            handler(self)
        else:
            self.process_meta_data(params)

    def process_collimation(self, params):
        def process_name(obj):
            obj.collimation.name = data_point

        def process_length(obj):
            obj.collimation.length = data_point
            obj.collimation.length_unit = unit

        def process_aperture_distance(obj):
            obj.aperture.distance = data_point
            obj.aperture.distance_unit = unit

        def process_x(obj):
            obj.aperture.size.x = data_point
            obj.collimation.size_unit = unit

        def process_y(obj):
            obj.aperture.size.y = data_point
            obj.collimation.size_unit = unit

        def process_z(obj):
            obj.aperture.size.z = data_point
            obj.collimation.size_unit = unit

        tagname = params.get('tagname', '')
        data_point = params.get('data_point', '')
        unit = params.get('unit', '')
        process_switcher = {
            'name': process_name,
            'length': process_length,
            'distance': process_aperture_distance,
            'x': process_x,
            'y': process_y,
            'z': process_z,
        }
        handler = process_switcher.get(tagname, '')
        if callable(handler):
            handler(self)
        else:
            self.process_meta_data(params)

    def process_process(self, params):
        def process_name(obj):
            obj.process.name = data_point

        def process_desciption(obj):
            obj.process.description = data_point

        def process_date(obj):
            try:
                obj.process.date = datetime.datetime.fromtimestamp(data_point)
            except:
                obj.process.date = data_point

        def process_note(obj):
            obj.process.notes.append(data_point)

        def process_term(obj):
            dic = {"name": name, "value": data_point, "unit": unit}
            obj.process.term.append(dic)

        tagname = params.get('tagname', '')
        data_point = params.get('data_point', '')
        unit = params.get('unit', '')
        name = params.get('name', '')
        process_switcher = {
            'name': process_name,
            'description': process_desciption,
            'date': process_date,
            'SASprocessnote': process_note,
            'term': process_term,
        }
        handler = process_switcher.get(tagname, '')
        if callable(handler):
            handler(self)
        else:
            self.process_meta_data(params)

    def process_transmission_spectrum(self, params):
        def process_t(obj):
            obj.transspectrum.transmission = np.append(
                obj.transspectrum.transmission, data_point)
            obj.transspectrum.transmission_unit = unit

        def process_t_dev(obj):
            obj.transspectrum.transmission_deviation = np.append(
                obj.transspectrum.transmission_deviation, data_point)
            obj.transspectrum.transmission_deviation_unit = unit

        def process_lambda(obj):
            obj.transspectrum.wavelength = np.append(
                obj.transspectrum.wavelength, data_point)
            obj.transspectrum.wavelength_unit = unit

        tag = params.get('tagname', '')
        data_point = params.get('data_point', '')
        unit = params.get('unit', '')
        process_switcher = {
            'T': process_t,
            'Tdev': process_t_dev,
            'Lambda': process_lambda,
        }
        handler = process_switcher.get(tag, '')
        if callable(handler):
            handler(self)
        else:
            self.process_meta_data(params)

    def process_source(self, params):
        def process_wavelength(obj):
            obj.current_datainfo.source.wavelength = data_point
            obj.current_datainfo.source.wavelength_unit = unit

        def process_wavelength_min(obj):
            obj.current_datainfo.source.wavelength_min = data_point
            obj.current_datainfo.source.wavelength_min_unit = unit

        def process_wavelength_max(obj):
            obj.current_datainfo.source.wavelength_max = data_point
            obj.current_datainfo.source.wavelength_max_unit = unit

        def process_wavelength_spread(obj):
            obj.current_datainfo.source.wavelength_spread = data_point
            obj.current_datainfo.source.wavelength_spread_unit = unit

        def process_beam_size_x(obj):
            obj.current_datainfo.source.beam_size.x = data_point
            obj.current_datainfo.source.beam_size_unit = unit

        def process_beam_size_y(obj):
            obj.current_datainfo.source.beam_size.y = data_point
            obj.current_datainfo.source.beam_size_unit = unit

        def process_beam_size_z(obj):
            obj.current_datainfo.source.beam_size.z = data_point
            obj.current_datainfo.source.beam_size_unit = unit

        def process_radiation(obj):
            obj.current_datainfo.source.radiation = data_point

        def process_beam_shape(obj):
            obj.current_datainfo.source.beam_shape = data_point

        tag = params.get('tagname', '')
        data_point = params.get('data_point', '')
        unit = params.get('unit', '')
        source_switcher = {
            'wavelength': process_wavelength,
            'wavelength_min': process_wavelength_min,
            'wavelength_max': process_wavelength_max,
            'wavelength_spread': process_wavelength_spread,
            'x': process_beam_size_x,
            'y': process_beam_size_y,
            'z': process_beam_size_z,
            'radiation': process_radiation,
            'beam_shape': process_beam_shape,
        }
        # TODO: this is repeated in multiple methods - generalize
        handler = source_switcher.get(tag, '')
        if callable(handler):
            handler(self)
        else:
            self.process_meta_data(params)

    def _is_call_local(self):
        if self.frm == "":
            inter = inspect.stack()
            self.frm = inter[2]
        mod_name = self.frm[1].replace("\\", "/").replace(".pyc", "")
        mod_name = mod_name.replace(".py", "")
        mod = mod_name.split("sas/")
        mod_name = mod[1]
        if mod_name != "sascalc/dataloader/readers/cansas_reader":
            return False
        return True

    def _add_intermediate(self):
        """
        This method stores any intermediate objects within the final data set after fully reading the set.
        """
        if self.parent_class == 'SASprocess':
            self.current_datainfo.process.append(self.process)
            self.process = Process()
        elif self.parent_class == 'SASdetector':
            self.current_datainfo.detector.append(self.detector)
            self.detector = Detector()
        elif self.parent_class == 'SAStransmission_spectrum':
            self.current_datainfo.trans_spectrum.append(self.transspectrum)
            self.transspectrum = TransmissionSpectrum()
        elif self.parent_class == 'SAScollimation':
            self.current_datainfo.collimation.append(self.collimation)
            self.collimation = Collimation()
        elif self.parent_class == 'aperture':
            self.collimation.aperture.append(self.aperture)
            self.aperture = Aperture()
        elif self.parent_class == 'SASdata':
            self.data.append(self.current_dataset)

    def _get_node_value(self, node, tagname):
        """
        Get the value of a node and any applicable units

        :param node: The XML node to get the value of
        :param tagname: The tagname of the node
        """
        #Get the text from the node and convert all whitespace to spaces
        units = ''
        node_value = node.text
        if node_value is not None:
            node_value = ' '.join(node_value.split())
        else:
            node_value = ""

        # If the value is a float, compile with units.
        if self.ns_list.ns_datatype == "float":
            # If an empty value is given, set as zero.
            if node_value is None or node_value.isspace() \
                                    or node_value.lower() == "nan":
                node_value = "0.0"
            #Convert the value to the base units
            node_value, units = self._unit_conversion(node, tagname, node_value)

        # If the value is a timestamp, convert to a datetime object
        elif self.ns_list.ns_datatype == "timestamp":
            if node_value is None or node_value.isspace():
                pass
            else:
                try:
                    node_value = \
                        datetime.datetime.fromtimestamp(node_value)
                except ValueError:
                    node_value = None
        return node_value, units

    def _unit_conversion(self, node, tagname, node_value):
        """
        A unit converter method used to convert the data included in the file
        to the default units listed in data_info

        :param node: XML node
        :param tagname: name of the node
        :param node_value: The value of the current dom node
        """
        attr = node.attrib
        value_unit = ''
        err_msg = None
        default_unit = None
        if not isinstance(node_value, float):
            node_value = float(node_value)
        if 'unit' in attr and attr.get('unit') is not None:
            try:
                unit = attr['unit']
                # Split the units to retain backwards compatibility with
                # projects, analyses, and saved data from v4.1.0
                unit_list = unit.split("|")
                if len(unit_list) > 1:
                    local_unit = unit_list[1]
                else:
                    local_unit = unit
                unitname = self.ns_list.current_level.get("unit", "")
                if "SASdetector" in self.names:
                    save_in = "detector"
                elif "aperture" in self.names:
                    save_in = "aperture"
                elif "SAScollimation" in self.names:
                    save_in = "collimation"
                elif "SAStransmission_spectrum" in self.names:
                    save_in = "transspectrum"
                elif "SASdata" in self.names:
                    x = np.zeros(1)
                    y = np.zeros(1)
                    self.current_data1d = Data1D(x, y)
                    save_in = "current_data1d"
                elif "SASsource" in self.names:
                    save_in = "current_datainfo.source"
                elif "SASsample" in self.names:
                    save_in = "current_datainfo.sample"
                elif "SASprocess" in self.names:
                    save_in = "process"
                else:
                    save_in = "current_datainfo"
                default_unit = getattrchain(self, '.'.join((save_in, unitname)))
                if (local_unit and default_unit
                        and local_unit.lower() != default_unit.lower()
                        and local_unit.lower() != "none"):
                    # Check local units - bad units raise KeyError
                    #print("loading", tagname, node_value, local_unit, default_unit)
                    data_conv_q = Converter(local_unit)
                    value_unit = default_unit
                    node_value = data_conv_q(node_value, units=default_unit)
                else:
                    value_unit = local_unit
            except KeyError:
                # Do not throw an error for loading Sesans data in cansas xml
                # This is a temporary fix.
                if local_unit != "A" and local_unit != 'pol':
                    err_msg = "CanSAS reader: unexpected "
                    err_msg += "\"{0}\" unit [{1}]; "
                    err_msg = err_msg.format(tagname, local_unit)
                    err_msg += "expecting [{0}]".format(default_unit)
                value_unit = local_unit
            except Exception:
                err_msg = "CanSAS reader: unknown error converting "
                err_msg += "\"{0}\" unit [{1}]"
                err_msg = err_msg.format(tagname, local_unit)
                value_unit = local_unit
        elif 'unit' in attr:
            value_unit = attr['unit']
        if err_msg:
            self.errors.add(err_msg)
        return node_value, value_unit

    def _initialize_new_data_set(self, node=None):
        if node is not None:
            for child in node:
                if child.tag.replace(self.base_ns, "") == "Idata":
                    for i_child in child:
                        if i_child.tag.replace(self.base_ns, "") == "Qx":
                            self.current_dataset = plottable_2D()
                            return
        self.current_dataset = plottable_1D(np.array(0), np.array(0))

    ## Writing Methods
    def write(self, filename, datainfo):
        """
        Write the content of a Data1D as a CanSAS XML file

        :param filename: name of the file to write
        :param datainfo: Data1D object
        """
        # Create XML document
        doc, _ = self._to_xml_doc(datainfo)
        # Write the file
        file_ref = open(filename, 'wb')
        if self.encoding is None:
            self.encoding = "UTF-8"
        doc.write(file_ref, encoding=self.encoding,
                  pretty_print=True, xml_declaration=True)
        file_ref.close()

    def _to_xml_doc(self, datainfo):
        """
        Create an XML document to contain the content of a Data1D

        :param datainfo: Data1D object
        """
        is_2d = False
        if issubclass(datainfo.__class__, Data2D):
            is_2d = True

        # Get PIs and create root element
        pi_string = self._get_pi_string()
        # Define namespaces and create SASroot object
        main_node = self._create_main_node()
        # Create ElementTree, append SASroot and apply processing instructions
        base_string = pi_string + self.to_string(main_node)
        base_element = self.create_element_from_string(base_string)
        doc = self.create_tree(base_element)
        # Create SASentry Element
        entry_node = self.create_element("SASentry")
        root = doc.getroot()
        root.append(entry_node)

        # Add Title to SASentry
        self.write_node(entry_node, "Title", datainfo.title)
        # Add Run to SASentry
        self._write_run_names(datainfo, entry_node)
        # Add Data info to SASEntry
        if is_2d:
            self._write_data_2d(datainfo, entry_node)
        else:
            self._write_data(datainfo, entry_node)
        # Transmission Spectrum Info
        # TODO: fix the writer to linearize all data, including T_spectrum
        # self._write_trans_spectrum(datainfo, entry_node)
        # Sample info
        self._write_sample_info(datainfo, entry_node)
        # Instrument info
        instr = self._write_instrument(datainfo, entry_node)
        #   Source
        self._write_source(datainfo, instr)
        #   Collimation
        self._write_collimation(datainfo, instr)
        #   Detectors
        self._write_detectors(datainfo, instr)
        # Processes info
        self._write_process_notes(datainfo, entry_node)
        # Note info
        self._write_notes(datainfo, entry_node)
        # Return the document, and the SASentry node associated with
        #      the data we just wrote
        # If the calling function was not the cansas reader, return a minidom
        #      object rather than an lxml object.
        self.frm = inspect.stack()[1]
        doc, entry_node = self._check_origin(entry_node, doc)
        return doc, entry_node

    def write_node(self, parent, name, value, attr=None):
        """
        :param doc: document DOM
        :param parent: parent node
        :param name: tag of the element
        :param value: value of the child text node
        :param attr: attribute dictionary

        :return: True if something was appended, otherwise False
        """
        if value is not None:
            parent = self.ebuilder(parent, name, value, attr)
            return True
        return False

    def _get_pi_string(self):
        """
        Creates the processing instructions header for writing to file
        """
        pis = self.return_processing_instructions()
        if len(pis) > 0:
            pi_tree = self.create_tree(pis[0])
            i = 1
            for i in range(1, len(pis) - 1):
                pi_tree = self.append(pis[i], pi_tree)
            pi_string = self.to_string(pi_tree)
        else:
            pi_string = ""
        return pi_string

    def _create_main_node(self):
        """
        Creates the primary xml header used when writing to file
        """
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        version = self.cansas_version
        n_s = CANSAS_NS.get(version).get("ns")
        if version == "1.1":
            url = "http://www.cansas.org/formats/1.1/"
        else:
            url = "http://svn.smallangles.net/svn/canSAS/1dwg/trunk/"
        schema_location = "{0} {1}cansas1d.xsd".format(n_s, url)
        attrib = {"{" + xsi + "}schemaLocation" : schema_location,
                  "version" : version}
        nsmap = {'xsi' : xsi, None: n_s}

        main_node = self.create_element("{" + n_s + "}SASroot",
                                        attrib=attrib, nsmap=nsmap)
        return main_node

    def _write_run_names(self, datainfo, entry_node):
        """
        Writes the run names to the XML file

        :param datainfo: The Data1D object the information is coming from
        :param entry_node: lxml node ElementTree object to be appended to
        """
        if datainfo.run is None or datainfo.run == []:
            datainfo.run.append(RUN_NAME_DEFAULT)
            datainfo.run_name[RUN_NAME_DEFAULT] = RUN_NAME_DEFAULT
        for item in datainfo.run:
            runname = {}
            if item in datainfo.run_name and \
            len(str(datainfo.run_name[item])) > 1:
                runname = {'name': datainfo.run_name[item]}
            self.write_node(entry_node, "Run", item, runname)

    def _write_data(self, datainfo, entry_node):
        """
        Writes 1D I and Q data to the XML file

        :param datainfo: The Data1D object the information is coming from
        :param entry_node: lxml node ElementTree object to be appended to
        """
        node = self.create_element("SASdata")
        self.append(node, entry_node)

        for i in range(len(datainfo.x)):
            point = self.create_element("Idata")
            node.append(point)
            self.write_node(point, "Q", datainfo.x[i],
                            {'unit': datainfo._xunit})
            if len(datainfo.y) >= i:
                self.write_node(point, "I", datainfo.y[i],
                                {'unit': datainfo._yunit})
            if datainfo.dy is not None and len(datainfo.dy) > i:
                self.write_node(point, "Idev", datainfo.dy[i],
                                {'unit': datainfo._yunit})
            if datainfo.dx is not None and len(datainfo.dx) > i:
                self.write_node(point, "Qdev", datainfo.dx[i],
                                {'unit': datainfo._xunit})
            if datainfo.dxw is not None and len(datainfo.dxw) > i:
                self.write_node(point, "dQw", datainfo.dxw[i],
                                {'unit': datainfo._xunit})
            if datainfo.dxl is not None and len(datainfo.dxl) > i:
                self.write_node(point, "dQl", datainfo.dxl[i],
                                {'unit': datainfo._xunit})
        if datainfo.isSesans:
            sesans_attrib = {'x_axis': datainfo._xaxis,
                             'y_axis': datainfo._yaxis,
                             'x_unit': datainfo.x_unit,
                             'y_unit': datainfo.y_unit}
            sesans = self.create_element("Sesans", attrib=sesans_attrib)
            sesans.text = str(datainfo.isSesans)
            entry_node.append(sesans)
            self.write_node(entry_node, "yacceptance", datainfo.sample.yacceptance[0],
                             {'unit': datainfo.sample.yacceptance[1]})
            self.write_node(entry_node, "zacceptance", datainfo.sample.zacceptance[0],
                             {'unit': datainfo.sample.zacceptance[1]})


    def _write_data_2d(self, datainfo, entry_node):
        """
        Writes 2D data to the XML file

        :param datainfo: The Data2D object the information is coming from
        :param entry_node: lxml node ElementTree object to be appended to
        """
        attr = {}
        if datainfo.data.shape:
            attr["x_bins"] = str(len(datainfo.x_bins))
            attr["y_bins"] = str(len(datainfo.y_bins))
        node = self.create_element("SASdata", attr)
        self.append(node, entry_node)

        point = self.create_element("Idata")
        node.append(point)
        qx = ','.join(str(v) for v in datainfo.qx_data)
        qy = ','.join(str(v) for v in datainfo.qy_data)
        intensity = ','.join(str(v) for v in datainfo.data)

        self.write_node(point, "Qx", qx,
                        {'unit': datainfo._xunit})
        self.write_node(point, "Qy", qy,
                        {'unit': datainfo._yunit})
        self.write_node(point, "I", intensity,
                        {'unit': datainfo._zunit})
        if datainfo.err_data is not None:
            err = ','.join(str(v) for v in datainfo.err_data)
            self.write_node(point, "Idev", err,
                            {'unit': datainfo._zunit})
        if datainfo.dqy_data is not None:
            dqy = ','.join(str(v) for v in datainfo.dqy_data)
            self.write_node(point, "Qydev", dqy,
                            {'unit': datainfo._yunit})
        if datainfo.dqx_data is not None:
            dqx = ','.join(str(v) for v in datainfo.dqx_data)
            self.write_node(point, "Qxdev", dqx,
                            {'unit': datainfo._xunit})
        if datainfo.mask is not None:
            mask = ','.join("1" if v else "0" for v in datainfo.mask)
            self.write_node(point, "Mask", mask)

    def _write_trans_spectrum(self, datainfo, entry_node):
        """
        Writes the transmission spectrum data to the XML file

        :param datainfo: The Data1D object the information is coming from
        :param entry_node: lxml node ElementTree object to be appended to
        """
        for i in range(len(datainfo.trans_spectrum)):
            spectrum = datainfo.trans_spectrum[i]
            node = self.create_element("SAStransmission_spectrum",
                                       {"name" : spectrum.name})
            self.append(node, entry_node)
            if isinstance(spectrum.timestamp, datetime.datetime):
                node.setAttribute("timestamp", spectrum.timestamp)
            for i in range(len(spectrum.wavelength)):
                point = self.create_element("Tdata")
                node.append(point)
                self.write_node(point, "Lambda", spectrum.wavelength[i],
                                {'unit': spectrum.wavelength_unit})
                self.write_node(point, "T", spectrum.transmission[i],
                                {'unit': spectrum.transmission_unit})
                if spectrum.transmission_deviation is not None \
                and len(spectrum.transmission_deviation) >= i:
                    self.write_node(point, "Tdev",
                                    spectrum.transmission_deviation[i],
                                    {'unit':
                                     spectrum.transmission_deviation_unit})

    def _write_sample_info(self, datainfo, entry_node):
        """
        Writes the sample information to the XML file

        :param datainfo: The Data1D object the information is coming from
        :param entry_node: lxml node ElementTree object to be appended to
        """
        sample = self.create_element("SASsample")
        if datainfo.sample.name is not None:
            self.write_attribute(sample, "name",
                                 str(datainfo.sample.name))
        self.append(sample, entry_node)
        self.write_node(sample, "ID", str(datainfo.sample.ID))
        self.write_node(sample, "thickness", datainfo.sample.thickness,
                        {"unit": datainfo.sample.thickness_unit})
        self.write_node(sample, "transmission", datainfo.sample.transmission)
        self.write_node(sample, "temperature", datainfo.sample.temperature,
                        {"unit": datainfo.sample.temperature_unit})

        pos = self.create_element("position")
        written = self.write_node(pos,
                                  "x",
                                  datainfo.sample.position.x,
                                  {"unit": datainfo.sample.position_unit})
        written = written | self.write_node( \
            pos, "y", datainfo.sample.position.y,
            {"unit": datainfo.sample.position_unit})
        written = written | self.write_node( \
            pos, "z", datainfo.sample.position.z,
            {"unit": datainfo.sample.position_unit})
        if written:
            self.append(pos, sample)

        ori = self.create_element("orientation")
        written = self.write_node(ori, "roll",
                                  datainfo.sample.orientation.x,
                                  {"unit": datainfo.sample.orientation_unit})
        written = written | self.write_node( \
            ori, "pitch", datainfo.sample.orientation.y,
            {"unit": datainfo.sample.orientation_unit})
        written = written | self.write_node( \
            ori, "yaw", datainfo.sample.orientation.z,
            {"unit": datainfo.sample.orientation_unit})
        if written:
            self.append(ori, sample)

        for item in datainfo.sample.details:
            self.write_node(sample, "details", item)

    def _write_instrument(self, datainfo, entry_node):
        """
        Writes the instrumental information to the XML file

        :param datainfo: The Data1D object the information is coming from
        :param entry_node: lxml node ElementTree object to be appended to
        """
        instr = self.create_element("SASinstrument")
        self.append(instr, entry_node)
        self.write_node(instr, "name", datainfo.instrument)
        return instr

    def _write_source(self, datainfo, instr):
        """
        Writes the source information to the XML file

        :param datainfo: The Data1D object the information is coming from
        :param instr: instrument node  to be appended to
        """
        source = self.create_element("SASsource")
        if datainfo.source.name is not None:
            self.write_attribute(source, "name",
                                 str(datainfo.source.name))
        self.append(source, instr)
        if datainfo.source.radiation is None or datainfo.source.radiation == '':
            datainfo.source.radiation = "neutron"
        self.write_node(source, "radiation", datainfo.source.radiation)

        size = self.create_element("beam_size")
        if datainfo.source.beam_size_name is not None:
            self.write_attribute(size, "name",
                                 str(datainfo.source.beam_size_name))
        written = self.write_node( \
            size, "x", datainfo.source.beam_size.x,
            {"unit": datainfo.source.beam_size_unit})
        written = written | self.write_node( \
            size, "y", datainfo.source.beam_size.y,
            {"unit": datainfo.source.beam_size_unit})
        written = written | self.write_node( \
            size, "z", datainfo.source.beam_size.z,
            {"unit": datainfo.source.beam_size_unit})
        if written:
            self.append(size, source)

        self.write_node(source, "beam_shape", datainfo.source.beam_shape)
        self.write_node(source, "wavelength",
                        datainfo.source.wavelength,
                        {"unit": datainfo.source.wavelength_unit})
        self.write_node(source, "wavelength_min",
                        datainfo.source.wavelength_min,
                        {"unit": datainfo.source.wavelength_min_unit})
        self.write_node(source, "wavelength_max",
                        datainfo.source.wavelength_max,
                        {"unit": datainfo.source.wavelength_max_unit})
        self.write_node(source, "wavelength_spread",
                        datainfo.source.wavelength_spread,
                        {"unit": datainfo.source.wavelength_spread_unit})

    def _write_collimation(self, datainfo, instr):
        """
        Writes the collimation information to the XML file

        :param datainfo: The Data1D object the information is coming from
        :param instr: lxml node ElementTree object to be appended to
        """
        if datainfo.collimation == [] or datainfo.collimation is None:
            coll = Collimation()
            datainfo.collimation.append(coll)
        for item in datainfo.collimation:
            coll = self.create_element("SAScollimation")
            if item.name is not None:
                self.write_attribute(coll, "name", str(item.name))
            self.append(coll, instr)

            self.write_node(coll, "length", item.length,
                            {"unit": item.length_unit})

            for aperture in item.aperture:
                apert = self.create_element("aperture")
                if aperture.name is not None:
                    self.write_attribute(apert, "name", str(aperture.name))
                if aperture.type is not None:
                    self.write_attribute(apert, "type", str(aperture.type))
                self.append(apert, coll)

                size = self.create_element("size")
                if aperture.size_name is not None:
                    self.write_attribute(size, "name",
                                         str(aperture.size_name))
                written = self.write_node(size, "x", aperture.size.x,
                                          {"unit": aperture.size_unit})
                written = written | self.write_node( \
                    size, "y", aperture.size.y,
                    {"unit": aperture.size_unit})
                written = written | self.write_node( \
                    size, "z", aperture.size.z,
                    {"unit": aperture.size_unit})
                if written:
                    self.append(size, apert)

                self.write_node(apert, "distance", aperture.distance,
                                {"unit": aperture.distance_unit})

    def _write_detectors(self, datainfo, instr):
        """
        Writes the detector information to the XML file

        :param datainfo: The Data1D object the information is coming from
        :param inst: lxml instrument node to be appended to
        """
        if datainfo.detector is None or datainfo.detector == []:
            det = Detector()
            det.name = ""
            datainfo.detector.append(det)

        for item in datainfo.detector:
            det = self.create_element("SASdetector")
            written = self.write_node(det, "name", item.name)
            written = written | self.write_node(det, "SDD", item.distance,
                                                {"unit": item.distance_unit})
            if written:
                self.append(det, instr)

            off = self.create_element("offset")
            written = self.write_node(off, "x", item.offset.x,
                                      {"unit": item.offset_unit})
            written = written | self.write_node(off, "y", item.offset.y,
                                                {"unit": item.offset_unit})
            written = written | self.write_node(off, "z", item.offset.z,
                                                {"unit": item.offset_unit})
            if written:
                self.append(off, det)

            ori = self.create_element("orientation")
            written = self.write_node(ori, "roll", item.orientation.x,
                                      {"unit": item.orientation_unit})
            written = written | self.write_node(ori, "pitch",
                                                item.orientation.y,
                                                {"unit": item.orientation_unit})
            written = written | self.write_node(ori, "yaw",
                                                item.orientation.z,
                                                {"unit": item.orientation_unit})
            if written:
                self.append(ori, det)

            center = self.create_element("beam_center")
            written = self.write_node(center, "x", item.beam_center.x,
                                      {"unit": item.beam_center_unit})
            written = written | self.write_node(center, "y",
                                                item.beam_center.y,
                                                {"unit": item.beam_center_unit})
            written = written | self.write_node(center, "z",
                                                item.beam_center.z,
                                                {"unit": item.beam_center_unit})
            if written:
                self.append(center, det)

            pix = self.create_element("pixel_size")
            written = self.write_node(pix, "x", item.pixel_size.x,
                                      {"unit": item.pixel_size_unit})
            written = written | self.write_node(pix, "y", item.pixel_size.y,
                                                {"unit": item.pixel_size_unit})
            written = written | self.write_node(pix, "z", item.pixel_size.z,
                                                {"unit": item.pixel_size_unit})
            if written:
                self.append(pix, det)
            self.write_node(det, "slit_length", item.slit_length,
                {"unit": item.slit_length_unit})


    def _write_process_notes(self, datainfo, entry_node):
        """
        Writes the process notes to the XML file

        :param datainfo: The Data1D object the information is coming from
        :param entry_node: lxml node ElementTree object to be appended to

        """
        for item in datainfo.process:
            node = self.create_element("SASprocess")
            self.append(node, entry_node)
            self.write_node(node, "name", item.name)
            self.write_node(node, "date", item.date)
            self.write_node(node, "description", item.description)
            for term in item.term:
                if isinstance(term, list):
                    value = term['value']
                    del term['value']
                elif isinstance(term, dict):
                    value = term.get("value")
                    del term['value']
                else:
                    value = term
                self.write_node(node, "term", value, term)
            for note in item.notes:
                self.write_node(node, "SASprocessnote", note)
            if len(item.notes) == 0:
                self.write_node(node, "SASprocessnote", "")

    def _write_notes(self, datainfo, entry_node):
        """
        Writes the notes to the XML file and creates an empty note if none
        exist

        :param datainfo: The Data1D object the information is coming from
        :param entry_node: lxml node ElementTree object to be appended to

        """
        if len(datainfo.notes) == 0:
            node = self.create_element("SASnote")
            self.append(node, entry_node)
        else:
            for item in datainfo.notes:
                node = self.create_element("SASnote")
                self.write_text(node, item)
                self.append(node, entry_node)

    def _check_origin(self, entry_node, doc):
        """
        Return the document, and the SASentry node associated with
        the data we just wrote.
        If the calling function was not the cansas reader, return a minidom
        object rather than an lxml object.

        :param entry_node: lxml node ElementTree object to be appended to
        :param doc: entire xml tree
        """
        if not self.frm:
            self.frm = inspect.stack()[1]
        mod_name = self.frm[1].replace("\\", "/").replace(".pyc", "")
        mod_name = mod_name.replace(".py", "")
        mod = mod_name.split("sas/")
        mod_name = mod[1]
        if mod_name != "sascalc/dataloader/readers/cansas_reader":
            string = self.to_string(doc, pretty_print=False)
            doc = parseString(string)
            node_name = entry_node.tag
            node_list = doc.getElementsByTagName(node_name)
            entry_node = node_list.item(0)
        return doc, entry_node

    # DO NOT REMOVE - used in saving and loading panel states.
    def _store_float(self, location, node, variable, storage, optional=True):
        """
        Get the content of a xpath location and store
        the result. Check that the units are compatible
        with the destination. The value is expected to
        be a float.

        The xpath location might or might not exist.
        If it does not exist, nothing is done

        :param location: xpath location to fetch
        :param node: node to read the data from
        :param variable: name of the data member to store it in [string]
        :param storage: data object that has the 'variable' data member
        :param optional: if True, no exception will be raised
            if unit conversion can't be done

        :raise ValueError: raised when the units are not recognized
        """
        entry = get_content(location, node)
        try:
            value = float(entry.text)
        except ValueError:
            value = None

        if value is not None:
            # If the entry has units, check to see that they are
            # compatible with what we currently have in the data object
            units = entry.get('unit')
            if units is not None:
                toks = variable.split('.')
                local_unit = getattr(storage, toks[0]+"_unit")
                if local_unit is not None and units.lower() != local_unit.lower():
                    try:
                        conv = Converter(units)
                        setattrchain(storage, variable, conv(value, units=local_unit))
                    except Exception as exc:
                        err_mess = "CanSAS reader: could not convert"
                        err_mess += " %s unit [%s]; expecting [%s]\n  %s" \
                            % (variable, units, local_unit, exc)
                        self.errors.add(err_mess)
                        if optional:
                            logger.info(err_mess)
                        else:
                            raise ValueError(err_mess)
                else:
                    setattrchain(storage, variable, value)
            else:
                setattrchain(storage, variable, value)

    # DO NOT REMOVE - used in saving and loading panel states.
    def _store_content(self, location, node, variable, storage):
        """
        Get the content of a xpath location and store
        the result. The value is treated as a string.

        The xpath location might or might not exist.
        If it does not exist, nothing is done

        :param location: xpath location to fetch
        :param node: node to read the data from
        :param variable: name of the data member to store it in [string]
        :param storage: data object that has the 'variable' data member

        :return: return a list of errors
        """
        entry = get_content(location, node)
        if entry is not None and entry.text is not None:
            setattrchain(storage, variable, entry.text.strip())

# DO NOT REMOVE Called by outside packages:
#    sas.sasgui.perspectives.invariant.invariant_state
#    sas.sasgui.perspectives.fitting.pagestate
def get_content(location, node):
    """
    Get the first instance of the content of a xpath location.

    :param location: xpath location
    :param node: node to start at

    :return: Element, or None
    """
    nodes = node.xpath(location,
                       namespaces={'ns': CANSAS_NS.get("1.0").get("ns")})
    if len(nodes) > 0:
        return nodes[0]
    else:
        return None

# DO NOT REMOVE Called by outside packages:
#    sas.sasgui.perspectives.fitting.pagestate
def write_node(doc, parent, name, value, attr=None):
    """
    :param doc: document DOM
    :param parent: parent node
    :param name: tag of the element
    :param value: value of the child text node
    :param attr: attribute dictionary

    :return: True if something was appended, otherwise False
    """
    if attr is None:
        attr = {}
    if value is not None:
        node = doc.createElement(name)
        node.appendChild(doc.createTextNode(str(value)))
        for item in attr:
            node.setAttribute(item, attr[item])
        parent.appendChild(node)
        return True
    return False

def getattrchain(obj, chain, default=None):
    """Like getattr, but the attr may contain multiple parts separated by '.'"""
    for part in chain.split('.'):
        if hasattr(obj, part):
            obj = getattr(obj, part, None)
        else:
            return default
    return obj

def setattrchain(obj, chain, value):
    """Like setattr, but the attr may contain multiple parts separated by '.'"""
    parts = list(chain.split('.'))
    for part in parts[-1]:
        obj = getattr(obj, part, None)
        if obj is None:
            raise ValueError("missing parent object "+part)
    setattr(obj, value)
