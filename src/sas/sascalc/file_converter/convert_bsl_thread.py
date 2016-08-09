import os
import wx
from sas.sascalc.data_util.calcthread import CalcThread
from sas.sascalc.dataloader.data_info import Data2D
from sas.sascalc.file_converter.bsl_loader import BSLLoader
from sas.sascalc.dataloader.readers.red2d_reader import Reader as Red2DWriter

class ConvertBSLThread(CalcThread):

    def __init__(self, parent, in_file, out_file,
        updatefn=None, completefn=None):
        CalcThread.__init__(self, updatefn=updatefn, completefn=completefn)
        self.parent = parent
        self.in_file = in_file
        self.out_file = out_file

    def compute(self):
        self.ready(delay=0.0)
        self.update(msg="Extracting data...")

        try:
            x, y, frame_data = self._extract_bsl_data(self.in_file)
        except Exception as e:
            self.ready()
            self.update(exception=e)
            self.complete(success=False)
            return

        if x == None and y == None and frame_data == None:
            # Cancelled by user
            self.ready()
            self.update(msg="Conversion cancelled")
            self.complete(success=False)
            return

        if self.isquit():
            self.complete(success=False)
            return

        self.ready(delay=0.0)
        self.update(msg="Exporting data...")

        try:
            completed = self._convert_to_red2d(self.out_file, x, y, frame_data)
        except Exception as e:
            self.ready()
            self.update(exception=e)
            self.complete(success=False)
            return

        self.complete(success=completed)


    def _extract_bsl_data(self, filename):
        """
        Extracts data from a 2D BSL file

        :param filename: The header file to extract the data from
        :return x_data: A 1D array containing all the x coordinates of the data
        :return y_data: A 1D array containing all the y coordinates of the data
        :return frame_data: A dictionary of the form frame_number: data, where
        data is a 2D numpy array containing the intensity data
        """
        loader = BSLLoader(filename)
        frames = [0]
        should_continue = True

        if loader.n_frames > 1:
            params = self.parent.ask_frame_range(loader.n_frames)
            frames = params['frames']
        elif loader.n_rasters == 1 and loader.n_frames == 1:
            message = ("The selected file is an OTOKO file. Please select the "
            "'OTOKO 1D' option if you wish to convert it.")
            dlg = wx.MessageDialog(self.parent,
            message,
            'Error!',
            wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            should_continue = False
            dlg.Destroy()
        else:
            message = ("The selected data file only has 1 frame, it might be"
                " a multi-frame OTOKO file.\nContinue conversion?")
            dlg = wx.MessageDialog(self.parent,
            message,
            'Warning!',
            wx.YES_NO | wx.ICON_WARNING)
            should_continue = (dlg.ShowModal() == wx.ID_YES)
            dlg.Destroy()

        if not should_continue:
            return None, None, None

        frame_data = {}

        for frame in frames:
            loader.frame = frame
            frame_data[frame] = loader.load_data()

        # TODO: Tidy this up
        # Prepare axes values (arbitrary scale)
        x_data = []
        y_data = range(loader.n_pixels) * loader.n_rasters
        for i in range(loader.n_rasters):
            x_data += [i] * loader.n_pixels

        return x_data, y_data, frame_data

    def _convert_to_red2d(self, filepath, x, y, frame_data):
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
        filename = os.path.split(filepath)[-1]
        filepath = os.path.split(filepath)[0]
        writer = Red2DWriter()

        for i, frame in frame_data.iteritems():
            # If more than 1 frame is being exported, append the frame
            # number to the filename
            if self.isquit():
                return False

            if len(frame_data) > 1:
                frame_filename = filename.split('.')
                frame_filename[0] += str(i+1)
                frame_filename = '.'.join(frame_filename)
            else:
                frame_filename = filename

            data_i = frame.reshape((len(x),1))
            data_info = Data2D(data=data_i, qx_data=x, qy_data=y)
            writer.write(os.path.join(filepath, frame_filename), data_info)
            self.ready()
            self.update(msg="Written file: {}".format(frame_filename))

        return True
