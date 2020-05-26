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

from sas.sascalc.dataloader.file_reader_base_class import decode
from sas.sascalc.dataloader.loader import Loader
from sas.sascalc.dataloader.data_info import Data1D, Data2D
from sas.sascalc.dataloader.readers.xml_reader import XMLreader
from sas.sascalc.dataloader.readers.cansas_reader import Reader

logger = logging.getLogger(__name__)

warnings.simplefilter("ignore")


def find(filename):
    return os.path.join(os.path.dirname(__file__), 'test_data', filename)


class cansas_reader_xml(unittest.TestCase):

    def setUp(self):
        self.loader = Loader()
        self.reader = Reader()
        self.xml_valid = find("cansas_test_modified.xml")
        self.xml_invalid = find("cansas_test.xml")
        self.cansas1d_badunits = find("cansas1d_badunits.xml")
        self.cansas1d = find("cansas1d.xml")
        self.cansas1d_slit = find("cansas1d_slit.xml")
        self.cansas1d_units = find("cansas1d_units.xml")
        self.cansas1d_notitle = find("cansas1d_notitle.xml")
        self.cansas1d_multiple_entries = find("latex_smeared.xml")
        self.isis_1_0 = find("ISIS_1_0.xml")
        self.isis_1_1 = find("ISIS_1_1.xml")
        self.isis_1_1_notrans = find("ISIS_1_1_notrans.xml")
        self.isis_1_1_doubletrans = find("ISIS_1_1_doubletrans.xml")
        self.schema_1_0 = find("cansas1d_v1_0.xsd")
        self.schema_1_1 = find("cansas1d_v1_1.xsd")
        self.write_1_0_filename = find("isis_1_0_write_test.xml")
        self.write_1_1_filename = find("isis_1_1_write_test.xml")
        self.write_filename = find("write_test.xml")

    def test_generic_loader(self):
        # the generic loader should work as well
        data = self.loader.load(self.cansas1d)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].meta_data['loader'], "CanSAS XML 1D")

    def test_cansas_checkdata(self):
        self.data_list = self.loader.load(self.cansas1d)
        self.data = self.data_list[0]
        self.assertEqual(os.path.basename(self.data.filename), "cansas1d.xml")
        self._checkdata()

    def _checkdata(self):
        """
            Check the data content to see whether
            it matches the specific file we loaded.
            Check the units too to see whether the
            Data1D defaults changed. Otherwise the
            tests won't pass
        """
        self.assertEqual(len(self.data_list), 1)
        self.assertEqual(self.data.run[0], "1234")
        self.assertEqual(self.data.meta_data['loader'], "CanSAS XML 1D")

        # Data
        self.assertEqual(len(self.data.x), 2)
        self.assertEqual(self.data._xunit, 'A^{-1}')
        self.assertEqual(self.data._yunit, 'cm^{-1}')
        self.assertEqual(self.data.x_unit, self.data.x_loaded_unit)
        self.assertEqual(self.data.y_unit, self.data.y_loaded_unit)
        self.assertAlmostEqual(self.data.x[0], 0.02, 6)
        self.assertAlmostEqual(self.data.y[0], 1000, 6)
        self.assertAlmostEqual(self.data.dx[0], 0.01, 6)
        self.assertAlmostEqual(self.data.dy[0], 3, 6)
        self.assertAlmostEqual(self.data.x[1], 0.03, 6)
        self.assertAlmostEqual(self.data.y[1], 1001.0)
        self.assertAlmostEqual(self.data.dx[1], 0.02, 6)
        self.assertAlmostEqual(self.data.dy[1], 4, 6)
        self.assertEqual(self.data.run_name['1234'], 'run name')
        self.assertEqual(self.data.title, "Test title")

        # Sample info
        self.assertEqual(self.data.sample.ID, "SI600-new-long")
        self.assertEqual(self.data.sample.name, "my sample")
        self.assertTrue(self.data.sample.thickness_unit in ['mm', 'cm', 'm'])
        self.assertTrue(self.data.sample.thickness in [1.03, 0.00103])

        self.assertAlmostEqual(self.data.sample.transmission, 0.327)

        self.assertEqual(self.data.sample.temperature_unit, 'C')
        self.assertEqual(self.data.sample.temperature, 0)

        self.assertEqual(self.data.sample.position_unit, 'mm')
        self.assertTrue(self.data.sample.position.x, [10, 0.10])
        self.assertEqual(self.data.sample.position.y, 0)

        self.assertTrue(self.data.sample.orientation_unit in ['degree', 'rad'])

        self.assertEqual(self.data.sample.details[0],
                         "http://chemtools.chem.soton.ac.uk/projects/blog/blogs.php/bit_id/2720")
        self.assertEqual(self.data.sample.details[1], "Some text here")

        # Instrument info
        self.assertEqual(self.data.instrument, "canSAS instrument")

        # Source
        self.assertEqual(self.data.source.radiation, "neutron")

        self.assertEqual(self.data.source.beam_size_name, "bm")
        self.assertTrue(self.data.source.beam_size.x in [12, 0.012])
        self.assertEqual(self.data.source.beam_shape, "disc")

        self.assertTrue(self.data.source.wavelength_unit in ['A', 'nm'])
        self.assertTrue(self.data.source.wavelength in [6, 0.6])
        self.assertTrue(self.data.source.wavelength_max_unit in ['A', 'nm'])
        self.assertTrue(self.data.source.wavelength_max in [10, 1.0])
        self.assertTrue(self.data.source.wavelength_min_unit in ['A', 'nm'])
        self.assertTrue(self.data.source.wavelength_min in [2.2, 0.22])
        self.assertEqual(self.data.source.wavelength_spread_unit, "percent")
        self.assertEqual(self.data.source.wavelength_spread, 14.3)

        # Collimation
        _found1 = False
        _found2 = False
        self.assertTrue(self.data.collimation[0].length in [123., 0.123])
        self.assertEqual(self.data.collimation[0].name, 'test coll name')
        self.assertEqual(len(self.data.collimation[0].aperture), 2)

        for item in self.data.collimation[0].aperture:
            self.assertEqual(item.size_unit, 'mm')
            self.assertTrue(item.distance_unit in ['mm', 'cm', 'm'])

            if item.name == 'source' and item.type == 'radius':
                _found1 = True
            elif item.name == 'sample' and item.type == 'radius':
                _found2 = True

        if not _found1 or not _found2:
            raise RuntimeError("Could not find all data %s %s"
                               % (_found1, _found2))

        # Detector
        self.assertEqual(self.data.detector[0].name, "fictional hybrid")
        self.assertTrue(self.data.detector[0].distance_unit in ["mm", 'm'])
        self.assertTrue(self.data.detector[0].distance in [4150, 4.150])

        self.assertEqual(self.data.detector[0].orientation.y, 0.0)
        self.assertEqual(self.data.detector[0].orientation.z, 0.0)

        self.assertTrue(self.data.detector[0].offset_unit in ['micron', 'mm'])
        self.assertTrue(self.data.detector[0].offset.x in [1000000.0, 1.0])
        self.assertTrue(self.data.detector[0].offset.y in [2000.0, 2.0])
        self.assertEqual(self.data.detector[0].offset.z, None)

        self.assertTrue(self.data.detector[0].beam_center_unit in ['m', "mm"])
        self.assertTrue(self.data.detector[0].beam_center.x in [322.64, 0.32264])
        self.assertTrue(self.data.detector[0].beam_center.y in [327.68, 0.32768])
        self.assertEqual(self.data.detector[0].beam_center.z, None)

        self.assertTrue(self.data.detector[0].pixel_size_unit in ['mm', 'cm'])
        self.assertTrue(self.data.detector[0].pixel_size.x in [5, 0.5])
        self.assertTrue(self.data.detector[0].pixel_size.y in [5, 0.5])
        self.assertEqual(self.data.detector[0].pixel_size.z, None)

        # Process
        _found_term1 = False
        _found_term2 = False
        for item in self.data.process:
            self.assertTrue(item.name in ['NCNR-IGOR', 'spol'])
            self.assertTrue(item.date in ['04-Sep-2007 18:35:02',
                                          '03-SEP-2006 11:42:47'])
            for t in item.term:
                if (t['name'] == "ABS:DSTAND"
                        and t['unit'] == 'mm'
                        and float(t['value']) == 1.0):
                    _found_term2 = True
                elif (t['name'] == "radialstep"
                      and t['unit'] == 'mm'
                      and float(t['value']) == 10.0):
                    _found_term1 = True

        if not _found_term1 or not _found_term2:
            raise RuntimeError("Could not find all process terms %s %s"
                               % (_found_term1, _found_term2))

    def test_writer(self):
        data = self.reader.read(self.cansas1d)
        self.reader.write(self.write_filename, data[0])
        self.data_list = self.loader.load(self.write_filename)
        self.data = self.data_list[0]
        self.assertEqual(self.data.filename,
                         self.write_filename.split('\\')[-1])
        self._checkdata()
        if os.path.isfile(self.write_filename):
            os.remove(self.write_filename)

    def test_multiple_sasentries(self):
        self.data_list = self.loader.load(self.cansas1d_multiple_entries)
        self.assertTrue(len(self.data_list) == 2)

    def test_units(self):
        """
            Check units.
            Note that not all units are available.
        """
        self.data_list = self.reader.read(self.cansas1d_units)
        self.data = self.data_list[0]
        self.assertEqual(self.data.x_loaded_unit, 'nm^{-1}')
        self.assertEqual(self.data.y_loaded_unit, 'nm^{-1}')
        self.data.convert_q_units('1/A')
        self.data.convert_i_units('1/cm')
        self.assertEqual(self.data.filename,
                         self.cansas1d_units.split('\\')[-1])
        self._checkdata()

    def test_badunits(self):
        """
            Check units.
            Note that not all units are available.
        """
        self.data_list = self.reader.read(self.cansas1d_badunits)
        self.data = self.data_list[0]
        self.assertEqual(len(self.data_list), 1)
        self.assertEqual(self.data.filename,
                         self.cansas1d_badunits.split('\\')[-1])
        # The followed should not have been loaded
        self.assertAlmostEqual(self.data.sample.thickness, 0.00103)
        # This one should
        self.assertAlmostEqual(self.data.sample.transmission, 0.327)

        self.assertEqual(self.data.meta_data['loader'], "CanSAS XML 1D")
        self.assertEqual(len(self.data.errors), 0)

    def test_slits(self):
        """
            Check slit data
        """
        self.data_list = self.reader.read(self.cansas1d_slit)
        self.data = self.data_list[0]
        self.assertEqual(len(self.data_list), 1)
        self.assertEqual(self.data.filename, self.cansas1d_slit.split('\\')[-1])
        self.assertEqual(self.data.run[0], "1234")

        # Data
        self.assertEqual(len(self.data.x), 2)
        self.assertEqual(self.data.x_unit, 'A^{-1}')
        self.assertEqual(self.data.y_unit, 'cm^{-1}')
        self.assertEqual(self.data.x[0], 0.02)
        self.assertEqual(self.data.y[0], 1000)
        self.assertEqual(self.data.dxl[0], 0.005)
        self.assertEqual(self.data.dxw[0], 0.001)
        self.assertEqual(self.data.dy[0], 3)
        self.assertEqual(self.data.x[1], 0.03)
        self.assertAlmostEqual(self.data.y[1], 1001.0)
        self.assertEqual(self.data.dxl[1], 0.005)
        self.assertEqual(self.data.dxw[1], 0.001)
        self.assertEqual(self.data.dy[1], 4)
        self.assertEqual(self.data.run_name['1234'], 'run name')
        self.assertEqual(self.data.title, "Test title")

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
        self.assertTrue(valid)

    def _check_data(self, data):
        self.assertTrue(data.title == "TK49 c10_SANS")
        self.assertEqual(data.x.size, 138)
        self.assertEqual(len(data.meta_data), 3)
        self.assertTrue(data.detector[0].distance_unit == "m")
        self.assertTrue(data.detector[1].distance_unit == "m")
        self.assertTrue(data.detector[0].name == "HAB")
        self.assertTrue(data.detector[1].name == "main-detector-bank")
        self.assertAlmostEqual(data.detector[0].distance, 0.5750)
        self.assertAlmostEqual(data.detector[1].distance, 4.14502)
        self.assertTrue(data.process[0].name == "Mantid generated CanSAS1D XML")
        self.assertTrue(data.meta_data["xmlpreprocess"] is not None)

    def _check_data_1_1(self, data):
        spectrum = data.trans_spectrum[0]
        self.assertEqual(len(spectrum.wavelength), 138)
        self.assertEqual(len(spectrum.transmission), 138)
        self.assertEqual(len(spectrum.transmission_deviation), 138)

    def test_cansas_xml(self):
        xmlreader = XMLreader(self.isis_1_1, self.schema_1_1)
        valid = xmlreader.validate_xml()
        xmlreader.set_processing_instructions()
        self.assertTrue(valid)
        dataloader = self.loader.load(self.isis_1_1)
        cansasreader = self.reader.read(self.isis_1_1)
        for i in range(len(dataloader)):
            self._check_data(dataloader[i])
            self._check_data_1_1(dataloader[i])
            self._check_data(cansasreader[i])
            self._check_data_1_1(cansasreader[i])
            self.loader.save(self.write_1_1_filename, dataloader[i], None)
            reader2 = Loader()
            self.assertTrue(os.path.isfile(self.write_1_1_filename))
            return_data = reader2.load(self.write_1_1_filename)
            written_data = return_data[0]
            self._check_data(written_data)
            self._check_data_1_1(written_data)
        if os.path.isfile(self.write_1_1_filename):
            os.remove(self.write_1_1_filename)

    def test_double_trans_spectra(self):
        xmlreader = XMLreader(self.isis_1_1_doubletrans, self.schema_1_1)
        self.assertTrue(xmlreader.validate_xml())
        data = self.loader.load(self.isis_1_1_doubletrans)
        for item in data:
            self._check_data(item)

    def test_entry_name_recurse(self):
        test_values = [1, 2, 3, 4, 5, 6]
        base_key = "key"
        d = {}
        for value in test_values:
            new_key = self.get_number_of_entries(d, base_key, i=0)
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
        self.assertTrue(data.detector[0].distance_unit == "m")
        self.assertTrue(data.detector[0].name == "fictional hybrid")
        self.assertTrue(data.detector[0].distance == 4.150)

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
        self.assertTrue(xmlreader.validate_xml())
        dataloader = self.loader.load(self.isis_1_0)
        cansasreader = self.reader.read(self.isis_1_0)
        for i in range(len(dataloader)):
            self._check_data(dataloader[i])
            self._check_data(cansasreader[i])
            self.loader.save(self.write_1_0_filename, dataloader[i], None)
            reader2 = Reader()
            self.assertTrue(os.path.isfile(self.write_1_0_filename))
            return_data = reader2.read(self.write_1_0_filename)
            written_data = return_data[0]
            xmlreader = XMLreader(self.write_1_0_filename, self.schema_1_0)
            self.assertTrue(xmlreader.validate_xml())
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
        self.datafile_basic = find("simpleexamplefile.h5")
        self.datafile_nodi = find("x25000_no_di.h5")
        self.datafile_multiplesasentry = find(
            "nxcansas_1Dand2D_multisasentry.h5")
        self.datafile_multiplesasdata = find(
            "nxcansas_1Dand2D_multisasdata.h5")
        self.datafile_multiplesasdata_multiplesasentry = find(
            "nxcansas_1Dand2D_multisasentry_multisasdata.h5")
        self.datafile_multiple_frames = find("multiframe_1d.nxs")

    def test_real_data(self):
        self.data = self.loader.load(self.datafile_basic)
        self._check_example_data(self.data[0])

    def test_multi_frame_data(self):
        self.data = self.loader.load(self.datafile_multiple_frames)
        self.assertEqual(len(self.data), 120)
        for frame in self.data:
            self.assertTrue(isinstance(frame, Data1D))
            self.assertEqual(frame.run[0], 'BBAA_processed_180309_132658')
            self.assertEqual(frame.run[0], frame.title)
            self.assertEqual(len(frame.y), 1617)
            self.assertEqual(frame.y_loaded_unit, None)

    def test_no_di(self):
        self.data = self.loader.load(self.datafile_nodi)
        self.assertTrue(self.data is not None)
        self.assertTrue(len(self.data) == 1)
        dataset = self.data[0]
        self.assertTrue(dataset.err_data is None)
        self.assertTrue(dataset.q_data is not None)

    def test_multiple_sasentries(self):
        self.data = self.loader.load(self.datafile_multiplesasentry)
        self.assertTrue(len(self.data) == 2)
        self._check_multiple_data(self.data[0])
        self._check_multiple_data(self.data[1])
        if isinstance(self.data[0], Data1D):
            self._check_1d_data(self.data[0])
            self._check_2d_data(self.data[1])
        else:
            self._check_1d_data(self.data[1])
            self._check_2d_data(self.data[0])

    def test_multiple_sasdatas(self):
        self.data = self.loader.load(self.datafile_multiplesasdata)
        self.assertTrue(len(self.data) == 2)
        self._check_multiple_data(self.data[0])
        self._check_multiple_data(self.data[1])
        if isinstance(self.data[0], Data1D):
            self._check_1d_data(self.data[0])
            self._check_2d_data(self.data[1])
        else:
            self._check_1d_data(self.data[1])
            self._check_2d_data(self.data[0])

    def test_multiple_sasentries_multiplesasdatas(self):
        self.data = self.loader.load(
            self.datafile_multiplesasdata_multiplesasentry)
        self.assertTrue(len(self.data) == 4)
        self._check_multiple_data(self.data[0])
        self._check_multiple_data(self.data[1])
        self._check_multiple_data(self.data[2])
        self._check_multiple_data(self.data[3])
        for data in self.data:
            if isinstance(data, Data1D):
                self._check_1d_data(data)
            else:
                self._check_2d_data(data)

    def _check_multiple_data(self, data):
        self.assertEqual(data.title, "MH4_5deg_16T_SLOW")
        self.assertEqual(data.run[0], '33837')
        self.assertEqual(len(data.run), 1)
        self.assertEqual(data.instrument, "SANS2D")
        self.assertEqual(data.source.radiation, "Spallation Neutron Source")
        self.assertEqual(len(data.detector), 2)
        self.assertTrue(data.detector[0].name == "rear-detector"
                        or data.detector[1].name == "rear-detector")
        self.assertTrue(data.detector[0].name == "front-detector"
                        or data.detector[1].name == "front-detector")
        self.assertAlmostEqual(data.detector[0].distance +
                               data.detector[1].distance, 7230.54, 2)
        self.assertEqual(data.detector[0].distance_unit, 'mm')
        self.assertEqual(len(data.trans_spectrum), 1)

    def _check_1d_data(self, data):
        self.assertEqual(len(data.x), 66)
        self.assertEqual(len(data.x), len(data.y))
        self.assertAlmostEqual(data.dy[10], 0.207214)
        self.assertAlmostEqual(data.y[10], 24.1939)
        self.assertAlmostEqual(data.x[10], 0.00898113)

    def _check_2d_data(self, data):
        self.assertTrue(isinstance(data, Data2D))
        self.assertEqual(len(data.q_data), 150*150)
        self.assertEqual(len(data.q_data), len(data.data))
        self.assertAlmostEqual(data.err_data[10], 0.186723989418)
        self.assertAlmostEqual(data.data[10], 0.465181)
        self.assertAlmostEqual(data.qx_data[10], -0.129)
        self.assertAlmostEqual(data.qy_data[10], -0.149)

    def _check_example_data(self, data):
        self.assertEqual(data.title, "")
        self.assertEqual(data.x.size, 100)
        self.assertEqual(data._xunit, "A^{-1}")
        self.assertEqual(data._yunit, "cm^{-1}")
        self.assertEqual(data.y.size, 100)
        self.assertAlmostEqual(data.y[40], 0.952749011516985)
        self.assertAlmostEqual(data.x[40], 0.3834415188257777)
        self.assertAlmostEqual(len(data.meta_data), 0)


if __name__ == '__main__':
    unittest.main()
