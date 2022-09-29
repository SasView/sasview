import sys
import os
import numpy as np
from lxml import etree

import pytest

from unittest.mock import MagicMock, patch

from PyQt5 import QtWidgets

from sas.qtgui.Utilities.GuiUtils import Communicate
from sas.qtgui.Utilities.FileConverter import FileConverterWidget
import sasdata.file_converter.FileConverterUtilities as Utilities


class FileConverterTest:
    """ Test the simple FileConverter dialog """

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the FileConverter'''
        class dummy_manager(object):
            communicate = Communicate()
            _parent = QtWidgets.QDialog()

        w = FileConverterWidget(dummy_manager())
        yield w
        w.close()

    def testDefaults(self, widget):
        """ Test the GUI in its default state """

        assert isinstance(widget, QtWidgets.QDialog)

        # Default title
        assert widget.windowTitle() == "File Converter"

        # Modal window
        assert not widget.isModal()

        # Size policy
        assert widget.sizePolicy().Policy() == QtWidgets.QSizePolicy.Fixed

        assert widget.is1D
        assert not widget.isBSL
        assert widget.ifile == ''
        assert widget.qfile == ''
        assert widget.ofile == ''
        assert widget.metadata == {}


    def testOnHelp(self, widget):
        """ Test the default help renderer """

        widget.parent.showHelp = MagicMock()
        widget.onHelp()
        assert widget.parent.showHelp.called_once()
     
    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testOnIFileOpen(self, widget):
        """
        Testing intensity file read in.
        :return:
        """
        filename = os.path.join("UnitTesting", "FIT2D_I.TXT")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[filename, ''])
        widget.onIFileOpen()

        # check updated values in ui, read from loaded file
        assert widget.txtIFile.text() == 'FIT2D_I.TXT'
        assert widget.ifile == filename
        assert widget.cmdConvert

        iqdata = np.array([Utilities.extract_ascii_data(widget.ifile)])
        assert round(abs(iqdata[0][0]-224.08691), 5) == 0

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testOnQFileOpen(self, widget):
        """
        Testing intensity file read in.
        :return:
        """
        filename = os.path.join("UnitTesting", "FIT2D_Q.TXT")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[filename, ''])
        widget.onQFileOpen()

        # check updated values in ui, read from loaded file
        assert widget.txtQFile.text() == 'FIT2D_Q.TXT'
        assert widget.qfile == filename
        assert widget.cmdConvert

        qdata = Utilities.extract_ascii_data(widget.qfile)
        assert round(abs(qdata[0]-0.13073), 5) == 0

    @pytest.mark.xfail(reason="2022-09 already broken - input file issue")
    def testOnConvert(self, widget):
        """

        :return:
        """
        ifilename = os.path.join("UnitTesting", "FIT2D_I.TXT")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[ifilename, ''])
        widget.onIFileOpen()
        qfilename = os.path.join("UnitTesting", "FIT2D_Q.TXT")
        QtWidgets.QFileDialog.getOpenFileName = MagicMock(return_value=[qfilename, ''])
        widget.onQFileOpen()

        assert not widget.isBSL
        assert widget.is1D

        ofilemame = os.path.join('UnitTesting', 'FIT2D_IQ.xml')
        widget.ofile = ofilemame

        widget.chkLoadFile.setChecked(False)
        widget.onConvert()

        test_metadata = widget.metadata
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
