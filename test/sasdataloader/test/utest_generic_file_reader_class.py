"""
    Unit tests for the generic file reader class
"""

import os
import unittest
import logging
import numpy as np

from sas.sascalc.dataloader.data_info import DataInfo, plottable_1D
from sas.sascalc.dataloader.loader import Loader
from sas.sascalc.dataloader.file_reader_base_class import FileReader

logger = logging.getLogger(__name__)


def find(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class GenericFileReaderTests(unittest.TestCase):

    def setUp(self):
        self.reader = TestFileReader()
        self.bad_file = find("ACB123.txt")
        self.good_file = find("123ABC.txt")
        self.generic_reader = Loader()
        self.deprecated_file_type = find("FEB18012.ASC")

    def test_bad_file_path(self):
        output = self.reader.read(self.bad_file)
        self.assertEqual(output, [])

    def test_good_file_path(self):
        f = open(self.good_file, 'w')
        f.write('123ABC exists!')
        f.close()
        output = self.reader.read(self.good_file)
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0].meta_data["blah"], '123ABC exists!')

    def test_old_file_types(self):
        f = self.generic_reader.load(self.deprecated_file_type)
        last_f = f[0]
        if hasattr(last_f, "errors"):
            self.assertEquals(len(last_f.errors), 1)
        else:
            self.fail("Errors did not propogate to the file properly.")

    def tearDown(self):
        if os.path.isfile(self.bad_file):
            os.remove(self.bad_file)
        if os.path.isfile(self.good_file):
            os.remove(self.good_file)

class TestFileReader(FileReader):
    def get_file_contents(self):
        """
        Reader specific class to access the contents of the file
        All reader classes that inherit from FileReader must implement
        """
        x = np.zeros(0)
        y = np.zeros(0)
        self.current_dataset = plottable_1D(x,y)
        self.current_datainfo = DataInfo()
        self.current_datainfo.meta_data["blah"] = self.nextline()
        self.send_to_output()
