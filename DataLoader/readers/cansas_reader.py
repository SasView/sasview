"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""

#TODO: Unit conversion
#TODO: Store error list
#TODO: convert from pixel to mm for beam center...
#TODO: Allow for additional meta data for each section
#TODO: Notes need to be implemented. They can be any XML structure in version 1.0
#      Process notes have the same problem.


import logging
import numpy
import os, sys
from DataLoader.data_info import Data1D, Collimation, Detector, Process
from xml import xpath

has_converter = True
try:
    from data_util.nxsunit import Converter
except:
    has_converter = False

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
            exec "local_unit = storage.%s_unit.lower()" % toks[0]
            if attr['unit'].lower()!=local_unit:
                if has_converter==True:
                    try:
                        conv = Converter(attr['unit'])
                        exec "storage.%s = %g" % (variable, conv(value, units=local_unit))
                    except:
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
        _store_content('Run', dom, 'run', data_info)                    
        # Look up instrument name              
        value, attr = get_content('SASinstrument', dom)
        if attr.has_key('name'):
            data_info.instrument = attr['name']

        note_list = xpath.Evaluate('SASnote', dom)
        for note in note_list:
            try:
                note_value, note_attr = get_node_text(note)
                if note_value is not None:
                    data_info.notes.append(note_value)
            except:
                logging.error("cansas_reader.read: error processing entry notes\n  %s" % sys.exc_value)

        
        # Sample info ###################
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
            _store_float('length', item, 'length', collim)  
            
            # Look for apertures
            apert_list = xpath.Evaluate('aperture', item)
            for apert in apert_list:
                aperture =  collim.Aperture()
                
                _store_float('distance', apert, 'distance', aperture)    
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
            _store_float('orientation/pitch', item, 'orientation.x', detector)    
            _store_float('orientation/yaw',   item, 'orientation.y', detector)    
            _store_float('orientation/roll',  item, 'orientation.z', detector)    
            
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
        nodes = xpath.Evaluate('SASdata/Idata', dom)
        x  = numpy.zeros(0)
        y  = numpy.zeros(0)
        dx = numpy.zeros(0)
        dy = numpy.zeros(0)
        
        for item in nodes:
            _x, attr = get_float('Q', item)
            _dx, attr = get_float('Qdev', item)
            if _dx == None:
                _dx = 0.0
            if attr.has_key('unit') and attr['unit'].lower() != data_info.x_unit.lower():
                raise ValueError, "CanSAS reader: unrecognized %s unit [%s]; expecting [%s]" \
                    % (variable, attr['unit'], local_unit)
                
            _y, attr = get_float('I', item)
            _dy, attr = get_float('Idev', item)
            if _dy == None:
                _dy = 0.0
            if attr.has_key('unit') and attr['unit'].lower() != data_info.y_unit.lower():
                raise ValueError, "CanSAS reader: unrecognized %s unit [%s]; expecting [%s]" \
                    % (variable, attr['unit'], local_unit)
                
            if _x is not None and _y is not None:
                x  = numpy.append(x, _x)
                y  = numpy.append(x, _y)
                dx = numpy.append(x, _dx)
                dy = numpy.append(x, _dy)
            
        data_info.x = x
        data_info.y = y
        data_info.dx = dx
        data_info.dy = dy
        if data_conv_q is not None:
            data_info.xaxis("\\rm{Q}", output.x_unit)
        else:
            data_info.xaxis("\\rm{Q}", 'A^{-1}')
        if data_conv_i is not None:
            data_info.yaxis("\\{I(Q)}", output.y_unit)
        else:
            data_info.yaxis("\\rm{I(Q)}","cm^{-1}")
        
        return data_info

    
if __name__ == "__main__": 
    logging.basicConfig(level=logging.ERROR,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='cansas_reader.log',
                        filemode='w')
    reader = Reader()
    print reader.read("../test/cansas1d.xml")
    
    
                        