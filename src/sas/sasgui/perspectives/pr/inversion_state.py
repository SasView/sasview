"""
    Handling of P(r) inversion states
"""
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################


import time
import os
import sys
import logging
from lxml import etree
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sascalc.dataloader.readers.cansas_reader import Reader as CansasReader
from sas.sascalc.dataloader.readers.cansas_reader import get_content

logger = logging.getLogger(__name__)

PRNODE_NAME = 'pr_inversion'
CANSAS_NS = "cansas1d/1.0"

# Translation of names between stored and object data
## List of P(r) inversion inputs
in_list = [["nterms", "nfunc"],
           ["d_max", "d_max"],
           ["alpha", "alpha"],
           ["slit_width", "width"],
           ["slit_height", "height"],
           ["qmin", "qmin"],
           ["qmax", "qmax"],
           ["estimate_bck", "estimate_bck"],
           ["bck_value", "bck_value"]]

## List of P(r) inversion outputs
out_list = [["elapsed", "elapsed"],
            ["rg", "rg"],
            ["iq0", "iq0"],
            ["bck", "bck"],
            ["chi2", "chi2"],
            ["osc", "osc"],
            ["pos", "pos"],
            ["pos_err", "pos_err"],
            ["alpha_estimate", "alpha_estimate"],
            ["nterms_estimate", "nterms_estimate"]]

class InversionState(object):
    """
    Class to hold the state information of the InversionControl panel.
    """
    def __init__(self):
        """
        Default values
        """
        # Input
        self.file = None
        self.estimate_bck = False
        self.timestamp = time.time()
        self.bck_value = 0.0

        # Inversion parameters
        self.nfunc = None
        self.d_max = None
        self.alpha = None

        # Slit parameters
        self.height = None
        self.width = None

        # Q range
        self.qmin = None
        self.qmax = None

        # Outputs
        self.elapsed = None
        self.rg = None
        self.iq0 = None
        self.bck = None
        self.chi2 = None
        self.osc = None
        self.pos = None
        self.pos_err = None

        # Estimates
        self.alpha_estimate = None
        self.nterms_estimate = None

        # Data
        self.q = None
        self.iq_obs = None
        self.iq_calc = None

        # Coefficients
        self.coefficients = None
        self.covariance = None

    def __str__(self):
        """
        Pretty print

        :return: string representing the state

        """
        state = "File:         %s\n" % self.file
        state += "Timestamp:    %s\n" % self.timestamp
        state += "Estimate bck: %s\n" % str(self.estimate_bck)
        state += "Bck Value:    %s\n" % str(self.bck_value)
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
        is required. An optional entry node in the XML document
        may also be given.

        :param file: file to write to
        :param doc: XML document object [optional]
        :param entry_node: XML node within the XML document at which
            we will append the data [optional]

        """
        #TODO: Get this to work
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
            element.appendChild(newdoc.createTextNode(str(getattr(self, item[1]))))
            inputs.appendChild(element)

        # Outputs
        outputs = newdoc.createElement("outputs")
        top_element.appendChild(outputs)

        for item in out_list:
            element = newdoc.createElement(item[0])
            element.appendChild(newdoc.createTextNode(str(getattr(self, item[1]))))
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
            return newdoc

    def fromXML(self, file=None, node=None):
        """
        Load a P(r) inversion state from a file

        :param file: .prv file
        :param node: node of a XML document to read from

        """
        if file is not None:
            msg = "InversionState no longer supports non-CanSAS"
            msg += " format for P(r) files"
            raise RuntimeError(msg)

        if node.get('version') and node.get('version') == '1.0':

            # Get file name
            entry = get_content('ns:filename', node)
            if entry is not None:
                self.file = entry.text.strip()

            # Get time stamp
            entry = get_content('ns:timestamp', node)
            if entry is not None and entry.get('epoch'):
                try:
                    self.timestamp = float(entry.get('epoch'))
                except:
                    msg = "InversionState.fromXML: Could not read "
                    msg += "timestamp\n %s" % sys.exc_info()[1]
                    logger.error(msg)

            # Parse inversion inputs
            entry = get_content('ns:inputs', node)
            if entry is not None:
                for item in in_list:
                    input_field = get_content('ns:%s' % item[0], entry)
                    if input_field is not None:
                        try:
                            setattr(self, item[1], float(input_field.text.strip()))
                        except:
                            setattr(self, item[1], None)
                input_field = get_content('ns:estimate_bck', entry)
                if input_field is not None:
                    try:
                        self.estimate_bck = input_field.text.strip() == 'True'
                    except:
                        self.estimate_bck = False

            # Parse inversion outputs
            entry = get_content('ns:outputs', node)
            if entry is not None:
                # Output parameters (scalars)
                for item in out_list:
                    input_field = get_content('ns:%s' % item[0], entry)
                    if input_field is not None:
                        try:
                            setattr(self, item[1], float(input_field.text.strip()))
                        except:
                            setattr(self, item[1], None)

                # Look for coefficients
                # Format is [value, value, value, value]
                coeff = get_content('ns:coefficients', entry)
                if coeff is not None:
                    # Remove brackets
                    c_values = coeff.text.strip().replace('[', '')
                    c_values = c_values.replace(']', '')
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
                        # Inconsistent number of coefficients.
                        # Don't keep the data.
                        err_msg = "InversionState.fromXML: inconsistant "
                        err_msg += "number of coefficients: "
                        err_msg += "%d %d" % (len(self.coefficients),
                                              self.nfunc)
                        logger.error(err_msg)
                        self.coefficients = None

                # Look for covariance matrix
                # Format is [ [value, value], [value, value] ]
                coeff = get_content('ns:covariance', entry)
                if coeff is not None:
                    # Parse rows
                    rows = coeff.text.strip().split('[')
                    self.covariance = []
                    for row in rows:
                        row = row.strip()
                        if len(row) == 0: continue
                        # Remove end bracket
                        row = row.replace(']', '')
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
                        err_msg = "InversionState.fromXML: "
                        err_msg += "inconsistant dimensions of the "
                        err_msg += " covariance matrix: "
                        err_msg += "%d %d" % (len(self.covariance), self.nfunc)
                        logger.error(err_msg)
                        self.covariance = None

class Reader(CansasReader):
    """
    Class to load a .prv P(r) inversion file
    """
    ## File type
    type_name = "P(r)"

    ## Wildcards
    type = ["P(r) files (*.prv)|*.prv",
            "SASView files (*.svs)|*.svs"]
    ## List of allowed extensions
    ext = ['.prv', '.PRV', '.svs', '.SVS']

    def __init__(self, call_back, cansas=True):
        """
        Initialize the call-back method to be called
        after we load a file

        :param call_back: call-back method
        :param cansas:  True = files will be written/read in CanSAS format
                        False = write CanSAS format

        """
        ## Call back method to be executed after a file is read
        self.call_back = call_back
        ## CanSAS format flag
        self.cansas = cansas
        self.state = None

    def read(self, path):
        """
        Load a new P(r) inversion state from file

        :param path: file path

        :return: None

        """
        if self.cansas == True:
            return self._read_cansas(path)
        else:
            return self._read_standalone(path)

    def _read_standalone(self, path):
        """
        Load a new P(r) inversion state from file.
        The P(r) node is assumed to be the top element.

        :param path: file path

        :return: None

        """
        # Read the new state from file
        state = InversionState()
        state.fromXML(file=path)

        # Call back to post the new state
        self.state = state
        #self.call_back(state)
        return None

    def _parse_prstate(self, entry):
        """
        Read a p(r) inversion result from an XML node

        :param entry: XML node to read from

        :return: InversionState object

        """
        state = None

        # Locate the P(r) node
        try:
            nodes = entry.xpath('ns:%s' % PRNODE_NAME,
                                namespaces={'ns': CANSAS_NS})
            if nodes != []:
                # Create an empty state
                state = InversionState()
                state.fromXML(node=nodes[0])
        except:
            msg = "XML document does not contain P(r) "
            msg += "information.\n %s" % sys.exc_info()[1]
            logger.info(msg)

        return state

    def _read_cansas(self, path):
        """
        Load data and P(r) information from a CanSAS XML file.

        :param path: file path

        :return: Data1D object if a single SASentry was found,
                    or a list of Data1D objects if multiple entries were found,
                    or None of nothing was found

        :raise RuntimeError: when the file can't be opened
        :raise ValueError: when the length of the data vectors are inconsistent

        """
        output = []

        if os.path.isfile(path):
            basename = os.path.basename(path)
            root, extension = os.path.splitext(basename)
            #TODO: eventually remove the check for .xml once
            # the P(r) writer/reader is truly complete.
            if  extension.lower() in self.ext or extension.lower() == '.xml':

                tree = etree.parse(path, parser=etree.ETCompatXMLParser())
                # Check the format version number
                # Specifying the namespace will take care of the file
                #format version
                root = tree.getroot()

                entry_list = root.xpath('/ns:SASroot/ns:SASentry',
                                        namespaces={'ns': CANSAS_NS})

                for entry in entry_list:
                    prstate = self._parse_prstate(entry)
                    #prstate could be None when .svs file is loaded
                    #in this case, skip appending to output
                    if prstate is not None:
                        sas_entry, _ = self._parse_entry(entry)
                        sas_entry.meta_data['prstate'] = prstate
                        sas_entry.filename = prstate.file
                        output.append(sas_entry)
        else:
            raise RuntimeError("%s is not a file" % path)

        # Return output consistent with the loader's api
        if len(output) == 0:
            return None
        elif len(output) == 1:
            # Call back to post the new state
            self.call_back(output[0].meta_data['prstate'], datainfo=output[0])
            #self.state = output[0].meta_data['prstate']
            return output[0]
        else:
            return output


    def write(self, filename, datainfo=None, prstate=None):
        """
        Write the content of a Data1D as a CanSAS XML file

        :param filename: name of the file to write
        :param datainfo: Data1D object
        :param prstate: InversionState object

        """
        # Sanity check
        if self.cansas == True:
            doc = self.write_toXML(datainfo, prstate)
            # Write the XML document
            fd = open(filename, 'w')
            fd.write(doc.toprettyxml())
            fd.close()
        else:
            prstate.toXML(file=filename)

    def write_toXML(self, datainfo=None, state=None):
        """
        Write toXML, a helper for write()

        : return: xml doc
        """
        if datainfo is None:
            datainfo = Data1D(x=[], y=[])
        elif not issubclass(datainfo.__class__, Data1D):
            msg = "The cansas writer expects a Data1D "
            msg += "instance: %s" % str(datainfo.__class__.__name__)
            raise RuntimeError(msg)

        # Create basic XML document
        doc, sasentry = self._to_xml_doc(datainfo)

        # Add the invariant information to the XML document
        if state is not None:
            doc = state.toXML(doc=doc, entry_node=sasentry)

        return doc
