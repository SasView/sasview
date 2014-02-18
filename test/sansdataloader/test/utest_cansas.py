"""
    Unit tests for the new recursive cansas reader
"""
import warnings
warnings.simplefilter("ignore")

import unittest
import numpy
import sans.dataloader.readers.cansas_reader as cansas
from sans.dataloader.loader import Loader
from sans.dataloader.data_info import Data1D
from sans.dataloader.readers.xml_reader import XMLreader
from sans.dataloader.readers.cansas_reader import Reader
from sans.dataloader.readers.cansas_constants import cansasConstants

import os
import sys
import urllib2
import StringIO

from lxml import etree
import xml.dom.minidom
 
CANSAS_FORMAT = cansasConstants.CANSAS_FORMAT
CANSAS_NS = cansasConstants.CANSAS_NS
    
class cansas_reader(unittest.TestCase):
    
    def setUp(self):
        self.loader = Loader()
        self.xml_valid = "cansas_test_modified.xml"
        self.xml_invalid = "cansas_test.xml"
        self.cansas1d_badunits = "cansas1d_badunits.xml"
        self.cansas1d = "cansas1d.xml"
        self.cansas1d_slit = "cansas1d_slit.xml"
        self.cansas1d_units = "cansas1d_units.xml"
        self.isis_1_0 = "ISIS_1_0.xml"
        self.isis_1_1 = "ISIS_1_1.xml"
        self.isis_1_1_notrans = "ISIS_1_1_notrans.xml"
        self.isis_1_1_doubletrans = "ISIS_1_1_doubletrans.xml"
        self.schema_1_0 = "cansas1d_v1_0.xsd"
        self.schema_1_1 = "cansas1d_v1_1.xsd"
        
    
    def get_number_of_entries(self, dictionary, name, i):
        if dictionary.get(name) is not None:
            i += 1
            name = name.split("_")[0]
            name += "_{0}".format(i)
            name = self.get_number_of_entries(dictionary, name, i)
        return name
    

    def test_xml_validate(self):
        string = "<xsd:schema xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\">\n"
        string += "\t<xsd:element name=\"a\" type=\"AType\"/>\n"
        string += "\t<xsd:complexType name=\"AType\">\n"
        string += "\t\t<xsd:sequence>\n"
        string += "\t\t\t<xsd:element name=\"b\" type=\"xsd:string\" />\n"
        string += "\t\t</xsd:sequence>\n"
        string += "\t</xsd:complexType>\n"
        string += "</xsd:schema>"
        f = StringIO.StringIO(string)
        xmlschema_doc = etree.parse(f)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        valid = etree.parse(StringIO.StringIO('<a><b></b></a>'))
        invalid = etree.parse(StringIO.StringIO('<a><c></c></a>'))
        self.assertTrue(xmlschema.validate(valid))
        self.assertFalse(xmlschema.validate(invalid))
        
        
    def test_real_xml(self):
        reader = XMLreader(self.xml_valid, self.schema_1_0)
        valid = reader.validateXML()
        if valid:
            self.assertTrue(valid)
        else:
            self.assertFalse(valid)
            
            
    def _check_data(self, data):
        self.assertTrue(data.title == "TK49 c10_SANS")
        self.assertTrue(data.x.size == 138)
        self.assertTrue(len(data.meta_data) == 2)
        self.assertTrue(data.detector[0].distance_unit == "mm")
        self.assertTrue(data.detector[1].distance_unit == "mm")
        self.assertTrue(data.detector[0].name == "HAB")
        self.assertTrue(data.detector[1].name == "main-detector-bank")
        self.assertTrue(data.detector[0].distance == 575.0)
        self.assertTrue(data.detector[1].distance == 4145.02)
        self.assertTrue(data.process[0].name == "Mantid generated CanSAS1D XML")
        
    
    def _check_data_1_1(self, data):
        spectrum = data.trans_spectrum[0]
        self.assertTrue(len(spectrum.wavelength) == 138)
        
    
    def test_cansas_xml(self):
        filename = "isis_1_1_write_test.xml"
        xmlreader = XMLreader(self.isis_1_1, self.schema_1_1)
        valid = xmlreader.validateXML()
        self.assertTrue(valid)
        reader_generic = Loader()
        dataloader = reader_generic.load(self.isis_1_1)
        reader_cansas = Reader()
        cansasreader = reader_cansas.read(self.isis_1_1)
        for i in range(len(dataloader)):
            self._check_data(dataloader[i])
            self._check_data_1_1(dataloader[i])
            self._check_data(cansasreader[i])
            self._check_data_1_1(cansasreader[i])
            reader_generic.save(filename, dataloader[i], None)
            reader2 = Reader()
            return_data = reader2.read(filename)
            data_new = return_data
            written_data = return_data[0]
            self._check_data(written_data)
            
    
    def test_double_trans_spectra(self):
        xmlreader = XMLreader(self.isis_1_1_doubletrans, self.schema_1_1)
        self.assertTrue(xmlreader.validateXML())
        reader = Loader()
        data = reader.load(self.isis_1_1_doubletrans)
        for item in data:
            self._check_data(item)
    
                    
    def test_entry_name_recurse(self):
        test_values = [1,2,3,4,5,6]
        base_key = "key"
        d = {}
        for value in test_values:
            new_key = self.get_number_of_entries(d, base_key, i = 0)
            d[new_key] = value
        self.assertTrue(len(d) == 6)
        
    
    def test_load_cansas_file(self):
        valid = []
        reader1 = XMLreader(self.xml_valid, self.schema_1_0)
        self.assertTrue(reader1.validateXML())
        reader2 = XMLreader(self.xml_invalid, self.schema_1_0)
        self.assertFalse(reader2.validateXML())
        reader3 = XMLreader(self.xml_valid, self.schema_1_1)
        self.assertFalse(reader3.validateXML())
        reader4 = XMLreader(self.xml_invalid, self.schema_1_1)
        self.assertFalse(reader4.validateXML())
        reader5 = XMLreader(self.isis_1_0, self.schema_1_0)
        self.assertTrue(reader5.validateXML())
        reader6 = XMLreader(self.isis_1_1, self.schema_1_1)
        self.assertTrue(reader6.validateXML())
        reader7 = XMLreader(self.isis_1_1, self.schema_1_0)
        self.assertFalse(reader7.validateXML())
        
    
    def test_old_cansas_files(self):
        reader1 = XMLreader(self.cansas1d, self.schema_1_0)
        self.assertTrue(reader1.validateXML())
        reader2 = XMLreader(self.cansas1d_units, self.schema_1_0)
        self.assertTrue(reader2.validateXML())
        reader3 = XMLreader(self.cansas1d_badunits, self.schema_1_0)
        self.assertTrue(reader3.validateXML())
        reader4 = XMLreader(self.cansas1d_slit, self.schema_1_0)
        self.assertTrue(reader4.validateXML())
        
    
    def test_save_cansas_v1_0(self):
        filename = "isis_1_0_write_test.xml"
        xmlreader = XMLreader(self.isis_1_0, self.schema_1_0)
        valid = xmlreader.validateXML()
        self.assertTrue(valid)
        reader_generic = Loader()
        dataloader = reader_generic.load(self.isis_1_0)
        reader_cansas = Reader()
        cansasreader = reader_cansas.read(self.isis_1_0)
        for i in range(len(dataloader)):
            self._check_data(dataloader[i])
            self._check_data(cansasreader[i])
            reader_generic.save(filename, dataloader[i], None)
            reader2 = Reader()
            return_data = reader2.read(filename)
            data_new = return_data
            written_data = return_data[0]
            self._check_data(written_data)
        

if __name__ == '__main__':
    unittest.main()    