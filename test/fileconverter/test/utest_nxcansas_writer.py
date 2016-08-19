from sas.sascalc.file_converter.nxcansas_writer import NXcanSASWriter
from sas.sascalc.dataloader.readers.cansas_reader import Reader as XMLReader
from sas.sascalc.dataloader.readers.red2d_reader import Reader as DATReader
from sas.sascalc.dataloader.readers.cansas_reader_HDF5 import Reader as HDF5Reader

import os
import pylint
import unittest
import warnings

warnings.simplefilter("ignore")

class nxcansas_writer(unittest.TestCase):

    def setUp(self):
        self.writer = NXcanSASWriter()
        self.read_file_1d = "cansas1d.xml"
        self.write_file_1d = "export1d.h5"
        self.read_file_2d = "exp18_14_igor_2dqxqy.dat"
        self.write_file_2d = "export2d.h5"
        self.hdf5_reader = HDF5Reader()

        xml_reader = XMLReader()
        self.data_1d = xml_reader.read(self.read_file_1d)[0]

        dat_reader = DATReader()
        self.data_2d = dat_reader.read(self.read_file_2d)
        self.data_2d.detector[0].name = ''
        self.data_2d.source.radiation = 'neutron'

    def test_write_1d(self):
        self.writer.write([self.data_1d], self.write_file_1d)
        data = self.hdf5_reader.read(self.write_file_1d)
        self.assertTrue(len(data) == 1)
        data = data[0]
        self.assertTrue(len(data.x) == len(self.data_1d.x))
        self.assertTrue(len(data.y) == len(self.data_1d.y))
        self.assertTrue(len(data.dy) == len(self.data_1d.dy))
        self._check_metadata(data, self.data_1d)

    def test_write_2d(self):
        self.writer.write([self.data_2d], self.write_file_2d)
        data = self.hdf5_reader.read(self.write_file_2d)
        self.assertTrue(len(data) == 1)
        data = data[0]
        self.assertTrue(len(data.data) == len(self.data_2d.data))
        self.assertTrue(len(data.qx_data) == len(self.data_2d.qx_data))
        self.assertTrue(len(data.qy_data) == len(self.data_2d.qy_data))
        self._check_metadata(data, self.data_2d)

    def _check_metadata(self, written, correct):
        self.assertTrue(written.title == correct.title)
        self.assertTrue(written.sample.name == correct.sample.name)
        self.assertAlmostEqual(written.sample.thickness, correct.sample.thickness)
        self.assertAlmostEqual(written.sample.temperature, correct.sample.temperature)
        self.assertTrue(written.instrument == correct.instrument)
        self.assertTrue(len(written.detector) == len(correct.detector))
        for i in range(len(written.detector)):
            written_det = written.detector[i]
            correct_det = correct.detector[i]
            self.assertAlmostEqual(written_det.distance, correct_det.distance)
            self.assertTrue(written_det.name == correct_det.name)
        self.assertTrue(written.source.radiation == correct.source.radiation)

    def tearDown(self):
        if os.path.isfile(self.write_file_1d):
            os.remove(self.write_file_1d)
