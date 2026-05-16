import os

from PySide6 import QtCore, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.CustomGUI.CodeEditor import QCodeEditor


class RigidBodyRefinementUI(QtWidgets.QDialog):
    finished = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rigid-body refinement")
        self.resize(1200, 800)

        self._buildUI()
        self._connectSignals()

        self.plain_text = ""
        self.on_load_pdb_hook = None
        self.on_load_data_hook = None

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
        self.editor.textChanged.connect(self._onTextChanged)
        layout.addWidget(self.editor)

        # Bottom button row
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        self.btnFinish = QtWidgets.QPushButton("Finish")
        self.btnFinish.setDefault(True)
        button_layout.addWidget(self.btnFinish)
        layout.addLayout(button_layout)

    def _connectSignals(self):
        self.btnLoadPdb.clicked.connect(self._onLoadPDB)
        self.btnLoadData.clicked.connect(self._onLoadData)
        self.btnFinish.clicked.connect(self._onFinish)

    def _onLoadPDB(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open PDB file", "",
            "PDB files (*.pdb *.PDB);;All files (*.*)"
        )
        if path:
            self.txtPdbFile.setText(os.path.basename(path))
            if self.on_load_pdb_hook: self.on_load_pdb_hook(path)

    def _onLoadData(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open data file", "",
            "Data files (*.dat *.DAT *.txt *.csv);;All files (*.*)"
        )
        if path:
            self.txtDataFile.setText(os.path.basename(path))
            if self.on_load_data_hook: self.on_load_data_hook(path)

    def _onFinish(self):
        """Emit the current editor text and close the dialog."""
        self.finished.emit(self.editor.toPlainText())
        self.accept()

    def getText(self) -> str:
        """Return the current contents of the code editor."""
        return self.plain_text

    def get_valid_operations(self) -> list[str]:
        """Return a list of valid operation keywords for syntax highlighting."""
        return ["output", "load", "save", "parameter_strategy", "print", "loop", "end"]
    
    def get_valid_keywords(self) -> list[str]:
        """Return a list of valid keywords for syntax highlighting."""
        return ["pdb", "saxs", "split", "iterations", "translate", "rotate", "msg", "colour"]

    def get_scope_keywords(self) -> list[str]:
        """Return a list of keywords that introduce new scopes."""
        return ["loop", "optimize_once", "on_improvement"]

    def get_syntax_colored_string(self, text: str) -> str:
        """Return the given text wrapped in HTML for syntax coloring"""
        if "#" in text: 
            comment_index = text.index("#")
            code_part = text[:comment_index]
            comment_part = text[comment_index:]
            text = code_part + f"<span style='color: green'>{comment_part}</span>"

        i = 0
        # consume leading whitespace safely (handle empty or all-whitespace lines)
        while i < len(text) and text[i].isspace():
            i += 1
        whitespace = text[:i]
        text = text[i:]

        tokens = text.split()
        token = tokens[0] if tokens else ""

        if token in self.get_valid_operations():
            # highlight only the leading token
            text = f"<span style='color: blue; font-weight: bold'>{token}</span>" + text[len(token):]
        elif token in self.get_valid_keywords():
            text = f"<span style='color: purple'>{token}</span>" + text[len(token):]
        # convert leading whitespace to non-breaking spaces so HTML preserves indentation
        whitespace_html = whitespace.replace(' ', '&nbsp;').replace('\t', '&nbsp;'*4)
        return whitespace_html + text

    def _onTextChanged(self):
        """Update the plain text version of the editor contents whenever it changes."""
        # self.editor.blockSignals(True)
        # line_index = self.editor.textCursor().blockNumber()
        # current_line = self.editor.document().findBlockByNumber(line_index).text()
        # syntaxed_line = self.get_syntax_colored_string(current_line)
        # text = self.editor.toPlainText()
        # self.plain_text = text
        # lines = text.splitlines()
        # if line_index < len(lines):
        #     lines[line_index] = syntaxed_line
        # self.editor.clear()
        # for line in lines:
        #     self.editor.appendHtml(line)
        # self.editor.blockSignals(False)
        return

    def setText(self, text: str):
        """Replace the entire contents of the code editor."""
        self.editor.clear()
        self.plain_text = text
        for line in text.splitlines():
            self.editor.appendHtml(self.get_syntax_colored_string(line))

    def set_load_pdb_hook(self, hook):
        """Set a callback function to be called when a PDB file is loaded."""
        self.on_load_pdb_hook = hook
    
    def set_load_data_hook(self, hook):
        """Set a callback function to be called when a data file is loaded."""
        self.on_load_data_hook = hook
