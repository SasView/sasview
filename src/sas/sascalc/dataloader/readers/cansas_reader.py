"""
    CanSAS data reader - new recursive cansas_version.
"""
############################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#If you use DANSE applications to do scientific research that leads to
#publication, we ask that you acknowledge the use of the software with the
#following sentence:
#This work benefited from DANSE software developed under NSF award DMR-0520547.
#copyright 2008,2009 University of Tennessee
#############################################################################

import logging
import numpy as np
import os
import sys
import datetime
import inspect
# For saving individual sections of data
from sas.sascalc.dataloader.data_info import Data1D, Data2D, DataInfo, \
    plottable_1D, plottable_2D
from sas.sascalc.dataloader.data_info import Collimation, TransmissionSpectrum, \
    Detector, Process, Aperture
from sas.sascalc.dataloader.data_info import \
    combine_data_info_with_plottable as combine_data
import sas.sascalc.dataloader.readers.xml_reader as xml_reader
from sas.sascalc.dataloader.readers.xml_reader import XMLreader
from sas.sascalc.dataloader.readers.cansas_constants import CansasConstants, CurrentLevel
from sas.sascalc.dataloader.loader_exceptions import FileContentsException

# The following 2 imports *ARE* used. Do not remove either.
import xml.dom.minidom
from xml.dom.minidom import parseString

logger = logging.getLogger(__name__)

PREPROCESS = "xmlpreprocess"
ENCODING = "encoding"
RUN_NAME_DEFAULT = "None"
INVALID_SCHEMA_PATH_1_1 = "{0}/sas/sascalc/dataloader/readers/schema/cansas1d_invalid_v1_1.xsd"
INVALID_SCHEMA_PATH_1_0 = "{0}/sas/sascalc/dataloader/readers/schema/cansas1d_invalid_v1_0.xsd"
INVALID_XML = "\n\nThe loaded xml file, {0} does not fully meet the CanSAS v1.x specification. SasView loaded " + \
              "as much of the data as possible.\n\n"
HAS_CONVERTER = True
try:
    from sas.sascalc.data_util.nxsunit import Converter
except ImportError:
    HAS_CONVERTER = False

CONSTANTS = CansasConstants()
CANSAS_FORMAT = CONSTANTS.format
CANSAS_NS = CONSTANTS.names
ALLOW_ALL = True

class Reader(XMLreader):
    """
    Class to load cansas 1D XML files

    :Dependencies:
        The CanSAS reader requires PyXML 0.8.4 or later.
    """
    # CanSAS version - defaults to version 1.0
    cansas_version = "1.0"
    base_ns = "{cansas1d/1.0}"
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
    current_datainfo = None
    current_dataset = None
    current_data1d = None
    data = None
    # List of data1D objects to be sent back to SasView
    output = None
    # Wildcards
    type = ["XML files (*.xml)|*.xml", "SasView Save Files (*.svs)|*.svs"]
    # List of allowed extensions
    ext = ['.xml', '.XML', '.svs', '.SVS']
    # Flag to bypass extension check
    allow_all = True

    def reset_state(self):
        """
        Resets the class state to a base case when loading a new data file so previous
        data files do not appear a second time
        """
        self.current_datainfo = None
        self.current_dataset = None
        self.current_data1d = None
        self.data = []
        self.process = Process()
        self.transspectrum = TransmissionSpectrum()
        self.aperture = Aperture()
        self.collimation = Collimation()
        self.detector = Detector()
        self.names = []
        self.cansas_defaults = {}
        self.output = []
        self.ns_list = None
        self.logging = []
        self.encoding = None

    def read(self, xml_file, schema_path="", invalid=True):
        """
        Validate and read in an xml_file file in the canSAS format.

        :param xml_file: A canSAS file path in proper XML format
        :param schema_path: A file path to an XML schema to validate the xml_file against
        """
        # For every file loaded, reset everything to a base state
        self.reset_state()
        self.invalid = invalid
        # Check that the file exists
        if os.path.isfile(xml_file):
            basename, extension = os.path.splitext(os.path.basename(xml_file))
            # If the file type is not allowed, return nothing
            if extension in self.ext or self.allow_all:
                # Get the file location of
                self.load_file_and_schema(xml_file, schema_path)
                self.add_data_set()
                # Try to load the file, but raise an error if unable to.
                # Check the file matches the XML schema
                try:
                    self.is_cansas(extension)
                    self.invalid = False
                    # Get each SASentry from XML file and add it to a list.
                    entry_list = self.xmlroot.xpath(
                            '/ns:SASroot/ns:SASentry',
                            namespaces={'ns': self.cansas_defaults.get("ns")})
                    self.names.append("SASentry")

                    # Get all preprocessing events and encoding
                    self.set_processing_instructions()

                    # Parse each <SASentry> item
                    for entry in entry_list:
                        # Create a new DataInfo object for every <SASentry>

                        # Set the file name and then parse the entry.
                        self.current_datainfo.filename = basename + extension
                        self.current_datainfo.meta_data["loader"] = "CanSAS XML 1D"
                        self.current_datainfo.meta_data[PREPROCESS] = \
                            self.processing_instructions

                        # Parse the XML SASentry
                        self._parse_entry(entry)
                        # Combine datasets with datainfo
                        self.add_data_set()
                except RuntimeError:
                    # If the file does not match the schema, raise this error
                    invalid_xml = self.find_invalid_xml()
                    invalid_xml = INVALID_XML.format(basename + extension) + invalid_xml
                    self.errors.add(invalid_xml)
                    # Try again with an invalid CanSAS schema, that requires only a data set in each
                    base_name = xml_reader.__file__
                    base_name = base_name.replace("\\", "/")
                    base = base_name.split("/sas/")[0]
                    if self.cansas_version == "1.1":
                        invalid_schema = INVALID_SCHEMA_PATH_1_1.format(base, self.cansas_defaults.get("schema"))
                    else:
                        invalid_schema = INVALID_SCHEMA_PATH_1_0.format(base, self.cansas_defaults.get("schema"))
                    self.set_schema(invalid_schema)
                    try:
                        if self.invalid:
                            if self.is_cansas():
                                self.output = self.read(xml_file, invalid_schema, False)
                            else:
                                raise RuntimeError
                        else:
                            raise RuntimeError
                    except RuntimeError:
                        x = np.zeros(1)
                        y = np.zeros(1)
                        self.current_data1d = Data1D(x,y)
                        self.current_data1d.errors = self.errors
                        return [self.current_data1d]
        else:
            self.output.append("Not a valid file path.")
        # Return a list of parsed entries that dataloader can manage
        return self.output

    def _parse_entry(self, dom, recurse=False):
        """
        Parse a SASEntry - new recursive method for parsing the dom of
            the CanSAS data format. This will allow multiple data files
            and extra nodes to be read in simultaneously.

        :param dom: dom object with a namespace base of names
        """

        if not self._is_call_local() and not recurse:
            self.reset_state()
            self.add_data_set()
            self.names.append("SASentry")
            self.parent_class = "SASentry"
        self._check_for_empty_data()
        self.base_ns = "{0}{1}{2}".format("{", \
                            CANSAS_NS.get(self.cansas_version).get("ns"), "}")

        # Go through each child in the parent element
        for node in dom:
            attr = node.attrib
            name = attr.get("name", "")
            type = attr.get("type", "")
            # Get the element name and set the current names level
            tagname = node.tag.replace(self.base_ns, "")
            tagname_original = tagname
            # Skip this iteration when loading in save state information
            if tagname == "fitting_plug_in" or tagname == "pr_inversion" or tagname == "invariant":
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
                # Recursion step to access data within the group
                self._parse_entry(node, True)
                if tagname == "SASsample":
                    self.current_datainfo.sample.name = name
                elif tagname == "beam_size":
                    self.current_datainfo.source.beam_size_name = name
                elif tagname == "SAScollimation":
                    self.collimation.name = name
                elif tagname == "aperture":
                    self.aperture.name = name
                    self.aperture.type = type
                self.add_intermediate()
            else:
                if isinstance(self.current_dataset, plottable_2D):
                    data_point = node.text
                    unit = attr.get('unit', '')
                else:
                    data_point, unit = self._get_node_value(node, tagname)

                # If this is a dataset, store the data appropriately
                if tagname == 'Run':
                    self.current_datainfo.run_name[data_point] = name
                    self.current_datainfo.run.append(data_point)
                elif tagname == 'Title':
                    self.current_datainfo.title = data_point
                elif tagname == 'SASnote':
                    self.current_datainfo.notes.append(data_point)

                # I and Q - 1D data
                elif tagname == 'I' and isinstance(self.current_dataset, plottable_1D):
                    unit_list = unit.split("|")
                    if len(unit_list) > 1:
                        self.current_dataset.yaxis(unit_list[0].strip(),
                                                   unit_list[1].strip())
                    else:
                        self.current_dataset.yaxis("Intensity", unit)
                    self.current_dataset.y = np.append(self.current_dataset.y, data_point)
                elif tagname == 'Idev' and isinstance(self.current_dataset, plottable_1D):
                    self.current_dataset.dy = np.append(self.current_dataset.dy, data_point)
                elif tagname == 'Q':
                    unit_list = unit.split("|")
                    if len(unit_list) > 1:
                        self.current_dataset.xaxis(unit_list[0].strip(),
                                                   unit_list[1].strip())
                    else:
                        self.current_dataset.xaxis("Q", unit)
                    self.current_dataset.x = np.append(self.current_dataset.x, data_point)
                elif tagname == 'Qdev':
                    self.current_dataset.dx = np.append(self.current_dataset.dx, data_point)
                elif tagname == 'dQw':
                    self.current_dataset.dxw = np.append(self.current_dataset.dxw, data_point)
                elif tagname == 'dQl':
                    self.current_dataset.dxl = np.append(self.current_dataset.dxl, data_point)
                elif tagname == 'Qmean':
                    pass
                elif tagname == 'Shadowfactor':
                    pass
                elif tagname == 'Sesans':
                    self.current_datainfo.isSesans = bool(data_point)
                elif tagname == 'yacceptance':
                    self.current_datainfo.sample.yacceptance = (data_point, unit)
                elif tagname == 'zacceptance':
                    self.current_datainfo.sample.zacceptance = (data_point, unit)

                # I and Qx, Qy - 2D data
                elif tagname == 'I' and isinstance(self.current_dataset, plottable_2D):
                    self.current_dataset.yaxis("Intensity", unit)
                    self.current_dataset.data = np.fromstring(data_point, dtype=float, sep=",")
                elif tagname == 'Idev' and isinstance(self.current_dataset, plottable_2D):
                    self.current_dataset.err_data = np.fromstring(data_point, dtype=float, sep=",")
                elif tagname == 'Qx':
                    self.current_dataset.xaxis("Qx", unit)
                    self.current_dataset.qx_data = np.fromstring(data_point, dtype=float, sep=",")
                elif tagname == 'Qy':
                    self.current_dataset.yaxis("Qy", unit)
                    self.current_dataset.qy_data = np.fromstring(data_point, dtype=float, sep=",")
                elif tagname == 'Qxdev':
                    self.current_dataset.xaxis("Qxdev", unit)
                    self.current_dataset.dqx_data = np.fromstring(data_point, dtype=float, sep=",")
                elif tagname == 'Qydev':
                    self.current_dataset.yaxis("Qydev", unit)
                    self.current_dataset.dqy_data = np.fromstring(data_point, dtype=float, sep=",")
                elif tagname == 'Mask':
                    inter = [item == "1" for item in data_point.split(",")]
                    self.current_dataset.mask = np.asarray(inter, dtype=bool)

                # Sample Information
                elif tagname == 'ID' and self.parent_class == 'SASsample':
                    self.current_datainfo.sample.ID = data_point
                elif tagname == 'Title' and self.parent_class == 'SASsample':
                    self.current_datainfo.sample.name = data_point
                elif tagname == 'thickness' and self.parent_class == 'SASsample':
                    self.current_datainfo.sample.thickness = data_point
                    self.current_datainfo.sample.thickness_unit = unit
                elif tagname == 'transmission' and self.parent_class == 'SASsample':
                    self.current_datainfo.sample.transmission = data_point
                elif tagname == 'temperature' and self.parent_class == 'SASsample':
                    self.current_datainfo.sample.temperature = data_point
                    self.current_datainfo.sample.temperature_unit = unit
                elif tagname == 'details' and self.parent_class == 'SASsample':
                    self.current_datainfo.sample.details.append(data_point)
                elif tagname == 'x' and self.parent_class == 'position':
                    self.current_datainfo.sample.position.x = data_point
                    self.current_datainfo.sample.position_unit = unit
                elif tagname == 'y' and self.parent_class == 'position':
                    self.current_datainfo.sample.position.y = data_point
                    self.current_datainfo.sample.position_unit = unit
                elif tagname == 'z' and self.parent_class == 'position':
                    self.current_datainfo.sample.position.z = data_point
                    self.current_datainfo.sample.position_unit = unit
                elif tagname == 'roll' and self.parent_class == 'orientation' and 'SASsample' in self.names:
                    self.current_datainfo.sample.orientation.x = data_point
                    self.current_datainfo.sample.orientation_unit = unit
                elif tagname == 'pitch' and self.parent_class == 'orientation' and 'SASsample' in self.names:
                    self.current_datainfo.sample.orientation.y = data_point
                    self.current_datainfo.sample.orientation_unit = unit
                elif tagname == 'yaw' and self.parent_class == 'orientation' and 'SASsample' in self.names:
                    self.current_datainfo.sample.orientation.z = data_point
                    self.current_datainfo.sample.orientation_unit = unit

                # Instrumental Information
                elif tagname == 'name' and self.parent_class == 'SASinstrument':
                    self.current_datainfo.instrument = data_point
                # Detector Information
                elif tagname == 'name' and self.parent_class == 'SASdetector':
                    self.detector.name = data_point
                elif tagname == 'SDD' and self.parent_class == 'SASdetector':
                    self.detector.distance = data_point
                    self.detector.distance_unit = unit
                elif tagname == 'slit_length' and self.parent_class == 'SASdetector':
                    self.detector.slit_length = data_point
                    self.detector.slit_length_unit = unit
                elif tagname == 'x' and self.parent_class == 'offset':
                    self.detector.offset.x = data_point
                    self.detector.offset_unit = unit
                elif tagname == 'y' and self.parent_class == 'offset':
                    self.detector.offset.y = data_point
                    self.detector.offset_unit = unit
                elif tagname == 'z' and self.parent_class == 'offset':
                    self.detector.offset.z = data_point
                    self.detector.offset_unit = unit
                elif tagname == 'x' and self.parent_class == 'beam_center':
                    self.detector.beam_center.x = data_point
                    self.detector.beam_center_unit = unit
                elif tagname == 'y' and self.parent_class == 'beam_center':
                    self.detector.beam_center.y = data_point
                    self.detector.beam_center_unit = unit
                elif tagname == 'z' and self.parent_class == 'beam_center':
                    self.detector.beam_center.z = data_point
                    self.detector.beam_center_unit = unit
                elif tagname == 'x' and self.parent_class == 'pixel_size':
                    self.detector.pixel_size.x = data_point
                    self.detector.pixel_size_unit = unit
                elif tagname == 'y' and self.parent_class == 'pixel_size':
                    self.detector.pixel_size.y = data_point
                    self.detector.pixel_size_unit = unit
                elif tagname == 'z' and self.parent_class == 'pixel_size':
                    self.detector.pixel_size.z = data_point
                    self.detector.pixel_size_unit = unit
                elif tagname == 'roll' and self.parent_class == 'orientation' and 'SASdetector' in self.names:
                    self.detector.orientation.x = data_point
                    self.detector.orientation_unit = unit
                elif tagname == 'pitch' and self.parent_class == 'orientation' and 'SASdetector' in self.names:
                    self.detector.orientation.y = data_point
                    self.detector.orientation_unit = unit
                elif tagname == 'yaw' and self.parent_class == 'orientation' and 'SASdetector' in self.names:
                    self.detector.orientation.z = data_point
                    self.detector.orientation_unit = unit
                # Collimation and Aperture
                elif tagname == 'length' and self.parent_class == 'SAScollimation':
                    self.collimation.length = data_point
                    self.collimation.length_unit = unit
                elif tagname == 'name' and self.parent_class == 'SAScollimation':
                    self.collimation.name = data_point
                elif tagname == 'distance' and self.parent_class == 'aperture':
                    self.aperture.distance = data_point
                    self.aperture.distance_unit = unit
                elif tagname == 'x' and self.parent_class == 'size':
                    self.aperture.size.x = data_point
                    self.collimation.size_unit = unit
                elif tagname == 'y' and self.parent_class == 'size':
                    self.aperture.size.y = data_point
                    self.collimation.size_unit = unit
                elif tagname == 'z' and self.parent_class == 'size':
                    self.aperture.size.z = data_point
                    self.collimation.size_unit = unit

                # Process Information
                elif tagname == 'name' and self.parent_class == 'SASprocess':
                    self.process.name = data_point
                elif tagname == 'description' and self.parent_class == 'SASprocess':
                    self.process.description = data_point
                elif tagname == 'date' and self.parent_class == 'SASprocess':
                    try:
                        self.process.date = datetime.datetime.fromtimestamp(data_point)
                    except:
                        self.process.date = data_point
                elif tagname == 'SASprocessnote':
                    self.process.notes.append(data_point)
                elif tagname == 'term' and self.parent_class == 'SASprocess':
                    unit = attr.get("unit", "")
                    dic = {}
                    dic["name"] = name
                    dic["value"] = data_point
                    dic["unit"] = unit
                    self.process.term.append(dic)

                # Transmission Spectrum
                elif tagname == 'T' and self.parent_class == 'Tdata':
                    self.transspectrum.transmission = np.append(self.transspectrum.transmission, data_point)
                    self.transspectrum.transmission_unit = unit
                elif tagname == 'Tdev' and self.parent_class == 'Tdata':
                    self.transspectrum.transmission_deviation = np.append(self.transspectrum.transmission_deviation, data_point)
                    self.transspectrum.transmission_deviation_unit = unit
                elif tagname == 'Lambda' and self.parent_class == 'Tdata':
                    self.transspectrum.wavelength = np.append(self.transspectrum.wavelength, data_point)
                    self.transspectrum.wavelength_unit = unit

                # Source Information
                elif tagname == 'wavelength' and (self.parent_class == 'SASsource' or self.parent_class == 'SASData'):
                    self.current_datainfo.source.wavelength = data_point
                    self.current_datainfo.source.wavelength_unit = unit
                elif tagname == 'wavelength_min' and self.parent_class == 'SASsource':
                    self.current_datainfo.source.wavelength_min = data_point
                    self.current_datainfo.source.wavelength_min_unit = unit
                elif tagname == 'wavelength_max' and self.parent_class == 'SASsource':
                    self.current_datainfo.source.wavelength_max = data_point
                    self.current_datainfo.source.wavelength_max_unit = unit
                elif tagname == 'wavelength_spread' and self.parent_class == 'SASsource':
                    self.current_datainfo.source.wavelength_spread = data_point
                    self.current_datainfo.source.wavelength_spread_unit = unit
                elif tagname == 'x' and self.parent_class == 'beam_size':
                    self.current_datainfo.source.beam_size.x = data_point
                    self.current_datainfo.source.beam_size_unit = unit
                elif tagname == 'y' and self.parent_class == 'beam_size':
                    self.current_datainfo.source.beam_size.y = data_point
                    self.current_datainfo.source.beam_size_unit = unit
                elif tagname == 'z' and self.parent_class == 'pixel_size':
                    self.current_datainfo.source.data_point.z = data_point
                    self.current_datainfo.source.beam_size_unit = unit
                elif tagname == 'radiation' and self.parent_class == 'SASsource':
                    self.current_datainfo.source.radiation = data_point
                elif tagname == 'beam_shape' and self.parent_class == 'SASsource':
                    self.current_datainfo.source.beam_shape = data_point

                # Everything else goes in meta_data
                else:
                    new_key = self._create_unique_key(self.current_datainfo.meta_data, tagname)
                    self.current_datainfo.meta_data[new_key] = data_point

            self.names.remove(tagname_original)
            length = 0
            if len(self.names) > 1:
                length = len(self.names) - 1
            self.parent_class = self.names[length]
        if not self._is_call_local() and not recurse:
            self.frm = ""
            self.add_data_set()
            empty = None
            return self.output[0], empty


    def _is_call_local(self):
        """

        """
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

    def is_cansas(self, ext="xml"):
        """
        Checks to see if the xml file is a CanSAS file

        :param ext: The file extension of the data file
        """
        if self.validate_xml():
            name = "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"
            value = self.xmlroot.get(name)
            if CANSAS_NS.get(self.cansas_version).get("ns") == \
                    value.rsplit(" ")[0]:
                return True
        if ext == "svs":
            return True
        raise RuntimeError

    def load_file_and_schema(self, xml_file, schema_path=""):
        """
        Loads the file and associates a schema, if a schema is passed in or if one already exists

        :param xml_file: The xml file path sent to Reader.read
        :param schema_path: The path to a schema associated with the xml_file, or find one based on the file
        """
        base_name = xml_reader.__file__
        base_name = base_name.replace("\\", "/")
        base = base_name.split("/sas/")[0]

        # Load in xml file and get the cansas version from the header
        from lxml import etree
        try:
            self.set_xml_file(xml_file)
        except etree.XMLSyntaxError:
            msg = "Cansas cannot load this file"
            raise FileContentsException, msg
        self.cansas_version = self.xmlroot.get("version", "1.0")

        # Generic values for the cansas file based on the version
        self.cansas_defaults = CANSAS_NS.get(self.cansas_version, "1.0")
        if schema_path == "":
            schema_path = "{0}/sas/sascalc/dataloader/readers/schema/{1}".format \
                (base, self.cansas_defaults.get("schema")).replace("\\", "/")

        # Link a schema to the XML file.
        self.set_schema(schema_path)

    def add_data_set(self):
        """
        Adds the current_dataset to the list of outputs after preforming final processing on the data and then calls a
        private method to generate a new data set.

        :param key: NeXus group name for current tree level
        """

        if self.current_datainfo and self.current_dataset:
            self._final_cleanup()
        self.data = []
        self.current_datainfo = DataInfo()

    def _initialize_new_data_set(self, node=None):
        """
        A private class method to generate a new 1D data object.
        Outside methods should call add_data_set() to be sure any existing data is stored properly.

        :param node: XML node to determine if 1D or 2D data
        """
        x = np.array(0)
        y = np.array(0)
        for child in node:
            if child.tag.replace(self.base_ns, "") == "Idata":
                for i_child in child:
                    if i_child.tag.replace(self.base_ns, "") == "Qx":
                        self.current_dataset = plottable_2D()
                        return
        self.current_dataset = plottable_1D(x, y)

    def add_intermediate(self):
        """
        This method stores any intermediate objects within the final data set after fully reading the set.

        :param parent: The NXclass name for the h5py Group object that just finished being processed
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
            self._check_for_empty_resolution()
            self.data.append(self.current_dataset)

    def _final_cleanup(self):
        """
        Final cleanup of the Data1D object to be sure it has all the
        appropriate information needed for perspectives
        """

        # Append errors to dataset and reset class errors
        self.current_datainfo.errors = set()
        for error in self.errors:
            self.current_datainfo.errors.add(error)
        self.errors.clear()

        # Combine all plottables with datainfo and append each to output
        # Type cast data arrays to float64 and find min/max as appropriate
        for dataset in self.data:
            if isinstance(dataset, plottable_1D):
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
                np.trim_zeros(dataset.x)
                np.trim_zeros(dataset.y)
                np.trim_zeros(dataset.dy)
            elif isinstance(dataset, plottable_2D):
                dataset.data = dataset.data.astype(np.float64)
                dataset.qx_data = dataset.qx_data.astype(np.float64)
                dataset.xmin = np.min(dataset.qx_data)
                dataset.xmax = np.max(dataset.qx_data)
                dataset.qy_data = dataset.qy_data.astype(np.float64)
                dataset.ymin = np.min(dataset.qy_data)
                dataset.ymax = np.max(dataset.qy_data)
                dataset.q_data = np.sqrt(dataset.qx_data * dataset.qx_data
                                         + dataset.qy_data * dataset.qy_data)
                if dataset.err_data is not None:
                    dataset.err_data = dataset.err_data.astype(np.float64)
                if dataset.dqx_data is not None:
                    dataset.dqx_data = dataset.dqx_data.astype(np.float64)
                if dataset.dqy_data is not None:
                    dataset.dqy_data = dataset.dqy_data.astype(np.float64)
                if dataset.mask is not None:
                    dataset.mask = dataset.mask.astype(dtype=bool)

                if len(dataset.shape) == 2:
                    n_rows, n_cols = dataset.shape
                    dataset.y_bins = dataset.qy_data[0::int(n_cols)]
                    dataset.x_bins = dataset.qx_data[:int(n_cols)]
                    dataset.data = dataset.data.flatten()
                else:
                    dataset.y_bins = []
                    dataset.x_bins = []
                    dataset.data = dataset.data.flatten()

            final_dataset = combine_data(dataset, self.current_datainfo)
            self.output.append(final_dataset)

    def _create_unique_key(self, dictionary, name, numb=0):
        """
        Create a unique key value for any dictionary to prevent overwriting
        Recurse until a unique key value is found.

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
                local_unit = attr['unit']
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
                exec "default_unit = self.{0}.{1}".format(save_in, unitname)
                if local_unit and default_unit and local_unit.lower() != default_unit.lower() \
                        and local_unit.lower() != "none":
                    if HAS_CONVERTER == True:
                        # Check local units - bad units raise KeyError
                        data_conv_q = Converter(local_unit)
                        value_unit = default_unit
                        node_value = data_conv_q(node_value, units=default_unit)
                    else:
                        value_unit = local_unit
                        err_msg = "Unit converter is not available.\n"
                else:
                    value_unit = local_unit
            except KeyError:
                err_msg = "CanSAS reader: unexpected "
                err_msg += "\"{0}\" unit [{1}]; "
                err_msg = err_msg.format(tagname, local_unit)
                err_msg += "expecting [{0}]".format(default_unit)
                value_unit = local_unit
            except:
                err_msg = "CanSAS reader: unknown error converting "
                err_msg += "\"{0}\" unit [{1}]"
                err_msg = err_msg.format(tagname, local_unit)
                value_unit = local_unit
        elif 'unit' in attr:
            value_unit = attr['unit']
        if err_msg:
            self.errors.add(err_msg)
        return node_value, value_unit

    def _check_for_empty_data(self):
        """
        Creates an empty data set if no data is passed to the reader

        :param data1d: presumably a Data1D object
        """
        if self.current_dataset is None:
            x_vals = np.empty(0)
            y_vals = np.empty(0)
            dx_vals = np.empty(0)
            dy_vals = np.empty(0)
            dxl = np.empty(0)
            dxw = np.empty(0)
            self.current_dataset = plottable_1D(x_vals, y_vals, dx_vals, dy_vals)
            self.current_dataset.dxl = dxl
            self.current_dataset.dxw = dxw

    def _check_for_empty_resolution(self):
        """
        A method to check all resolution data sets are the same size as I and Q
        """
        if isinstance(self.current_dataset, plottable_1D):
            dql_exists = False
            dqw_exists = False
            dq_exists = False
            di_exists = False
            if self.current_dataset.dxl is not None:
                dql_exists = True
            if self.current_dataset.dxw is not None:
                dqw_exists = True
            if self.current_dataset.dx is not None:
                dq_exists = True
            if self.current_dataset.dy is not None:
                di_exists = True
            if dqw_exists and not dql_exists:
                array_size = self.current_dataset.dxw.size - 1
                self.current_dataset.dxl = np.append(self.current_dataset.dxl,
                                                     np.zeros([array_size]))
            elif dql_exists and not dqw_exists:
                array_size = self.current_dataset.dxl.size - 1
                self.current_dataset.dxw = np.append(self.current_dataset.dxw,
                                                     np.zeros([array_size]))
            elif not dql_exists and not dqw_exists and not dq_exists:
                array_size = self.current_dataset.x.size - 1
                self.current_dataset.dx = np.append(self.current_dataset.dx,
                                                    np.zeros([array_size]))
            if not di_exists:
                array_size = self.current_dataset.y.size - 1
                self.current_dataset.dy = np.append(self.current_dataset.dy,
                                                    np.zeros([array_size]))
        elif isinstance(self.current_dataset, plottable_2D):
            dqx_exists = False
            dqy_exists = False
            di_exists = False
            mask_exists = False
            if self.current_dataset.dqx_data is not None:
                dqx_exists = True
            if self.current_dataset.dqy_data is not None:
                dqy_exists = True
            if self.current_dataset.err_data is not None:
                di_exists = True
            if self.current_dataset.mask is not None:
                mask_exists = True
            if not dqy_exists:
                array_size = self.current_dataset.qy_data.size - 1
                self.current_dataset.dqy_data = np.append(
                    self.current_dataset.dqy_data, np.zeros([array_size]))
            if not dqx_exists:
                array_size = self.current_dataset.qx_data.size - 1
                self.current_dataset.dqx_data = np.append(
                    self.current_dataset.dqx_data, np.zeros([array_size]))
            if not di_exists:
                array_size = self.current_dataset.data.size - 1
                self.current_dataset.err_data = np.append(
                    self.current_dataset.err_data, np.zeros([array_size]))
            if not mask_exists:
                array_size = self.current_dataset.data.size - 1
                self.current_dataset.mask = np.append(
                    self.current_dataset.mask,
                    np.ones([array_size] ,dtype=bool))

    ####### All methods below are for writing CanSAS XML files #######

    def write(self, filename, datainfo):
        """
        Write the content of a Data1D as a CanSAS XML file

        :param filename: name of the file to write
        :param datainfo: Data1D object
        """
        # Create XML document
        doc, _ = self._to_xml_doc(datainfo)
        # Write the file
        file_ref = open(filename, 'w')
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
                            {'unit': datainfo._xaxis + " | " + datainfo._xunit})
            if len(datainfo.y) >= i:
                self.write_node(point, "I", datainfo.y[i],
                                {'unit': datainfo._yaxis + " | " + datainfo._yunit})
            if datainfo.dy is not None and len(datainfo.dy) > i:
                self.write_node(point, "Idev", datainfo.dy[i],
                                {'unit': datainfo._yaxis + " | " + datainfo._yunit})
            if datainfo.dx is not None and len(datainfo.dx) > i:
                self.write_node(point, "Qdev", datainfo.dx[i],
                                {'unit': datainfo._xaxis + " | " + datainfo._xunit})
            if datainfo.dxw is not None and len(datainfo.dxw) > i:
                self.write_node(point, "dQw", datainfo.dxw[i],
                                {'unit': datainfo._xaxis + " | " + datainfo._xunit})
            if datainfo.dxl is not None and len(datainfo.dxl) > i:
                self.write_node(point, "dQl", datainfo.dxl[i],
                                {'unit': datainfo._xaxis + " | " + datainfo._xunit})
        if datainfo.isSesans:
            sesans = self.create_element("Sesans")
            sesans.text = str(datainfo.isSesans)
            node.append(sesans)
            self.write_node(node, "yacceptance", datainfo.sample.yacceptance[0],
                             {'unit': datainfo.sample.yacceptance[1]})
            self.write_node(node, "zacceptance", datainfo.sample.zacceptance[0],
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
        qx = ','.join([str(datainfo.qx_data[i]) for i in xrange(len(datainfo.qx_data))])
        qy = ','.join([str(datainfo.qy_data[i]) for i in xrange(len(datainfo.qy_data))])
        intensity = ','.join([str(datainfo.data[i]) for i in xrange(len(datainfo.data))])

        self.write_node(point, "Qx", qx,
                        {'unit': datainfo._xunit})
        self.write_node(point, "Qy", qy,
                        {'unit': datainfo._yunit})
        self.write_node(point, "I", intensity,
                        {'unit': datainfo._zunit})
        if datainfo.err_data is not None:
            err = ','.join([str(datainfo.err_data[i]) for i in
                            xrange(len(datainfo.err_data))])
            self.write_node(point, "Idev", err,
                            {'unit': datainfo._zunit})
        if datainfo.dqy_data is not None:
            dqy = ','.join([str(datainfo.dqy_data[i]) for i in
                            xrange(len(datainfo.dqy_data))])
            self.write_node(point, "Qydev", dqy,
                            {'unit': datainfo._yunit})
        if datainfo.dqx_data is not None:
            dqx = ','.join([str(datainfo.dqx_data[i]) for i in
                            xrange(len(datainfo.dqx_data))])
            self.write_node(point, "Qxdev", dqx,
                            {'unit': datainfo._xunit})
        if datainfo.mask is not None:
            mask = ','.join(
                ["1" if datainfo.mask[i] else "0"
                 for i in xrange(len(datainfo.mask))])
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
        if written == True:
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
        if written == True:
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
        if written == True:
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
                if written == True:
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
            if written == True:
                self.append(det, instr)

            off = self.create_element("offset")
            written = self.write_node(off, "x", item.offset.x,
                                      {"unit": item.offset_unit})
            written = written | self.write_node(off, "y", item.offset.y,
                                                {"unit": item.offset_unit})
            written = written | self.write_node(off, "z", item.offset.z,
                                                {"unit": item.offset_unit})
            if written == True:
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
            if written == True:
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
            if written == True:
                self.append(center, det)

            pix = self.create_element("pixel_size")
            written = self.write_node(pix, "x", item.pixel_size.x,
                                      {"unit": item.pixel_size_unit})
            written = written | self.write_node(pix, "y", item.pixel_size.y,
                                                {"unit": item.pixel_size_unit})
            written = written | self.write_node(pix, "z", item.pixel_size.z,
                                                {"unit": item.pixel_size_unit})
            if written == True:
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
        except:
            value = None

        if value is not None:
            # If the entry has units, check to see that they are
            # compatible with what we currently have in the data object
            units = entry.get('unit')
            if units is not None:
                toks = variable.split('.')
                local_unit = None
                exec "local_unit = storage.%s_unit" % toks[0]
                if local_unit is not None and units.lower() != local_unit.lower():
                    if HAS_CONVERTER == True:
                        try:
                            conv = Converter(units)
                            exec "storage.%s = %g" % \
                                (variable, conv(value, units=local_unit))
                        except:
                            _, exc_value, _ = sys.exc_info()
                            err_mess = "CanSAS reader: could not convert"
                            err_mess += " %s unit [%s]; expecting [%s]\n  %s" \
                                % (variable, units, local_unit, exc_value)
                            self.errors.add(err_mess)
                            if optional:
                                logger.info(err_mess)
                            else:
                                raise ValueError, err_mess
                    else:
                        err_mess = "CanSAS reader: unrecognized %s unit [%s];"\
                        % (variable, units)
                        err_mess += " expecting [%s]" % local_unit
                        self.errors.add(err_mess)
                        if optional:
                            logger.info(err_mess)
                        else:
                            raise ValueError, err_mess
                else:
                    exec "storage.%s = value" % variable
            else:
                exec "storage.%s = value" % variable

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
            exec "storage.%s = entry.text.strip()" % variable


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
