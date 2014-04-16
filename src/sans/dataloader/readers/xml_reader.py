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

from lxml import etree
from lxml.builder import E
parser = etree.ETCompatXMLParser(remove_comments=True, remove_pis=False)

class XMLreader():
    
    xml = None
    xmldoc = None
    xmlroot = None
    schema = None
    schemadoc = None
    encoding = None
    processingInstructions = None
    
    def __init__(self, xml = None, schema = None, root = None):
        self.xml = xml
        self.schema = schema
        self.processingInstructions = {}
        if xml is not None:
            self.setXMLFile(xml, root)
        else:
            self.xmldoc = None
            self.xmlroot = None
        if schema is not None:
            self.setSchema(schema)
        else:
            self.schemadoc = None
    
    def reader(self):
        """
        Read in an XML file into memory and return an lxml dictionary
        """
        if self.validateXML():
            self.xmldoc = etree.parse(self.xml, parser = parser)
        else:
            raise etree.ValidationError(self, self.findInvalidXML())
        return self.xmldoc
    
    def setXMLFile(self, xml, root = None):
        """
        Set the XML file and parse
        """
        try:
            self.xml = xml
            self.xmldoc = etree.parse(self.xml, parser = parser)
            self.xmlroot = self.xmldoc.getroot()
        except Exception:
            self.xml = None
            self.xmldoc = None
            self.xmlroot = None
    
    def setSchema(self, schema):
        """
        Set the schema file and parse
        """
        try:
            self.schema = schema
            self.schemadoc = etree.parse(self.schema, parser = parser)
        except Exception:
            self.schema = None
            self.schemadoc = None
    
    def validateXML(self):
        """
        Checks to see if the XML file meets the schema
        """
        valid = True
        if self.schema is not None:
            self.parseSchemaAndDoc()
            schemaCheck = etree.XMLSchema(self.schemadoc)
            valid = schemaCheck.validate(self.xmldoc)
        return valid
    
    def findInvalidXML(self):
        """
        Finds the first offending element that should not be present in XML file
        """
        firstError = ""
        self.parseSchemaAndDoc()
        schema = etree.XMLSchema(self.schemadoc)
        try:
            firstError = schema.assertValid(self.xmldoc)
        except etree.DocumentInvalid as e:
            firstError = str(e)
        return firstError
    
    def parseSchemaAndDoc(self):
        """
        Creates a dictionary of the parsed schema and xml files.
        """
        self.setXMLFile(self.xml)
        self.setSchema(self.schema)
        
    def toString(self, elem, pp=False, encoding=None):
        """
        Converts an etree element into a string
        """
        return etree.tostring(elem, pretty_print = pp, encoding = encoding)
    
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
    
    def setProcessingInstructions(self):
        """
        Take out all processing instructions and create a dictionary from them
        If there is a default encoding, the value is also saved
        """
        dic = {}
        pi = self.xmlroot.getprevious()
        while pi is not None:
            pi_string = self.toString(pi)
            if "?>\n<?" in pi_string:
                pi_string = pi_string.split("?>\n<?")
            if isinstance(pi_string, str):
                dic = self.break_processing_instructions(pi_string, dic)
            elif isinstance(pi_string, list):
                for item in pi_string:
                    dic = self.break_processing_instructions(item, dic)
            pi = pi.getprevious()
        if 'xml' in dic:
            self.setEncoding(dic['xml'])
            del dic['xml']
        self.processingInstructions = dic
        
    def setEncoding(self, attr_str):
        """
        Find the encoding in the xml declaration and save it as a string
        
        :param attr_str: All attributes as a string
            e.g. "foo1="bar1" foo2="bar2" foo3="bar3" ... foo_n="bar_n""
        """
        attr_str = attr_str.replace(" = ", "=")
        attr_list = attr_str.split( )
        for item in attr_list:
            name_value = item.split("\"=")
            name = name_value[0].lower()
            value = name_value[1]
            if name == "encoding":
                self.encoding = value
                return
        self.encoding = None
        
    def _create_unique_key(self, dictionary, name, i = 0):
        """
        Create a unique key value for any dictionary to prevent overwriting
        Recurses until a unique key value is found.
        
        :param dictionary: A dictionary with any number of entries
        :param name: The index of the item to be added to dictionary
        :param i: The number to be appended to the name, starts at 0
        """
        if dictionary.get(name) is not None:
            i += 1
            name = name.split("_")[0]
            name += "_{0}".format(i)
            name = self._create_unique_key(dictionary, name, i)
        return name
    
    def create_tree(self, root):
        """
        Create an element tree for processing from an etree element
        
        :param root: etree Element(s) 
        """
        return etree.ElementTree(root)
    
    def create_element_from_string(self, s):
        """
        Create an element from an XML string
        
        :param s: A string of xml
        """
        return etree.fromstring(s)
    
    def create_element(self, name, attrib={}, nsmap=None):
        """
        Create an XML element for writing to file
        
        :param name: The name of the element to be created
        """
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
        for key in self.processingInstructions:
            value = self.processingInstructions.get(key)
            pi = etree.ProcessingInstruction(key, value)
            pi_list.append(pi)
        return pi_list
    
    def append(self, element, tree):
        """
        Append an etree Element to an ElementTree.
        
        :param element: etree Element to append
        :param tree: ElementTree object to append to
        """
        tree = tree.append(element)
        return tree
    
    def ebuilder(self, parent, elementname, text=None, attrib={}):
        text = str(text)
        elem = E(elementname, attrib, text)
        parent = parent.append(elem)
        return parent
        