from sas.sascalc.dataloader.readers.cansas_reader import Reader as CansasReader
from sas.sascalc.dataloader.data_info import Data1D

import inspect

class CansasWriter(CansasReader):

    def write(self, filename, datainfo, sasentry_attrs=None):
        """
        Write the content of a Data1D as a CanSAS XML file

        :param filename: name of the file to write
        :param datainfo: Data1D object
        """
        # Create XML document
        doc, _ = self._to_xml_doc(datainfo, sasentry_attrs)
        # Write the file
        file_ref = open(filename, 'w')
        if self.encoding == None:
            self.encoding = "UTF-8"
        doc.write(file_ref, encoding=self.encoding,
                  pretty_print=True, xml_declaration=True)
        file_ref.close()


    def _to_xml_doc(self, datainfo, sasentry_attrs=None):
        """
        Create an XML document to contain the content of a Data1D

        :param datainfo: Data1D object
        """
        if not issubclass(datainfo.__class__, Data1D):
            raise RuntimeError, "The cansas writer expects a Data1D instance"

        # Get PIs and create root element
        pi_string = self._get_pi_string()
        # Define namespaces and create SASroot object
        main_node = self._create_main_node()
        # Create ElementTree, append SASroot and apply processing instructions
        base_string = pi_string + self.to_string(main_node)
        base_element = self.create_element_from_string(base_string)
        doc = self.create_tree(base_element)
        # Create SASentry Element
        entry_node = self.create_element("SASentry", sasentry_attrs)
        root = doc.getroot()
        root.append(entry_node)

        # Add Title to SASentry
        self.write_node(entry_node, "Title", datainfo.title)
        # Add Run to SASentry
        self._write_run_names(datainfo, entry_node)
        # Add Data info to SASEntry
        self._write_data(datainfo, entry_node)
        # Transmission Spectrum Info
        self._write_trans_spectrum(datainfo, entry_node)
        # Sample info
        self._write_sample_info(datainfo, entry_node)
        # Instrument info
        instr = self._write_instrument(datainfo, entry_node)
        #   Source
        self._write_source(datainfo, instr)
        #   Collimation
        self._write_collimation(datainfo, instr)
        #   Detectors
        self._write_detectors(datainfo, instr)
        # Processes info
        self._write_process_notes(datainfo, entry_node)
        # Note info
        self._write_notes(datainfo, entry_node)
        # Return the document, and the SASentry node associated with
        #      the data we just wrote
        
        return doc, entry_node
