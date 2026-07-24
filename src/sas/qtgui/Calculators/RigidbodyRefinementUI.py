import html
import os
import re

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QTextFormat

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.CustomGUI.CodeEditor import QCodeEditor

# ANSI SGR code → CSS hex colour for a light-background widget.
# Codes not listed (0 = reset, 30 = black, 97 = bright-white) produce
# unstyled text so they remain legible on a white background.
_ANSI_RE = re.compile(r'\x1b\[(\d+)m')
_ANSI_COLOR_MAP: dict[int, str] = {
    31: "#cc0000",  # red          – warnings
    32: "#006600",  # green        – accepted steps
    33: "#cc6600",  # yellow/amber – cautions
    34: "#0000cc",  # blue
    35: "#990099",  # magenta
    36: "#007777",  # cyan
    37: "#777777",  # light grey
    90: "#555555",  # dark grey
    91: "#dd0000",  # bright red
    92: "#008800",  # bright green
    93: "#996600",  # bright yellow/amber
    94: "#0044cc",  # bright blue
    95: "#aa00aa",  # bright magenta
    96: "#007799",  # bright cyan
}


def _ansi_to_html(text: str) -> str:
    """Convert ANSI SGR colour codes in *text* to HTML <span> tags."""
    parts = []
    pos = 0
    color: str | None = None
    for match in _ANSI_RE.finditer(text):
        segment = html.escape(text[pos:match.start()])
        if segment:
            parts.append(f'<span style="color:{color};">{segment}</span>' if color else segment)
        color = _ANSI_COLOR_MAP.get(int(match.group(1)))
        pos = match.end()
    segment = html.escape(text[pos:])
    if segment:
        parts.append(f'<span style="color:{color};">{segment}</span>' if color else segment)
    return "".join(parts)


class RigidBodyHighlighter(QSyntaxHighlighter):
    # Colors assigned to successive nesting depths, cycling if deeper than 4
    _SCOPE_COLORS = ["blue", "#CC6600", "#990099", "#CC0000"]

    def __init__(self, document, operations, keywords, scope_keywords):
        super().__init__(document)

        self._op_fmt = QTextCharFormat()
        self._op_fmt.setForeground(QColor("blue"))
        self._op_fmt.setFontWeight(QFont.Weight.Bold)

        self._kw_fmt = QTextCharFormat()
        self._kw_fmt.setForeground(QColor("purple"))

        self._comment_fmt = QTextCharFormat()
        self._comment_fmt.setForeground(QColor("green"))

        self._error_fmt = QTextCharFormat()
        self._error_fmt.setForeground(QColor("red"))

        self._scope_fmts = []
        for color in self._SCOPE_COLORS:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            fmt.setFontWeight(QFont.Weight.Bold)
            self._scope_fmts.append(fmt)

        self._operations = set(operations)
        self._keywords = set(keywords)
        self._scope_openers = set(scope_keywords)
        self._first_token_re = re.compile(r'\S+')
        self._comment_re = re.compile(r'#.*')

    def _fmt_for_depth(self, depth: int) -> QTextCharFormat:
        return self._scope_fmts[depth % len(self._scope_fmts)]

    def highlightBlock(self, text: str):
        prev = self.previousBlockState()
        depth = prev if prev >= 0 else 0

        # Highlight comment suffix first (green wins over any keyword inside a comment)
        comment_match = self._comment_re.search(text)
        if comment_match:
            self.setFormat(comment_match.start(), len(comment_match.group()), self._comment_fmt)
            scannable = text[:comment_match.start()]
        else:
            scannable = text

        # Highlight first non-whitespace token only
        token_match = self._first_token_re.search(scannable)
        new_depth = depth
        if token_match:
            token = token_match.group()
            if token == "end":
                # Decrease depth first so `end` shares its opener's color
                new_depth = max(0, depth - 1)
                self.setFormat(token_match.start(), len(token), self._fmt_for_depth(new_depth))
            elif token in self._scope_openers:
                self.setFormat(token_match.start(), len(token), self._fmt_for_depth(depth))
                new_depth = depth + 1
            elif token in self._operations:
                self.setFormat(token_match.start(), len(token), self._op_fmt)
            elif token in self._keywords:
                self.setFormat(token_match.start(), len(token), self._kw_fmt)
            elif token != "}":
                self.setFormat(token_match.start(), len(token), self._error_fmt)

        self.setCurrentBlockState(new_depth)


class RigidBodyRefinementUI(QtWidgets.QDialog):
    finished = QtCore.Signal(str)
    validate_requested = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rigid-body refinement")
        self.resize(1200, 800)

        self._operations = []
        self._keywords   = []

        self._buildUI()
        self._connectSignals()

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
        self._highlighter = RigidBodyHighlighter(
            self.editor.document(),
            self.get_valid_operations(),
            self.get_valid_keywords(),
            self.get_scope_keywords(),
        )
        self.editor.cursorPositionChanged.connect(self._updateBracketHighlight)
        layout.addWidget(self.editor)

        # Output pane
        layout.addWidget(QtWidgets.QLabel("Output:"))
        self.outputPane = QtWidgets.QPlainTextEdit(self)
        self.outputPane.setReadOnly(True)
        self.outputPane.setFont(GuiUtils.getMonospaceFont())
        self.outputPane.setFixedHeight(150)
        layout.addWidget(self.outputPane)

        # Bottom button row
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        self.btnValidate = QtWidgets.QPushButton("Validate")
        button_layout.addWidget(self.btnValidate)
        self.btnFinish = QtWidgets.QPushButton("Finish")
        self.btnFinish.setDefault(True)
        button_layout.addWidget(self.btnFinish)
        layout.addLayout(button_layout)

    def _connectSignals(self):
        self.btnLoadPdb.clicked.connect(self._onLoadPDB)
        self.btnLoadData.clicked.connect(self._onLoadData)
        self.btnValidate.clicked.connect(self._onValidate)
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
        """Emit the current editor text; dialog stays open to show live output."""
        self.finished.emit(self.editor.toPlainText())

    def _onValidate(self):
        """Emit a validation request with the current editor text."""
        self.validate_requested.emit(self.editor.toPlainText())

    def appendOutput(self, text: str):
        """Append one line of (optionally ANSI-coloured) text to the output pane."""
        text = text.rstrip("\n")
        cursor = self.outputPane.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if self.outputPane.toPlainText():
            cursor.insertBlock()
        cursor.insertHtml(_ansi_to_html(text))
        self.outputPane.ensureCursorVisible()

    def clearOutput(self):
        """Clear the output pane."""
        self.outputPane.clear()

    def setRunning(self, running: bool):
        """Disable interactive elements while a refinement run is in progress."""
        self.btnFinish.setEnabled(not running)
        self.btnValidate.setEnabled(not running)

    def getText(self) -> str:
        """Return the current contents of the code editor."""
        return self.editor.toPlainText()

    def get_valid_operations(self) -> list[str]:
        """Return a list of valid operation keywords for syntax highlighting."""
        return list(self._operations)

    def get_valid_keywords(self) -> list[str]:
        """Return a list of valid keywords for syntax highlighting."""
        return list(self._keywords)

    def get_scope_keywords(self) -> list[str]:
        """Return a list of keywords that introduce new scopes."""
        return ["loop", "optimize_once", "on_improvement"]

    def setValidElements(self, elements_and_args: dict[str, list[str]]):
        """Update operations and keywords from backend data and re-install the highlighter.

        elements_and_args maps each valid element (first token of a line) to the list
        of argument keywords it accepts.  Elements that only appear as arguments of
        other elements (i.e. not themselves keys) are treated as keywords.
        """
        op_set = set(elements_and_args.keys())
        kw_set = {arg for args in elements_and_args.values() for arg in args} - op_set
        self._operations = list(op_set)
        self._keywords = list(kw_set)
        self._highlighter = RigidBodyHighlighter(
            self.editor.document(),
            self._operations,
            self._keywords,
            self.get_scope_keywords(),
        )

    def _updateBracketHighlight(self):
        """Highlight the scope opener/end pair under the cursor."""
        block = self.editor.textCursor().block()
        tokens = block.text().lstrip().split()
        first_token = tokens[0] if tokens else ""

        scope_openers = set(self.get_scope_keywords())
        if first_token not in scope_openers and first_token != "end":
            self.editor.setBracketSelections([])
            return

        pair_block = self._find_scope_pair(block, first_token, scope_openers)
        if pair_block is None:
            self.editor.setBracketSelections([])
            return

        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#D6EAF8"))
        fmt.setProperty(QTextFormat.FullWidthSelection, True)

        selections = []
        for b in (block, pair_block):
            sel = QtWidgets.QTextEdit.ExtraSelection()
            sel.format = fmt
            sel.cursor = QTextCursor(b)
            sel.cursor.clearSelection()
            selections.append(sel)

        self.editor.setBracketSelections(selections)

    def _find_scope_pair(self, block, first_token: str, scope_openers: set):
        """Return the block that matches the scope opener or 'end' on the given block."""
        if first_token in scope_openers:
            block_iter = block.next()
            stack = 0
            while block_iter.isValid():
                token = block_iter.text().lstrip().split()
                token = token[0] if token else ""
                if token in scope_openers:
                    stack += 1
                elif token == "end":
                    if stack == 0:
                        return block_iter
                    stack -= 1
                block_iter = block_iter.next()
        else:  # first_token == "end"
            block_iter = block.previous()
            stack = 0
            while block_iter.isValid():
                token = block_iter.text().lstrip().split()
                token = token[0] if token else ""
                if token == "end":
                    stack += 1
                elif token in scope_openers:
                    if stack == 0:
                        return block_iter
                    stack -= 1
                block_iter = block_iter.previous()
        return None

    def setText(self, text: str):
        """Replace the entire contents of the code editor."""
        self.editor.setPlainText(text)

    def set_load_pdb_hook(self, hook):
        """Set a callback function to be called when a PDB file is loaded."""
        self.on_load_pdb_hook = hook

    def set_load_data_hook(self, hook):
        """Set a callback function to be called when a data file is loaded."""
        self.on_load_data_hook = hook
