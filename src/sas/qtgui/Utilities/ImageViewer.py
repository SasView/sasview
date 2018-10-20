"""
Image viewer widget.
"""
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import os
import logging
import numpy as np
import matplotlib
matplotlib.interactive(False)
import matplotlib.image as mpimg

from sas.sascalc.dataloader.manipulations import reader2D_converter

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.Plotter2D import Plotter2D
from sas.qtgui.Plotting.PlotterData import Data2D
from sas.sascalc.dataloader.data_info import Detector

# Local UI
from sas.qtgui.Utilities.UI.ImageViewerUI import Ui_ImageViewerUI
from sas.qtgui.Utilities.UI.ImageViewerOptionsUI import Ui_ImageViewerOptionsUI

class ImageViewer(QtWidgets.QMainWindow, Ui_ImageViewerUI):
    """
    Implemented as QMainWindow to enable easy menus
    """
    def __init__(self, parent=None):
        super(ImageViewer, self).__init__(parent._parent)

        self.parent = parent
        self.setupUi(self)

        # add plotter to the frame
        self.plotter = None
        self.hbox = None

        # disable menu items on empty canvas
        self.disableMenus()

        # set up signal callbacks
        self.addCallbacks()

        # set up menu item triggers
        self.addTriggers()

    def addCallbacks(self):
        pass

    def disableMenus(self):
        """
        All menu items but "Load File" and "Help" should be disabled
        when no data is present
        """
        self.actionSave_Image.setEnabled(False)
        self.actionPrint_Image.setEnabled(False)
        self.actionCopy_Image.setEnabled(False)
        self.actionConvert_to_Data.setEnabled(False)

    def enableMenus(self):
        """
        Enable all menu items when data is present
        """
        self.actionSave_Image.setEnabled(True)
        self.actionPrint_Image.setEnabled(True)
        self.actionCopy_Image.setEnabled(True)
        self.actionConvert_to_Data.setEnabled(True)

    def addTriggers(self):
        """
        Trigger definitions for all menu/toolbar actions.
        """
        # File
        self.actionLoad_Image.triggered.connect(self.actionLoadImage)
        self.actionSave_Image.triggered.connect(self.actionSaveImage)
        self.actionPrint_Image.triggered.connect(self.actionPrintImage)
        # Edit
        self.actionCopy_Image.triggered.connect(self.actionCopyImage)
        # Image
        self.actionConvert_to_Data.triggered.connect(self.actionConvertToData)
        # Help
        self.actionHow_To.triggered.connect(self.actionHowTo)

    def actionLoadImage(self):
        """
        Image loader given files extensions
        """
        wildcards = "Images (*.bmp *.gif *jpeg *jpg *.png *tif *.tiff) ;;"\
                    "Bitmap (*.bmp *.BMP);; "\
                    "GIF (*.gif *.GIF);; "\
                    "JPEG (*.jpg  *.jpeg *.JPG *.JPEG);; "\
                    "PNG (*.png *.PNG);; "\
                    "TIFF (*.tif *.tiff *.TIF *.TIFF);; "\
                    "All files (*.*)"

        filepath = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose a file", "", wildcards)[0]

        if filepath:
            self.showImage(filepath)

    def actionSaveImage(self):
        """
        Use the internal MPL method for saving to file
        """
        if self.plotter is not None:
            self.plotter.onImageSave()

    def actionPrintImage(self):
        """
        Display printer dialog and print the MPL widget area
        """
        if self.plotter is not None:
            self.plotter.onImagePrint()

    def actionCopyImage(self):
        """
        Copy MPL widget area to buffer
        """
        if self.plotter is not None:
           self.plotter.onClipboardCopy()

    def actionConvertToData(self):
        """
        Show the options dialog and if accepted, send data to conversion
        """
        options = ImageViewerOptions(self)
        if options.exec_() != QtWidgets.QDialog.Accepted:
            return

        (xmin, xmax, ymin, ymax, zscale) = options.getState()
        image = self.image
        try:
            self.convertImage(image, xmin, xmax, ymin, ymax, zscale)
        except:
            err_msg = "Error occurred while converting Image to Data."
            logging.error(err_msg)

        pass

    def actionHowTo(self):
        ''' Send the image viewer help URL to the help viewer '''
        location = "/user/qtgui/Calculators/image_viewer_help.html"
        self.parent.showHelp(location)

    def addPlotter(self):
        """
        Add a new plotter to the frame
        """
        self.plotter = Plotter2D(self, quickplot=True)

        # remove existing layout
        if self.hbox is not None:
            for i in range(self.hbox.count()):
                layout_item = self.hbox.itemAt(i)
                self.hbox.removeItem(layout_item)
            self.hbox.addWidget(self.plotter)
        else:
            # add the plotter to the QLayout
            self.hbox = QtWidgets.QHBoxLayout()
            self.hbox.addWidget(self.plotter)
            self.imgFrame.setLayout(self.hbox)

    def showImage(self, filename):
        """
        Show the requested image in the main frame
        """
        self.filename = os.path.basename(filename)
        _, extension = os.path.splitext(self.filename)
        try:
            # Note that matplotlib only reads png natively.
            # Any other formats (tiff, jpeg, etc) are passed
            # to PIL which seems to have a problem in version
            # 1.1.7 that causes a close error which shows up in 
            # the log file.  This does not seem to have any adverse
            # effects.  PDB   --- September 17, 2017.
            self.image = mpimg.imread(filename)
            self.is_png = extension.lower() == '.png'
            self.addPlotter()
            ax = self.plotter.ax
            flipped_image = np.flipud(self.image)
            origin = None
            if self.is_png:
                origin='lower'
            self.plotter.imageShow(flipped_image, origin=origin)
            if not self.is_png:
                ax.set_ylim(ax.get_ylim()[::-1])
            ax.set_xlabel('x [pixel]')
            ax.set_ylabel('y [pixel]')
            self.plotter.figure.subplots_adjust(left=0.15, bottom=0.1,
                                        right=0.95, top=0.95)
            title = 'Picture: ' + self.filename
            self.setWindowTitle(title)
            self.plotter.draw()
        except IOError as ex:
            err_msg = "Failed to load '%s'.\n" % self.filename
            logging.error(err_msg)
            return
        except Exception as ex:
            err_msg = "Failed to show '%s'.\n" % self.filename
            logging.error(err_msg)
            return

        # Loading successful - enable menu items
        self.enableMenus()

    def convertImage(self, rgb, xmin, xmax, ymin, ymax, zscale):
        """
        Convert image to data2D
        """
        x_len = len(rgb[0])
        y_len = len(rgb)
        x_vals = np.linspace(xmin, xmax, num=x_len)
        y_vals = np.linspace(ymin, ymax, num=y_len)
        # Instantiate data object
        output = Data2D()
        output.filename = self.filename
        output.id = output.filename
        detector = Detector()
        detector.pixel_size.x = None
        detector.pixel_size.y = None
        # Store the sample to detector distance
        detector.distance = None
        output.detector.append(detector)
        # Initiazed the output data object
        output.data = zscale * self.rgb2gray(rgb)
        output.err_data = np.zeros([x_len, y_len])
        output.mask = np.ones([x_len, y_len], dtype=bool)
        output.xbins = x_len
        output.ybins = y_len
        output.x_bins = x_vals
        output.y_bins = y_vals
        output.qx_data = np.array(x_vals)
        output.qy_data = np.array(y_vals)
        output.xmin = xmin
        output.xmax = xmax
        output.ymin = ymin
        output.ymax = ymax
        output.xaxis('\\rm{Q_{x}}', '\AA^{-1}')
        output.yaxis('\\rm{Q_{y}}', '\AA^{-1}')
        # Store loading process information
        output.meta_data['loader'] = self.filename.split('.')[-1] + "Reader"
        output.is_data = True
        try:
            output = reader2D_converter(output)
        except Exception as ex:
            err_msg = "Image conversion failed: '%s'.\n" % str(ex)
            logging.error(err_msg)

        # Create item and add to the data explorer
        try:
            item = GuiUtils.createModelItemWithPlot(output, output.filename)
            self.parent.communicate.updateModelFromPerspectiveSignal.emit(item)
        except Exception as ex:
            err_msg = "Failed to create new index '%s'.\n" % str(ex)
            logging.error(err_msg)

    def rgb2gray(self, rgb):
        """
        RGB to Grey
        """
        if self.is_png:
            # png image limits: 0 to 1, others 0 to 255
            #factor = 255.0
            rgb = rgb[::-1]
        if rgb.ndim == 2:
            grey = np.rollaxis(rgb, axis=0)
        else:
            red, green, blue = np.rollaxis(rgb[..., :3], axis= -1)
            grey = 0.299 * red + 0.587 * green + 0.114 * blue
        max_i = rgb.max()
        factor = 255.0 / max_i
        grey *= factor
        return np.array(grey)

class ImageViewerOptions(QtWidgets.QDialog, Ui_ImageViewerOptionsUI):
    """
    Logics for the image viewer options UI
    """
    def __init__(self, parent=None):
        super(ImageViewerOptions, self).__init__(parent)

        self.parent = parent
        self.setupUi(self)

        # fill in defaults
        self.addDefaults()

        # add validators
        self.addValidators()

    def addDefaults(self):
        """
        Fill out textedits with default values
        """
        zscale_default = 1.0
        xmin_default = -0.3
        xmax_default = 0.3
        ymin_default = -0.3
        ymax_default = 0.3

        self.txtZmax.setText(str(zscale_default))
        self.txtXmin.setText(str(xmin_default))
        self.txtXmax.setText(str(xmax_default))
        self.txtYmin.setText(str(ymin_default))
        self.txtYmax.setText(str(ymax_default))

    def addValidators(self):
        """
        Define simple validators on line edits
        """
        self.txtXmin.setValidator(GuiUtils.DoubleValidator())
        self.txtXmax.setValidator(GuiUtils.DoubleValidator())
        self.txtYmin.setValidator(GuiUtils.DoubleValidator())
        self.txtYmax.setValidator(GuiUtils.DoubleValidator())
        zvalidator = GuiUtils.DoubleValidator()
        zvalidator.setBottom(0.0)
        zvalidator.setTop(255.0)
        self.txtZmax.setValidator(zvalidator)

    def getState(self):
        """
        return current state of the widget
        """
        zscale = float(self.txtZmax.text())
        xmin = float(self.txtXmin.text())
        xmax = float(self.txtXmax.text())
        ymin = float(self.txtYmin.text())
        ymax = float(self.txtYmax.text())

        return (xmin, xmax, ymin, ymax, zscale)

