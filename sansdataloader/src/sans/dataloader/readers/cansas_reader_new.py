"""
    CanSAS data reader
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

# Known issue: reader not compatible with multiple SASdata entries
# within a single SASentry. Will raise a runtime error.

#TODO: check that all vectors are written only if they have at 
#    least one non-empty value
#TODO: Writing only allows one SASentry per file.
#     Would be best to allow multiple entries.
#TODO: Store error list
#TODO: Allow for additional meta data for each section
#TODO: Notes need to be implemented. They can be any XML 
#    structure in version 1.0
#      Process notes have the same problem.
#TODO: Unit conversion is not complete (temperature units are missing)

import logging
import numpy
import os
import sys
from sans.dataloader.data_info import Data1D
from sans.dataloader.data_info import Collimation
from sans.dataloader.data_info import Detector
from sans.dataloader.data_info import Process
from sans.dataloader.data_info import Aperture
from lxml import etree
import xml.dom.minidom
_ZERO = 1e-16
HAS_CONVERTER = True
try:
    from data_util.nxsunit import Converter
except:
    HAS_CONVERTER = False

CANSAS_NS = "cansas1d/1.0"
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

            
class Reader:
    """
    Class to load cansas 1D XML files
    
    :Dependencies:
        The CanSas reader requires PyXML 0.8.4 or later.
    """
    ## CanSAS version
    version = '1.0'
    ## File type
    type_name = "CanSAS 1D"
    ## Wildcards
    type = ["CanSAS 1D files (*.xml)|*.xml",
                        "CanSAS 1D AVE files (*.AVEx)|*.AVEx",
                         "CanSAS 1D AVE files (*.ABSx)|*.ABSx"]

    ## List of allowed extensions
    ext = ['.xml', '.XML', '.avex', '.AVEx', '.absx', 'ABSx']
    
    def __init__(self):
        ## List of errors
        self.errors = []
    

    def read(self, path):
        output = []
        ns = []
        if os.path.isfile(path):
            basename = os.path.basename(path)
            root, extension = os.path.splitext(basename)
            if ALLOW_ALL or extension.lower() in self.ext:
                try:
                    tree = etree.parse(path, parser=etree.ETCompatXMLParser())
                    # Check the format version number
                    # Specifying the namespace will take care of the file
                    # format version
                    root = tree.getroot()
                    output.append("I made it here 1")
                    base_ns = '/ns:SASroot/ns:SASentry'
                    ns.append('SASroot')
                    ns.append('SASentry')
                    entry_list = root.xpath(base_ns,
                                             namespaces={'ns': CANSAS_NS})
                    
                    output.append("I made it here 2")
                    for entry in entry_list:
                        output.append(etree.tostring(entry))
                        new_name_entry = self._parse_entry(entry, ns)
                        output.append(new_name_entry)
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno, output)
                
            return output
        
    def _parse_entry(self, dom, ns):
        """
        Parse a SASEntry - new recursive method for parsing the dom of
            the CanSAS data format. This will allow multiple data files
            and extra nodes to be read in simultaneously.
        
        :param dom: dom object with a namespace base of ns
        
        :param ns: A list of namespaces that lead up to the dom object
        """
        
        # base method variables
        # namespace - the full dom namespace of the current level
        # tag - the name of the tag at the current level
        # text - The text of the current tag
        # attributes - A dictionary of attributes of the current tag
        # level - The recursion level within the DOM. Used for determining
        #        how to apply the data
        namespace = ''
        tag = ''
        text = ''
        attributes = {}
        namespace_dictionary = {}
        level = len(ns)
        
        for name in ns:
            namespace += 'ns:' + name + "/"
        try:
            nodes = dom.xpath(namespace, namespaces={'ns': CANSAS_NS})
            
            for node in nodes:
                nodes_in_node = len(node)
                if nodes_in_node > 1:
                    ns.append(node.tag)
                    self._parse_entry_new(node, ns)
                else:
                    fullns = ''
                    tag = node.tag
                    text = node.text
                    for name, value in node.items():
                        attributes.append(name, value)
                        basenamespace = ns.pop().strip('SAS')
                        name_space_dictionary.append(tag, text, attributes)
                        dictionary.append(namespace, name_space_dictionary)
            
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            dictionary.append("{!s}, {!s}, {!s}".format(exc_type, fname, exc_tb.tb_lineno))
        
        return dictionary
            
    def _to_xml_doc(self, datainfo):
        """
        Create an XML document to contain the content of a Data1D
        
        :param datainfo: Data1D object
        """
        
        if not issubclass(datainfo.__class__, Data1D):
            raise RuntimeError, "The cansas writer expects a Data1D instance"
        
        doc = xml.dom.minidom.Document()
        main_node = doc.createElement("SASroot")
        main_node.setAttribute("version", self.version)
        main_node.setAttribute("xmlns", "cansas1d/%s" % self.version)
        main_node.setAttribute("xmlns:xsi",
                               "http://www.w3.org/2001/XMLSchema-instance")
        main_node.setAttribute("xsi:schemaLocation",
                               "cansas1d/%s http://svn.smallangles.net/svn/canSAS/1dwg/trunk/cansas1d.xsd" % self.version)
        
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
                if local_unit != None and units.lower() != local_unit.lower():
                    if HAS_CONVERTER == True:
                        try:
                            conv = Converter(units)
                            exec "storage.%s = %g" % (variable,
                                            conv(value, units=local_unit))
                        except:
                            err_mess = "CanSAS reader: could not convert"
                            err_mess += " %s unit [%s]; expecting [%s]\n  %s" \
                                % (variable, units, local_unit, sys.exc_value)
                            self.errors.append(err_mess)
                            if optional:
                                logging.info(err_mess)
                            else:
                                raise ValueError, err_mess
                    else:
                        err_mess = "CanSAS reader: unrecognized %s unit [%s];"\
                        % (variable, units)
                        err_mess += " expecting [%s]" % local_unit
                        self.errors.append(err_mess)
                        if optional:
                            logging.info(err_mess)
                        else:
                            raise ValueError, err_mess
                else:
                    exec "storage.%s = value" % variable
            else:
                exec "storage.%s = value" % variable
                
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
