"""
ASCII 2D Loader
"""
from sas.sascalc.dataloader.data_info import Data2D
from sas.sascalc.file_converter.nxcansas_writer import NXcanSASWriter
import numpy as np

# ISIS 2D ASCII File Format
# http://www.isis.stfc.ac.uk/instruments/loq/software/colette-ascii-file-format-descriptions9808.pdf
# line: property
# 0: File header
# 1: q_x axis label and units
# 2: q_y axis label and units
# 3: Intensity axis label and units
# 4: n_use_rec - number of lines of user content following this line
# 5 to (5+n_use_rec): user content
# Number of qx points
# List of qx points
# Number of qy points
# List of qy points
# numqx numqy scale

class ASCII2DLoader(object):

    def __init__(self, data_path):
        """
        :param data_path: The path to the file to load
        """
        self.data_path = data_path

    def load(self):
        """
        Load the data from the file into a Data2D object

        :return: A Data2D instance containing data from the file
        :raises ValueError: Raises a ValueError if the file is incorrectly
            formatted
        """
        with open(self.data_path, 'r') as file_handle:
            file_buffer = file_handle.read()
            all_lines = file_buffer.splitlines()

            # Load num_points line-by-line from lines into a numpy array,
            # starting on line number start_line
            def _load_points(lines, start_line, num_points):
                qs = np.zeros(num_points)
                n = start_line
                filled = 0
                while filled < num_points:
                    row = np.fromstring(lines[n], dtype=np.float32, sep=' ')
                    qs[filled:filled+len(row)] = row
                    filled += len(row)
                    n += 1
                return n, qs

            current_line = 4
            try:
                # Skip n_use_rec lines
                n_use_rec = int(all_lines[current_line].strip()[0])
                current_line += n_use_rec + 1
                # Read qx data
                num_qs = int(all_lines[current_line].strip())
                current_line += 1
                current_line, qx = _load_points(all_lines, current_line, num_qs)

                # Read qy data
                num_qs = int(all_lines[current_line].strip())
                current_line += 1
                current_line, qy = _load_points(all_lines, current_line, num_qs)
            except ValueError as e:
                err_msg = "File incorrectly formatted.\n"
                if str(e).find('broadcast') != -1:
                    err_msg += "Incorrect number of q data points provided. "
                    err_msg += "Expected {}.".format(num_qs)
                elif str(e).find('invalid literal') != -1:
                    err_msg += ("Expected integer on line {}. "
                        "Instead got '{}'").format(current_line + 1,
                            all_lines[current_line])
                else:
                    err_msg += str(e)
                raise ValueError(err_msg)

            # dimensions: [width, height, scale]
            try:
                dimensions = np.fromstring(all_lines[current_line],
                    dtype=np.float32, sep=' ')
                if len(dimensions) != 3: raise ValueError()
                width = int(dimensions[0])
                height = int(dimensions[1])
            except ValueError as e:
                err_msg = "File incorrectly formatted.\n"
                err_msg += ("Expected line {} to be of the form: <num_qx> "
                    "<num_qy> <scale>.").format(current_line + 1)
                err_msg += " Instead got '{}'.".format(all_lines[current_line])
                raise ValueError(err_msg)

            if width > len(qx) or height > len(qy):
                err_msg = "File incorrectly formatted.\n"
                err_msg += ("Line {} says to use {}x{} points. "
                    "Only {}x{} provided.").format(current_line + 1, width,
                    height, len(qx), len(qy))
                raise ValueError(err_msg)

            # More qx and/or qy points can be provided than are actually used
            qx = qx[:width]
            qy = qy[:height]

            current_line += 1
            # iflag = 1 => Only intensity data (not dealt with here)
            # iflag = 2 => q axis and intensity data
            # iflag = 3 => q axis, intensity and error data
            try:
                iflag = int(all_lines[current_line].strip()[0])
                if iflag <= 0 or iflag > 3: raise ValueError()
            except:
                err_msg = "File incorrectly formatted.\n"
                iflag = all_lines[current_line].strip()[0]
                err_msg += ("Expected iflag on line {} to be 1, 2 or 3. "
                    "Instead got '{}'.").format(current_line+1, iflag)
                raise ValueError(err_msg)

            current_line += 1

            try:
                current_line, I = _load_points(all_lines, current_line,
                    width * height)
                dI = np.zeros(width*height)

                # Load error data if it's provided
                if iflag == 3:
                    _, dI = _load_points(all_lines, current_line, width*height)
            except Exception as e:
                err_msg = "File incorrectly formatted.\n"
                if str(e).find("list index") != -1:
                    err_msg += ("Incorrect number of data points. Expected {}"
                        " intensity").format(width * height)
                    if iflag == 3:
                        err_msg += " and error"
                    err_msg += " points."
                else:
                    err_msg += str(e)
                raise ValueError(err_msg)

            # Format data for use with Data2D
            qx = list(qx) * height
            qy = np.array([[y] * width for y in qy]).flatten()

            data = Data2D(qx_data=qx, qy_data=qy, data=I, err_data=dI)

        return data
