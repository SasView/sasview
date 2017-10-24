"""
    Unit tests for the generic file reader class
"""

import os
import unittest
import logging
import numpy as np

from sas.sascalc.dataloader.data_info import DataInfo, plottable_1D
from sas.sascalc.dataloader.file_reader_base_class import FileReader

logger = logging.getLogger(__name__)


class GenericFileReaderTests(unittest.TestCase):

    def setUp(self):
        self.reader = FileReader()
        self.bad_file = "ACB123.txt"
        self.good_file = "123ABC.txt"
        self.msg = "Unable to find file at: {}\n".format(self.bad_file)
        self.msg += "Please check your file path and try again."
        x = np.zeros(0)
        y = np.zeros(0)
        self.reader.current_dataset = plottable_1D(x, y)
        self.reader.current_datainfo = DataInfo()
        self.reader.send_to_output()

    def test_bad_file_path(self):
        output = self.reader.read(self.bad_file)
        self.assertEqual(len(output[0].errors), 1)
        self.assertEqual(output[0].errors[0], self.msg)

    def test_good_file_path(self):
        f_open = open(self.good_file, 'w')
        f_open.close()
        output = self.reader.read(self.good_file)
        self.assertEqual(len(output[0].errors), 1)
        self.assertEqual(output[0].errors[0], self.msg)

    def tearDown(self):
        if os.path.isfile(self.bad_file):
            os.remove(self.bad_file)
        if os.path.isfile(self.good_file):
            os.remove(self.good_file)
