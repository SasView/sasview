"""
    Unit tests for the new recursive cansas reader
"""
import warnings
warnings.simplefilter("ignore")

import unittest
from sans.dataloader.loader import  Loader
from sans.dataloader.readers.cansas_reader_new import Reader

import os
import sys

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
    
class cansas_reader(unittest.TestCase):
    
    def setUp(self):
        self.loader = Loader()
        self.reader = Reader()
        
    def test_checkdata(self):
        output = []
        ns = []
        path = "cansas_test.xml"
        if os.path.isfile(path):
            basename = os.path.basename(path)
            root, extension = os.path.splitext(basename)
            if ALLOW_ALL or extension.lower() in self.ext:
                try:
                    tree = tree = etree.parse(path, parser=etree.ETCompatXMLParser())
                    # Check the format version number
                    # Specifying the namespace will take care of the file
                    # format version
                    for elem in tree.iter():
                        tag = elem.tag.replace('{cansas1d/1.0}', '')
                        print 'element: {0}, stripped element: {1}, value: {2}'.format(
                                                                    elem.tag, tag, elem.text)
                    # reader_return = self.reader._parse_entry(tree)
                        
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
        
        print(output)
        
if __name__ == '__main__':
    unittest.main()