"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""

"""
    Module to associate default readers to file extensions.
    The module reads an xml file to get the readers for each file extension.
    The readers are tried in order they appear when reading a file.
"""

import os, sys
from xml import xpath
import xml.dom.minidom 
import logging

from xml.dom.minidom import parse

## Format version for the XML settings file
VERSION = '1.0'

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

def read_associations(loader, settings='defaults.xml'):
    """
        Read the specified settings file to associate
        default readers to file extension.
        
        @param loader: Loader object
        @param settings: path to the XML settings file [string]
    """
    reader_dir = os.path.dirname(__file__)
    path = os.path.join(reader_dir, settings)
    
    # If we can't find the file in the installation
    # directory, look into the execution directory.
    if not os.path.isfile(path):
        path = os.path.join(os.getcwd(), settings)
    
    if os.path.isfile(path):
        dom = parse(path)
        
        # Check the format version number
        nodes = xpath.Evaluate('SansLoader', dom)
        if nodes[0].hasAttributes():
            for i in range(nodes[0].attributes.length):
                if nodes[0].attributes.item(i).nodeName=='version':
                    if nodes[0].attributes.item(i).nodeValue != VERSION:
                        raise ValueError, "associations: unrecognized SansLoader version number %s" % \
                            nodes[0].attributes.item(i).nodeValue
        
        # Read in the file extension associations
        entry_list = xpath.Evaluate('SansLoader/FileType', dom)
        for entry in entry_list:
            value, attr = get_node_text(entry)
            if attr is not None \
                and attr.has_key('reader') and attr.has_key('extension'):
                
                # Associate the extension with a particular reader
                # TODO: Modify the Register code to be case-insensitive and remove the
                #       extra line below.
                try:
                    exec "import %s" % attr['reader']
                    exec "loader.associate_file_type('%s', %s)" % (attr['extension'].lower(), attr['reader'])
                    exec "loader.associate_file_type('%s', %s)" % (attr['extension'].upper(), attr['reader'])
                except:
                    logging.error("read_associations: skipping association for %s\n  %s" % (attr['extension'], sys.exc_value))
         
         
def register_readers(registry_function):
    """
        Function called by the registry/loader object to register
        all default readers using a call back function.
        
        WARNING: this method is now obsolete
    
        @param registry_function: function to be called to register each reader
    """
    import abs_reader
    import cansas_reader
    import ascii_reader
    import cansas_reader
    import danse_reader
    import hfir1d_reader
    import IgorReader
    import tiff_reader

    registry_function(abs_reader)
    registry_function(cansas_reader)
    registry_function(ascii_reader)
    registry_function(cansas_reader)
    registry_function(danse_reader)
    registry_function(hfir1d_reader)
    registry_function(IgorReader)
    registry_function(tiff_reader)
    
    return True            


if __name__ == "__main__": 
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='logger.log',
                        filemode='w')
    from DataLoader.loader import Loader
    l = Loader()
    read_associations(l)
    
    
    print l.get_wildcards()
    
    