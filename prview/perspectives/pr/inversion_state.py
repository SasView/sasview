"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""
import time, os

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
        
    def toXML(self, file="pr_state.prv"):
        """
            Writes the state of the InversionControl panel to file, as XML.
            
            @param file: file to write to
        """
        from xml.dom.minidom import getDOMImplementation

        impl = getDOMImplementation()
        
        doc_type = impl.createDocumentType("pr_inversion", "1.0", "1.0")     
        
        newdoc = impl.createDocument(None, "pr_inversion", doc_type)
        top_element = newdoc.documentElement
        attr = newdoc.createAttribute("version")
        attr.nodeValue = '1.0'
        top_element.setAttributeNode(attr)
        
        # File name
        element = newdoc.createElement("filename")
        element.appendChild(newdoc.createTextNode(self.file))
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
                    
        # Save the file
        fd = open(file, 'w')
        fd.write(newdoc.toprettyxml())
        fd.close()

    def fromXML(self, file):
        """
            Load a P(r) inversion state from a file
            
            @param file: .prv file
        """
        # Check whether the file is valid
        if not os.path.isfile(file):
            raise  RuntimeError, "P(r) reader: cannot open %s" % file
        
        from xml.dom.minidom import parse
        doc = parse(file)
        if doc.documentElement.tagName == 'pr_inversion':
            if doc.documentElement.hasAttribute('version')\
                and doc.documentElement.getAttribute('version') == '1.0':
                
                if doc.documentElement.hasChildNodes():
                    for node in doc.documentElement.childNodes:
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
                                    for out in out_list:
                                        if item.nodeName == out[0]:
                                            try:
                                                exec '%s = float(item.childNodes[0].nodeValue.strip())' % out[1]
                                            except:
                                                exec '%s = None' % out[1]
            else:
                raise RuntimeError, "Unsupported P(r) file version: %s" % doc.documentElement.getAttribute('version')
        
                    
class Reader:
    """
        Class to load a .prv P(r) inversion file
    """
    ## File type
    type_name = "P(r)"
    
    ## Wildcards
    type = ["P(r) files (*.prv)|*.prv"]
    ## List of allowed extensions
    ext=['.prv', '.PRV']  
    
    def __init__(self, call_back):
        """
            Initialize the call-back method to be called
            after we load a file
            @param call_back: call-back method
        """
        self.call_back = call_back
        
    def read(self, path):
        """ 
            Load a new P(r) inversion state from file
            
            @param path: file path
            @return: None
        """
        # Read the new state from file
        state = InversionState()
        state.fromXML(path)
        
        # Call back to post the new state
        self.call_back(state)
        return None
        
if __name__ == "__main__": 
    state = InversionState()
    #print state.fromXML('../../test/pr_state.prv')     
    print state.fromXML('../../test/test.prv')     
    print state   