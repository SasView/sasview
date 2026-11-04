"""The structure manager of the rigid-body refinement calculator.

It shows a large 3D view of the structure and lets the user inspect and re-organise its bodies without touching the run: re-split it,
rename, merge and delete bodies, add or fit symmetries, and add constraints. Every edit is staged and only reaches the script through
"Send to script…", after the user has reviewed the change as a side-by-side diff.

The bodies, the staged edits, the selections and what every action means come from pyausaxs.gui.core.structure, which pyAUSAXS's own GUI
shares; this module only draws them and forwards what the user types and clicks.
"""

import os
from collections.abc import Callable

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
from pyausaxs.gui.core.loads import RELAXED_LOADS
from pyausaxs.gui.core.palette import PALETTE
from pyausaxs.gui.core.plotting import PICK_CLICK_DRAG_TOLERANCE, draw_structure, nearest_ca_residue
from pyausaxs.gui.core.structure import ActionResult, StructureModel, side_by_side_diff
from PySide6 import QtCore, QtGui, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils

# display label -> draw_structure `color_by` mode; the first entry is the default
COLOUR_BY_MODES = {"Body": "body", "Symmetry copy": "copy", "Residue": "residue"}

# the status line holds a message legible, then fades it out (see StructurePane._setStatus)
_STATUS_HOLD_MS, _STATUS_FADE_MS = 2500, 2500

# an action button whose action has enough to go on: typed text, or a selection that stands in for it
_READY_STYLE = (
    f"QPushButton {{ background-color: {PALETTE['ready']}; color: white; border: none; border-radius: 3px; padding: 4px 10px; }}"
    f"QPushButton:hover {{ background-color: {PALETTE['ready_hover']}; }}"
)
# the "script changed" bar: amber, so it stands apart from the section headers
_REFRESH_STYLE = (
    "QPushButton { background-color: #f0ad4e; color: #4a3208; font-weight: bold; border: none; border-radius: 3px;"
    " padding: 6px; text-align: left; }"
    "QPushButton:hover { background-color: #eca23a; }"
)
_MUTED_STYLE = f"color: {PALETTE['muted']};"
_DIFF_REMOVED = (PALETTE["bad"], PALETTE["danger"])  # (background, foreground)
_DIFF_ADDED = ("#e3f4e9", "#2f7d4f")

# item data roles of a Bodies-list row: the body index, and the copy index (-1 for the whole body)
_BODY_ROLE = QtCore.Qt.ItemDataRole.UserRole
_COPY_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1


class CollapsibleSection(QtWidgets.QWidget):
    """A titled section whose body folds away behind its header. Sections are independent, so any number can be open at once."""

    def __init__(self, title: str, *, expanded: bool, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.header = QtWidgets.QToolButton()
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setAutoRaise(True)
        self.header.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.header.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        font = self.header.font()
        font.setBold(True)
        self.header.setFont(font)
        layout.addWidget(self.header)
        self.body = QtWidgets.QWidget()
        self.bodyLayout = QtWidgets.QVBoxLayout(self.body)
        self.bodyLayout.setContentsMargins(14, 0, 0, 6)
        layout.addWidget(self.body)
        self.header.toggled.connect(self.setExpanded)
        self.setExpanded(expanded)

    def setExpanded(self, expanded: bool):
        self.header.setChecked(expanded)
        self.header.setArrowType(QtCore.Qt.ArrowType.DownArrow if expanded else QtCore.Qt.ArrowType.RightArrow)
        self.body.setVisible(expanded)

    def isExpanded(self) -> bool:
        return self.header.isChecked()


class ActionRow(QtWidgets.QWidget):
    """A label, a field whose placeholder carries the format hint, and a button. `triggered` fires on the button and on Return.

    `prefill` seeds the field with a real value rather than a hint, for a row whose one sensible answer can just be submitted; it is
    restored whenever the row is cleared. `advanced`, if given, is the placeholder of an optional second field (e.g. a tolerance
    override), folded away behind a chevron since the common case doesn't need it."""

    triggered = QtCore.Signal()

    def __init__(self, label: str, hint: str, button: str = "Apply", *, prefill: str = "", advanced: str | None = None, parent=None):
        super().__init__(parent)
        self._prefill = prefill
        grid = QtWidgets.QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 4)
        grid.setHorizontalSpacing(4)
        title = QtWidgets.QLabel(label)
        title.setStyleSheet(_MUTED_STYLE)
        grid.addWidget(title, 0, 0, 1, 3)
        self.edit = QtWidgets.QLineEdit(prefill)
        self.edit.setPlaceholderText(hint)
        grid.addWidget(self.edit, 1, 0)
        self.button = QtWidgets.QPushButton(button)
        grid.addWidget(self.button, 1, 1)
        grid.setColumnStretch(0, 1)
        self.edit.returnPressed.connect(self.triggered.emit)
        self.button.clicked.connect(lambda: self.triggered.emit())

        self.advanced: QtWidgets.QLineEdit | None = None
        if advanced is not None:
            self.advanced = QtWidgets.QLineEdit()
            self.advanced.setPlaceholderText(advanced)
            self.advanced.hide()
            self.advanced.returnPressed.connect(self.triggered.emit)
            grid.addWidget(self.advanced, 2, 0, 1, 2)
            self.chevron = QtWidgets.QToolButton()
            self.chevron.setAutoRaise(True)
            self.chevron.setArrowType(QtCore.Qt.ArrowType.RightArrow)
            self.chevron.setToolTip("More options")
            self.chevron.clicked.connect(self._toggleAdvanced)
            grid.addWidget(self.chevron, 1, 2)

    def _toggleAdvanced(self):
        show = self.advanced.isHidden()
        self.advanced.setVisible(show)
        self.chevron.setArrowType(QtCore.Qt.ArrowType.DownArrow if show else QtCore.Qt.ArrowType.RightArrow)

    def text(self) -> str:
        return self.edit.text()

    def advancedText(self) -> str:
        return self.advanced.text() if self.advanced is not None else ""

    def clear(self):
        self.edit.setText(self._prefill)
        if self.advanced is not None:
            self.advanced.clear()

    def setReady(self, ready: bool):
        """Turn the button green while clicking it would actually do something."""
        self.button.setStyleSheet(_READY_STYLE if ready else "")


class StructurePane(QtWidgets.QWidget):
    """Interactive structure-inspection and body-management view for a single structure file.

    `base_script` returns the user's current script, which staged edits are composed onto; `scriptApplied` carries the new script once
    the user has confirmed sending the staged edits to it."""

    scriptApplied = QtCore.Signal(str)

    def __init__(self, pdb_path: str, *, splits: str = "", base_script: Callable[[], str] | None = None, relaxed_loads=None,
                 parent=None):
        super().__init__(parent)
        self.pdb_path = pdb_path
        self.title = "Structure: " + os.path.splitext(os.path.basename(pdb_path))[0]
        # the bodies, staged elements and selections; this view only shows them and forwards the user's actions
        self.model = StructureModel(pdb_path, splits=splits, base_script=base_script,
                                    relaxed_loads=relaxed_loads if relaxed_loads is not None else RELAXED_LOADS)
        self._busy = False                # a refinement owns the backend; no action may rebuild the structure meanwhile
        self._preserveView = False        # keep the camera across redraws, once there is a first view to keep
        self._pressXY = None              # where a left press on the preview landed, to tell a click from a rotation
        self._renaming = None             # (item, body, copy, old name) of the Bodies-list row being renamed in place
        self._readyChecks: list[tuple[ActionRow, Callable[[str], bool]]] = []
        self._bodyItems: dict[tuple[int, int | None], QtWidgets.QTreeWidgetItem] = {}

        self._redrawTimer = QtCore.QTimer(self)
        self._redrawTimer.setSingleShot(True)
        self._redrawTimer.setInterval(0)
        self._redrawTimer.timeout.connect(self._redraw)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        layout.addWidget(self.splitter)
        self.splitter.addWidget(self._buildPlot())
        self.splitter.addWidget(self._buildControls())
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([1000, 360])

        ok, msg = self._rebuild()  # initial draw of the untouched structure
        if not ok:
            self._setStatus(f"Could not load the structure: {msg}", ok=False)
            self._redraw()

    # ----- layout -------------------------------------------------------------
    def _buildPlot(self) -> QtWidgets.QWidget:
        pane = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(pane)
        layout.setContentsMargins(0, 0, 0, 0)
        # a thin readout above the canvas: the residue under the cursor, and a chip that clears everything selected in the plot. The chip is
        # only shown while something is selected, see _refreshClearChip.
        top = QtWidgets.QHBoxLayout()
        top.setContentsMargins(6, 0, 0, 0)
        self.lblHover = QtWidgets.QLabel("")
        self.lblHover.setStyleSheet(_MUTED_STYLE)
        top.addWidget(self.lblHover, 1)
        self.btnClearSelection = QtWidgets.QToolButton()
        self.btnClearSelection.setText("✕  Clear selection")
        self.btnClearSelection.setToolTip("Deselect every body and residue")
        self.btnClearSelection.clicked.connect(self._clearAllSelection)
        self.btnClearSelection.hide()
        top.addWidget(self.btnClearSelection)
        layout.addLayout(top)

        self.figure = Figure()
        self.axes = self.figure.add_subplot(111, projection="3d")
        self.axes.set_axis_off()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas, 1)
        self.toolbar = NavigationToolbar2QT(self.canvas, pane)
        layout.addWidget(self.toolbar)

        # hover to read the nearest residue, click to toggle it in the selection. A left press only counts as a click if the cursor barely
        # moved by its release; otherwise it was a rotation.
        self.canvas.mpl_connect("motion_notify_event", self._onPreviewHover)
        self.canvas.mpl_connect("button_press_event", self._onPreviewPress)
        self.canvas.mpl_connect("button_release_event", self._onPreviewRelease)
        return pane

    def _buildControls(self) -> QtWidgets.QWidget:
        column = QtWidgets.QWidget()
        column.setMinimumWidth(300)
        outer = QtWidgets.QVBoxLayout(column)
        outer.setContentsMargins(4, 0, 0, 0)

        # shown above the sections only while the script changed since the view was built, see _setStale
        self.btnRefresh = QtWidgets.QPushButton("↻  Script changed — refresh")
        self.btnRefresh.setStyleSheet(_REFRESH_STYLE)
        self.btnRefresh.setToolTip("Reload the structure from the current script, discarding the staged changes")
        self.btnRefresh.clicked.connect(self._doRefresh)
        self.btnRefresh.hide()
        outer.addWidget(self.btnRefresh)

        # the sections scroll, while the status line and the Send button stay pinned below them, whichever sections are open
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sections = QtWidgets.QWidget()
        self._sectionsLayout = QtWidgets.QVBoxLayout(sections)
        self._sectionsLayout.setContentsMargins(0, 0, 4, 0)
        scroll.setWidget(sections)
        outer.addWidget(scroll, 1)

        self._buildDisplaySection()
        self._buildBodiesSection()
        self._buildManageSection()
        self._buildSymmetrySection()
        self._buildConstraintsSection()
        self._buildAppliedSection()
        self._sectionsLayout.addStretch(1)

        self.lblStatus = QtWidgets.QLabel("")
        self.lblStatus.setWordWrap(True)
        self._statusEffect = QtWidgets.QGraphicsOpacityEffect(self.lblStatus)
        self.lblStatus.setGraphicsEffect(self._statusEffect)
        self._statusFade = QtCore.QPropertyAnimation(self._statusEffect, b"opacity", self)
        self._statusFade.setDuration(_STATUS_FADE_MS)
        self._statusFade.setStartValue(1.0)
        self._statusFade.setEndValue(0.0)
        self._statusFade.finished.connect(self.lblStatus.clear)
        self._statusHold = QtCore.QTimer(self)
        self._statusHold.setSingleShot(True)
        self._statusHold.setInterval(_STATUS_HOLD_MS)
        self._statusHold.timeout.connect(self._statusFade.start)
        outer.addWidget(self.lblStatus)

        self.btnSend = QtWidgets.QPushButton("Send to script…")
        self.btnSend.setToolTip("Review the staged changes as a diff of the script, and apply them to it")
        font = self.btnSend.font()
        font.setBold(True)
        self.btnSend.setFont(font)
        self.btnSend.clicked.connect(self._sendToScript)
        outer.addWidget(self.btnSend)
        self._controls = column
        return column

    def _section(self, title: str, *, expanded: bool) -> QtWidgets.QVBoxLayout:
        section = CollapsibleSection(title, expanded=expanded)
        self._sectionsLayout.addWidget(section)
        return section.bodyLayout

    def _actionRow(self, layout, label: str, hint: str, command: Callable[[], None], button: str = "Apply", *,
                   ready_check: Callable[[str], bool] | None = None, **kwargs) -> ActionRow:
        """Add an ActionRow running `command`. `ready_check(text)`, if given, is re-evaluated on every keystroke and selection change, and
        turns the button green while it holds (see _refreshActionReadiness)."""
        row = ActionRow(label, hint, button, **kwargs)
        row.triggered.connect(command)
        if ready_check is not None:
            self._readyChecks.append((row, ready_check))
            row.edit.textChanged.connect(self._refreshActionReadiness)
        layout.addWidget(row)
        return row

    def _buildDisplaySection(self):
        layout = self._section("Display", expanded=False)
        self.chkAtoms = QtWidgets.QCheckBox("Atomic detail")
        self.chkAtoms.setToolTip("Draw every atom, not just the Cα trace")
        # hiding the trace only makes sense once the atom cloud is there to replace it, so it hangs off "Atomic detail"
        self.chkBackbone = QtWidgets.QCheckBox("Backbone trace")
        self.chkBackbone.setChecked(True)
        self.chkBackbone.setEnabled(False)
        self.chkCopies = QtWidgets.QCheckBox("Symmetry copies")
        self.chkCopies.setChecked(True)
        self.chkConstraints = QtWidgets.QCheckBox("Constraints")
        self.chkConstraints.setChecked(True)
        layout.addWidget(self.chkAtoms)
        indented = QtWidgets.QHBoxLayout()
        indented.setContentsMargins(20, 0, 0, 0)
        indented.addWidget(self.chkBackbone)
        layout.addLayout(indented)
        layout.addWidget(self.chkCopies)
        layout.addWidget(self.chkConstraints)
        self.chkAtoms.toggled.connect(self.chkBackbone.setEnabled)
        for box in (self.chkAtoms, self.chkBackbone, self.chkCopies, self.chkConstraints):
            box.toggled.connect(self._scheduleRedraw)

        colour_row = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Colour by")
        label.setStyleSheet(_MUTED_STYLE)
        colour_row.addWidget(label)
        self.cbColourBy = QtWidgets.QComboBox()
        self.cbColourBy.addItems(list(COLOUR_BY_MODES))
        self.cbColourBy.currentIndexChanged.connect(self._scheduleRedraw)
        colour_row.addWidget(self.cbColourBy, 1)
        layout.addLayout(colour_row)

    def _buildBodiesSection(self):
        layout = self._section("Bodies", expanded=True)
        title = QtWidgets.QLabel("Split at residues")
        title.setStyleSheet(_MUTED_STYLE)
        layout.addWidget(title)
        splits_row = QtWidgets.QHBoxLayout()
        splits_row.setSpacing(4)
        self.txtSplits = QtWidgets.QLineEdit(self.model.splits)
        self.txtSplits.setPlaceholderText("residue ids, or click residues")
        self.txtSplits.setToolTip("Re-split the whole structure at these residues. Left empty, the residues selected in the view are used.")
        self.txtSplits.returnPressed.connect(self._applySplits)
        splits_row.addWidget(self.txtSplits, 1)
        self.btnApplySplits = QtWidgets.QPushButton("Apply")
        self.btnApplySplits.clicked.connect(self._applySplits)
        splits_row.addWidget(self.btnApplySplits)
        # A chevron reveals a second, distinct kind of split. The field above re-partitions the freshly-read structure and defines the whole
        # body set. The per-body split below instead partitions a body already in the setup (e.g. one fitted to a symmetry), keeping its
        # fragments tied together, and is staged like every other edit. Folded away, since re-splitting the whole structure is the common case.
        self.btnBodySplitChevron = QtWidgets.QToolButton()
        self.btnBodySplitChevron.setAutoRaise(True)
        self.btnBodySplitChevron.setArrowType(QtCore.Qt.ArrowType.RightArrow)
        self.btnBodySplitChevron.setToolTip("Split a single existing body")
        self.btnBodySplitChevron.clicked.connect(lambda: self._toggleBodySplit())
        splits_row.addWidget(self.btnBodySplitChevron)
        layout.addLayout(splits_row)
        self.rowBodySplit = self._actionRow(
            layout, "Additional splits (an existing body)", "body residues…", self._applyBodySplit, "Add",
            ready_check=self.model.can_split_body,
        )
        self.rowBodySplit.hide()

        # base bodies, with their symmetry replicas folded beneath them. Selection is the model's own (plain, ctrl- and shift-clicks, see
        # StructureModel.toggle_highlight), so the tree's is switched off and the selected rows are tinted by hand.
        self.bodyTree = QtWidgets.QTreeWidget()
        self.bodyTree.setColumnCount(2)
        self.bodyTree.setHeaderHidden(True)
        self.bodyTree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.bodyTree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bodyTree.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.bodyTree.setMinimumHeight(160)
        self.bodyTree.setToolTip("Click to select a body; ctrl- and shift-click select several. Double-click a name to rename it.")
        header = self.bodyTree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.bodyTree.itemClicked.connect(self._onBodyClicked)
        self.bodyTree.itemDoubleClicked.connect(self._onBodyDoubleClicked)
        self.bodyTree.itemExpanded.connect(lambda item: self.model.expanded_bodies.add(item.data(0, _BODY_ROLE)))
        self.bodyTree.itemCollapsed.connect(lambda item: self.model.expanded_bodies.discard(item.data(0, _BODY_ROLE)))
        self.bodyTree.itemDelegate().closeEditor.connect(self._onRenameEditorClosed)
        layout.addWidget(self.bodyTree)

    def _buildManageSection(self):
        layout = self._section("Manage bodies", expanded=False)
        # Rename takes its "old" half from the selection when exactly one row is selected; Merge and Delete take the selected bodies when
        # their field is left empty. The buttons turn green whenever that would work, so the shortcut is discoverable.
        self.rowRename = self._actionRow(layout, "Rename", "old new", self._applyRename, "Rename", ready_check=self.model.can_rename)
        self.rowMerge = self._actionRow(layout, "Merge", "first others…", self._applyMerge, ready_check=self.model.can_merge)
        self.rowDelete = self._actionRow(layout, "Delete", "body", self._applyDelete, ready_check=self.model.can_delete)

    def _buildSymmetrySection(self):
        layout = self._section("Symmetry", expanded=False)
        self.rowAddSymmetry = self._actionRow(layout, "Add symmetry to a body", "body type", self._applyAddSymmetry)
        self.rowConvertSymmetry = self._actionRow(
            layout, "Decompose bodies into a symmetry", "body(s)… type", self._applyConvertSymmetry, "Convert",
            advanced="tolerance (default 5.0 Å)",
        )

    def _buildConstraintsSection(self):
        layout = self._section("Constraints", expanded=False)
        # `backbone` is prefilled since it is the only generator available: the row is then a one-click affair
        self.rowAutoconstrain = self._actionRow(layout, "Auto-generate constraints", "backbone", self._applyAutoconstrain, "Generate",
                                                prefill="backbone")
        self.rowConstraint = self._actionRow(layout, "Constrain two bodies", "body1 body2 type", self._applyAddConstraint, "Add")

    def _buildAppliedSection(self):
        layout = self._section("Applied elements", expanded=True)
        self.lblNoChanges = QtWidgets.QLabel("No changes staged yet.")
        self.lblNoChanges.setStyleSheet(_MUTED_STYLE)
        layout.addWidget(self.lblNoChanges)
        self.appliedTree = QtWidgets.QTreeWidget()
        self.appliedTree.setColumnCount(2)
        self.appliedTree.setHeaderHidden(True)
        self.appliedTree.setRootIsDecorated(False)
        self.appliedTree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.appliedTree.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.appliedTree.setMaximumHeight(150)
        self.appliedTree.setFont(GuiUtils.getMonospaceFont())
        header = self.appliedTree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 28)
        self.appliedTree.hide()
        layout.addWidget(self.appliedTree)

    # ----- refresh from the model ---------------------------------------------
    def _rebuild(self) -> tuple[bool, str]:
        """Rebuild the model from its current base and staged elements, and refresh the view on success."""
        ok, msg = self.model.rebuild()
        if ok:
            self._onRebuilt()
        return ok, msg

    def _onRebuilt(self, *, rebuild_rows: bool = True):
        """Refresh the view from a freshly rebuilt model. A rename changes nothing but names, so it passes rebuild_rows=False to relabel
        the Bodies list in place instead."""
        if rebuild_rows:
            self._rebuildBodyList()
        else:
            self._refreshBodyNames()
        self._refreshActionReadiness()
        self._refreshSplitField()
        self._scheduleRedraw()
        self._setStale(False)  # the view now matches this base

    def _showResult(self, result: ActionResult, *, rebuild_rows: bool = True):
        """Reflect an action's outcome: refresh from the model if it was rebuilt, and show its status message."""
        if result.rebuilt:
            self._onRebuilt(rebuild_rows=rebuild_rows)
            self._rebuildAppliedList()
        if result.message:
            self._setStatus(result.message, ok=result.ok)

    def _refreshActionReadiness(self):
        for row, check in self._readyChecks:
            row.setReady(check(row.text()))

    def _refreshSplitField(self):
        """Dim the whole-structure splits field once applying it would override an existing split. It stays usable: this only stops it
        reading as the obvious next step, since the per-body split is."""
        self.txtSplits.setStyleSheet(f"QLineEdit {{ color: {PALETTE['muted']}; }}" if self.model.split_would_override() else "")

    def _toggleBodySplit(self, *, expand: bool | None = None):
        """Fold the per-body split row in or out; `expand` forces a direction instead of toggling."""
        expand = self.rowBodySplit.isHidden() if expand is None else expand
        self.rowBodySplit.setVisible(expand)
        self.btnBodySplitChevron.setArrowType(QtCore.Qt.ArrowType.DownArrow if expand else QtCore.Qt.ArrowType.RightArrow)

    # ----- staleness / refresh ------------------------------------------------
    def checkStale(self):
        """Flag the view as stale when the script changed since it was built. If the structure never loaded, retry instead: there is no
        built view or staged edit to protect, and a relaxed load granted meanwhile may now let it through. Called when the view is shown."""
        if self._busy:
            return
        if not self.model.built:
            ok, msg = self._rebuild()
            if not ok:
                self._setStatus(f"Could not load the structure: {msg}", ok=False)
                self._redraw()
            return
        self._setStale(self.model.is_stale())

    def _setStale(self, stale: bool):
        self.btnRefresh.setVisible(stale)

    def _doRefresh(self):
        """Reload the view from the current script, discarding the staged edits (confirmed only when there are any to lose)."""
        if self.model.elements:
            n = len(self.model.elements)
            answer = QtWidgets.QMessageBox.question(
                self, "Refresh from script", f"Discard {n} staged change{'' if n == 1 else 's'} and reload from the current script?")
            if answer != QtWidgets.QMessageBox.StandardButton.Yes:
                return
        ok, msg = self.model.refresh_from_base()
        self._rebuildAppliedList()
        self.txtSplits.setText(self.model.splits)  # mirror the (possibly re-edited) script's splits again
        if ok:
            self._onRebuilt()
        self._setStatus("Reloaded from the current script." if ok else f"Could not reload from the script: {msg}", ok=ok)

    def setBusy(self, busy: bool):
        """Lock the controls while a refinement runs: every action rebuilds the structure through the backend, which the run owns until
        it finishes. The view itself stays live."""
        self._busy = busy
        self._controls.setEnabled(not busy)
        self._controls.setToolTip("Unavailable while a refinement runs." if busy else "")

    # ----- body list ----------------------------------------------------------
    def _rebuildBodyList(self):
        self.bodyTree.clear()
        self._bodyItems = {}
        muted, accent = QtGui.QColor(PALETTE["muted"]), QtGui.QColor(PALETTE["accent"])
        self.bodyTree.blockSignals(True)  # expanding rows below must not echo back into the model's fold state
        for b in self.model.bodies:
            replicas = b["copies"][1:]
            res = f"res {b['res'][0]}–{b['res'][1]}" if b["res"] else "no residues"
            extra = f" · {len(replicas)} copies" if replicas else ""
            item = QtWidgets.QTreeWidgetItem([b["name"], f"{b['atoms']} atoms · {res}{extra}"])
            item.setIcon(0, self._swatch(b["colour"], 12))
            item.setForeground(1, muted)
            self._tagItem(item, b["index"], None)
            self.bodyTree.addTopLevelItem(item)
            for copy in replicas:
                info = self.model.replica_info[(b["index"], copy)]
                child = QtWidgets.QTreeWidgetItem([info["name"], f"[{info['type']}]"])
                child.setIcon(0, self._swatch(b["colour"], 8))
                child.setForeground(0, muted)
                child.setForeground(1, accent)
                self._tagItem(child, b["index"], copy)
                item.addChild(child)
            item.setExpanded(b["index"] in self.model.expanded_bodies)
        self.bodyTree.blockSignals(False)
        self._refreshRowHighlight()

    def _tagItem(self, item: QtWidgets.QTreeWidgetItem, body: int, copy: int | None):
        item.setData(0, _BODY_ROLE, body)
        item.setData(0, _COPY_ROLE, -1 if copy is None else copy)
        self._bodyItems[(body, copy)] = item

    @staticmethod
    def _selector(item: QtWidgets.QTreeWidgetItem) -> tuple[int, int | None]:
        copy = item.data(0, _COPY_ROLE)
        return item.data(0, _BODY_ROLE), None if copy < 0 else copy

    @staticmethod
    def _swatch(colour: str, size: int) -> QtGui.QIcon:
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtGui.QColor(colour))
        return QtGui.QIcon(pixmap)

    def _refreshBodyNames(self):
        """Relabel the rows from the model, after a rename. Renaming a body can rename its replicas too, so every row is relabelled."""
        for (body, copy), item in self._bodyItems.items():
            name = self.model.name_of(body, copy)
            if name is not None:
                item.setText(0, name)

    def _refreshRowHighlight(self):
        tint = QtGui.QBrush(QtGui.QColor(PALETTE["accent_soft"]))
        for selector, item in self._bodyItems.items():
            brush = tint if selector in self.model.highlighted else QtGui.QBrush()
            item.setBackground(0, brush)
            item.setBackground(1, brush)

    def _onBodyClicked(self, item: QtWidgets.QTreeWidgetItem, _column: int):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        self._toggleHighlight(*self._selector(item),
                              shift=bool(modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier),
                              ctrl=bool(modifiers & QtCore.Qt.KeyboardModifier.ControlModifier))

    def _toggleHighlight(self, body: int, copy: int | None, *, shift: bool = False, ctrl: bool = False):
        """Select/deselect a row; see StructureModel.toggle_highlight for what plain, ctrl- and shift-clicks do."""
        # isolating a single replica is pointless while copies are hidden, so reveal them
        if self.model.toggle_highlight(body, copy, shift=shift, ctrl=ctrl) and not self.chkCopies.isChecked():
            self.chkCopies.setChecked(True)
        self._refreshRowHighlight()
        self._refreshActionReadiness()
        self._scheduleRedraw()

    def _onBodyDoubleClicked(self, item: QtWidgets.QTreeWidgetItem, _column: int):
        """Rename a body or replica in place. The double-click's first press already toggled the row's selection, so toggle it straight
        back, as if the row had never been clicked."""
        if self._busy:
            return
        body, copy = self._selector(item)
        self._toggleHighlight(body, copy)
        self._renaming = (item, body, copy, self.model.name_of(body, copy))
        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
        self.bodyTree.editItem(item, 0)

    def _onRenameEditorClosed(self, *_args):
        """Apply the in-place rename once its editor closes; Escape leaves the name as it was, which is a no-op."""
        if self._renaming is None:
            return
        item, body, copy, old = self._renaming
        self._renaming = None
        item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        new = item.text(0)
        item.setText(0, old)  # the label follows the model, which only changes if the backend accepts the rename
        self._showResult(self.model.rename(old, new), rebuild_rows=False)

    # ----- drawing ------------------------------------------------------------
    def _scheduleRedraw(self, *_args):
        """Coalesce the (comparatively expensive) redraws requested by one event into a single one, once control returns to the event loop."""
        self._redrawTimer.start()

    def _redraw(self):
        ax = self.axes
        view = self._orientation()
        lims = (ax.get_xlim(), ax.get_ylim(), ax.get_zlim()) if self.model.data is not None else None
        ax.clear()
        ax.set_axis_off()
        if self.model.data is None:
            ax.text2D(0.5, 0.5, "Could not read the structure", transform=ax.transAxes, ha="center", va="center", color=PALETTE["muted"])
        else:
            draw_structure(
                ax, self.model.data, self.model.split_residues(),
                show_atoms=self.chkAtoms.isChecked(),
                show_copies=self.chkCopies.isChecked(),
                show_backbone=self.chkBackbone.isChecked() or not self.chkAtoms.isChecked(),
                show_constraints=self.chkConstraints.isChecked(),
                highlight=self.model.highlighted,
                color_by=COLOUR_BY_MODES[self.cbColourBy.currentText()],
                body_names={b["index"]: b["name"] for b in self.model.bodies},
                selected_residues=self.model.selected_residues,
            )
            if lims is not None and self._preserveView:  # keep the zoom across redraws
                ax.set_xlim(lims[0])
                ax.set_ylim(lims[1])
                ax.set_zlim(lims[2])
        if self._preserveView:  # and the camera angle
            self._setOrientation(view)
        self._preserveView = True
        self.figure.set_layout_engine("tight")
        self.canvas.draw_idle()
        self._refreshClearChip()

    def _refreshClearChip(self):
        self.btnClearSelection.setVisible(bool(self.model.selected_residues or self.model.highlighted))

    def _clearAllSelection(self):
        """Drop both selections at once, the click-selected residues and the selected bodies: in the plot they read as one."""
        self.model.clear_all_selection()
        self._refreshRowHighlight()
        self._refreshActionReadiness()
        self._scheduleRedraw()
        self._setStatus("Selection cleared.", ok=True)

    # ----- clickable preview --------------------------------------------------
    def _onPreviewHover(self, event):
        hit = nearest_ca_residue(self.axes, self.model.data, event)
        if hit is None:
            self.lblHover.setText("")
            return
        name = self.model.name_of(hit["body"], None) or f"b{hit['body'] + 1}"
        verb = "deselect" if (hit["body"], hit["residue"]) in self.model.selected_residues else "select"
        self.lblHover.setText(f"{name} · residue {hit['residue']} · click to {verb}")

    def _onPreviewPress(self, event):
        self._pressXY = (event.x, event.y) if event.button == 1 else None

    def _onPreviewRelease(self, event):
        """A left release that barely moved from its press is a click: toggle the nearest residue in the selection. A release after a drag
        (a rotation), or while a toolbar pan/zoom mode is active, is ignored."""
        press, self._pressXY = self._pressXY, None
        if event.button != 1 or press is None or event.x is None or event.y is None or self.toolbar.mode:
            return
        if abs(event.x - press[0]) + abs(event.y - press[1]) > PICK_CLICK_DRAG_TOLERANCE:
            return
        hit = nearest_ca_residue(self.axes, self.model.data, event)
        if hit is not None:
            self._toggleSelectedResidue(hit["body"], hit["residue"])

    def _toggleSelectedResidue(self, body: int, resid: int):
        message = self.model.toggle_selected_residue(body, resid)
        self._scheduleRedraw()
        self._refreshActionReadiness()  # the residue selection stands in for an empty field, so it changes what is clickable
        # once re-splitting the whole structure would override the existing split, the per-body split is the only thing a click can usefully
        # feed, so reveal it rather than leave it behind a chevron
        if self.model.selected_residues and self.model.split_would_override():
            self._toggleBodySplit(expand=True)
        self._setStatus(message, ok=True)

    # ----- camera -------------------------------------------------------------
    # The calculator's own preview and this view show the same structure in two figures. Rather than truly sync them, each adopts the other's
    # camera angle when the user switches to it, which reads as continuous. Only the orientation is carried, not the zoom, since the two
    # structures diverge after a merge or delete and shared limits would clip.
    def cameraOrientation(self) -> tuple:
        return self._orientation()

    def setCameraOrientation(self, cam: tuple | None):
        if cam is None:
            return
        self._setOrientation(cam)
        self.canvas.draw_idle()

    def _orientation(self) -> tuple:
        return self.axes.elev, self.axes.azim, getattr(self.axes, "roll", 0.0)

    def _setOrientation(self, cam: tuple):
        elev, azim, roll = cam
        self.axes.view_init(elev=elev, azim=azim, roll=roll)

    # ----- setup actions ------------------------------------------------------
    def _applySplits(self):
        """Re-split the whole structure at the residues in the splits field, or at the selected residues if it is left empty."""
        result, shown = self.model.apply_splits(self.txtSplits.text())
        self.txtSplits.setText(shown)
        if result.rebuilt:
            self._onRebuilt()
        elif result.ok:  # nothing to re-split, but a consumed residue selection still has to disappear from the plot
            self._scheduleRedraw()
            self._refreshActionReadiness()
        if result.message:
            self._setStatus(result.message, ok=result.ok)

    def _runAction(self, row: ActionRow, action: Callable[..., ActionResult], *args):
        result = action(*args)
        self._showResult(result)
        if result.ok:
            row.clear()
        self._refreshActionReadiness()

    def _applyBodySplit(self):
        self._runAction(self.rowBodySplit, self.model.apply_body_split, self.rowBodySplit.text())

    def _applyRename(self):
        self._runAction(self.rowRename, self.model.apply_rename, self.rowRename.text())

    def _applyMerge(self):
        self._runAction(self.rowMerge, self.model.apply_merge, self.rowMerge.text())

    def _applyDelete(self):
        self._runAction(self.rowDelete, self.model.apply_delete, self.rowDelete.text())

    def _applyAddSymmetry(self):
        self._runAction(self.rowAddSymmetry, self.model.apply_add_symmetry, self.rowAddSymmetry.text())

    def _applyConvertSymmetry(self):
        self._runAction(self.rowConvertSymmetry, self.model.apply_convert_symmetry, self.rowConvertSymmetry.text(),
                        self.rowConvertSymmetry.advancedText())

    def _applyAutoconstrain(self):
        self._runAction(self.rowAutoconstrain, self.model.apply_autoconstrain, self.rowAutoconstrain.text())

    def _applyAddConstraint(self):
        self._runAction(self.rowConstraint, self.model.apply_add_constraint, self.rowConstraint.text())

    def _rebuildAppliedList(self):
        self.appliedTree.clear()
        self.lblNoChanges.setVisible(not self.model.elements)
        self.appliedTree.setVisible(bool(self.model.elements))
        for i, element in enumerate(self.model.elements):
            # a multi-line element (e.g. a constrain block) collapses to one line, elided to the width; the tooltip has it in full
            item = QtWidgets.QTreeWidgetItem([" ".join(element.split())])
            item.setToolTip(0, element)
            self.appliedTree.addTopLevelItem(item)
            remove = QtWidgets.QToolButton()
            remove.setText("✕")
            remove.setAutoRaise(True)
            remove.setToolTip("Remove this change")
            remove.clicked.connect(lambda _checked=False, i=i: self._removeElement(i))
            self.appliedTree.setItemWidget(item, 1, remove)

    def _removeElement(self, i: int):
        self._showResult(self.model.remove_element(i))

    def _setStatus(self, text: str, *, ok: bool):
        """Show a transient status message: it holds at full strength, then fades out and clears, so a long message doesn't keep squeezing
        the sections above it."""
        self._statusHold.stop()
        self._statusFade.stop()
        self._statusEffect.setOpacity(1.0)
        self.lblStatus.setStyleSheet(f"color: {PALETTE['ok_border'] if ok else PALETTE['danger']};")
        self.lblStatus.setText(text)
        if text:
            self._statusHold.start()

    # ----- send to script -----------------------------------------------------
    def _sendToScript(self):
        change = self.model.send_script()
        if change is None:  # neither the splits nor the staged elements differ from the script
            self._setStatus("No changes to send.", ok=False)
            return
        old, new = change
        if not self._confirmChange(old, new):
            return
        self.scriptApplied.emit(new)
        # the staged edits now live in the script; keeping them staged would apply them twice on the next rebuild
        ok, _msg = self.model.sent()
        self._rebuildAppliedList()
        if ok:
            self._onRebuilt()

    def _confirmChange(self, old: str, new: str) -> bool:
        return ScriptDiffDialog(old, new, self).exec() == QtWidgets.QDialog.DialogCode.Accepted


class ScriptDiffDialog(QtWidgets.QDialog):
    """A side-by-side diff of the script: the original on the left with removed lines tinted red, the new one on the right with added lines
    tinted green. The two sides scroll together, since their rows are aligned."""

    def __init__(self, old: str, new: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preview script changes")
        self.resize(900, 560)
        layout = QtWidgets.QVBoxLayout(self)
        sides = QtWidgets.QGridLayout()
        self.original = self._side(sides, "Original", 0)
        self.changed = self._side(sides, "With changes", 1)
        layout.addLayout(sides, 1)
        rows = side_by_side_diff(old, new)
        self._fill(self.original, [(r.old, r.old_changed) for r in rows], _DIFF_REMOVED)
        self._fill(self.changed, [(r.new, r.new_changed) for r in rows], _DIFF_ADDED)
        left, right = self.original.verticalScrollBar(), self.changed.verticalScrollBar()
        left.valueChanged.connect(right.setValue)
        right.valueChanged.connect(left.setValue)

        buttons = QtWidgets.QDialogButtonBox()
        buttons.addButton("Apply changes", QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole).setDefault(True)
        buttons.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _side(grid: QtWidgets.QGridLayout, heading: str, column: int) -> QtWidgets.QPlainTextEdit:
        label = QtWidgets.QLabel(heading)
        label.setStyleSheet(_MUTED_STYLE)
        grid.addWidget(label, 0, column)
        text = QtWidgets.QPlainTextEdit()
        text.setReadOnly(True)
        text.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        text.setFont(GuiUtils.getMonospaceFont())
        grid.addWidget(text, 1, column)
        return text

    @staticmethod
    def _fill(text: QtWidgets.QPlainTextEdit, lines: list[tuple[str, bool]], colours: tuple[str, str]):
        text.setPlainText("\n".join(line for line, _changed in lines))
        fmt = QtGui.QTextCharFormat()
        fmt.setBackground(QtGui.QColor(colours[0]))
        fmt.setForeground(QtGui.QColor(colours[1]))
        fmt.setProperty(QtGui.QTextFormat.Property.FullWidthSelection, True)
        selections = []
        document = text.document()
        for number, (_line, changed) in enumerate(lines):
            if changed:
                selection = QtWidgets.QTextEdit.ExtraSelection()
                selection.format = fmt
                selection.cursor = QtGui.QTextCursor(document.findBlockByNumber(number))
                selections.append(selection)
        text.setExtraSelections(selections)
