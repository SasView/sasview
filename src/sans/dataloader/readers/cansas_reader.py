"""
    CanSAS data reader - new recursive cansasVersion.
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
import numpy
import os
import sys
from sans.dataloader.data_info import Data1D
from sans.dataloader.data_info import Collimation
from sans.dataloader.data_info import Detector
from sans.dataloader.data_info import Process
from sans.dataloader.data_info import Aperture
import xml_reader
import xml.dom.minidom
from cansas_constants import cansasConstants

_ZERO = 1e-16
HAS_CONVERTER = True
try:
    from sans.data_util.nxsunit import Converter
except:
    HAS_CONVERTER = False
    
CANSAS_FORMAT = cansasConstants.CANSAS_FORMAT
CANSAS_NS = cansasConstants.CANSAS_NS
ALLOW_ALL = True


def write_node(doc, parent, name, value, attr={}):
    """
    :param doc: document DOM
    :param parent: parent node
    :param name: tag of the element
    :param value: value of the child text node
    :param attr: attribute dictionary
    
    :return: True if something was appended, otherwise False
    """
    if value is not None:
        node = doc.createElement(name)
        node.appendChild(doc.createTextNode(str(value)))
        for item in attr:
            node.setAttribute(item, attr[item])
        parent.appendChild(node)
        return True
    return False
                

def get_content(location, node):
    """
    Get the first instance of the content of a xpath location.
    
    :param location: xpath location
    :param node: node to start at
    
    :return: Element, or None
    """
    nodes = node.xpath(location, namespaces={'ns': CANSAS_NS})
    
    if len(nodes) > 0:
        return nodes[0]
    else:
        return None


def get_float(location, node):
    """
    Get the content of a node as a float
    
    :param location: xpath location
    :param node: node to start at
    """
    nodes = node.xpath(location, namespaces={'ns': CANSAS_NS})
    
    value = None
    attr = {}
    if len(nodes) > 0:
        try:
            value = float(nodes[0].text)
        except:
            # Could not pass, skip and return None
            msg = "cansas_reader.get_float: could not "
            msg += " convert '%s' to float" % nodes[0].text
            logging.error(msg)
        if nodes[0].get('unit') is not None:
            attr['unit'] = nodes[0].get('unit')
    return value, attr



class CANSASError(Exception):
    """Base class all CANSAS reader exceptions are derived"""
    pass

class NotCANSASFileError(CANSASError):
    def __init__(self):
        self.value = "This is not a proper CanSAS file."
    def __str__(self):
        return repr(self.value)

class Reader():
    """
    Class to load cansas 1D XML files
    
    :Dependencies:
        The CanSAS reader requires PyXML 0.8.4 or later.
    """
    ##CanSAS version - defaults to version 1.0
    cansasVersion = "1.0"
    ##Data reader
    reader = xml_reader.XMLreader()
    errors = []
    
    def __init__(self):
        ## List of errors
        self.errors = []
        
    def isCansas(self):
        """
        Checks to see if the xml file is a CanSAS file
        """
        if self.reader.validateXML():
            xmlns = self.reader.xmlroot.keys()
            if (CANSAS_NS.get(self.cansasVersion).get("ns") == self.reader.xmlroot.get(xmlns[1]).rsplit(" ")[0]):
                return True
        return False
    
    def read(self, xml):
        """
        Validate and read in an xml file in the canSAS format.
        
        :param xml: A canSAS file path in proper XML format
        """
        # X - Q value; Y - Intensity (Abs)
        x = numpy.empty(0)
        y = numpy.empty(0)
        dx = numpy.empty(0)
        dy = numpy.empty(0)
        dxl = numpy.empty(0)
        dxw = numpy.empty(0)
        
        # output - Final list of Data1D objects
        output = []
        # ns - Namespace hierarchy for current xml object
        ns = []
        
        try:
            # Load in the xml file and get the cansas version from the header
            self.reader.setXMLFile(xml)
            root = self.reader.xmlroot
            self.cansasVersion = root.get("version")
            # Generic values for the cansas file based on the version
            cansas_defaults = CANSAS_NS.get(self.cansasVersion)
        
            # Link a schema to the XML file.
            basename = os.path.basename(xml)
            base_name = xml_reader.__file__
            base = base_name.split("\\sans\\")[0]
            schema_path = "{0}\\sans\\dataloader\\readers\\schema\\{1}".format(base, cansas_defaults.get("schema")).replace("\\", "/")
            self.reader.setSchema(schema_path)
        
            # Try to load the file, but raise an error if unable to.
            # Check the file matches the XML schema
            if self.isCansas():
                # Get each SASentry from the XML file and add it to a list.
                entry_list = root.xpath('/ns:SASroot/ns:SASentry',
                                             namespaces={'ns': cansas_defaults.get("ns")})
                ns.append("SASentry")
                
                # If there are multiple files, modify the name for each is unique
                multipleFiles = len(entry_list) - 1
                n = 0
                name = basename
                # Parse each SASentry item
                for entry in entry_list:
                    
                    # Define a new Data1D object with zeroes for x and y
                    data1D = Data1D(x,y,dx,dy)
                    data1D.dxl = dxl
                    data1D.dxw = dxw
                    
                    # If more than one SASentry, number each in order
                    if multipleFiles:
                        name += "_{0}".format(n)
                        n += 1
                    
                    # Set the Data1D name and then parse the entry. The entry is appended to a list of entry values
                    data1D.filename = name
                    data1D.meta_data["loader"] = "CanSAS 1D"
                    return_value, extras = self._parse_entry(entry, ns, data1D)
                    del extras[:]
                    
                    #Final cleanup - Remove empty nodes, verify array sizes are correct
                    return_value.errors = self.errors
                    del self.errors[:]
                    numpy.trim_zeros(return_value.x)
                    numpy.trim_zeros(return_value.y)
                    numpy.trim_zeros(return_value.dy)
                    size_dx = return_value.dx.size
                    size_dxl = return_value.dxl.size
                    size_dxw = return_value.dxw.size
                    if size_dxl == 0 and size_dxw == 0:
                        return_value.dxl = None
                        return_value.dxw = None
                        numpy.trim_zeros(return_value.dx)
                    elif size_dx == 0:
                        return_value.dx = None
                        size_dx = size_dxl
                        numpy.trim_zeros(return_value.dxl)
                        numpy.trim_zeros(return_value.dxw)
                    
                    output.append(return_value)
            else:
                # If the file does not match the schema, raise this error
                raise RuntimeError, "%s cannot be read \n" % xml
        # If an exception occurs while loading the file, give a descriptive output.
        except Exception:
            raise RuntimeError, "%s cannot be read \n" % xml
            
        # Return a list of parsed entries that dataloader can manage
        return output
    
    def _create_unique_key(self, dictionary, name, i):
        if dictionary.get(name) is not None:
            i += 1
            name = name.split("_")[0]
            name += "_{0}".format(i)
            name = self._create_unique_key(dictionary, name, i)
        return name
    
    def _iterate_namespace(self, ns):
        # The current level to look through in cansas_constants.
        current_level = CANSAS_FORMAT.get("SASentry")
        # Defaults for variable and datatype
        ns_variable = "{0}.meta_data[\"{2}\"] = \"{1}\""
        ns_datatype = "content"
        ns_optional = True
        for name in ns:
            if name != "SASentry":
                current_level = current_level.get("children").get(name, "")
                if current_level == "":
                    current_level = current_level.get("<any>", "")
                cl_variable = current_level.get("variable", "")
                cl_datatype = current_level.get("storeas", "")
                cl_units_optional = current_level.get("units_required", "")
                # Where are how to store the variable for the given namespace
                # The CANSAS_CONSTANTS tree is hierarchical, so is no value, inherit
                ns_variable = cl_variable if cl_variable != "" else ns_variable
                ns_datatype = cl_datatype if cl_datatype != "" else ns_datatype
                ns_optional = cl_units_optional if cl_units_optional != ns_optional else ns_optional
        return current_level, ns_variable, ns_datatype, ns_optional
    
    def _unit_conversion(self, new_current_level, attr, data1D, node_value, optional = True):
        value_unit = ''
        if 'unit' in attr and 'unit' in new_current_level:
            try:
                if isinstance(node_value, float) is False:
                    exec("node_value = float({0})".format(node_value))
                default_unit = None
                unitname = new_current_level.get("unit")
                exec "default_unit = data1D.{0}.lower()".format(unitname)
                local_unit = attr['unit'].lower()
                if local_unit != default_unit:
                    if HAS_CONVERTER == True:
                        try:
                            data_conv_q = Converter(attr['unit'])
                            value_unit = default_unit
                            exec "node_value = data_conv_q(node_value, units=data1D.{0})".format(unitname)
                        except:
                            msg = "CanSAS reader: could not convert "
                            msg += "Q unit [%s]; " % attr['unit'],
                            exec "msg += \"expecting [%s]\n  %s\" % (data1D.{0}, sys.exc_info()[1])".format(unitname)
                            raise ValueError, msg
                    else:
                        value_unit = local_unit
                        err_mess = "CanSAS reader: unrecognized %s unit [%s];"\
                        % (node_value, default_unit)
                        err_mess += " expecting [%s]" % local_unit
                        self.errors.append(err_mess)
                        if optional:
                            logging.info(err_mess)
                        else:
                            raise ValueError, err_mess
            except Exception as e:
                msg = "CanSAS reader: could not convert "
                msg += "Q unit [%s]; " % attr['unit'],
                exec "msg += \"expecting [%s]\n  %s\" % (data1D.{0}, sys.exc_info()[1])".format(unitname)
                self.errors.append(msg)
                raise ValueError, msg
        elif 'unit' in attr:
            value_unit = attr['unit']
        node_value = "float({0})".format(node_value)
        return node_value, value_unit
    
    def _parse_entry(self, dom, ns, data1D, extras = []):
        """
        Parse a SASEntry - new recursive method for parsing the dom of
            the CanSAS data format. This will allow multiple data files
            and extra nodes to be read in simultaneously.
        
        :param dom: dom object with a namespace base of ns
        :param ns: A list of element names that lead up to the dom object
        :param data1D: The data1D object that will be modified
        """
         
        # A portion of every namespace entry
        base_ns = "{0}{1}{2}".format("{", CANSAS_NS.get(self.cansasVersion).get("ns"), "}")
        unit = ''
        
        # Go through each child in the parent element
        for node in dom:
            try:
                # Get the element name and set the current ns level
                tagname = node.tag.replace(base_ns, "")
                tagname_original = tagname
                ns.append(tagname)
                attr = node.attrib
                
                # Look for special cases
                save_data1D = data1D
                if tagname == "SASdetector":
                    data1D = Detector()
                elif tagname == "SAScollimation":
                    data1D = Collimation()
                elif tagname == "SASprocess":
                    data1D = Process()
                    for child in node:
                        if child.tag.replace(base_ns, "") == "term":
                            term_attr = {}
                            for attr in child.keys():
                                term_attr[attr] = child.get(attr).strip()
                            if child.text is not None:
                                term_attr['value'] = child.text.strip()
                                data1D.term.append(term_attr)
                elif tagname == "aperture":
                    data1D = Aperture()
                
                # Get where to store content
                new_current_level, ns_variable, ns_datatype, optional = self._iterate_namespace(ns)
                # If the element is a child element, recurse
                if node.getchildren() is not None:
                    # Returned value is new Data1D object with all previous and new values in it.
                    data1D, extras = self._parse_entry(node, ns, data1D, extras)
                    
                #Get the information from the node
                node_value = node.text
                if node_value is not None:
                    node_value = node_value.strip().replace("\r"," ").replace("\n"," ")
                if node_value == "":
                    node_value = None
                
                # If the value is a float, compile with units.
                if ns_datatype == "float":
                    # If an empty value is given, store as zero.
                    if node_value is None:
                        node_value = "0.0"
                    elif node_value.isspace():
                        node_value = "0.0"
                    node_value, unit = self._unit_conversion(new_current_level, attr, data1D, node_value, optional)
                    
                # If appending to a dictionary (meta_data | run_name), name sure the key is unique
                if ns_variable == "{0}.meta_data[\"{2}\"] = \"{1}\"":
                    # If we are within a Process, Detector, Collimation or Aperture instance, pull out old data1D
                    tagname = self._create_unique_key(data1D.meta_data, tagname, 0)
                    if isinstance(data1D, Data1D) == False:
                        store_me = ns_variable.format("data1D", node_value, tagname)
                        extras.append(store_me)
                        ns_variable = None
                if ns_variable == "{0}.run_name[\"{2}\"] = \"{1}\"":
                    tagname = self._create_unique_key(data1D.run_name, tagname, 0)
                
                # Check for Data1D object and any extra commands to save
                if isinstance(data1D, Data1D):
                    for item in extras:
                        exec item
                # Don't bother saving empty information unless it is a float
                if ns_variable is not None and node_value is not None and node_value.isspace() == False:
                    # Format a string and then execute it.
                    store_me = ns_variable.format("data1D", node_value, tagname)
                    exec store_me
                # Get attributes and process them
                if attr is not None:
                    for key in node.keys():
                        try:
                            cansas_attrib = new_current_level.get("attributes").get(key)
                            attrib_variable = cansas_attrib.get("variable")
                            if key == 'unit' and unit != '':
                                attrib_value = unit
                            else:
                                attrib_value = node.attrib[key]
                            store_attr = attrib_variable.format("data1D", attrib_value, key)
                            exec store_attr
                        except AttributeError as e:
                            pass
                            
                     
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(e, exc_type, fname, exc_tb.tb_lineno, tagname, exc_obj)
            finally:
                # Save special cases in original data1D object and then restore the data1D
                if tagname_original == "SASdetector":
                    save_data1D.detector.append(data1D)
                elif tagname_original == "SAScollimation":
                    save_data1D.collimation.append(data1D)
                elif tagname_original == "SASprocess":
                    save_data1D.process.append(data1D)
                elif tagname_original == "aperture":
                    save_data1D.aperture.append(data1D)
                else:
                    save_data1D = data1D
                data1D = save_data1D
                # Remove tagname from ns to restore original base
                ns.remove(tagname_original)
        
        return data1D, extras
        
    def _to_xml_doc(self, datainfo):
        """
        Create an XML document to contain the content of a Data1D
        
        :param datainfo: Data1D object
        """
        
        if not issubclass(datainfo.__class__, Data1D):
            raise RuntimeError, "The cansas writer expects a Data1D instance"
        
        doc = xml.dom.minidom.Document()
        main_node = doc.createElement("SASroot")
        main_node.setAttribute("cansasVersion", self.cansasVersion)
        main_node.setAttribute("xmlns", "cansas1d/%s" % self.cansasVersion)
        main_node.setAttribute("xmlns:xsi",
                               "http://www.w3.org/2001/XMLSchema-instance")
        main_node.setAttribute("xsi:schemaLocation",
                               "cansas1d/%s http://svn.smallangles.net/svn/canSAS/1dwg/trunk/cansas1d.xsd" % self.cansasVersion)
        
        doc.appendChild(main_node)
        
        entry_node = doc.createElement("SASentry")
        main_node.appendChild(entry_node)
        
        write_node(doc, entry_node, "Title", datainfo.title)
        for item in datainfo.run:
            runname = {}
            if item in datainfo.run_name and \
            len(str(datainfo.run_name[item])) > 1:
                runname = {'name': datainfo.run_name[item]}
            write_node(doc, entry_node, "Run", item, runname)
        
        # Data info
        node = doc.createElement("SASdata")
        entry_node.appendChild(node)
        
        for i in range(len(datainfo.x)):
            pt = doc.createElement("Idata")
            node.appendChild(pt)
            write_node(doc, pt, "Q", datainfo.x[i], {'unit': datainfo.x_unit})
            if len(datainfo.y) >= i:
                write_node(doc, pt, "I", datainfo.y[i],
                            {'unit': datainfo.y_unit})
            if datainfo.dx != None and len(datainfo.dx) >= i:
                write_node(doc, pt, "Qdev", datainfo.dx[i],
                            {'unit': datainfo.x_unit})
            if datainfo.dxl != None and len(datainfo.dxl) >= i:
                write_node(doc, pt, "dQl", datainfo.dxl[i],
                            {'unit': datainfo.x_unit})
            if datainfo.dxw != None and len(datainfo.dxw) >= i:
                write_node(doc, pt, "dQw", datainfo.dxw[i],
                            {'unit': datainfo.x_unit})
            if datainfo.dy != None and len(datainfo.dy) >= i:
                write_node(doc, pt, "Idev", datainfo.dy[i],
                            {'unit': datainfo.y_unit})

        # Sample info
        sample = doc.createElement("SASsample")
        if datainfo.sample.name is not None:
            sample.setAttribute("name", str(datainfo.sample.name))
        entry_node.appendChild(sample)
        write_node(doc, sample, "ID", str(datainfo.sample.ID))
        write_node(doc, sample, "thickness", datainfo.sample.thickness,
                   {"unit": datainfo.sample.thickness_unit})
        write_node(doc, sample, "transmission", datainfo.sample.transmission)
        write_node(doc, sample, "temperature", datainfo.sample.temperature,
                   {"unit": datainfo.sample.temperature_unit})
        
        for item in datainfo.sample.details:
            write_node(doc, sample, "details", item)
        
        pos = doc.createElement("position")
        written = write_node(doc, pos, "x", datainfo.sample.position.x,
                             {"unit": datainfo.sample.position_unit})
        written = written | write_node(doc, pos, "y",
                                       datainfo.sample.position.y,
                                       {"unit": datainfo.sample.position_unit})
        written = written | write_node(doc, pos, "z",
                                       datainfo.sample.position.z,
                                       {"unit": datainfo.sample.position_unit})
        if written == True:
            sample.appendChild(pos)
        
        ori = doc.createElement("orientation")
        written = write_node(doc, ori, "roll",
                             datainfo.sample.orientation.x,
                             {"unit": datainfo.sample.orientation_unit})
        written = written | write_node(doc, ori, "pitch",
                                       datainfo.sample.orientation.y,
                                    {"unit": datainfo.sample.orientation_unit})
        written = written | write_node(doc, ori, "yaw",
                                       datainfo.sample.orientation.z,
                                    {"unit": datainfo.sample.orientation_unit})
        if written == True:
            sample.appendChild(ori)
        
        # Instrument info
        instr = doc.createElement("SASinstrument")
        entry_node.appendChild(instr)
        
        write_node(doc, instr, "name", datainfo.instrument)
        
        #   Source
        source = doc.createElement("SASsource")
        if datainfo.source.name is not None:
            source.setAttribute("name", str(datainfo.source.name))
        instr.appendChild(source)
        
        write_node(doc, source, "radiation", datainfo.source.radiation)
        write_node(doc, source, "beam_shape", datainfo.source.beam_shape)
        size = doc.createElement("beam_size")
        if datainfo.source.beam_size_name is not None:
            size.setAttribute("name", str(datainfo.source.beam_size_name))
        written = write_node(doc, size, "x", datainfo.source.beam_size.x,
                             {"unit": datainfo.source.beam_size_unit})
        written = written | write_node(doc, size, "y",
                                       datainfo.source.beam_size.y,
                                       {"unit": datainfo.source.beam_size_unit})
        written = written | write_node(doc, size, "z",
                                       datainfo.source.beam_size.z,
                                       {"unit": datainfo.source.beam_size_unit})
        if written == True:
            source.appendChild(size)
            
        write_node(doc, source, "wavelength",
                   datainfo.source.wavelength,
                   {"unit": datainfo.source.wavelength_unit})
        write_node(doc, source, "wavelength_min",
                   datainfo.source.wavelength_min,
                   {"unit": datainfo.source.wavelength_min_unit})
        write_node(doc, source, "wavelength_max",
                   datainfo.source.wavelength_max,
                   {"unit": datainfo.source.wavelength_max_unit})
        write_node(doc, source, "wavelength_spread",
                   datainfo.source.wavelength_spread,
                   {"unit": datainfo.source.wavelength_spread_unit})
        
        #   Collimation
        for item in datainfo.collimation:
            coll = doc.createElement("SAScollimation")
            if item.name is not None:
                coll.setAttribute("name", str(item.name))
            instr.appendChild(coll)
            
            write_node(doc, coll, "length", item.length,
                       {"unit": item.length_unit})
            
            for apert in item.aperture:
                ap = doc.createElement("aperture")
                if apert.name is not None:
                    ap.setAttribute("name", str(apert.name))
                if apert.type is not None:
                    ap.setAttribute("type", str(apert.type))
                coll.appendChild(ap)
                
                write_node(doc, ap, "distance", apert.distance,
                           {"unit": apert.distance_unit})
                
                size = doc.createElement("size")
                if apert.size_name is not None:
                    size.setAttribute("name", str(apert.size_name))
                written = write_node(doc, size, "x", apert.size.x,
                                     {"unit": apert.size_unit})
                written = written | write_node(doc, size, "y", apert.size.y,
                                               {"unit": apert.size_unit})
                written = written | write_node(doc, size, "z", apert.size.z,
                                               {"unit": apert.size_unit})
                if written == True:
                    ap.appendChild(size)

        #   Detectors
        for item in datainfo.detector:
            det = doc.createElement("SASdetector")
            written = write_node(doc, det, "name", item.name)
            written = written | write_node(doc, det, "SDD", item.distance,
                                           {"unit": item.distance_unit})
            written = written | write_node(doc, det, "slit_length",
                                           item.slit_length,
                                           {"unit": item.slit_length_unit})
            if written == True:
                instr.appendChild(det)
            
            off = doc.createElement("offset")
            written = write_node(doc, off, "x", item.offset.x,
                                 {"unit": item.offset_unit})
            written = written | write_node(doc, off, "y", item.offset.y,
                                           {"unit": item.offset_unit})
            written = written | write_node(doc, off, "z", item.offset.z,
                                           {"unit": item.offset_unit})
            if written == True:
                det.appendChild(off)
            
            center = doc.createElement("beam_center")
            written = write_node(doc, center, "x", item.beam_center.x,
                                 {"unit": item.beam_center_unit})
            written = written | write_node(doc, center, "y",
                                           item.beam_center.y,
                                           {"unit": item.beam_center_unit})
            written = written | write_node(doc, center, "z",
                                           item.beam_center.z,
                                           {"unit": item.beam_center_unit})
            if written == True:
                det.appendChild(center)
                
            pix = doc.createElement("pixel_size")
            written = write_node(doc, pix, "x", item.pixel_size.x,
                                 {"unit": item.pixel_size_unit})
            written = written | write_node(doc, pix, "y", item.pixel_size.y,
                                           {"unit": item.pixel_size_unit})
            written = written | write_node(doc, pix, "z", item.pixel_size.z,
                                           {"unit": item.pixel_size_unit})
            if written == True:
                det.appendChild(pix)
                
            ori = doc.createElement("orientation")
            written = write_node(doc, ori, "roll", item.orientation.x,
                                 {"unit": item.orientation_unit})
            written = written | write_node(doc, ori, "pitch",
                                           item.orientation.y,
                                           {"unit": item.orientation_unit})
            written = written | write_node(doc, ori, "yaw",
                                           item.orientation.z,
                                           {"unit": item.orientation_unit})
            if written == True:
                det.appendChild(ori)
                
        # Processes info
        for item in datainfo.process:
            node = doc.createElement("SASprocess")
            entry_node.appendChild(node)

            write_node(doc, node, "name", item.name)
            write_node(doc, node, "date", item.date)
            write_node(doc, node, "description", item.description)
            for term in item.term:
                value = term['value']
                del term['value']
                write_node(doc, node, "term", value, term)
            for note in item.notes:
                write_node(doc, node, "SASprocessnote", note)
        
        # Return the document, and the SASentry node associated with
        # the data we just wrote
        return doc, entry_node
            
    def write(self, filename, datainfo):
        """
        Write the content of a Data1D as a CanSAS XML file
        
        :param filename: name of the file to write
        :param datainfo: Data1D object
        """
        # Create XML document
        doc, _ = self._to_xml_doc(datainfo)
        # Write the file
        fd = open(filename, 'w')
        fd.write(doc.toprettyxml())
        fd.close()
