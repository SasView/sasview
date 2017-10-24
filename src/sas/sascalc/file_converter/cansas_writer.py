from sas.sascalc.dataloader.readers.cansas_reader import Reader as CansasReader
from sas.sascalc.dataloader.data_info import Data1D

import inspect

class CansasWriter(CansasReader):

    def write(self, filename, frame_data, sasentry_attrs=None):
        """
        Write the content of a Data1D as a CanSAS XML file

        :param filename: name of the file to write
        :param datainfo: Data1D object
        """
        # Create XML document
        doc, _ = self._to_xml_doc(frame_data, sasentry_attrs)
        # Write the file
        file_ref = open(filename, 'w')
        if self.encoding is None:
            self.encoding = "UTF-8"
        doc.write(file_ref, encoding=self.encoding,
                  pretty_print=True, xml_declaration=True)
        file_ref.close()


    def _to_xml_doc(self, frame_data, sasentry_attrs=None):
        """
        Create an XML document to contain the content of an array of Data1Ds

        :param frame_data: An array of Data1D objects
        """
        valid_class = all([issubclass(data.__class__, Data1D) for data in frame_data])
        if not valid_class:
            raise RuntimeError("The cansas writer expects an array of "
                "Data1D instances")

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

        # Use the first element in the array for writing metadata
        datainfo = frame_data[0]
        # Add Title to SASentry
        self.write_node(entry_node, "Title", datainfo.title)
        # Add Run to SASentry
        self._write_run_names(datainfo, entry_node)
        # Add Data info to SASEntry
        for data_info in frame_data:
            self._write_data(data_info, entry_node)
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

    def _write_data(self, datainfo, entry_node):
        """
        Writes the I and Q data to the XML file

        :param datainfo: The Data1D object the information is coming from
        :param entry_node: lxml node ElementTree object to be appended to
        """
        node = self.create_element("SASdata")
        self.append(node, entry_node)

        for i in range(len(datainfo.x)):
            point = self.create_element("Idata")
            node.append(point)
            self.write_node(point, "Q", datainfo.x[i],
                            {'unit': datainfo.x_unit})
            if len(datainfo.y) >= i:
                self.write_node(point, "I", datainfo.y[i],
                                {'unit': datainfo.y_unit})
            if datainfo.dy is not None and len(datainfo.dy) > i:
                self.write_node(point, "Idev", datainfo.dy[i],
                                {'unit': datainfo.y_unit})
            if datainfo.dx is not None and len(datainfo.dx) > i:
                self.write_node(point, "Qdev", datainfo.dx[i],
                                {'unit': datainfo.x_unit})
            if datainfo.dxw is not None and len(datainfo.dxw) > i:
                self.write_node(point, "dQw", datainfo.dxw[i],
                                {'unit': datainfo.x_unit})
            if datainfo.dxl is not None and len(datainfo.dxl) > i:
                self.write_node(point, "dQl", datainfo.dxl[i],
                                {'unit': datainfo.x_unit})
