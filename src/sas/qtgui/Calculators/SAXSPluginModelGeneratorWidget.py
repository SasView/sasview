import os

from PySide6 import QtCore, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.CustomGUI.CodeEditor import QCodeEditor


class RigidBodyRefinementWidget(QtWidgets.QDialog):
    """
    Dialog with file-load fields for a PDB file and a data file,
    a code editor, and a Finish button.
    """

    finished = QtCore.Signal(str)

    def __init__(self, parent=None, initial_text: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Rigid-body refinement")
        self.resize(800, 600)

        self._buildUI()
        self._connectSignals()

        if initial_text:
            self.editor.setPlainText(initial_text)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _buildUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # PDB file row
        pdb_layout = QtWidgets.QHBoxLayout()
        pdb_layout.addWidget(QtWidgets.QLabel("PDB file:"))
        self.txtPdbFile = QtWidgets.QLineEdit()
        self.txtPdbFile.setReadOnly(True)
        self.txtPdbFile.setPlaceholderText("No file loaded")
        pdb_layout.addWidget(self.txtPdbFile)
        self.btnLoadPdb = QtWidgets.QPushButton("Browse...")
        pdb_layout.addWidget(self.btnLoadPdb)
        layout.addLayout(pdb_layout)

        # Data file row
        data_layout = QtWidgets.QHBoxLayout()
        data_layout.addWidget(QtWidgets.QLabel("Data file:"))
        self.txtDataFile = QtWidgets.QLineEdit()
        self.txtDataFile.setReadOnly(True)
        self.txtDataFile.setPlaceholderText("No file loaded")
        data_layout.addWidget(self.txtDataFile)
        self.btnLoadData = QtWidgets.QPushButton("Browse...")
        data_layout.addWidget(self.btnLoadData)
        layout.addLayout(data_layout)

        # Code editor
        self.editor = QCodeEditor(self)
        self.editor.setFont(GuiUtils.getMonospaceFont())
        layout.addWidget(self.editor)

        # Bottom button row
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        self.btnFinish = QtWidgets.QPushButton("Finish")
        self.btnFinish.setDefault(True)
        button_layout.addWidget(self.btnFinish)
        layout.addLayout(button_layout)

    # ------------------------------------------------------------------
    # Signal connections
    # ------------------------------------------------------------------

    def _connectSignals(self):
        self.btnLoadPdb.clicked.connect(self._onLoadPdb)
        self.btnLoadData.clicked.connect(self._onLoadData)
        self.btnFinish.clicked.connect(self._onFinish)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _onLoadPdb(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open PDB file", "",
            "PDB files (*.pdb *.PDB);;All files (*.*)"
        )
        if path:
            self.txtPdbFile.setText(os.path.basename(path))
            self.on_pdb_load(path)

    def _onLoadData(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open data file", "",
            "Data files (*.dat *.DAT *.txt *.csv);;All files (*.*)"
        )
        if path:
            self.txtDataFile.setText(os.path.basename(path))
            self.on_data_load(path)

    def on_pdb_load(self, path: str):
        """Called after a PDB file is chosen. Override to add custom behaviour."""
        pdbfile = os.path.basename(path)
        self.write_load_block(pdbfile)

    def on_data_load(self, path: str):
        """Called after a data file is chosen. Override to add custom behaviour."""
        datafile = os.path.basename(path)
        self.write_load_block(datafile)

    def rebuild(self):
        """Rebuild the editor text to reflect any changes to the load block."""
        return

    def static_vars(**kwargs):
        def decorate(func):
            for k in kwargs:
                setattr(func, k, kwargs[k])
            return func
        return decorate

    @static_vars(pdbfile=None, datafile=None, splits=None)
    def write_load_block(self, pdbfile = None, datafile = None, splits = None):
        """Write the load block for the given files to the top of the editor."""
        if pdbfile:
            self.write_load_block.pdbfile = pdbfile
        if datafile:
            self.write_load_block.datafile = datafile
        if splits:
            self.write_load_block.splits = splits

        block = "load {\n"
        if self.write_load_block.pdbfile:  block += f"    pdb {pdbfile}\n"
        if self.write_load_block.datafile: block += f"    saxs {datafile}\n"
        if self.write_load_block.splits:   block += f"    split {splits.join(', ')}\n"
        block += "}\n\n"
        self._prependLine(block)

    def _prependLine(self, text: str):
        """Insert *text* as a new line at the top of the editor."""
        current = self.editor.toPlainText()
        self.editor.setPlainText(text + ("\n" + current if current else ""))

    def _onFinish(self):
        """Emit the current editor text and close the dialog."""
        self.finished.emit(self.editor.toPlainText())
        self.accept()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def getText(self) -> str:
        """Return the current contents of the code editor."""
        return self.editor.toPlainText()

    def setText(self, text: str):
        """Replace the entire contents of the code editor."""
        self.editor.setPlainText(text)
