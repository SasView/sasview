"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""
# Known issue: reader not compatible with multiple SASdata entries
# within a single SASentry. Will raise a runtime error.

#TODO: check that all vectors are written only if they have at least one non-empty value
#TODO: Writing only allows one SASentry per file. Would be best to allow multiple entries.
#TODO: Store error list
#TODO: Allow for additional meta data for each section
#TODO: Notes need to be implemented. They can be any XML structure in version 1.0
#      Process notes have the same problem.
#TODO: Unit conversion is not complete (temperature units are missing)


import logging
import numpy
import os, sys
from DataLoader.data_info import Data1D, Collimation, Detector, Process, Aperture
from xml import xpath
import xml.dom.minidom 


has_converter = True
try:
    from data_util.nxsunit import Converter
except:
    has_converter = False

def write_node(doc, parent, name, value, attr={}):
    """
        @param doc: document DOM
        @param parent: parent node
        @param name: tag of the element
        @param value: value of the child text node
        @param attr: attribute dictionary
        @return: True if something was appended, otherwise False
    """
    if value is not None:
        node = doc.createElement(name)
        node.appendChild(doc.createTextNode(str(value)))
        for item in attr:
            node.setAttribute(item, attr[item])
        parent.appendChild(node)
        return True
    return False

def get_node_text(node):
    """
        Get the text context of a node
        
        @param node: node to read from
        @return: content, attribute list
    """
    content = None
    attr    = {}
    for item in node.childNodes:
        if item.nodeName.find('text')>=0 \
            and len(item.nodeValue.strip())>0:
            content = item.nodeValue.strip()
            break
        
    if node.hasAttributes():
        for i in range(node.attributes.length):
            attr[node.attributes.item(i).nodeName] \
                = node.attributes.item(i).nodeValue

    return content, attr

def get_content(location, node):
    """
        Get the first instance of the content of a xpath location
        
        @param location: xpath location
        @param node: node to start at
    """
    value = None
    attr  = {}
    nodes = xpath.Evaluate(location, node)
    if len(nodes)>0:
        try:
            # Skip comments and empty lines 
            for item in nodes[0].childNodes:
                if item.nodeName.find('text')>=0 \
                    and len(item.nodeValue.strip())>0:
                    value = item.nodeValue.strip()
                    break
                
            if nodes[0].hasAttributes():
                for i in range(nodes[0].attributes.length):
                    attr[nodes[0].attributes.item(i).nodeName] \
                        = nodes[0].attributes.item(i).nodeValue
        except:
            # problem reading the node. Skip it and return that
            # nothing was found
            logging.error("cansas_reader.get_content: %s\n  %s" % (location, sys.exc_value))
        
    return value, attr

def get_float(location, node):
    """
        Get the content of a node as a float
        
        @param location: xpath location
        @param node: node to start at
    """
    value = None
    attr = {}
    content, attr = get_content(location, node)
    if content is not None:
        try:
            value = float(content)   
        except:
            # Could not pass, skip and return None
            logging.error("cansas_reader.get_float: could not convert '%s' to float" % content)
        
    return value, attr

def _store_float(location, node, variable, storage):
    """
        Get the content of a xpath location and store
        the result. Check that the units are compatible
        with the destination. The value is expected to
        be a float.
        
        The xpath location might or might not exist.
        If it does not exist, nothing is done
        
        @param location: xpath location to fetch
        @param node: node to read the data from
        @param variable: name of the data member to store it in [string]
        @param storage: data object that has the 'variable' data member
        
        @raise ValueError: raised when the units are not recognized
    """
    value, attr = get_float(location, node)
    if value is not None:
        # If the entry has units, check to see that they are
        # compatible with what we currently have in the data object
        if attr.has_key('unit'):
            toks = variable.split('.')
            exec "local_unit = storage.%s_unit" % toks[0]
            if attr['unit'].lower()!=local_unit.lower():
                if has_converter==True:
                    try:
                        conv = Converter(attr['unit'])
                        exec "storage.%s = %g" % (variable, conv(value, units=local_unit))
                    except:
                        #Below three lines were added for the unit = 1/A. local unit is defined in 'mm'. Need to check!!!
                        if variable == 'slit_length' and attr['unit'] !=local_unit:
                            pass
                        else:
                            raise ValueError, "CanSAS reader: could not convert %s unit [%s]; expecting [%s]\n  %s" \
                            % (variable, attr['unit'], local_unit, sys.exc_value)
                else:
                    raise ValueError, "CanSAS reader: unrecognized %s unit [%s]; expecting [%s]" \
                        % (variable, attr['unit'], local_unit)
            else:
                exec "storage.%s = value" % variable
        else:
            exec "storage.%s = value" % variable
            

def _store_content(location, node, variable, storage):
    """
        Get the content of a xpath location and store
        the result. The value is treated as a string.
        
        The xpath location might or might not exist.
        If it does not exist, nothing is done
        
        @param location: xpath location to fetch
        @param node: node to read the data from
        @param variable: name of the data member to store it in [string]
        @param storage: data object that has the 'variable' data member
    """
    value, attr = get_content(location, node)
    if value is not None:
        exec "storage.%s = value" % variable


class Reader:
    """
        Class to load cansas 1D XML files
        
        Dependencies:
            The CanSas reader requires PyXML 0.8.4 or later.
    """
    ## CanSAS version
    version = '1.0'
    ## File type
    type_name = "CanSAS 1D"
    ## Wildcards
    type = ["CanSAS 1D files (*.xml)|*.xml"]
    ## List of allowed extensions
    ext=['.xml', '.XML']  
    
    def read(self, path):
        """ 
            Load data file
            
            @param path: file path
            @return: Data1D object if a single SASentry was found, 
                        or a list of Data1D objects if multiple entries were found,
                        or None of nothing was found
            @raise RuntimeError: when the file can't be opened
            @raise ValueError: when the length of the data vectors are inconsistent
        """
        from xml.dom.minidom import parse
        
        output = []
        
        if os.path.isfile(path):
            basename  = os.path.basename(path)
            root, extension = os.path.splitext(basename)
            if extension.lower() in self.ext:
                
                dom = parse(path)
                
                # Check the format version number
                nodes = xpath.Evaluate('SASroot', dom)
                if nodes[0].hasAttributes():
                    for i in range(nodes[0].attributes.length):
                        if nodes[0].attributes.item(i).nodeName=='version':
                            if nodes[0].attributes.item(i).nodeValue != self.version:
                                raise ValueError, "cansas_reader: unrecognized version number %s" % \
                                    nodes[0].attributes.item(i).nodeValue
                
                entry_list = xpath.Evaluate('SASroot/SASentry', dom)
                for entry in entry_list:
                    sas_entry = self._parse_entry(entry)
                    sas_entry.filename = basename
                    output.append(sas_entry)
                
        else:
            raise RuntimeError, "%s is not a file" % path
        
        # Return output consistent with the loader's api
        if len(output)==0:
            return None
        elif len(output)==1:
            return output[0]
        else:
            return output                
                
    def _parse_entry(self, dom):
        """
            Parse a SASentry
            
            @param node: SASentry node
            @return: Data1D object
        """
        x = numpy.zeros(0)
        y = numpy.zeros(0)
        
        data_info = Data1D(x, y)
        
        # Look up title
        _store_content('Title', dom, 'title', data_info)
        # Look up run number   
        nodes = xpath.Evaluate('Run', dom)
        for item in nodes:    
            value, attr = get_node_text(item)
            if value is not None:
                data_info.run.append(value)
                if attr.has_key('name'):
                    data_info.run_name[value] = attr['name']         
                           
        # Look up instrument name              
        _store_content('SASinstrument/name', dom, 'instrument', data_info)
        #value, attr = get_content('SASinstrument', dom)
        #if attr.has_key('name'):
        #    data_info.instrument = attr['name']

        note_list = xpath.Evaluate('SASnote', dom)
        for note in note_list:
            try:
                note_value, note_attr = get_node_text(note)
                if note_value is not None:
                    data_info.notes.append(note_value)
            except:
                logging.error("cansas_reader.read: error processing entry notes\n  %s" % sys.exc_value)

        
        # Sample info ###################
        value, attr = get_content('SASsample', dom)
        if attr.has_key('name'):
            data_info.sample.name = attr['name']
            
        _store_content('SASsample/ID', 
                     dom, 'ID', data_info.sample)                    
        _store_float('SASsample/thickness', 
                     dom, 'thickness', data_info.sample)
        _store_float('SASsample/transmission', 
                     dom, 'transmission', data_info.sample)
        _store_float('SASsample/temperature', 
                     dom, 'temperature', data_info.sample)
        nodes = xpath.Evaluate('SASsample/details', dom)
        for item in nodes:
            try:
                detail_value, detail_attr = get_node_text(item)
                if detail_value is not None:
                    data_info.sample.details.append(detail_value)
            except:
                logging.error("cansas_reader.read: error processing sample details\n  %s" % sys.exc_value)
        
        # Position (as a vector)
        _store_float('SASsample/position/x', 
                     dom, 'position.x', data_info.sample)          
        _store_float('SASsample/position/y', 
                     dom, 'position.y', data_info.sample)          
        _store_float('SASsample/position/z', 
                     dom, 'position.z', data_info.sample)          
        
        # Orientation (as a vector)
        _store_float('SASsample/orientation/roll', 
                     dom, 'orientation.x', data_info.sample)          
        _store_float('SASsample/orientation/pitch', 
                     dom, 'orientation.y', data_info.sample)          
        _store_float('SASsample/orientation/yaw', 
                     dom, 'orientation.z', data_info.sample)          
       
        # Source info ###################
        value, attr = get_content('SASinstrument/SASsource', dom)
        if attr.has_key('name'):
            data_info.source.name = attr['name']
        
        _store_content('SASinstrument/SASsource/radiation', 
                     dom, 'radiation', data_info.source)                    
        _store_content('SASinstrument/SASsource/beam_shape', 
                     dom, 'beam_shape', data_info.source)                    
        _store_float('SASinstrument/SASsource/wavelength', 
                     dom, 'wavelength', data_info.source)          
        _store_float('SASinstrument/SASsource/wavelength_min', 
                     dom, 'wavelength_min', data_info.source)          
        _store_float('SASinstrument/SASsource/wavelength_max', 
                     dom, 'wavelength_max', data_info.source)          
        _store_float('SASinstrument/SASsource/wavelength_spread', 
                     dom, 'wavelength_spread', data_info.source)    
        
        # Beam size (as a vector)   
        value, attr = get_content('SASinstrument/SASsource/beam_size', dom)
        if attr.has_key('name'):
            data_info.source.beam_size_name = attr['name']
            
        _store_float('SASinstrument/SASsource/beam_size/x', 
                     dom, 'beam_size.x', data_info.source)    
        _store_float('SASinstrument/SASsource/beam_size/y', 
                     dom, 'beam_size.y', data_info.source)    
        _store_float('SASinstrument/SASsource/beam_size/z', 
                     dom, 'beam_size.z', data_info.source)    
        
        # Collimation info ###################
        nodes = xpath.Evaluate('SASinstrument/SAScollimation', dom)
        for item in nodes:
            collim = Collimation()
            value, attr = get_node_text(item)
            if attr.has_key('name'):
                collim.name = attr['name']
            _store_float('length', item, 'length', collim)  
            
            # Look for apertures
            apert_list = xpath.Evaluate('aperture', item)
            for apert in apert_list:
                aperture =  Aperture()
                
                # Get the name and type of the aperture
                ap_value, ap_attr = get_node_text(apert)
                if ap_attr.has_key('name'):
                    aperture.name = ap_attr['name']
                if ap_attr.has_key('type'):
                    aperture.type = ap_attr['type']
                    
                _store_float('distance', apert, 'distance', aperture)    
                
                value, attr = get_content('size', apert)
                if attr.has_key('name'):
                    aperture.size_name = attr['name']
                
                _store_float('size/x', apert, 'size.x', aperture)    
                _store_float('size/y', apert, 'size.y', aperture)    
                _store_float('size/z', apert, 'size.z', aperture)
                
                collim.aperture.append(aperture)
                
            data_info.collimation.append(collim)
        
        # Detector info ######################
        nodes = xpath.Evaluate('SASinstrument/SASdetector', dom)
        for item in nodes:
            
            detector = Detector()
            
            _store_content('name', item, 'name', detector)
            _store_float('SDD', item, 'distance', detector)    
            
            # Detector offset (as a vector)
            _store_float('offset/x', item, 'offset.x', detector)    
            _store_float('offset/y', item, 'offset.y', detector)    
            _store_float('offset/z', item, 'offset.z', detector)    
            
            # Detector orientation (as a vector)
            _store_float('orientation/roll',  item, 'orientation.x', detector)    
            _store_float('orientation/pitch', item, 'orientation.y', detector)    
            _store_float('orientation/yaw',   item, 'orientation.z', detector)    
            
            # Beam center (as a vector)
            _store_float('beam_center/x', item, 'beam_center.x', detector)    
            _store_float('beam_center/y', item, 'beam_center.y', detector)    
            _store_float('beam_center/z', item, 'beam_center.z', detector)    
            
            # Pixel size (as a vector)
            _store_float('pixel_size/x', item, 'pixel_size.x', detector)    
            _store_float('pixel_size/y', item, 'pixel_size.y', detector)    
            _store_float('pixel_size/z', item, 'pixel_size.z', detector)    
            
            _store_float('slit_length', item, 'slit_length', detector)
            
            data_info.detector.append(detector)    

        # Processes info ######################
        nodes = xpath.Evaluate('SASprocess', dom)
        for item in nodes:
            process = Process()
            _store_content('name', item, 'name', process)
            _store_content('date', item, 'date', process)
            _store_content('description', item, 'description', process)
            
            term_list = xpath.Evaluate('term', item)
            for term in term_list:
                try:
                    term_value, term_attr = get_node_text(term)
                    term_attr['value'] = term_value
                    if term_value is not None:
                        process.term.append(term_attr)
                except:
                    logging.error("cansas_reader.read: error processing process term\n  %s" % sys.exc_value)
            
            note_list = xpath.Evaluate('SASprocessnote', item)
            for note in note_list:
                try:
                    note_value, note_attr = get_node_text(note)
                    if note_value is not None:
                        process.notes.append(note_value)
                except:
                    logging.error("cansas_reader.read: error processing process notes\n  %s" % sys.exc_value)
            
            
            data_info.process.append(process)
            
            
        # Data info ######################
        nodes = xpath.Evaluate('SASdata', dom)
        if len(nodes)>1:
            raise RuntimeError, "CanSAS reader is not compatible with multiple SASdata entries"
        
        nodes = xpath.Evaluate('SASdata/Idata', dom)
        x  = numpy.zeros(0)
        y  = numpy.zeros(0)
        dx = numpy.zeros(0)
        dy = numpy.zeros(0)
        dxw = numpy.zeros(0)
        dxl = numpy.zeros(0)
        
        for item in nodes:
            _x, attr = get_float('Q', item)
            _dx, attr_d = get_float('Qdev', item)
            _dxl, attr_l = get_float('dQl', item)
            _dxw, attr_w = get_float('dQw', item)
            if _dx == None:
                _dx = 0.0
            if _dxl == None:
                _dxl = 0.0
            if _dxw == None:
                _dxw = 0.0
                
            if attr.has_key('unit') and attr['unit'].lower() != data_info.x_unit.lower():
                if has_converter==True:
                    try:
                        data_conv_q = Converter(attr['unit'])
                        _x = data_conv_q(_x, units=data_info.x_unit)
                    except:
                        raise ValueError, "CanSAS reader: could not convert Q unit [%s]; expecting [%s]\n  %s" \
                        % (attr['unit'], data_info.x_unit, sys.exc_value)
                else:
                    raise ValueError, "CanSAS reader: unrecognized Q unit [%s]; expecting [%s]" \
                        % (attr['unit'], data_info.x_unit)
            # Error in Q
            if attr_d.has_key('unit') and attr_d['unit'].lower() != data_info.x_unit.lower():
                if has_converter==True:
                    try:
                        data_conv_q = Converter(attr_d['unit'])
                        _dx = data_conv_q(_dx, units=data_info.x_unit)
                    except:
                        raise ValueError, "CanSAS reader: could not convert dQ unit [%s]; expecting [%s]\n  %s" \
                        % (attr['unit'], data_info.x_unit, sys.exc_value)
                else:
                    raise ValueError, "CanSAS reader: unrecognized dQ unit [%s]; expecting [%s]" \
                        % (attr['unit'], data_info.x_unit)
            # Slit length
            if attr_l.has_key('unit') and attr_l['unit'].lower() != data_info.x_unit.lower():
                if has_converter==True:
                    try:
                        data_conv_q = Converter(attr_l['unit'])
                        _dxl = data_conv_q(_dxl, units=data_info.x_unit)
                    except:
                        raise ValueError, "CanSAS reader: could not convert dQl unit [%s]; expecting [%s]\n  %s" \
                        % (attr['unit'], data_info.x_unit, sys.exc_value)
                else:
                    raise ValueError, "CanSAS reader: unrecognized dQl unit [%s]; expecting [%s]" \
                        % (attr['unit'], data_info.x_unit)
            # Slit width
            if attr_w.has_key('unit') and attr_w['unit'].lower() != data_info.x_unit.lower():
                if has_converter==True:
                    try:
                        data_conv_q = Converter(attr_w['unit'])
                        _dxw = data_conv_q(_dxw, units=data_info.x_unit)
                    except:
                        raise ValueError, "CanSAS reader: could not convert dQw unit [%s]; expecting [%s]\n  %s" \
                        % (attr['unit'], data_info.x_unit, sys.exc_value)
                else:
                    raise ValueError, "CanSAS reader: unrecognized dQw unit [%s]; expecting [%s]" \
                        % (attr['unit'], data_info.x_unit)
                    
            _y, attr = get_float('I', item)
            _dy, attr_d = get_float('Idev', item)
            if _dy == None:
                _dy = 0.0
            if attr.has_key('unit') and attr['unit'].lower() != data_info.y_unit.lower():
                if has_converter==True:
                    try:
                        data_conv_i = Converter(attr['unit'])
                        _y = data_conv_i(_y, units=data_info.y_unit)
                    except:
                        raise ValueError, "CanSAS reader: could not convert I(q) unit [%s]; expecting [%s]\n  %s" \
                        % (attr['unit'], data_info.y_unit, sys.exc_value)
                else:
                    raise ValueError, "CanSAS reader: unrecognized I(q) unit [%s]; expecting [%s]" \
                        % (attr['unit'], data_info.y_unit)
            if attr_d.has_key('unit') and attr_d['unit'].lower() != data_info.y_unit.lower():
                if has_converter==True:
                    try:
                        data_conv_i = Converter(attr_d['unit'])
                        _dy = data_conv_i(_dy, units=data_info.y_unit)
                    except:
                        raise ValueError, "CanSAS reader: could not convert dI(q) unit [%s]; expecting [%s]\n  %s" \
                        % (attr_d['unit'], data_info.y_unit, sys.exc_value)
                else:
                    raise ValueError, "CanSAS reader: unrecognized dI(q) unit [%s]; expecting [%s]" \
                        % (attr_d['unit'], data_info.y_unit)
                
            if _x is not None and _y is not None:
                x  = numpy.append(x, _x)
                y  = numpy.append(y, _y)
                dx = numpy.append(dx, _dx)
                dy = numpy.append(dy, _dy)
                dxl = numpy.append(dxl, _dxl)
                dxw = numpy.append(dxw, _dxw)
                
            
        data_info.x = x
        data_info.y = y
        data_info.dx = dx
        data_info.dy = dy
        data_info.dxl = dxl
        data_info.dxw = dxw
        
        data_conv_q = None
        data_conv_i = None
        
        if has_converter == True and data_info.x_unit != '1/A':
            data_conv_q = Converter('1/A')
            # Test it
            data_conv_q(1.0, output.Q_unit)
            
        if has_converter == True and data_info.y_unit != '1/cm':
            data_conv_i = Converter('1/cm')
            # Test it
            data_conv_i(1.0, output.I_unit)                    
                
        if data_conv_q is not None:
            data_info.xaxis("\\rm{Q}", data_info.x_unit)
        else:
            data_info.xaxis("\\rm{Q}", 'A^{-1}')
        if data_conv_i is not None:
            data_info.yaxis("\\rm{Intensity}", data_info.y_unit)
        else:
            data_info.yaxis("\\rm{Intensity}","cm^{-1}")
        
        return data_info

    def write(self, filename, datainfo):
        """
            Write the content of a Data1D as a CanSAS XML file
            
            @param filename: name of the file to write
            @param datainfo: Data1D object
        """
        
        if not datainfo.__class__ == Data1D: 
            raise RuntimeError, "The cansas writer expects a Data1D instance"
        
        doc = xml.dom.minidom.Document()
        main_node = doc.createElement("SASroot")
        main_node.setAttribute("version", self.version)
        main_node.setAttribute("xmlns", "cansas1d/%s" % self.version)
        main_node.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        main_node.setAttribute("xsi:schemaLocation", "cansas1d/%s http://svn.smallangles.net/svn/canSAS/1dwg/trunk/cansas1d.xsd" % self.version)
        
        doc.appendChild(main_node)
        
        entry_node = doc.createElement("SASentry")
        main_node.appendChild(entry_node)
        
        write_node(doc, entry_node, "Title", datainfo.title)
        
        for item in datainfo.run:
            runname = {}
            if datainfo.run_name.has_key(item) and len(str(datainfo.run_name[item]))>1:
                runname = {'name': datainfo.run_name[item] }
            write_node(doc, entry_node, "Run", item, runname)
        
        # Data info
        node = doc.createElement("SASdata")
        entry_node.appendChild(node)
        
        for i in range(len(datainfo.x)):
            pt = doc.createElement("Idata")
            node.appendChild(pt)
            write_node(doc, pt, "Q", datainfo.x[i], {'unit':datainfo.x_unit})
            if len(datainfo.y)>=i:
                write_node(doc, pt, "I", datainfo.y[i], {'unit':datainfo.y_unit})
            if datainfo.dx !=None and len(datainfo.dx)>=i:
                write_node(doc, pt, "Qdev", datainfo.dx[i], {'unit':datainfo.x_unit})
            if datainfo.dx !=None and len(datainfo.dy)>=i:
                write_node(doc, pt, "Idev", datainfo.dy[i], {'unit':datainfo.y_unit})

        
        # Sample info
        sample = doc.createElement("SASsample")
        if datainfo.sample.name is not None:
            sample.setAttribute("name", str(datainfo.sample.name))
        entry_node.appendChild(sample)
        write_node(doc, sample, "ID", str(datainfo.sample.ID))
        write_node(doc, sample, "thickness", datainfo.sample.thickness, {"unit":datainfo.sample.thickness_unit})
        write_node(doc, sample, "transmission", datainfo.sample.transmission)
        write_node(doc, sample, "temperature", datainfo.sample.temperature, {"unit":datainfo.sample.temperature_unit})
        
        for item in datainfo.sample.details:
            write_node(doc, sample, "details", item)
        
        pos = doc.createElement("position")
        written = write_node(doc, pos, "x", datainfo.sample.position.x, {"unit":datainfo.sample.position_unit})
        written = written | write_node(doc, pos, "y", datainfo.sample.position.y, {"unit":datainfo.sample.position_unit})
        written = written | write_node(doc, pos, "z", datainfo.sample.position.z, {"unit":datainfo.sample.position_unit})
        if written == True:
            sample.appendChild(pos)
        
        ori = doc.createElement("orientation")
        written = write_node(doc, ori, "roll",  datainfo.sample.orientation.x, {"unit":datainfo.sample.orientation_unit})
        written = written | write_node(doc, ori, "pitch", datainfo.sample.orientation.y, {"unit":datainfo.sample.orientation_unit})
        written = written | write_node(doc, ori, "yaw",   datainfo.sample.orientation.z, {"unit":datainfo.sample.orientation_unit})
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
        written = write_node(doc, size, "x", datainfo.source.beam_size.x, {"unit":datainfo.source.beam_size_unit})
        written = written | write_node(doc, size, "y", datainfo.source.beam_size.y, {"unit":datainfo.source.beam_size_unit})
        written = written | write_node(doc, size, "z", datainfo.source.beam_size.z, {"unit":datainfo.source.beam_size_unit})
        if written == True:
            source.appendChild(size)
            
        write_node(doc, source, "wavelength", datainfo.source.wavelength, {"unit":datainfo.source.wavelength_unit})
        write_node(doc, source, "wavelength_min", datainfo.source.wavelength_min, {"unit":datainfo.source.wavelength_min_unit})
        write_node(doc, source, "wavelength_max", datainfo.source.wavelength_max, {"unit":datainfo.source.wavelength_max_unit})
        write_node(doc, source, "wavelength_spread", datainfo.source.wavelength_spread, {"unit":datainfo.source.wavelength_spread_unit})
        
        #   Collimation
        for item in datainfo.collimation:
            coll = doc.createElement("SAScollimation")
            if item.name is not None:
                coll.setAttribute("name", str(item.name))
            instr.appendChild(coll)
            
            write_node(doc, coll, "length", item.length, {"unit":item.length_unit})
            
            for apert in item.aperture:
                ap = doc.createElement("aperture")
                if apert.name is not None:
                    ap.setAttribute("name", str(apert.name))
                if apert.type is not None:
                    ap.setAttribute("type", str(apert.type))
                coll.appendChild(ap)
                
                write_node(doc, ap, "distance", apert.distance, {"unit":apert.distance_unit})
                
                size = doc.createElement("size")
                if apert.size_name is not None:
                    size.setAttribute("name", str(apert.size_name))
                written = write_node(doc, size, "x", apert.size.x, {"unit":apert.size_unit})
                written = written | write_node(doc, size, "y", apert.size.y, {"unit":apert.size_unit})
                written = written | write_node(doc, size, "z", apert.size.z, {"unit":apert.size_unit})
                if written == True:
                    ap.appendChild(size)

        #   Detectors
        for item in datainfo.detector:
            det = doc.createElement("SASdetector")
            written = write_node(doc, det, "name", item.name)
            written = written | write_node(doc, det, "SDD", item.distance, {"unit":item.distance_unit})
            written = written | write_node(doc, det, "slit_length", item.slit_length, {"unit":item.slit_length_unit})
            if written == True:
                instr.appendChild(det)
            
            off = doc.createElement("offset")
            written = write_node(doc, off, "x", item.offset.x, {"unit":item.offset_unit})
            written = written | write_node(doc, off, "y", item.offset.y, {"unit":item.offset_unit})
            written = written | write_node(doc, off, "z", item.offset.z, {"unit":item.offset_unit})
            if written == True:
                det.appendChild(off)
            
            center = doc.createElement("beam_center")
            written = write_node(doc, center, "x", item.beam_center.x, {"unit":item.beam_center_unit})
            written = written | write_node(doc, center, "y", item.beam_center.y, {"unit":item.beam_center_unit})
            written = written | write_node(doc, center, "z", item.beam_center.z, {"unit":item.beam_center_unit})
            if written == True:
                det.appendChild(center)
                
            pix = doc.createElement("pixel_size")
            written = write_node(doc, pix, "x", item.pixel_size.x, {"unit":item.pixel_size_unit})
            written = written | write_node(doc, pix, "y", item.pixel_size.y, {"unit":item.pixel_size_unit})
            written = written | write_node(doc, pix, "z", item.pixel_size.z, {"unit":item.pixel_size_unit})
            if written == True:
                det.appendChild(pix)
                
            ori = doc.createElement("orientation")
            written = write_node(doc, ori, "roll",  item.orientation.x, {"unit":item.orientation_unit})
            written = written | write_node(doc, ori, "pitch", item.orientation.y, {"unit":item.orientation_unit})
            written = written | write_node(doc, ori, "yaw",   item.orientation.z, {"unit":item.orientation_unit})
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
            
        
        # Write the file
        fd = open(filename, 'w')
        fd.write(doc.toprettyxml())
        fd.close()
        
        
if __name__ == "__main__": 
    logging.basicConfig(level=logging.ERROR,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='cansas_reader.log',
                        filemode='w')
    reader = Reader()
    print reader.read("../test/cansas1d.xml")
    
    
                        