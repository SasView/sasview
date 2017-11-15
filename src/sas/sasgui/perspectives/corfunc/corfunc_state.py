import time
import sys
import os
import logging
import sas.sascalc.dataloader
from lxml import etree
from sas.sascalc.dataloader.readers.cansas_reader import Reader as CansasReader
from sas.sascalc.dataloader.readers.cansas_reader import get_content
from sas.sasgui.guiframe.utils import format_number
from sas.sasgui.guiframe.gui_style import GUIFRAME_ID
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sascalc.dataloader.data_info import Data1D as LoaderData1D
from sas.sascalc.dataloader.loader import Loader

logger = logging.getLogger(__name__)

CORNODE_NAME = 'corfunc'
CANSAS_NS = 'cansas1d/1.0'

# The default state
DEFAULT_STATE = {
    'qmin_tcl': None,
    'qmax1_tcl': None,
    'qmax2_tcl': None,
    'background_tcl': None
}

# List of output parameters, used by __str__
output_list = [
    ['max', "Long Period / 2 (A): "],
    ['Lc', "Average Hard Block Thickness (A): "],
    ['dtr', "Average Interface Thickness (A): "],
    ['d0', "Average Core Thickness: "],
    ['A', "PolyDispersity: "],
    ['fill', "Filling Fraction: "]
]

class CorfuncState(object):
    """
    Stores information about the state of CorfuncPanel
    """

    def __init__(self):
        # Inputs
        self.file = None
        self.data = None
        self.qmin = None
        self.qmax = [0, 0]
        self.background = None
        self.outputs = {}
        self.is_extrapolated = False
        self.transform_type = 'fourier'
        self.is_transformed = False

        self.saved_state = DEFAULT_STATE
        self.timestamp = time.time()

        # Raw Data
        self.q = None
        self.iq = None

    def __str__(self):
        """
        Pretty print the state

        :return: A string representing the state
        """
        state = "File:         {}\n".format(self.file)
        state += "Timestamp:    {}\n".format(self.timestamp)
        state += "Qmin:         {}\n".format(str(self.qmin))
        state += "Qmax:         {}\n".format(str(self.qmax))
        state += "Background:   {}\n".format(str(self.background))

        if self.outputs != {} and self.outputs is not None:
            state += "\nOutputs:\n"
            for key, value in self.outputs.items():
                name = output_list[key][1]
                state += "{}: {}\n".format(name, str(value))

        return state

    def set_saved_state(self, name, value):
        """
        Set a value in the current state.

        :param name: The name of the parameter to set
        :param value: The value to set the parameter to
        """
        self.saved_state[name] = value
        if name == 'qmin_tcl':
            self.qmin = value
        elif name == 'qmax1_tcl':
            self.qmax[0] = value
        elif name == 'qmax2_tcl':
            self.qmax[1] = value
        elif name == 'background_tcl':
            self.background = value

    def toXML(self, filename='corfunc_state.crf', doc=None, entry_node=None):
        """
        Writes the state of the CorfuncPanel panel to file, as XML.

        Compatible with standalone writing, or appending to an
        already existing XML document. In that case, the XML document
        is required. An optional entry node in the XML document
        may also be given.

        :param file: file to write to
        :param doc: XML document object [optional]
        :param entry_node: XML node within the XML document at which
            we will append the data [optional]

        :return: None if no doc is provided, modified XML document if doc!=None
        """
        from xml.dom.minidom import getDOMImplementation

        top_element = None
        new_doc = None
        if doc is None:
            # Create a new XML document
            impl = getDOMImplementation()
            doc_type = impl.createDocumentType(CORNODE_NAME, "1.0", "1.0")
            new_doc = impl.createDocument(None, CORNODE_NAME, doc_type)
            top_element = new_doc.documentElement
        else:
            # Create a new element in the document provided
            top_element = doc.createElement(CORNODE_NAME)
            if entry_node is None:
                doc.documentElement.appendChild(top_element)
            else:
                entry_node.appendChild(top_element)
            new_doc = doc

        # Version
        attr = new_doc.createAttribute("version")
        attr.nodeValue = '1.0'
        top_element.setAttributeNode(attr)

        # Filename
        element = new_doc.createElement("filename")
        if self.file is not None and self.file != '':
            element.appendChild(new_doc.createTextNode(str(self.file)))
        else:
            element.appendChild(new_doc.createTextNode(str(filename)))
        top_element.appendChild(element)

        # Timestamp
        element = new_doc.createElement("timestamp")
        # Pretty printed format
        element.appendChild(new_doc.createTextNode(time.ctime(self.timestamp)))
        attr = new_doc.createAttribute("epoch")
        # Epoch value (used in self.fromXML)
        attr.nodeValue = str(self.timestamp)
        element.setAttributeNode(attr)
        top_element.appendChild(element)

        # Current state
        state = new_doc.createElement("state")
        top_element.appendChild(state)
        for name, value in self.saved_state.items():
            element = new_doc.createElement(name)
            element.appendChild(new_doc.createTextNode(str(value)))
            state.appendChild(element)

        # Whether or not the extrapolate & transform buttons have been clicked
        element = new_doc.createElement("is_extrapolated")
        top_element.appendChild(element)
        element.appendChild(new_doc.createTextNode(str(int(self.is_extrapolated))))

        element = new_doc.createElement("is_transformed")
        top_element.appendChild(element)
        element.appendChild(new_doc.createTextNode(str(int(self.is_transformed))))

        if self.is_transformed:
            element = new_doc.createElement("transform_type")
            top_element.appendChild(element)
            element.appendChild(new_doc.createTextNode(self.transform_type))

        # Output parameters
        if self.outputs != {} and self.outputs is not None:
            output = new_doc.createElement("output")
            top_element.appendChild(output)
            for key, value in self.outputs.items():
                element = new_doc.createElement(key)
                element.appendChild(new_doc.createTextNode(str(value)))
                output.appendChild(element)

        # Save the file or return the original document with the state
        # data appended
        if doc is None:
            fd = open(filename, 'w')
            fd.write(new_doc.toprettyxml())
            fd.close()
            return None
        else:
            return new_doc


    def fromXML(self, node):
        """
        Load corfunc states from a file

        :param node: node of an XML document to read from (optional)
        """
        if node.get('version') and node.get('version') == '1.0':
            # Parse filename
            entry = get_content('ns:filename', node)
            if entry is not None:
                self.file = entry.text.strip()

            # Parse timestamp
            entry = get_content('ns:timestamp', node)
            if entry is not None and entry.get('epoch'):
                try:
                    self.timestamp = (entry.get('epoch'))
                except:
                    msg = ("CorfuncState.fromXML: Could not read timestamp",
                        "\n{}").format(sys.exc_info()[1])
                    logger.error(msg)

            # Parse current state
            entry = get_content('ns:state', node)
            if entry is not None:
                for item in DEFAULT_STATE.keys():
                    input_field = get_content("ns:{}".format(item), entry)
                    if input_field is not None:
                        try:
                            value = float(input_field.text.strip())
                        except:
                            value = None
                        self.set_saved_state(name=item, value=value)

            # Parse is_extrapolated and is_transformed
            entry = get_content('ns:is_extrapolated', node)
            if entry is not None:
                self.is_extrapolated = bool(int(entry.text.strip()))
            entry = get_content('ns:is_transformed', node)
            if entry is not None:
                self.is_transformed = bool(int(entry.text.strip()))
                entry = get_content('ns:transform_type', node)
                self.transform_type = entry.text.strip()

            # Parse outputs
            entry = get_content('ns:output', node)
            if entry is not None:
                for item in output_list:
                    parameter = get_content("ns:{}".format(item[0]), entry)
                    if parameter is not None:
                        self.outputs[item[0]] = float(parameter.text.strip())



class Reader(CansasReader):
    """
    Reads a CanSAS file containing the state of a CorfuncPanel
    """

    type_name = "Corfunc"

    type = ["Corfunc file (*.crf)|*.crf",
            "SASView file (*.svs)|*.svs"]

    ext = ['.crf', '.CRF', '.svs', '.SVS']

    def __init__(self, callback):
        self.callback = callback
        self.state = None

    def read(self, path):
        """
        Load data and corfunc information frmo a CanSAS file.

        :param path: The file path to read from
        :return: Data1D object, a list of Data1D objects, or None
        :raise IOError: When the file can't be found
        :raise IOError: When the file is an invalid file type
        :raise ValueError: When the length of the data vectors are inconsistent
        """
        output = []
        if os.path.isfile(path):
            # Load file
            basename = os.path.basename(path)
            root, ext = os.path.splitext(basename)
            if not ext.lower() in self.ext:
                raise IOError("{} is not a supported file type".format(ext))
            tree = etree.parse(path, parser=etree.ETCompatXMLParser())
            root = tree.getroot()
            entry_list = root.xpath('/ns:SASroot/ns:SASentry',
                namespaces={'ns': CANSAS_NS})
            for entry in entry_list:
                corstate = self._parse_state(entry)

                if corstate is not None:
                    sas_entry, _ = self._parse_entry(entry)
                    sas_entry.meta_data['corstate'] = corstate
                    sas_entry.filename = corstate.file
                    output.append(sas_entry)
        else:
            # File not found
            msg = "{} is not a valid file path or doesn't exist".format(path)
            raise IOError(msg)

        if len(output) == 0:
            return None
        elif len(output) == 1:
            self.callback(output[0].meta_data['corstate'], datainfo=output[0])
            return output[0]
        else:
            return output

    def write(self, filename, datainfo=None, state=None):
        """
        Write the content of a Data1D as a CanSAS file.

        : param filename: Name of the file to write
        : param datainfo: Data1D object
        : param state: CorfuncState object
        """
        # Prepare datainfo
        if datainfo is None:
            datainfo = Data1D(x=[], y=[])
        elif not (isinstance(datainfo, Data1D) or isinstance(datainfo, LoaderData1D)):
            msg = ("The CanSAS writer expects a Data1D instance. {} was "
                "provided").format(datainfo.__class__.__name__)
            raise RuntimeError(msg)
        if datainfo.title is None or datainfo.title == '':
            datainfo.title = datainfo.name
        if datainfo.run_name is None or datainfo.run_name == '':
            datainfo.run = [str(datainfo.name)]
            datainfo.run_name[0] = datainfo.name

        # Create the XMl doc
        doc, sasentry = self._to_xml_doc(datainfo)
        if state is not None:
            doc = state.toXML(doc=doc, entry_node=sasentry)

        # Write the XML doc to a file
        fd = open(filename, 'w')
        fd.write(doc.toprettyxml())
        fd.close()

    def get_state(self):
        return self.state


    def _parse_state(self, entry):
        """
        Read state data from an XML node

        :param entry: The XML node to read from
        :return: CorfuncState object
        """
        state = None
        try:
            nodes = entry.xpath('ns:{}'.format(CORNODE_NAME),
                namespaces={'ns': CANSAS_NS})
            if nodes != []:
                state = CorfuncState()
                state.fromXML(nodes[0])
        except:
            msg = "XML document does not contain CorfuncState information\n{}"
            msg.format(sys.exc_info()[1])
            logger.info(msg)
        return state
