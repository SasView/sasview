import sys
import os
import unittest
import numpy as np
from lxml import etree

import pytest

from unittest.mock import MagicMock, patch

from PyQt5 import QtWidgets

from sas.qtgui.Utilities.GuiUtils import Communicate
from sas.qtgui.Utilities.FileConverter import FileConverterWidget
import sasdata.file_converter.FileConverterUtilities as Utilities

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class dummy_manager(object):
    communicate = Communicate()
    _parent = QtWidgets.QDialog()

class FileConverterTest(unittest.TestCase):
    """ Test the simple FileConverter dialog """
    def setUp(self):
        """ Create FileConverter dialog """
        self.widget = FileConverterWidget(dummy_manager())

    def tearDown(self):
        """ Destroy the GUI """

        self.widget.close()
        self.widget = None

    def testDefaults(self):
        """ Test the GUI in its default state """

        assert isinstance(self.widget, QtWidgets.QDialog)

        # Default title
        assert self.widget.windowTitle() == "File Converter"

        # Modal window
        assert not self.widget.isModal()

        # Size policy
        assert self.widget.sizePolicy().Policy() == QtWidgets.QSizePolicy.Fixed

        assert self.widget.is1D
        assert not self.widget.isBSL
        assert self.widget.ifile == ''
        assert self.widget.qfile == ''
        assert self.widget.ofile == ''
        assert self.widget.metadata == {}


    def testOnHelp(self):
        """ Test the default help renderer """

        self.widget.parent.showHelp = MagicMock()
        self.widget.onHelp()
        assert self.widget.parent.showHelp.called_once()
     
    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testOnIFileOpen(self):
        """
        Testing intensity file read in.
        :return:
        """
        filename = os.path.join("UnitTesting", "FIT2D_I.TXT")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[filename, ''])
        self.widget.onIFileOpen()

        # check updated values in ui, read from loaded file
        assert self.widget.txtIFile.text() == 'FIT2D_I.TXT'
        assert self.widget.ifile == filename
        assert self.widget.cmdConvert

        iqdata = np.array([Utilities.extract_ascii_data(self.widget.ifile)])
        assert round(abs(iqdata[0][0]-224.08691), 5) == 0

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testOnQFileOpen(self):
        """
        Testing intensity file read in.
        :return:
        """
        filename = os.path.join("UnitTesting", "FIT2D_Q.TXT")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[filename, ''])
        self.widget.onQFileOpen()

        # check updated values in ui, read from loaded file
        assert self.widget.txtQFile.text() == 'FIT2D_Q.TXT'
        assert self.widget.qfile == filename
        assert self.widget.cmdConvert

        qdata = Utilities.extract_ascii_data(self.widget.qfile)
        assert round(abs(qdata[0]-0.13073), 5) == 0

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testOnConvert(self):
        """

        :return:
        """
        ifilename = os.path.join("UnitTesting", "FIT2D_I.TXT")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[ifilename, ''])
        self.widget.onIFileOpen()
        qfilename = os.path.join("UnitTesting", "FIT2D_Q.TXT")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[qfilename, ''])
        self.widget.onQFileOpen()

        assert not self.widget.isBSL
        assert self.widget.is1D

        ofilemame = os.path.join('UnitTesting', 'FIT2D_IQ.xml')
        self.widget.ofile = ofilemame

        self.widget.chkLoadFile.setChecked(False)
        self.widget.onConvert()

        test_metadata = self.widget.metadata
        assert test_metadata['title'] == ''
        assert test_metadata['run_name'] == {'': ''}
        assert test_metadata['instrument'] == ''
        assert test_metadata['detector'][0].name == '' #What is the reason to have it as array
        assert test_metadata['sample'].name == ''
        assert test_metadata['source'].name == ''

        tree = etree.parse(ofilemame, parser=etree.ETCompatXMLParser())

        def xml2dict(node):
            """
            Converts an lxml.etree to dict for a quick test of conversion results
            """
            result = {}
            for element in node.iterchildren():
                key = element.tag.split('}')[1] if '}' in element.tag else element.tag
                if element.text and element.text.strip():
                    value = element.text
                else:
                    value = xml2dict(element)
                result[key] = value
            return result

        xml_dict = xml2dict(tree.getroot())
        output_qdata = float(xml_dict['SASentry']['SASdata']['Idata']['Q'])
        output_idata = float(xml_dict['SASentry']['SASdata']['Idata']['I'])
        assert round(abs(output_qdata-0.86961), 5) == 0
        assert round(abs(output_idata-0.21477), 5) == 0
