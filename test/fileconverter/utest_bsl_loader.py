import os
import os.path
import unittest

from xml.etree import ElementTree as ET
import numpy as np

from sas.sascalc.file_converter.bsl_loader import BSLLoader

def find(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)

class bsl_test(unittest.TestCase):

    def setUp(self):
        self.read_file_q = find("Z83000.QAX")
        self.read_file_i = find("Z83000.I1D")

        self.q_reader = BSLLoader(self.read_file_q)
        self.i_reader = BSLLoader(self.read_file_i)

    def test_load(self):
        #Load the data from bsl files.
        q_data_load = self.q_reader.load_data(0)
        i_data_load = self.i_reader.load_data(0)

        #Load the correct data (in Z83000.xml)

        tree = ET.parse(find('Z83000.xml'))
        root = tree.getroot()

        q_data_correct = [elem.text for elem in root.iter('{cansas1d/1.0}Q')]
        i_data_correct = [elem.text for elem in root.iter('{cansas1d/1.0}I')]

        q_data_array = np.array(q_data_correct, dtype=np.float64)
        i_data_array = np.array(i_data_correct, dtype=np.float64)

        q_test = np.allclose(q_data_array, q_data_load, atol=1e-13)
        q_test = np.allclose(i_data_array, i_data_load, atol=1e-13)

        self.assertTrue(q_test)
