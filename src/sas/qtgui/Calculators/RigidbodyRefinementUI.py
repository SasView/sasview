"""The widgets of the rigid-body refinement calculator.

Only layout and presentation live here; RigidbodyRefinement drives them, with the script handling, the refinement runner and the structure
previews shared with pyAUSAXS's own GUI through pyausaxs.gui.core.
"""

import html
import re

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
from pyausaxs.gui.core.files import is_saxs_file, is_structure_file
from pyausaxs.gui.core.syntax import classify_line, scope_partner
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

# colours of messages written by the calculator itself, rather than streamed from the backend
_MESSAGE_COLORS = {"error": "#cc0000", "warning": "#cc6600", "success": "#006600"}

# file-field tints while a typed path does / doesn't point at a usable file
_VALID_STYLE = "QLineEdit { background-color: #e8f4ec; }"
_INVALID_STYLE = "QLineEdit { background-color: #fdeceb; }"


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
    """Colours the first token of each script line — scope keywords by nesting depth, line operations, argument keywords, and unrecognised
    tokens flagged as errors — plus trailing # comments. The classification itself is pyausaxs.gui.core.syntax; the nesting depth is carried
    from block to block in Qt's per-block state."""

    # Colors assigned to successive nesting depths, cycling if deeper than 4
    _SCOPE_COLORS = ["blue", "#CC6600", "#990099", "#CC0000"]

    def __init__(self, document, operations=(), keywords=()):
        super().__init__(document)

        def fmt(color, bold=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Weight.Bold)
            return f

        self._formats = {
            "operation": fmt("blue", bold=True),
            "keyword": fmt("purple"),
            "comment": fmt("green"),
            "error": fmt("red"),
        }
        self._scope_formats = [fmt(color, bold=True) for color in self._SCOPE_COLORS]
        self._operations, self._keywords = set(operations), set(keywords)

    def set_vocabulary(self, operations, keywords):
        """Replace the known operations/keywords once the backend reports them, and re-highlight."""
        self._operations = set(operations)
        self._keywords = set(keywords)
        self.rehighlight()

    def highlightBlock(self, text: str):
        prev = self.previousBlockState()
        spans, depth = classify_line(text, prev if prev >= 0 else 0, self._operations, self._keywords)
        for span in spans:
            f = self._scope_formats[span.depth % len(self._scope_formats)] if span.kind == "scope" else self._formats[span.kind]
            self.setFormat(span.start, span.end - span.start, f)
        self.setCurrentBlockState(depth)


class FileField(QtWidgets.QWidget):
    """A labelled path entry with a Browse button, tinted while the typed path is (in)valid. `committed` fires with the path whenever the user
    settles on one — by browsing, or by finishing an edit of the text. With a `view_tooltip`, a View button beside it fires `viewRequested`;
    it is enabled while the path is valid and the view isn't blocked (see setViewBlocked)."""

    committed = QtCore.Signal(str)
    viewRequested = QtCore.Signal()

    def __init__(self, label: str, file_filter: str, validator, parent=None, *, view_tooltip: str | None = None):
        super().__init__(parent)
        self._filter = file_filter
        self._validator = validator
        self._last_committed = ""
        self._view_blocked = False
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        title = QtWidgets.QLabel(label)
        title.setMinimumWidth(70)
        layout.addWidget(title)
        self.edit = QtWidgets.QLineEdit()
        self.edit.setPlaceholderText("No file selected")
        layout.addWidget(self.edit, 1)
        self.button = QtWidgets.QPushButton("Browse…")
        layout.addWidget(self.button)
        self.button.clicked.connect(self._browse)
        self.viewButton = None
        if view_tooltip is not None:
            self.viewButton = QtWidgets.QPushButton("View…")
            self.viewButton.setToolTip(view_tooltip)
            self.viewButton.setEnabled(False)
            self.viewButton.clicked.connect(self.viewRequested.emit)
            layout.addWidget(self.viewButton)
        self.edit.editingFinished.connect(lambda: self._commit(self.edit.text()))
        self.edit.textChanged.connect(self._tint)

    def text(self) -> str:
        return self.edit.text().strip()

    def set(self, path: str):
        """Show `path` without committing it, e.g. when it was read back from the script."""
        self._last_committed = path
        self.edit.setText(path)

    def valid(self) -> bool:
        return bool(self.text()) and self._validator(self.text())

    def setViewBlocked(self, blocked: bool):
        self._view_blocked = blocked
        self._tint()

    def _tint(self):
        self.edit.setStyleSheet("" if not self.text() else _VALID_STYLE if self.valid() else _INVALID_STYLE)
        if self.viewButton is not None:
            self.viewButton.setEnabled(self.valid() and not self._view_blocked)

    def _browse(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open file", self.text(), self._filter)
        if path:
            self.edit.setText(path)
            self._commit(path)

    def _commit(self, path: str):
        # editingFinished also fires on a mere loss of focus, so only an actual change counts
        path = path.strip()
        if path == self._last_committed:
            return
        self._last_committed = path
        self.committed.emit(path)


class RigidBodyRefinementUI(QtWidgets.QDialog):
    """A Refinement tab with three panes: inputs, run controls and output on the left; the refinement script in the middle; the structure
    preview and fit results on the right. The structure manager opens beside it as a closable tab."""

    closing = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rigid-body refinement")
        self.resize(1400, 850)
        self._buildUI()

    def closeEvent(self, event):
        self.closing.emit()
        super().closeEvent(event)

    # ----- layout -------------------------------------------------------------
    def _buildUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        layout.addWidget(self.tabs)
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.refinementTab = self.splitter
        self.tabs.addTab(self.splitter, "Refinement")
        for side in (QtWidgets.QTabBar.ButtonPosition.LeftSide, QtWidgets.QTabBar.ButtonPosition.RightSide):
            self.tabs.tabBar().setTabButton(0, side, None)  # the refinement itself can't be closed
        self.splitter.addWidget(self._buildControls())
        self.splitter.addWidget(self._buildEditor())
        self.splitter.addWidget(self._buildResults())
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setStretchFactor(2, 3)
        self.splitter.setSizes([340, 480, 580])

    def _buildControls(self) -> QtWidgets.QWidget:
        controls = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(controls)
        layout.setContentsMargins(0, 0, 4, 0)

        # the input fields are a shortcut for editing the script's load block: each one writes only its own directive, and the script itself
        # is always the authority
        inputs = QtWidgets.QGroupBox("Input")
        form = QtWidgets.QVBoxLayout(inputs)
        self.structureField = FileField("Structure", "Structure files (*.pdb *.ent *.cif *.xyz);;All files (*)", is_structure_file,
                                        view_tooltip="View the structure and manage its bodies, symmetries and constraints")
        self.saxsField = FileField("SAXS data", "SAXS data (*.dat *.rsr *.xvg);;All files (*)", is_saxs_file)
        form.addWidget(self.structureField)
        form.addWidget(self.saxsField)
        splits_row = QtWidgets.QHBoxLayout()
        splits_label = QtWidgets.QLabel("Splits")
        splits_label.setMinimumWidth(70)
        splits_row.addWidget(splits_label)
        self.txtSplits = QtWidgets.QLineEdit()
        self.txtSplits.setPlaceholderText("residue ids, e.g. 50 100")
        self.txtSplits.setToolTip("Residues at which the structure is split into rigid bodies")
        splits_row.addWidget(self.txtSplits)
        form.addLayout(splits_row)
        layout.addWidget(inputs)

        run_row = QtWidgets.QHBoxLayout()
        self.btnValidate = QtWidgets.QPushButton("Validate")
        self.btnRun = QtWidgets.QPushButton("Run refinement")
        self.btnRun.setDefault(True)
        self.btnStop = QtWidgets.QPushButton("Stop")
        self.btnStop.setToolTip("End the refinement after its current iteration, keeping the best conformation found so far")
        self.btnStop.hide()
        run_row.addWidget(self.btnValidate)
        run_row.addWidget(self.btnRun)
        run_row.addWidget(self.btnStop)
        layout.addLayout(run_row)
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)

        output = QtWidgets.QGroupBox("Output")
        output_layout = QtWidgets.QVBoxLayout(output)
        self.outputPane = QtWidgets.QTextEdit()
        self.outputPane.setReadOnly(True)
        self.outputPane.setFont(GuiUtils.getMonospaceFont())
        self.outputPane.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
        output_layout.addWidget(self.outputPane)
        layout.addWidget(output, 1)
        return controls

    def _buildEditor(self) -> QtWidgets.QWidget:
        pane = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(pane)
        layout.setContentsMargins(4, 0, 4, 0)
        header = QtWidgets.QHBoxLayout()
        header.addWidget(QtWidgets.QLabel("<b>Refinement script</b>"))
        header.addStretch()
        self.btnLoadScript = QtWidgets.QToolButton()
        self.btnLoadScript.setText("Load…")
        self.btnLoadScript.setToolTip("Load a script from a file")
        self.btnSaveScript = QtWidgets.QToolButton()
        self.btnSaveScript.setText("Save…")
        self.btnSaveScript.setToolTip("Save the script to a file")
        self.btnResetScript = QtWidgets.QToolButton()
        self.btnResetScript.setText("Reset")
        self.btnResetScript.setToolTip("Reset to the default script, keeping the current load element")
        for button in (self.btnLoadScript, self.btnSaveScript, self.btnResetScript):
            header.addWidget(button)
        layout.addLayout(header)

        self.editor = QCodeEditor(pane)
        self.editor.setFont(GuiUtils.getMonospaceFont())
        self.editor.setTabStopDistance(4 * self.editor.fontMetrics().horizontalAdvance(" "))
        self.highlighter = RigidBodyHighlighter(self.editor.document())
        self.editor.cursorPositionChanged.connect(self._updateBracketHighlight)
        layout.addWidget(self.editor)
        return pane

    def _buildResults(self) -> QtWidgets.QWidget:
        self.results = QtWidgets.QTabWidget()

        # a persistent structure tab: the Cα backbone per body with the split residues in red, kept across runs (fit tabs are added beside it)
        structure = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(structure)
        layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QtWidgets.QHBoxLayout()
        self.btnHomeView = QtWidgets.QToolButton()
        self.btnHomeView.setText("⌂")
        self.btnHomeView.setToolTip("Reset to the default view")
        toolbar.addWidget(self.btnHomeView)
        self.lblHover = QtWidgets.QLabel("")
        self.lblHover.setStyleSheet("color: #6b7785;")
        toolbar.addWidget(self.lblHover, 1)
        layout.addLayout(toolbar)
        self.structureFigure = Figure()
        self.structureAxes = self.structureFigure.add_subplot(111, projection="3d")
        self.structureCanvas = FigureCanvas(self.structureFigure)
        layout.addWidget(self.structureCanvas, 1)
        self.structureTab = structure
        self.results.addTab(structure, "Structure")
        self._fitTabs: list[QtWidgets.QWidget] = []
        return self.results

    # ----- results ------------------------------------------------------------
    def setFitFigures(self, figures: list[tuple[Figure, str]]):
        """Replace the fit tabs from a previous run with `figures`, given as (figure, title) pairs; the structure tab is kept."""
        for tab in self._fitTabs:
            self.results.removeTab(self.results.indexOf(tab))
            tab.deleteLater()
        self._fitTabs = []
        for fig, title in figures:
            tab = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(tab)
            layout.setContentsMargins(0, 0, 0, 0)
            canvas = FigureCanvas(fig)
            layout.addWidget(canvas)
            layout.addWidget(NavigationToolbar2QT(canvas, tab))
            self.results.addTab(tab, title)
            self._fitTabs.append(tab)
        if self._fitTabs:
            self.results.setCurrentWidget(self._fitTabs[0])

    def showStructureTab(self):
        self.results.setCurrentWidget(self.structureTab)

    # ----- top-level tabs -----------------------------------------------------
    def addTab(self, widget: QtWidgets.QWidget, title: str):
        """Add a closable top-level tab beside the refinement and switch to it."""
        self.tabs.addTab(widget, title)
        self.tabs.setCurrentWidget(widget)

    def removeTab(self, widget: QtWidgets.QWidget):
        self.tabs.removeTab(self.tabs.indexOf(widget))

    def showRefinementTab(self):
        self.tabs.setCurrentWidget(self.refinementTab)

    # ----- output -------------------------------------------------------------
    def appendOutput(self, text: str, kind: str | None = None):
        """Append (optionally ANSI-coloured) backend output to the output pane, or a message of the calculator's own when `kind` is one of
        "error", "warning" or "success". Partial lines are kept as they are, so streamed output reads as it was printed."""
        if kind is not None:
            body = f'<span style="color:{_MESSAGE_COLORS[kind]};">{html.escape(text)}</span>'
        else:
            body = _ansi_to_html(text)
        cursor = self.outputPane.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(body.replace("\n", "<br>"))
        self.outputPane.setTextCursor(cursor)
        self.outputPane.ensureCursorVisible()

    def clearOutput(self):
        self.outputPane.clear()

    def setRunning(self, running: bool, *, stoppable: bool = False):
        """Toggle the running state. A refinement (unlike a validation) can be stopped early, so Run turns into Stop while it is in flight."""
        self.btnValidate.setEnabled(not running)
        self.btnRun.setVisible(not (running and stoppable))
        self.btnRun.setEnabled(not running)
        self.btnStop.setVisible(running and stoppable)
        self.btnStop.setEnabled(True)
        self.btnStop.setText("Stop")
        self.progress.setVisible(running)
        self.structureField.setViewBlocked(running)  # the structure manager needs the backend, which the run owns

    def setStopping(self):
        self.btnStop.setEnabled(False)
        self.btnStop.setText("Stopping…")

    # ----- editor -------------------------------------------------------------
    def getText(self) -> str:
        return self.editor.toPlainText()

    def replaceText(self, text: str):
        """Replace the whole script as one undoable edit, keeping the scroll position, so a rewrite of the load block from the input fields
        doesn't throw away the user's undo history or their place in the script."""
        if text == self.getText():
            return
        scroll = self.editor.verticalScrollBar().value()
        cursor = QTextCursor(self.editor.document())
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.insertText(text)
        cursor.endEditBlock()
        self.editor.verticalScrollBar().setValue(scroll)

    def _updateBracketHighlight(self):
        """Tint the scope opener/`end` line pair around the cursor's line."""
        document = self.editor.document()
        block = self.editor.textCursor().block()
        pair = scope_partner(self.editor.toPlainText().split("\n"), block.blockNumber())
        if pair is None:
            self.editor.setBracketSelections([])
            return
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#D6EAF8"))
        fmt.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selections = []
        for b in (block, document.findBlockByNumber(pair)):
            sel = QtWidgets.QTextEdit.ExtraSelection()
            sel.format = fmt
            sel.cursor = QTextCursor(b)
            sel.cursor.clearSelection()
            selections.append(sel)
        self.editor.setBracketSelections(selections)
