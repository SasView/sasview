"""
ASCII 2D Loader
"""
from sas.sascalc.dataloader.data_info import Data2D
from sas.sascalc.file_converter.nxcansas_writer import NXcanSASWriter
import numpy as np

# ISIS 2D ASCII File Format
# line: property
# 0: File header
# 1: q_x axis label and units
# 2: q_y axis label and units
# 3: Intensity axis label and units
# 4: nUseRec - number of lines of user content following this line
# 5 - 5+nUseRec: user content
# Number of qx points
# List of qx points
# Number of qy points
# List of qy points
# numqx numqy scale

class ASCII2DLoader(object):

    def __init__(self, data_path):
        self.data_path = data_path

    def load(self):
        file_handle = open(self.data_path, 'r')
        file_buffer = file_handle.read()
        all_lines = file_buffer.splitlines()

        def _load_qs(lines, start_line, num_points):
            qs = np.zeros(num_points)
            n = start_line
            filled = 0
            while filled < num_points:
                row = np.fromstring(lines[n], dtype=np.float32, sep=' ')
                qs[filled:filled+len(row)] = row
                filled += len(row)
                n += 1
            return n, qs

        # Skip nUseRec lines
        current_line = 4
        nUseRec = int(all_lines[current_line].strip()[0])
        current_line += nUseRec + 1

        # Read qx data
        num_qs = int(all_lines[current_line].strip())
        current_line += 1
        current_line, qx = _load_qs(all_lines, current_line, num_qs)

        # Read qy data
        num_qs = int(all_lines[current_line].strip())
        current_line += 1
        current_line, qy = _load_qs(all_lines, current_line, num_qs)

        # dimensions: [width, height, scale]
        dimensions = np.fromstring(all_lines[current_line], dtype=np.float32, sep=' ')
        width = int(dimensions[0])
        height = int(dimensions[1])

        # More qx and/or qy points can be provided than are actually used
        qx = qx[:width]
        qy = qy[:height]

        current_line += 1
        # iflag = 1 => Only intensity data (not dealt with here)
        # iflag = 2 => q axis and intensity data
        # iflag = 3 => q axis, intensity and error data
        iflag = int(all_lines[current_line].strip()[0])
        current_line += 1

        current_line, I = _load_qs(all_lines, current_line, width*height)
        dI = np.zeros(width*height)

        if iflag == 3:
            _, dI = _load_qs(all_lines, current_line, width*height)

        # Format data for use with Data2D
        qx = list(qx) * height
        qy = np.array([[y] * width for y in qy]).flatten()

        data = Data2D(qx_data=qx, qy_data=qy, data=I, err_data=dI)

        return data
