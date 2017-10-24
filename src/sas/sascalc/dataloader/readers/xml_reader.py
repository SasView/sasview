"""
    Generic XML read and write utility

    Usage: Either extend xml_reader or add as a class variable.
"""
############################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#If you use DANSE applications to do scientific research that leads to
#publication, we ask that you acknowledge the use of the software with the
#following sentence:
#This work benefited from DANSE software developed under NSF award DMR-0520547.
#copyright 2008,2009 University of Tennessee
#############################################################################

import logging

from lxml import etree
from lxml.builder import E

from ..file_reader_base_class import FileReader, decode

logger = logging.getLogger(__name__)

PARSER = etree.ETCompatXMLParser(remove_comments=True, remove_pis=False)

class XMLreader(FileReader):
    """
    Generic XML read and write class. Mostly helper functions.
    Makes reading/writing XML a bit easier than calling lxml libraries directly.

    :Dependencies:
        This class requires lxml 2.3 or higher.
    """

    xml = None
    xmldoc = None
    xmlroot = None
    schema = None
    schemadoc = None
    encoding = None
    processing_instructions = None

    def __init__(self, xml=None, schema=None):
        self.xml = xml
        self.schema = schema
        self.processing_instructions = {}
        if xml is not None:
            self.set_xml_file(xml)
        else:
            self.xmldoc = None
            self.xmlroot = None
        if schema is not None:
            self.set_schema(schema)
        else:
            self.schemadoc = None

    def reader(self):
        """
        Read in an XML file into memory and return an lxml dictionary
        """
        if self.validate_xml():
            self.xmldoc = etree.parse(self.xml, parser=PARSER)
        else:
            raise etree.XMLSchemaValidateError(self, self.find_invalid_xml())
        return self.xmldoc

    def set_xml_file(self, xml):
        """
        Set the XML file and parse
        """
        try:
            self.xml = xml
            self.xmldoc = etree.parse(self.xml, parser=PARSER)
            self.xmlroot = self.xmldoc.getroot()
        except etree.XMLSyntaxError as xml_error:
            logger.info(xml_error)
            raise xml_error
        except Exception:
            self.xml = None
            self.xmldoc = None
            self.xmlroot = None

    def set_xml_string(self, tag_soup):
        """
        Set an XML string as the working XML.

        :param tag_soup: XML formatted string
        """
        try:
            self.xml = tag_soup
            self.xmldoc = tag_soup
            self.xmlroot = etree.fromstring(tag_soup)
        except etree.XMLSyntaxError as xml_error:
            logger.info(xml_error)
            raise xml_error
        except Exception as exc:
            self.xml = None
            self.xmldoc = None
            self.xmlroot = None
            raise exc

    def set_schema(self, schema):
        """
        Set the schema file and parse
        """
        try:
            self.schema = schema
            self.schemadoc = etree.parse(self.schema, parser=PARSER)
        except etree.XMLSyntaxError as xml_error:
            logger.info(xml_error)
        except Exception:
            self.schema = None
            self.schemadoc = None

    def validate_xml(self):
        """
        Checks to see if the XML file meets the schema
        """
        valid = True
        if self.schema is not None:
            self.parse_schema_and_doc()
            schema_check = etree.XMLSchema(self.schemadoc)
            valid = schema_check.validate(self.xmldoc)
        return valid

    def find_invalid_xml(self):
        """
        Finds the first offending element that should not be present in XML file
        """
        first_error = ""
        self.parse_schema_and_doc()
        schema = etree.XMLSchema(self.schemadoc)
        try:
            first_error = schema.assertValid(self.xmldoc)
        except etree.DocumentInvalid as err:
            # Suppress errors for <'any'> elements
            if "##other" in str(err):
                return first_error
            first_error = str(err)
        return first_error

    def parse_schema_and_doc(self):
        """
        Creates a dictionary of the parsed schema and xml files.
        """
        self.set_xml_file(self.xml)
        self.set_schema(self.schema)

    def to_string(self, elem, pretty_print=False, encoding=None):
        """
        Converts an etree element into a string
        """
        return decode(etree.tostring(elem, pretty_print=pretty_print,
                                     encoding=encoding))

    def break_processing_instructions(self, string, dic):
        """
        Method to break a processing instruction string apart and add to a dict

        :param string: A processing instruction as a string
        :param dic: The dictionary to save the PIs to
        """
        pi_string = string.replace("<?", "").replace("?>", "")
        split = pi_string.split(" ", 1)
        pi_name = split[0]
        attr = split[1]
        new_pi_name = self._create_unique_key(dic, pi_name)
        dic[new_pi_name] = attr
        return dic

    def set_processing_instructions(self):
        """
        Take out all processing instructions and create a dictionary from them
        If there is a default encoding, the value is also saved
        """
        dic = {}
        proc_instr = self.xmlroot.getprevious()
        while proc_instr is not None:
            pi_string = self.to_string(proc_instr)
            if "?>\n<?" in pi_string:
                pi_string = pi_string.split("?>\n<?")
            if isinstance(pi_string, str):
                dic = self.break_processing_instructions(pi_string, dic)
            elif isinstance(pi_string, list):
                for item in pi_string:
                    dic = self.break_processing_instructions(item, dic)
            proc_instr = proc_instr.getprevious()
        if 'xml' in dic:
            self.set_encoding(dic['xml'])
            del dic['xml']
        self.processing_instructions = dic

    def set_encoding(self, attr_str):
        """
        Find the encoding in the xml declaration and save it as a string

        :param attr_str: All attributes as a string
            e.g. "foo1="bar1" foo2="bar2" foo3="bar3" ... foo_n="bar_n""
        """
        attr_str = attr_str.replace(" = ", "=")
        attr_list = attr_str.split()
        for item in attr_list:
            name_value = item.split("\"=")
            name = name_value[0].lower()
            value = name_value[1]
            if name == "encoding":
                self.encoding = value
                return
        self.encoding = None

    def _create_unique_key(self, dictionary, name, numb=0):
        """
        Create a unique key value for any dictionary to prevent overwriting
        Recurses until a unique key value is found.

        :param dictionary: A dictionary with any number of entries
        :param name: The index of the item to be added to dictionary
        :param numb: The number to be appended to the name, starts at 0
        """
        if dictionary.get(name) is not None:
            numb += 1
            name = name.split("_")[0]
            name += "_{0}".format(numb)
            name = self._create_unique_key(dictionary, name, numb)
        return name

    def create_tree(self, root):
        """
        Create an element tree for processing from an etree element

        :param root: etree Element(s)
        """
        return etree.ElementTree(root)

    def create_element_from_string(self, xml_string):
        """
        Create an element from an XML string

        :param xml_string: A string of xml
        """
        return etree.fromstring(xml_string)

    def create_element(self, name, attrib=None, nsmap=None):
        """
        Create an XML element for writing to file

        :param name: The name of the element to be created
        """
        if attrib is None:
            attrib = {}
        return etree.Element(name, attrib, nsmap)

    def write_text(self, elem, text):
        """
        Write text to an etree Element

        :param elem: etree.Element object
        :param text: text to write to the element
        """
        elem.text = text
        return elem

    def write_attribute(self, elem, attr_name, attr_value):
        """
        Write attributes to an Element

        :param elem: etree.Element object
        :param attr_name: attribute name to write
        :param attr_value: attribute value to set
        """
        attr = elem.attrib
        attr[attr_name] = attr_value

    def return_processing_instructions(self):
        """
        Get all processing instructions saved when loading the document

        :param tree: etree.ElementTree object to write PIs to
        """
        pi_list = []
        if self.processing_instructions is not None:
            for key in self.processing_instructions:
                value = self.processing_instructions.get(key)
                pi_item = etree.ProcessingInstruction(key, value)
                pi_list.append(pi_item)
        return pi_list

    def append(self, element, tree):
        """
        Append an etree Element to an ElementTree.

        :param element: etree Element to append
        :param tree: ElementTree object to append to
        """
        tree = tree.append(element)
        return tree

    def ebuilder(self, parent, elementname, text=None, attrib=None):
        """
        Use lxml E builder class with arbitrary inputs.

        :param parnet: The parent element to append a child to
        :param elementname: The name of the child in string form
        :param text: The element text
        :param attrib: A dictionary of attribute names to attribute values
        """
        text = str(text)
        if attrib is None:
            attrib = {}
        elem = E(elementname, attrib, text)
        parent = parent.append(elem)
        return parent
