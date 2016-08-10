import os
import wx
from sas.sascalc.data_util.calcthread import CalcThread
from sas.sascalc.dataloader.data_info import Data2D
from sas.sascalc.file_converter.red2d_writer import Red2DWriter

import sys

if sys.platform.count("darwin") > 0:
    import time
    stime = time.time()

    def clock():
        return time.time() - stime

    def sleep(t):
        return time.sleep(t)
else:
    from time import clock
    from time import sleep

class ConvertBSLThread(CalcThread):

    def __init__(self, xy, frame_data, out_file, frame_number=None,
        updatefn=None, completefn=None):
        CalcThread.__init__(self, updatefn=updatefn, completefn=completefn)
        (self.x_data, self.y_data) = xy
        self.frame_data = frame_data
        self.frame_number = frame_number
        self.frame_filename = ''
        self.out_file = out_file

    def compute(self):
        try:
            completed = self._convert_to_red2d()
        except Exception as e:
            self.ready()
            self.update(exception=e)
            self.complete(success=False)
            return

        self.complete(success=completed)

    def isquit(self):
        """Check for interrupts.  Should be called frequently to
        provide user responsiveness.  Also yields to other running
        threads, which is required for good performance on OS X."""

        # # Only called from within the running thread so no need to lock
        # if self._running and self.yieldtime > 0 \
        #     and clock() > self._time_for_nap:
        #     sleep(self.yieldtime)
        #     self._time_for_nap = clock() + self.worktime
        return self._interrupting

    def _convert_to_red2d(self):
        """
        Writes Data2D objects to Red2D .dat files. If more than one frame is
        provided, the frame number will be appended to the filename of each
        file written.

        :param filepath: The filepath to write to
        :param x: The x column of the data
        :param y: The y column of the data
        :param frame_data: A dictionary of the form frame_number: data, where
        data is a 2D numpy array containing the intensity data

        :return: True if export completed, False if export cancelled by user
        """
        filename = os.path.split(self.out_file)[-1]
        filepath = os.path.split(self.out_file)[0]
        writer = Red2DWriter()

        if self.isquit():
            return False

        if self.frame_number is not None:
            frame_filename = filename.split('.')
            frame_filename[0] += str(self.frame_number)
            frame_filename = '.'.join(frame_filename)
        else:
            frame_filename = filename

        self.ready()
        self.update(msg="Writing file: {}".format(frame_filename))
        data_i = self.frame_data.reshape((len(self.x_data),1))
        data_info = Data2D(data=data_i, qx_data=self.x_data, qy_data=self.y_data)
        success = writer.write(os.path.join(filepath, frame_filename), data_info, self)

        # Used by ConverterPanel.conversion_complete to notify user that file
        # has been written (or that there was an error)
        self.frame_filename = frame_filename

        return success
