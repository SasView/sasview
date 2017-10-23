"""
    Unit tests for the new recursive cansas reader
"""
import os
import sys
import unittest
import logging
import warnings
if sys.version_info[0] >= 3:
    from io import StringIO
else:
    from StringIO import StringIO

from lxml import etree
from lxml.etree import XMLSyntaxError
from xml.dom import minidom

import sas.sascalc.dataloader.readers.cansas_reader as cansas
from sas.sascalc.dataloader.file_reader_base_class import decode
from sas.sascalc.dataloader.loader import Loader
from sas.sascalc.dataloader.data_info import Data1D, Data2D
from sas.sascalc.dataloader.readers.xml_reader import XMLreader
from sas.sascalc.dataloader.readers.cansas_reader import Reader
from sas.sascalc.dataloader.readers.cansas_constants import CansasConstants

logger = logging.getLogger(__name__)

warnings.simplefilter("ignore")

CANSAS_FORMAT = CansasConstants.CANSAS_FORMAT
CANSAS_NS = CansasConstants.CANSAS_NS

class cansas_reader_xml(unittest.TestCase):

    def setUp(self):
        self.loader = Loader()
        self.xml_valid = "cansas_test_modified.xml"
        self.xml_invalid = "cansas_test.xml"
        self.cansas1d_badunits = "cansas1d_badunits.xml"
        self.cansas1d = "cansas1d.xml"
        self.cansas1d_slit = "cansas1d_slit.xml"
        self.cansas1d_units = "cansas1d_units.xml"
        self.cansas1d_notitle = "cansas1d_notitle.xml"
        self.isis_1_0 = "ISIS_1_0.xml"
        self.isis_1_1 = "ISIS_1_1.xml"
        self.isis_1_1_notrans = "ISIS_1_1_notrans.xml"
        self.isis_1_1_doubletrans = "ISIS_1_1_doubletrans.xml"
        self.schema_1_0 = "cansas1d_v1_0.xsd"
        self.schema_1_1 = "cansas1d_v1_1.xsd"
        self.write_1_0_filename = "isis_1_0_write_test.xml"
        self.write_1_1_filename = "isis_1_1_write_test.xml"

    def get_number_of_entries(self, dictionary, name, i):
        if dictionary.get(name) is not None:
            i += 1
            name = name.split("_")[0]
            name += "_{0}".format(i)
            name = self.get_number_of_entries(dictionary, name, i)
        return name

    def test_invalid_xml(self):
        """
        Should fail gracefully and send a message to logger.info()
        """
        invalid = StringIO('<a><c></b></a>')
        self.assertRaises(XMLSyntaxError, lambda: XMLreader(invalid))

    def test_xml_validate(self):
        string = "<xsd:schema xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\">\n"
        string += "\t<xsd:element name=\"a\" type=\"AType\"/>\n"
        string += "\t<xsd:complexType name=\"AType\">\n"
        string += "\t\t<xsd:sequence>\n"
        string += "\t\t\t<xsd:element name=\"b\" type=\"xsd:string\" />\n"
        string += "\t\t</xsd:sequence>\n"
        string += "\t</xsd:complexType>\n"
        string += "</xsd:schema>"
        f = StringIO(string)
        xmlschema_doc = etree.parse(f)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        valid = etree.parse(StringIO('<a><b></b></a>'))
        invalid = etree.parse(StringIO('<a><c></c></a>'))
        self.assertTrue(xmlschema.validate(valid))
        self.assertFalse(xmlschema.validate(invalid))

    def test_real_xml(self):
        reader = XMLreader(self.xml_valid, self.schema_1_0)
        valid = reader.validate_xml()
        if valid:
            self.assertTrue(valid)
        else:
            self.assertFalse(valid)

    def _check_data(self, data):
        self.assertTrue(data.title == "TK49 c10_SANS")
        self.assertTrue(data.x.size == 138)
        self.assertTrue(len(data.meta_data) == 3)
        self.assertTrue(data.detector[0].distance_unit == "mm")
        self.assertTrue(data.detector[1].distance_unit == "mm")
        self.assertTrue(data.detector[0].name == "HAB")
        self.assertTrue(data.detector[1].name == "main-detector-bank")
        self.assertTrue(data.detector[0].distance == 575.0)
        self.assertAlmostEqual(data.detector[1].distance, 4145.02)
        self.assertTrue(data.process[0].name == "Mantid generated CanSAS1D XML")
        self.assertTrue(data.meta_data["xmlpreprocess"] is not None)

    def _check_data_1_1(self, data):
        spectrum = data.trans_spectrum[0]
        self.assertTrue(len(spectrum.wavelength) == 138)

    def test_cansas_xml(self):
        xmlreader = XMLreader(self.isis_1_1, self.schema_1_1)
        valid = xmlreader.validate_xml()
        xmlreader.set_processing_instructions()
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
            reader_generic.save(self.write_1_1_filename, dataloader[i], None)
            reader2 = Loader()
            self.assertTrue(os.path.isfile(self.write_1_1_filename))
            return_data = reader2.load(self.write_1_1_filename)
            written_data = return_data[0]
            self._check_data(written_data)
        if os.path.isfile(self.write_1_1_filename):
            os.remove(self.write_1_1_filename)

    def test_double_trans_spectra(self):
        xmlreader = XMLreader(self.isis_1_1_doubletrans, self.schema_1_1)
        self.assertTrue(xmlreader.validate_xml())
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
        reader1 = XMLreader(self.xml_valid, self.schema_1_0)
        self.assertTrue(reader1.validate_xml())
        reader2 = XMLreader(self.xml_invalid, self.schema_1_0)
        self.assertFalse(reader2.validate_xml())
        reader3 = XMLreader(self.xml_valid, self.schema_1_1)
        self.assertFalse(reader3.validate_xml())
        reader4 = XMLreader(self.xml_invalid, self.schema_1_1)
        self.assertFalse(reader4.validate_xml())
        reader5 = XMLreader(self.isis_1_0, self.schema_1_0)
        self.assertTrue(reader5.validate_xml())
        reader6 = XMLreader(self.isis_1_1, self.schema_1_1)
        self.assertTrue(reader6.validate_xml())
        reader7 = XMLreader(self.isis_1_1, self.schema_1_0)
        self.assertFalse(reader7.validate_xml())

    def test_invalid_cansas(self):
        list = self.loader.load(self.cansas1d_notitle)
        data = list[0]
        self.assertTrue(data.x.size == 2)
        self.assertTrue(len(data.meta_data) == 2)
        self.assertTrue(len(data.errors) == 1)
        self.assertTrue(data.detector[0].distance_unit == "mm")
        self.assertTrue(data.detector[0].name == "fictional hybrid")
        self.assertTrue(data.detector[0].distance == 4150)

    def test_old_cansas_files(self):
        reader1 = XMLreader(self.cansas1d, self.schema_1_0)
        self.assertTrue(reader1.validate_xml())
        file_loader = Loader()
        file_loader.load(self.cansas1d)
        reader2 = XMLreader(self.cansas1d_units, self.schema_1_0)
        self.assertTrue(reader2.validate_xml())
        reader3 = XMLreader(self.cansas1d_badunits, self.schema_1_0)
        self.assertTrue(reader3.validate_xml())
        reader4 = XMLreader(self.cansas1d_slit, self.schema_1_0)
        self.assertTrue(reader4.validate_xml())

    def test_save_cansas_v1_0(self):
        xmlreader = XMLreader(self.isis_1_0, self.schema_1_0)
        valid = xmlreader.validate_xml()
        self.assertTrue(valid)
        reader_generic = Loader()
        dataloader = reader_generic.load(self.isis_1_0)
        reader_cansas = Reader()
        cansasreader = reader_cansas.read(self.isis_1_0)
        for i in range(len(dataloader)):
            self._check_data(dataloader[i])
            self._check_data(cansasreader[i])
            reader_generic.save(self.write_1_0_filename, dataloader[i], None)
            reader2 = Reader()
            self.assertTrue(os.path.isfile(self.write_1_0_filename))
            return_data = reader2.read(self.write_1_0_filename)
            written_data = return_data[0]
            XMLreader(self.write_1_0_filename, self.schema_1_0)
            valid = xmlreader.validate_xml()
            self.assertTrue(valid)
            self._check_data(written_data)
        if os.path.isfile(self.write_1_0_filename):
            os.remove(self.write_1_0_filename)

    def test_processing_instructions(self):
        reader = XMLreader(self.isis_1_1, self.schema_1_1)
        valid = reader.validate_xml()
        if valid:
            # find the processing instructions and make into a dictionary
            dic = self.get_processing_instructions(reader)
            self.assertEqual(dic, {'xml-stylesheet':
                                   'type="text/xsl" href="cansas1d.xsl" '})

            xml = "<test><a><b><c></c></b></a></test>"
            xmldoc = minidom.parseString(xml)

            # take the processing instructions and put them back in
            xmldoc = self.set_processing_instructions(xmldoc, dic)
            xmldoc.toprettyxml()

    def set_processing_instructions(self, minidom_object, dic):
        xmlroot = minidom_object.firstChild
        for item in dic:
            pi = minidom_object.createProcessingInstruction(item, dic[item])
            minidom_object.insertBefore(pi, xmlroot)
        return minidom_object

    def get_processing_instructions(self, xml_reader_object):
        dict = {}
        pi = xml_reader_object.xmlroot.getprevious()
        i = 0
        while pi is not None:
            attr = {}
            pi_name = ""
            pi_string = decode(etree.tostring(pi))
            if isinstance(pi_string, str):
                pi_string = pi_string.replace("<?", "").replace("?>", "")
                split = pi_string.split(" ", 1)
                pi_name = split[0]
                attr = split[1]
            dict[pi_name] = attr
            pi = pi.getprevious()
        return dict


class cansas_reader_hdf5(unittest.TestCase):

    def setUp(self):
        self.loader = Loader()
        self.datafile_basic = "simpleexamplefile.h5"
        self.datafile_multiplesasentry = "cansas_1Dand2D_samedatafile.h5"
        self.datafile_multiplesasdata = "cansas_1Dand2D_samesasentry.h5"
        self.datafile_multiplesasdata_multiplesasentry = "cansas_1Dand2D_multiplesasentry_multiplesasdata.h5"

    def test_real_data(self):
        self.data = self.loader.load(self.datafile_basic)
        self._check_example_data(self.data[0])

    def test_multiple_sasentries(self):
        self.data = self.loader.load(self.datafile_multiplesasentry)
        self.assertTrue(len(self.data) == 2)
        self._check_multiple_data(self.data[0])
        self._check_multiple_data(self.data[1])
        self._check_1d_data(self.data[0])

    def _check_multiple_data(self, data):
        self.assertTrue(data.title == "MH4_5deg_16T_SLOW")
        self.assertTrue(data.run[0] == '33837')
        self.assertTrue(len(data.run) == 1)
        self.assertTrue(data.instrument == "SANS2D")
        self.assertTrue(data.source.radiation == "Spallation Neutron Source")
        self.assertTrue(len(data.detector) == 1)
        self.assertTrue(data.detector[0].name == "rear-detector")
        self.assertTrue(data.detector[0].distance == 4.385281)
        self.assertTrue(data.detector[0].distance_unit == 'm')
        self.assertTrue(len(data.trans_spectrum) == 1)

    def _check_1d_data(self, data):
        self.assertTrue(isinstance(data, Data1D))
        self.assertTrue(len(data.x) == 66)
        self.assertTrue(len(data.x) == len(data.y))
        self.assertTrue(data.dy[10] == 0.20721350111248701)
        self.assertTrue(data.y[10] == 24.193889608153476)
        self.assertTrue(data.x[10] == 0.008981127988654792)

    def _check_2d_data(self, data):
        self.assertTrue(isinstance(data, Data2D))
        self.assertTrue(len(data.x) == 66)
        self.assertTrue(len(data.x) == len(data.y))
        self.assertTrue(data.dy[10] == 0.20721350111248701)
        self.assertTrue(data.y[10] == 24.193889608153476)
        self.assertTrue(data.x[10] == 0.008981127988654792)

    def _check_example_data(self, data):
        self.assertTrue(data.title == "")
        self.assertTrue(data.x.size == 100)
        self.assertTrue(data._xunit == "A^{-1}")
        self.assertTrue(data._yunit == "cm^{-1}")
        self.assertTrue(data.y.size == 100)
        self.assertAlmostEqual(data.y[40], 0.952749011516985)
        self.assertAlmostEqual(data.x[40], 0.3834415188257777)
        self.assertAlmostEqual(len(data.meta_data), 0)


if __name__ == '__main__':
    unittest.main()
