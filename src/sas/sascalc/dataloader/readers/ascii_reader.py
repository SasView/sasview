"""
    Generic multi-column ASCII data reader
"""
############################################################################
# This software was developed by the University of Tennessee as part of the
# Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
# project funded by the US National Science Foundation.
# If you use DANSE applications to do scientific research that leads to
# publication, we ask that you acknowledge the use of the software with the
# following sentence:
# This work benefited from DANSE software developed under NSF award DMR-0520547.
# copyright 2008, University of Tennessee
#############################################################################

import logging
from sas.sascalc.dataloader.file_reader_base_class import FileReader
from sas.sascalc.dataloader.data_info import DataInfo, plottable_1D
from sas.sascalc.dataloader.loader_exceptions import FileContentsException,\
    DefaultReaderException

logger = logging.getLogger(__name__)


class Reader(FileReader):
    """
    Class to load ascii files (2, 3 or 4 columns).
    """
    # File type
    type_name = "ASCII"
    # Wildcards
    type = ["ASCII files (*.txt)|*.txt",
            "ASCII files (*.dat)|*.dat",
            "ASCII files (*.abs)|*.abs",
            "CSV files (*.csv)|*.csv"]
    # List of allowed extensions
    ext = ['.txt', '.dat', '.abs', '.csv']
    # Flag to bypass extension check
    allow_all = True
    # data unless that is the only data
    min_data_pts = 5

    def get_file_contents(self):
        """
        Get the contents of the file
        """

        buff = self.readall()
        filepath = self.f_open.name
        lines = buff.splitlines()
        self.output = []
        self.current_datainfo = DataInfo()
        self.current_datainfo.filename = filepath
        self.reset_data_list(len(lines))

        # The first good line of data will define whether
        # we have 2-column or 3-column ascii
        has_error_dx = None
        has_error_dy = None

        # Initialize counters for data lines and header lines.
        is_data = False
        # More than "5" lines of data is considered as actual
        # To count # of current data candidate lines
        candidate_lines = 0
        # To count total # of previous data candidate lines
        candidate_lines_previous = 0
        # Current line number
        line_no = 0
        # minimum required number of columns of data
        lentoks = 2
        for line in lines:
            toks = self.splitline(line.strip())
            # To remember the number of columns in the current line of data
            new_lentoks = len(toks)
            try:
                if new_lentoks == 0:
                    # If the line is blank, skip and continue on
                    # In case of breaks within data sets.
                    continue
                elif new_lentoks != lentoks and is_data:
                    # If a footer is found, break the loop and save the data
                    break
                elif new_lentoks != lentoks and not is_data:
                    # If header lines are numerical
                    candidate_lines = 0
                    self.reset_data_list(len(lines) - line_no)

                self.current_dataset.x[candidate_lines] = float(toks[0])

                if new_lentoks > 1:
                    self.current_dataset.y[candidate_lines] = float(toks[1])

                # If a 3rd row is present, consider it dy
                if new_lentoks > 2:
                    self.current_dataset.dy[candidate_lines] = \
                        float(toks[2])
                    has_error_dy = True

                # If a 4th row is present, consider it dx
                if new_lentoks > 3:
                    self.current_dataset.dx[candidate_lines] = \
                        float(toks[3])
                    has_error_dx = True

                candidate_lines += 1
                # If 5 or more lines, this is considering the set data
                if candidate_lines >= self.min_data_pts:
                    is_data = True

                if is_data and new_lentoks >= 8:
                    msg = "This data looks like 2D ASCII data. Use the file "
                    msg += "converter tool to convert it to NXcanSAS."
                    raise FileContentsException(msg)

                # To remember the # of columns on the current line
                # for the next line of data
                lentoks = new_lentoks
                line_no += 1
            except ValueError:
                # ValueError is raised when non numeric strings conv. to float
                # It is data and meet non - number, then stop reading
                if is_data:
                    break
                # Delete the previously stored lines of data candidates if
                # the list is not data
                self.reset_data_list(len(lines) - line_no)
                lentoks = 2
                has_error_dx = None
                has_error_dy = None
                # Reset # of lines of data candidates
                candidate_lines = 0

        if not is_data:
            self.set_all_to_none()
            if self.extension in self.ext:
                msg = "ASCII Reader error: Fewer than five Q data points found "
                msg += "in {}.".format(filepath)
                raise FileContentsException(msg)
            else:
                msg = "ASCII Reader could not load the file {}".format(filepath)
                raise DefaultReaderException(msg)
        # Sanity check
        if has_error_dy and not len(self.current_dataset.y) == \
                len(self.current_dataset.dy):
            msg = "ASCII Reader error: Number of I and dI data points are"
            msg += " different in {}.".format(filepath)
            # TODO: Add error to self.current_datainfo.errors instead?
            self.set_all_to_none()
            raise FileContentsException(msg)
        if has_error_dx and not len(self.current_dataset.x) == \
                len(self.current_dataset.dx):
            msg = "ASCII Reader error: Number of Q and dQ data points are"
            msg += " different in {}.".format(filepath)
            # TODO: Add error to self.current_datainfo.errors instead?
            self.set_all_to_none()
            raise FileContentsException(msg)

        self.remove_empty_q_values()
        self.current_dataset.xaxis("\\rm{Q}", 'A^{-1}')
        self.current_dataset.yaxis("\\rm{Intensity}", "cm^{-1}")

        # Store loading process information
        self.current_datainfo.meta_data['loader'] = self.type_name
        self.send_to_output()
