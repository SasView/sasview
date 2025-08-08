# pylint: disable=C0103, I1101
"""
FrameSelect class describes behaviour of the FrameSelect dialog

"""
from PySide6 import QtGui, QtWidgets

from .UI.FrameSelectUI import Ui_FrameSelect


class FrameSelect(QtWidgets.QDialog, Ui_FrameSelect):
    """
    Class to describe the behaviour of the Frame Selector widget
    """
    def __init__(self, parent=None, frames=1, isBSL=True):
        super(FrameSelect, self).__init__(parent)
        self.setupUi(self)

        self.n_frames = frames
        self.isBSL = isBSL
        self.firstFrame = None
        self.lastFrame = None
        self.increment = None

        self.setWindowTitle("Frame Select")

        self.addState()
        self.addSlots()
        self.addText()

    def addText(self):
        """
        Initialize view
        """
        instructions = (f"The file you've selected has {self.n_frames} frames. "
                        "Please select a subset of frames to convert to CanSAS "
                        "format")

        self.lblDescription.setText(instructions)
        self.lblDescription.setWordWrap(True)

        self.updateDisplay()

        if self.isBSL:
            self.chkSeparateFiles.setVisible(False)
            self.chkSeparateFiles.setEnabled(False)

    def addState(self):
        """
        Minor bookkeeping
        """
        self.firstFrame = 0
        self.lastFrame = self.n_frames-1
        self.increment = 1
        self.updateDisplay()

    def addSlots(self):
        """
        Describe behaviour of OK and Cancel buttons
        """
        self.cmdOK.clicked.connect(self.accept)
        self.cmdCancel.clicked.connect(self.reject)
        self.txtFirstFrame.setValidator(QtGui.QIntValidator(0, self.n_frames-1))
        self.txtLastFrame.setValidator(QtGui.QIntValidator(0, self.n_frames-1))
        self.txtIncrement.setValidator(QtGui.QIntValidator())
        self.txtFirstFrame.editingFinished.connect(self.onFirstChanged)
        self.txtLastFrame.editingFinished.connect(self.onLastChanged)
        self.txtIncrement.editingFinished.connect(self.onIncrementChanged)

    def updateDisplay(self):
        """
        manage model-view sync
        """
        self.txtFirstFrame.setText(str(self.firstFrame))
        self.txtLastFrame.setText(str(self.lastFrame))
        self.txtIncrement.setText(str(self.increment))

    def onFirstChanged(self):
        """
        Manage view-model sync
        """
        self.cmdOK.setEnabled(False)
        try:
            frame = int(self.txtFirstFrame.text())
        except ValueError:
            return
        if frame > self.lastFrame:
            return
        if frame < 0:
            return
        self.firstFrame = frame
        self.cmdOK.setEnabled(True)

    def onLastChanged(self):
        """
        Manage view-model sync
        """
        self.cmdOK.setEnabled(False)
        try:
            frame = int(self.txtLastFrame.text())
        except ValueError:
            return
        if frame < self.firstFrame:
            return
        if frame < 0:
            return
        self.lastFrame = frame
        self.cmdOK.setEnabled(True)

    def onIncrementChanged(self):
        """
        Manage view-model sync
        """
        self.cmdOK.setEnabled(False)
        try:
            inc = int(self.txtIncrement.text())
        except ValueError:
            return
        if inc < 0:
            return
        self.increment = inc
        self.cmdOK.setEnabled(True)

    def getFrames(self):
        """
        Accessor for state values
        """
        return (self.firstFrame, self.lastFrame, self.increment)
