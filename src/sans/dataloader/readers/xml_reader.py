"""
    Generic XML reader
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
parser = etree.ETCompatXMLParser()

class XMLreader():
    
    def __init__(self, xml = None, schema = None, root = None):
        self.xml = xml
        self.schema = schema
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
        try:
            self.xml = xml
            self.xmldoc = etree.parse(self.xml, parser = parser)
            self.xmlroot = self.xmldoc.getroot()
        except Exception:
            ##!TODO: raise exception if no xml is passed to this function
            print "No xml file was found!"
    
    def setSchema(self, schema):
        try:
            self.schema = schema
            self.schemadoc = etree.parse(self.schema, parser = parser)
        except Exception:
            ##!TODO: raise exception if no schema is passed to this function
            print "No schema file was found!"
    
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
        Finds the first offending element that should not be present in an XML file
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
        