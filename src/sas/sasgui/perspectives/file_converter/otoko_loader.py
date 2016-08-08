"""
Here we handle loading of "OTOKO" data (for more info about this format see
the comment in load_bsl_data).  Given the paths of header and data files, we
aim to load the data into numpy arrays for use later.
"""

import itertools
import os
import struct
import numpy as np

class CStyleStruct:
    """A nice and easy way to get "C-style struct" functionality."""
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

class OTOKOParsingError(Exception):
    pass

class OTOKOData:
    def __init__(self, q_axis, data_axis):
        self.q_axis = q_axis
        self.data_axis = data_axis

class OTOKOLoader(object):

    def __init__(self, qaxis_path, data_path):
        self.qaxis_path = qaxis_path
        self.data_path = data_path

    def load_bsl_data(self):
        """
        Loads "OTOKO" data, which is a format that stores each axis separately.
        An axis is represented by a "header" file, which in turn will give details
        of one or more binary files where the actual data is stored.

        Given the paths of two header files, this function will load each axis in
        turn.  If loading is successfull then an instance of the OTOKOData class
        will be returned, else an exception will be raised.

        For more information on the OTOKO file format, please see:
        http://www.diamond.ac.uk/Home/Beamlines/small-angle/SAXS-Software/CCP13/
        XOTOKO.html

        The BSL format, which is based on OTOKO, is also supported.  Find out more
        about the BSL format at http://www.diamond.ac.uk/Home/Beamlines/small-angle
        /SAXS-Software/CCP13/BSL.html.
        """
        q_axis    = self._load_bsl_axis(self.qaxis_path)
        data_axis = self._load_bsl_axis(self.data_path)

        return OTOKOData(q_axis, data_axis)

    def _load_bsl_axis(self, header_path):
        """
        Loads an "OTOKO" axis, given the header file path.  Essentially, the
        header file contains information about the data in the form of integer
        "indicators", as well as the names of each of the binary files which are
        assumed to be in the same directory as the header.
        """
        if not os.path.exists(header_path):
            raise OTOKOParsingError("The header file %s does not exist." % header_path)

        binary_file_info_list = []
        total_frames = 0
        header_dir = os.path.dirname(os.path.abspath(header_path))

        with open(header_path, "r") as header_file:
            lines = header_file.readlines()
            if len(lines) < 4:
                raise OTOKOParsingError("Expected more lines in %s." % header_path)

            info = lines[0] + lines[1]

            def pairwise(iterable):
                """
                s -> (s0,s1), (s2,s3), (s4, s5), ...
                From http://stackoverflow.com/a/5389547/778572
                """
                a = iter(iterable)
                return itertools.izip(a, a)

            for indicators, filename in pairwise(lines[2:]):
                indicators = indicators.split()

                if len(indicators) != 10:
                    raise OTOKOParsingError(
                        "Expected 10 integer indicators on line 3 of %s." \
                        % header_path)
                if not all([i.isdigit() for i in indicators]):
                    raise OTOKOParsingError(
                        "Expected all indicators on line 3 of %s to be integers." \
                        % header_path)

                binary_file_info = CStyleStruct(
                    # The indicators at indices 4 to 8 are always zero since they
                    # have been reserved for future use by the format.  Also, the
                    # "last_file" indicator seems to be there for legacy reasons,
                    # as it doesn't appear to be something we have to bother
                    # enforcing correct use of; we just define the last file as
                    # being the last file in the list.
                    file_path  = os.path.join(header_dir, filename.strip()),
                    n_channels = int(indicators[0]),
                    n_frames   = int(indicators[1]),
                    dimensions = int(indicators[2]),
                    swap_bytes = int(indicators[3]) == 0,
                    last_file  = int(indicators[9]) == 0 # We don't use this.
                )
                binary_file_info_list.append(binary_file_info)

                total_frames += binary_file_info.n_frames

        # Check that all binary files are listed in the header as having the same
        # number of channels, since I don't think CorFunc can handle ragged data.
        all_n_channels = [info.n_channels for info in binary_file_info_list]
        if not all(all_n_channels[0] == c for c in all_n_channels):
            raise OTOKOParsingError(
                "Expected all binary files listed in %s to have the same number of channels." % header_path)

        data = np.zeros(shape=(total_frames, all_n_channels[0]))
        frames_so_far = 0

        for info in binary_file_info_list:
            if not os.path.exists(info.file_path):
                raise OTOKOParsingError(
                    "The data file %s does not exist." % info.file_path)

            with open(info.file_path, "rb") as binary_file:
                # Ideally we'd like to use numpy's fromfile() to read in binary
                # data, but we are forced to roll our own float-by-float file
                # reader because of the rules imposed on us by the file format;
                # namely, if the swap indicator flag has been raised then the bytes
                # of each float occur in reverse order.
                for frame in range(info.n_frames):
                    for channel in range(info.n_channels):
                        b = bytes(binary_file.read(4))
                        if info.swap_bytes:
                            b = b[::-1] # "Extended slice" syntax, used to reverse.
                        value = struct.unpack('f', b)[0]
                        data[frames_so_far + frame][channel] = value

                frames_so_far += info.n_frames

        return CStyleStruct(
            header_path = header_path,
            data = data,
            binary_file_info_list = binary_file_info_list,
            header_info = info
        )
