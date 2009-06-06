"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""
import time, os
import logging
import DataLoader
from DataLoader.readers.cansas_reader import Reader as CansasReader

PRNODE_NAME = 'pr_inversion'

## List of P(r) inversion inputs 
in_list=  [["nterms",       "self.nfunc"],
           ["d_max",        "self.d_max"],
           ["alpha",        "self.alpha"],
           ["slit_width",   "self.width"],
           ["slit_height",  "self.height"],
           ["qmin",         "self.qmin"],
           ["qmax",         "self.qmax"]]                      

## List of P(r) inversion outputs
out_list= [["elapsed", "self.elapsed"],
           ["rg",      "self.rg"],
           ["iq0",     "self.iq0"],
           ["bck",     "self.bck"],
           ["chi2",    "self.chi2"],
           ["osc",     "self.osc"],
           ["pos",     "self.pos"],
           ["pos_err", "self.pos_err"],
           ["alpha_estimate", "self.alpha_estimate"],
           ["nterms_estimate", "self.nterms_estimate"]]

class InversionState(object):
    """
        Class to hold the state information of the InversionControl panel.
    """
    def __init__(self):
        """
            Default values
        """
        # Input 
        self.file  = None
        self.estimate_bck = False
        self.timestamp = time.time()
        
        # Inversion parameters
        self.nfunc = None
        self.d_max = None
        self.alpha = None
        
        # Slit parameters
        self.height = None
        self.width  = None
        
        # Q range
        self.qmin  = None
        self.qmax  = None
        
        # Outputs
        self.elapsed = None
        self.rg    = None
        self.iq0   = None
        self.bck   = None
        self.chi2  = None
        self.osc   = None
        self.pos   = None
        self.pos_err = None
        
        # Estimates
        self.alpha_estimate = None
        self.nterms_estimate = None
        
        # Data
        self.q       = None
        self.iq_obs  = None
        self.iq_calc = None
        
        # Coefficients
        self.coefficients = None
        self.covariance = None
    
    def __str__(self):
        """
            Pretty print
            
            @return: string representing the state
        """
        state  = "File:         %s\n" % self.file
        state += "Timestamp:    %s\n" % self.timestamp
        state += "Estimate bck: %s\n" % str(self.estimate_bck)
        state += "No. terms:    %s\n" % str(self.nfunc)
        state += "D_max:        %s\n" % str(self.d_max)
        state += "Alpha:        %s\n" % str(self.alpha)
        
        state += "Slit height:  %s\n" % str(self.height)
        state += "Slit width:   %s\n" % str(self.width)
        
        state += "Qmin:         %s\n" % str(self.qmin)
        state += "Qmax:         %s\n" % str(self.qmax)
        
        state += "\nEstimates:\n"
        state += "  Alpha:      %s\n" % str(self.alpha_estimate)
        state += "  Nterms:     %s\n" % str(self.nterms_estimate)
        
        state += "\nOutputs:\n"
        state += "  Elapsed:    %s\n" % str(self.elapsed)
        state += "  Rg:         %s\n" % str(self.rg)
        state += "  I(q=0):     %s\n" % str(self.iq0)
        state += "  Bck:        %s\n" % str(self.bck)
        state += "  Chi^2:      %s\n" % str(self.chi2)
        state += "  Oscillation:%s\n" % str(self.osc)
        state += "  Positive:   %s\n" % str(self.pos)
        state += "  1-sigma pos:%s\n" % str(self.pos_err)
        
        return state
        
    def toXML(self, file="pr_state.prv", doc=None, entry_node=None):
        """
            Writes the state of the InversionControl panel to file, as XML.
            
            Compatible with standalone writing, or appending to an
            already existing XML document. In that case, the XML document
            is required. An optional entry node in the XML document may also be given.
            
            @param file: file to write to
            @param doc: XML document object [optional]
            @param entry_node: XML node within the XML document at which we will append the data [optional]
        """
        from xml.dom.minidom import getDOMImplementation

        # Check whether we have to write a standalone XML file
        if doc is None:
            impl = getDOMImplementation()
        
            doc_type = impl.createDocumentType(PRNODE_NAME, "1.0", "1.0")     
        
            newdoc = impl.createDocument(None, PRNODE_NAME, doc_type)
            top_element = newdoc.documentElement
        else:
            # We are appending to an existing document
            newdoc = doc
            top_element = newdoc.createElement(PRNODE_NAME)
            if entry_node is None:
                newdoc.documentElement.appendChild(top_element)
            else:
                entry_node.appendChild(top_element)
            
        attr = newdoc.createAttribute("version")
        attr.nodeValue = '1.0'
        top_element.setAttributeNode(attr)
        
        # File name
        element = newdoc.createElement("filename")
        if self.file is not None:
            element.appendChild(newdoc.createTextNode(str(self.file)))
        else:
            element.appendChild(newdoc.createTextNode(str(file)))
        top_element.appendChild(element)
        
        element = newdoc.createElement("timestamp")
        element.appendChild(newdoc.createTextNode(time.ctime(self.timestamp)))
        attr = newdoc.createAttribute("epoch")
        attr.nodeValue = str(self.timestamp)
        element.setAttributeNode(attr)
        top_element.appendChild(element)
        
        # Inputs
        inputs = newdoc.createElement("inputs")
        top_element.appendChild(inputs)
        
        for item in in_list:
            element = newdoc.createElement(item[0])
            exec "element.appendChild(newdoc.createTextNode(str(%s)))" % item[1]
            inputs.appendChild(element)
              
        # Outputs
        outputs = newdoc.createElement("outputs")
        top_element.appendChild(outputs)
        
        for item in out_list:
            element = newdoc.createElement(item[0])
            exec "element.appendChild(newdoc.createTextNode(str(%s)))" % item[1]
            outputs.appendChild(element)
                    
        # Save output coefficients and its covariance matrix
        element = newdoc.createElement("coefficients")
        element.appendChild(newdoc.createTextNode(str(self.coefficients)))
        outputs.appendChild(element)
        element = newdoc.createElement("covariance")
        element.appendChild(newdoc.createTextNode(str(self.covariance)))
        outputs.appendChild(element)
                    
        # Save the file
        if doc is None:
            fd = open(file, 'w')
            fd.write(newdoc.toprettyxml())
            fd.close()
            return None
        else:
            return newdoc.toprettyxml()

    def fromXML(self, file=None, node=None):
        """
            Load a P(r) inversion state from a file
            
            @param file: .prv file
            @param node: node of a XML document to read from
        """
        if file is not None:
            # Check whether the file is valid
            if not os.path.isfile(file):
                raise  RuntimeError, "P(r) reader: cannot open %s" % file
        
            from xml.dom.minidom import parse
            doc = parse(file)
            node = doc.documentElement
            
        if node.tagName == PRNODE_NAME:
            if node.hasAttribute('version')\
                and node.getAttribute('version') == '1.0':
                
                if node.hasChildNodes():
                    for node in node.childNodes:
                        if node.nodeName == 'filename':
                            if node.hasChildNodes():
                                self.file = node.childNodes[0].nodeValue.strip()
                        elif node.nodeName == 'timestamp':
                            if node.hasAttribute('epoch'):
                                try:
                                    self.timestamp = float(node.getAttribute('epoch'))
                                except:
                                    # Could not read timestamp: pass
                                    pass
                                
                        # Parse inversion inputs
                        elif node.nodeName == 'inputs':
                            if node.hasChildNodes():
                                for item in node.childNodes:
                                    for out in in_list:
                                        if item.nodeName == out[0]:
                                            try:
                                                exec '%s = float(item.childNodes[0].nodeValue.strip())' % out[1]
                                            except:
                                                exec '%s = None' % out[1]
                                        elif item.nodeName == 'estimate_bck':
                                            try:
                                                self.estimate_bck = item.childNodes[0].nodeValue.strip()=='True'
                                            except:
                                                self.estimate_bck = False
                            
                        # Parse inversion outputs
                        elif node.nodeName == 'outputs':
                            if node.hasChildNodes():
                                for item in node.childNodes:
                                    # Look for standard outputs
                                    for out in out_list:
                                        if item.nodeName == out[0]:
                                            try:
                                                exec '%s = float(item.childNodes[0].nodeValue.strip())' % out[1]
                                            except:
                                                exec '%s = None' % out[1]
                                                
                                    # Look for coefficients
                                    # Format is [value, value, value, value]
                                    if item.nodeName == 'coefficients':
                                        # Remove brackets
                                        c_values = item.childNodes[0].nodeValue.strip().replace('[','')
                                        c_values = c_values.replace(']','')
                                        toks = c_values.split()
                                        self.coefficients = []
                                        for c in toks:
                                            try:
                                                self.coefficients.append(float(c))
                                            except:
                                                # Bad data, skip. We will count the number of 
                                                # coefficients at the very end and deal with 
                                                # inconsistencies then.
                                                pass
                                        # Sanity check
                                        if not len(self.coefficients) == self.nfunc:
                                            # Inconsistent number of coefficients. Don't keep the data.
                                            err_msg = "InversionState.fromXML: inconsistant number of coefficients: "
                                            err_msg += "%d %d" % (len(self.coefficients), self.nfunc)
                                            logging.error(err_msg)
                                            self.coefficients = None
                                            
                                    # Look for covariance matrix
                                    # Format is [ [value, value], [value, value] ]
                                    elif item.nodeName == "covariance":
                                        # Parse rows
                                        rows = item.childNodes[0].nodeValue.strip().split('[')
                                        self.covariance = []
                                        for row in rows:
                                            row = row.strip()
                                            if len(row) == 0: continue
                                            # Remove end bracket
                                            row = row.replace(']','')
                                            c_values = row.split()
                                            cov_row = []
                                            for c in c_values:
                                                try:
                                                    cov_row.append(float(c))
                                                except:
                                                    # Bad data, skip. We will count the number of 
                                                    # coefficients at the very end and deal with 
                                                    # inconsistencies then.
                                                    pass
                                            # Sanity check: check the number of entries in the row
                                            if len(cov_row) == self.nfunc:
                                                self.covariance.append(cov_row)
                                        # Sanity check: check the number of rows in the covariance
                                        # matrix
                                        if not len(self.covariance) == self.nfunc:
                                            # Inconsistent dimensions of the covariance matrix.
                                            # Don't keep the data.
                                            err_msg = "InversionState.fromXML: inconsistant dimensions of the covariance matrix: "
                                            err_msg += "%d %d" % (len(self.covariance), self.nfunc)
                                            logging.error(err_msg)
                                            self.covariance = None
            else:
                raise RuntimeError, "Unsupported P(r) file version"
        
                    
class Reader(CansasReader):
    """
        Class to load a .prv P(r) inversion file
    """
    ## File type
    type_name = "P(r)"
    
    ## Wildcards
    type = ["P(r) files (*.prv)|*.prv"]
    ## List of allowed extensions
    ext=['.prv', '.PRV']  
    
    def __init__(self, call_back, cansas=False):
        """
            Initialize the call-back method to be called
            after we load a file
            @param call_back: call-back method
            @param cansas:  True = files will be written/read in CanSAS format
                            False = standalone mode
            
        """
        ## Call back method to be executed after a file is read
        self.call_back = call_back
        ## CanSAS format flag
        self.cansas = cansas
        
    def read(self, path):
        """ 
            Load a new P(r) inversion state from file
            
            @param path: file path
            @return: None
        """
        if self.cansas==True:
            return self._read_cansas(path)
        else:
            return self._read_standalone(path)
        
    def _read_standalone(self, path):
        """ 
            Load a new P(r) inversion state from file.
            The P(r) node is assumed to be the top element.
            
            @param path: file path
            @return: None
        """
        # Read the new state from file
        state = InversionState()
        state.fromXML(file=path)
        
        # Call back to post the new state
        self.call_back(state)
        return None
    
    def _parse_prstate(self, entry):
        """
            Read a p(r) inversion result from an XML node
            @param entry: XML node to read from 
            @return: InversionState object
        """
        from xml import xpath

        # Create an empty state
        state = InversionState()
        
        # Locate the P(r) node
        try:
            nodes = xpath.Evaluate(PRNODE_NAME, entry)
            state.fromXML(node=nodes[0])
        except:
            #raise RuntimeError, "%s is not a file with P(r) information." % path
            logging.info("XML document does not contain P(r) information.")
            import sys
            print sys.exc_value
            
        return state
    
    def _read_cansas(self, path):
        """ 
            Load data and P(r) information from a CanSAS XML file.
            
            @param path: file path
            @return: Data1D object if a single SASentry was found, 
                        or a list of Data1D objects if multiple entries were found,
                        or None of nothing was found
            @raise RuntimeError: when the file can't be opened
            @raise ValueError: when the length of the data vectors are inconsistent
        """
        from xml.dom.minidom import parse
        from xml import xpath
        output = []
        
        if os.path.isfile(path):
            basename  = os.path.basename(path)
            root, extension = os.path.splitext(basename)
            #TODO: eventually remove the check for .xml once
            # the P(r) writer/reader is truly complete.
            if  extension.lower() in self.ext or \
                extension.lower() == '.xml':
                
                dom = parse(path)
                
                # Format 1: check whether we have a CanSAS file
                nodes = xpath.Evaluate('SASroot', dom)
                # Check the format version number
                if nodes[0].hasAttributes():
                    for i in range(nodes[0].attributes.length):
                        if nodes[0].attributes.item(i).nodeName=='version':
                            if nodes[0].attributes.item(i).nodeValue != self.version:
                                raise ValueError, "cansas_reader: unrecognized version number %s" % \
                                    nodes[0].attributes.item(i).nodeValue
                
                entry_list = xpath.Evaluate('SASroot/SASentry', dom)
                for entry in entry_list:
                    sas_entry = self._parse_entry(entry)
                    prstate = self._parse_prstate(entry)
                    sas_entry.meta_data['prstate'] = prstate
                    sas_entry.filename = prstate.file
                    output.append(sas_entry)
        else:
            raise RuntimeError, "%s is not a file" % path
        
        # Return output consistent with the loader's api
        if len(output)==0:
            return None
        elif len(output)==1:
            # Call back to post the new state
            self.call_back(output[0].meta_data['prstate'], datainfo = output[0])
            return output[0]
        else:
            return output                
    
    
    def write(self, filename, datainfo=None, prstate=None):
        """
            Write the content of a Data1D as a CanSAS XML file
            
            @param filename: name of the file to write
            @param datainfo: Data1D object
            @param prstate: InversionState object
        """

        # Sanity check
        if self.cansas == True:
            if datainfo is None:
                datainfo = DataLoader.data_info.Data1D(x=[], y=[])    
            elif not issubclass(datainfo.__class__, DataLoader.data_info.Data1D):
                raise RuntimeError, "The cansas writer expects a Data1D instance: %s" % str(datainfo.__class__.__name__)
        
            # Create basic XML document
            doc, sasentry = self._to_xml_doc(datainfo)
        
            # Add the P(r) information to the XML document
            if prstate is not None:
                prstate.toXML(doc=doc, entry_node=sasentry)
        
            # Write the XML document
            fd = open(filename, 'w')
            fd.write(doc.toprettyxml())
            fd.close()
        else:
            prstate.toXML(file=filename)
        
        
if __name__ == "__main__": 
    #TODO: turn all this into unit tests
    
    state = InversionState()
    #print state.fromXML('../../test/pr_state.prv')     
    print state.fromXML('../../test/test.prv')     
    print state   
    state.toXML('test_copy.prv')
    
    from DataLoader.loader import Loader
    l = Loader()
    datainfo = l.load("../../test/cansas1d.xml")
    
    def call_back(state, datainfo=None):
        print state
        
    reader = Reader(call_back)
    reader.cansas = False
    reader.write("test_copy_from_reader.prv", prstate=state)
    reader.cansas = True
    reader.write("testout.prv", datainfo, state)
    reader.write("testout_wo_datainfo.prv", prstate=state)
    
    # Now try to load things back
    reader.cansas = False
    #print reader.read("test_copy_from_reader.prv")
    reader.cansas = True
    #data = reader.read("testout.prv")
    data = reader.read("testout_wo_datainfo.prv")
    print data
    print data.meta_data['prstate']
    
    