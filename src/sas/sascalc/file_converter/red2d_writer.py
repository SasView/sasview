import os
import time
from sas.sascalc.dataloader.readers.red2d_reader import Reader as Red2DReader

class Red2DWriter(Red2DReader):

    def write(self, filename, data, thread):
        """
        Write to .dat

        :param filename: file name to write
        :param data: data2D
        """
        # Write the file
        fd = open(filename, 'w')
        t = time.localtime()
        time_str = time.strftime("%H:%M on %b %d %y", t)

        header_str = "Data columns are Qx - Qy - I(Qx,Qy)\n\nASCII data"
        header_str += " created at %s \n\n" % time_str
        # simple 2D header
        fd.write(header_str)
        # write qx qy I values
        for i in range(len(data.data)):
            if thread.isquit():
                fd.close()
                os.remove(filename)
                return False

            fd.write("%g  %g  %g\n" % (data.qx_data[i],
                                        data.qy_data[i],
                                       data.data[i]))

        fd.close()

        return True
