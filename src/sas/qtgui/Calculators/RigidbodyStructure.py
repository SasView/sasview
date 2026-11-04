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
from matplotlib.figure import Figure
from pyausaxs.gui.core.loads import RELAXED_LOADS
from pyausaxs.gui.core.palette import PALETTE
from pyausaxs.gui.core.plotting import PICK_CLICK_DRAG_TOLERANCE, draw_structure, nearest_ca_residue
from pyausaxs.gui.core.script import norm_splits
from pyausaxs.gui.core.structure import ActionResult, StructureModel, side_by_side_diff
from PySide6 import QtCore, QtGui, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Calculators.RigidbodyWidgets import (
    MUTED_STYLE,
    PRIMARY_STYLE,
    ActionField,
    CollapsibleSection,
    GlyphButton,
    ToggleChip,
    add_action_row,
)

# display label -> draw_structure `color_by` mode; the first entry is the default
COLOUR_BY_MODES = {"Body": "body", "Symmetry copy": "copy", "Residue": "residue"}

# the status line holds a message legible, then fades it out (see StructurePane._setStatus)
_STATUS_HOLD_MS, _STATUS_FADE_MS = 2500, 2500

# the "script changed" bar: amber, so it stands apart from the section headers
_REFRESH_STYLE = (
    "QPushButton { background-color: #f0ad4e; color: #4a3208; font-weight: bold; border: none; border-radius: 4px;"
    " padding: 6px; text-align: left; }"
    "QPushButton:hover { background-color: #eca23a; }"
)
_DIFF_REMOVED = (PALETTE["bad"], PALETTE["danger"])  # (background, foreground)
_DIFF_ADDED = ("#e3f4e9", "#2f7d4f")

# item data roles of a Bodies-list row: the body index, and the copy index (-1 for the whole body)
_BODY_ROLE = QtCore.Qt.ItemDataRole.UserRole
_COPY_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1


class StructurePane(QtWidgets.QWidget):
    """Interactive structure-inspection and body-management view for a single structure file: the view and its display options on the
    left, the bodies and the edits on the right.

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
        self._pressXY = None              # where a left press on the view landed, to tell a click from a rotation
        self._renaming = None             # (item, body, copy, old name) of the Bodies-list row being renamed in place
        self._readyChecks: list[tuple[ActionField, Callable[[str], bool]]] = []
        self._bodyItems: dict[tuple[int, int | None], QtWidgets.QTreeWidgetItem] = {}

        self._redrawTimer = QtCore.QTimer(self)
        self._redrawTimer.setSingleShot(True)
        self._redrawTimer.setInterval(0)
        self._redrawTimer.timeout.connect(self._redraw)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        layout.addWidget(self.splitter)
        self.splitter.addWidget(self._buildView())
        self.splitter.addWidget(self._buildControls())
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setSizes([1000, 340])

        ok, msg = self._rebuild()  # initial draw of the untouched structure
        if not ok:
            self._setStatus(f"Could not load the structure: {msg}", ok=False)
            self._redraw()

    # ----- layout -------------------------------------------------------------
    def _buildView(self) -> QtWidgets.QWidget:
        """The 3D view, with the options for how it is drawn in a slim bar above it and a readout of the residue under the cursor below."""
        pane = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(pane)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        bar = QtWidgets.QHBoxLayout()
        bar.setSpacing(4)
        self.btnHome = GlyphButton("⌂", "Reset to the default view")
        self.btnHome.clicked.connect(self._homeView)
        bar.addWidget(self.btnHome)
        bar.addSpacing(6)
        self.chipAtoms = ToggleChip("Atoms", "Draw every atom, not just the Cα trace")
        # hiding the trace only makes sense once the atom cloud is there to replace it
        self.chipBackbone = ToggleChip("Backbone", "Draw the Cα trace of each body", checked=True)
        self.chipBackbone.setEnabled(False)
        self.chipCopies = ToggleChip("Copies", "Draw the symmetry copies", checked=True)
        self.chipConstraints = ToggleChip("Constraints", "Draw the constraints between bodies", checked=True)
        self.chipAtoms.toggled.connect(self.chipBackbone.setEnabled)
        for chip in (self.chipAtoms, self.chipBackbone, self.chipCopies, self.chipConstraints):
            chip.toggled.connect(self._scheduleRedraw)
            bar.addWidget(chip)
        bar.addStretch(1)
        colour = QtWidgets.QLabel("Colour by")
        colour.setStyleSheet(MUTED_STYLE)
        bar.addWidget(colour)
        self.cbColourBy = QtWidgets.QComboBox()
        self.cbColourBy.addItems(list(COLOUR_BY_MODES))
        self.cbColourBy.currentIndexChanged.connect(self._scheduleRedraw)
        bar.addWidget(self.cbColourBy)
        layout.addLayout(bar)

        self.figure = Figure()
        self.axes = self.figure.add_subplot(111, projection="3d")
        self.axes.set_axis_off()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas, 1)

        readout = QtWidgets.QHBoxLayout()
        self.lblHover = QtWidgets.QLabel("Drag to rotate, scroll to zoom, click a residue to select it.")
        self.lblHover.setStyleSheet(MUTED_STYLE)
        readout.addWidget(self.lblHover, 1)
        # shown only while something is selected, see _refreshClearChip
        self.btnClearSelection = GlyphButton("✕  Clear selection", "Deselect every body and residue", size=12)
        self.btnClearSelection.clicked.connect(self._clearAllSelection)
        self.btnClearSelection.hide()
        readout.addWidget(self.btnClearSelection)
        layout.addLayout(readout)

        # hover to read the nearest residue, click to toggle it in the selection. A left press only counts as a click if the cursor barely
        # moved by its release; otherwise it was a rotation.
        self.canvas.mpl_connect("motion_notify_event", self._onPreviewHover)
        self.canvas.mpl_connect("button_press_event", self._onPreviewPress)
        self.canvas.mpl_connect("button_release_event", self._onPreviewRelease)
        return pane

    def _buildControls(self) -> QtWidgets.QWidget:
        column = QtWidgets.QWidget()
        column.setMinimumWidth(290)
        outer = QtWidgets.QVBoxLayout(column)
        outer.setContentsMargins(6, 0, 0, 0)

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
        self._sectionsLayout.setSpacing(4)
        scroll.setWidget(sections)
        outer.addWidget(scroll, 1)

        self._buildBodiesSection()
        self._buildEditSection()
        self._buildStagedSection()
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
        self.btnSend.setStyleSheet(PRIMARY_STYLE)
        self.btnSend.setEnabled(False)
        self.btnSend.clicked.connect(self._sendToScript)
        outer.addWidget(self.btnSend)
        self._controls = column
        return column

    def _section(self, title: str, *, expanded: bool) -> CollapsibleSection:
        section = CollapsibleSection(title, expanded=expanded)
        self._sectionsLayout.addWidget(section)
        return section

    def _actionRow(self, section: CollapsibleSection, label: str, hint: str, tooltip: str, command: Callable[[], None], *,
                   ready_check: Callable[[str], bool] | None = None, prefill: str = "") -> ActionField:
        """Add a one-line action. `ready_check(text)`, if given, is re-evaluated on every keystroke and selection change, and turns the
        field's ⏎ green while it holds (see _refreshActionReadiness)."""
        field = add_action_row(section, label, hint, tooltip, command, prefill=prefill)
        if ready_check is not None:
            self._readyChecks.append((field, ready_check))
            field.edit.textChanged.connect(self._refreshActionReadiness)
        return field

    def _buildBodiesSection(self):
        section = self._section("Bodies", expanded=True)
        # Two kinds of split. "Split all" re-partitions the freshly-read structure and defines the whole body set; "Split body" partitions a
        # single body already in the setup (e.g. one fitted to a symmetry), keeping its fragments tied together. Both take the residues
        # selected in the view when left empty.
        self.rowSplits = self._actionRow(
            section, "Split all", "residue ids", "Re-split the whole structure at these residues; left empty, at the residues selected in "
            "the view", self._applySplits, ready_check=self._canResplit, prefill=self.model.splits)
        self.rowBodySplit = self._actionRow(
            section, "Split body", "body residues…", "Split one existing body at these residues, e.g. b2 50; the residues selected in the "
            "view are enough on their own", self._applyBodySplit, ready_check=self.model.can_split_body)

        # base bodies, with their symmetry replicas folded beneath them. Selection is the model's own (plain, ctrl- and shift-clicks, see
        # StructureModel.toggle_highlight), so the tree's is switched off and the selected rows are tinted by hand.
        self.bodyTree = QtWidgets.QTreeWidget()
        self.bodyTree.setColumnCount(2)
        self.bodyTree.setHeaderHidden(True)
        self.bodyTree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.bodyTree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bodyTree.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.bodyTree.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.bodyTree.setMinimumHeight(120)
        self.bodyTree.setToolTip("Click to select a body; ctrl- and shift-click select several. Double-click a name to rename it.")
        header = self.bodyTree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.bodyTree.itemClicked.connect(self._onBodyClicked)
        self.bodyTree.itemDoubleClicked.connect(self._onBodyDoubleClicked)
        self.bodyTree.itemExpanded.connect(lambda item: self._onBodyFolded(item, True))
        self.bodyTree.itemCollapsed.connect(lambda item: self._onBodyFolded(item, False))
        self.bodyTree.itemDelegate().closeEditor.connect(self._onRenameEditorClosed)
        section.form.addRow(self.bodyTree)

    def _buildEditSection(self):
        # Rename takes its "old" half from the selection when exactly one row is selected; Merge and Delete take the selected bodies, and the
        # symmetry and constraint rows the selected bodies they need, when only the rest is typed. The ⏎ turns green whenever that would work.
        section = self._section("Edit", expanded=True)
        self.rowRename = self._actionRow(section, "Rename", "old new", "Rename a body, e.g. b1 core; with one body selected, just the new "
                                         "name", self._applyRename, ready_check=self.model.can_rename)
        self.rowMerge = self._actionRow(section, "Merge", "first others…", "Merge bodies into the first; left empty, the selected bodies",
                                        self._applyMerge, ready_check=self.model.can_merge)
        self.rowDelete = self._actionRow(section, "Delete", "bodies…", "Delete bodies; left empty, the selected bodies",
                                         self._applyDelete, ready_check=self.model.can_delete)

        section.addHeading("Symmetry")
        self.rowAddSymmetry = self._actionRow(section, "Add", "body type", "Add a symmetry to a body, e.g. b1 c4", self._applyAddSymmetry)
        self.rowConvertSymmetry = self._actionRow(
            section, "Fit", "bodies… type", "Decompose one or more bodies into a fitted symmetry, e.g. b1 b2 c2", self._applyConvertSymmetry)
        # an optional tolerance for the fit, folded away since the default is usually right
        self.btnTolerance = GlyphButton("⚙", "Set the fit's tolerance")
        self.btnTolerance.setCheckable(True)
        self.rowConvertSymmetry.addButton(self.btnTolerance)
        self.txtTolerance = QtWidgets.QLineEdit()
        self.txtTolerance.setPlaceholderText("default 5.0 Å")
        self.txtTolerance.setToolTip("How far the bodies may deviate from the fitted symmetry, in Å")
        self.txtTolerance.returnPressed.connect(self._applyConvertSymmetry)
        tolerance = QtWidgets.QLabel("Tolerance")
        tolerance.setStyleSheet(MUTED_STYLE)
        section.form.addRow(tolerance, self.txtTolerance)
        section.form.setRowVisible(self.txtTolerance, False)
        self.btnTolerance.toggled.connect(lambda shown: section.form.setRowVisible(self.txtTolerance, shown))

        section.addHeading("Constraints")
        # `backbone` is prefilled since it is the only generator available: the row is then a one-click affair
        self.rowAutoconstrain = self._actionRow(section, "Generate", "backbone", "Generate a set of constraints automatically",
                                                self._applyAutoconstrain, prefill="backbone")
        self.rowConstraint = self._actionRow(section, "Constrain", "body1 body2 type", "Constrain two bodies, e.g. b1 b2 cm, or "
                                             "b1 b2 attract 30", self._applyAddConstraint)

    def _buildStagedSection(self):
        self.stagedSection = self._section("Staged changes", expanded=True)
        self.lblNoChanges = QtWidgets.QLabel("Nothing staged yet.")
        self.lblNoChanges.setStyleSheet(MUTED_STYLE)
        self.stagedSection.form.addRow(self.lblNoChanges)
        self.appliedTree = QtWidgets.QTreeWidget()
        self.appliedTree.setColumnCount(2)
        self.appliedTree.setHeaderHidden(True)
        self.appliedTree.setRootIsDecorated(False)
        self.appliedTree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.appliedTree.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.appliedTree.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.appliedTree.setMaximumHeight(150)
        self.appliedTree.setFont(GuiUtils.getMonospaceFont())
        header = self.appliedTree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 26)
        self.appliedTree.hide()
        self.stagedSection.form.addRow(self.appliedTree)

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
        self._refreshSendState()
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
        for field, check in self._readyChecks:
            field.setReady(check(field.text()))

    def _canResplit(self, text: str) -> bool:
        """Whether "Split all" would change anything: a different split typed, or residues selected for an empty field to stand in."""
        if not text.strip():
            return bool(self.model.selected_residues) or bool(self.model.splits.strip())
        return norm_splits(text) != norm_splits(self.model.splits)

    def _refreshSplitField(self):
        """Dim the whole-structure split once applying it would override an existing split. It stays usable: this only stops it reading as
        the obvious next step, since the per-body split is."""
        self.rowSplits.setDimmed(self.model.split_would_override())

    def _refreshSendState(self):
        self.btnSend.setEnabled(not self._busy and self.model.send_script() is not None)

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
        self.rowSplits.edit.setText(self.model.splits)  # mirror the (possibly re-edited) script's splits again
        if ok:
            self._onRebuilt()
        self._setStatus("Reloaded from the current script." if ok else f"Could not reload from the script: {msg}", ok=ok)

    def setBusy(self, busy: bool):
        """Lock the controls while a refinement runs: every action rebuilds the structure through the backend, which the run owns until
        it finishes. The view itself stays live."""
        self._busy = busy
        self._controls.setEnabled(not busy)
        self._controls.setToolTip("Unavailable while a refinement runs." if busy else "")
        self._refreshSendState()

    # ----- body list ----------------------------------------------------------
    def _rebuildBodyList(self):
        self.bodyTree.clear()
        self._bodyItems = {}
        muted, accent = QtGui.QColor(PALETTE["muted"]), QtGui.QColor(PALETTE["accent"])
        self.bodyTree.blockSignals(True)  # expanding rows below must not echo back into the model's fold state
        for b in self.model.bodies:
            replicas = b["copies"][1:]
            res = f"res {b['res'][0]}–{b['res'][1]}" if b["res"] else "no residues"
            extra = f" · ×{len(replicas) + 1}" if replicas else ""
            item = QtWidgets.QTreeWidgetItem([b["name"], f"{res} · {b['atoms']} atoms{extra}"])
            item.setIcon(0, self._swatch(b["colour"], 10))
            item.setForeground(1, muted)
            self._tagItem(item, b["index"], None)
            self.bodyTree.addTopLevelItem(item)
            for copy in replicas:
                info = self.model.replica_info[(b["index"], copy)]
                child = QtWidgets.QTreeWidgetItem([info["name"], info["type"]])
                child.setIcon(0, self._swatch(b["colour"], 7))
                child.setForeground(0, muted)
                child.setForeground(1, accent)
                self._tagItem(child, b["index"], copy)
                item.addChild(child)
            item.setExpanded(b["index"] in self.model.expanded_bodies)
        self.bodyTree.blockSignals(False)
        # leave room for fold arrows only when some body has copies to fold
        self.bodyTree.setRootIsDecorated(any(len(b["copies"]) > 1 for b in self.model.bodies))
        _fitHeight(self.bodyTree, 260)
        self._refreshRowHighlight()

    def _onBodyFolded(self, item: QtWidgets.QTreeWidgetItem, expanded: bool):
        """Track which bodies show their copies: a shift-click range runs over the rows as shown."""
        body = item.data(0, _BODY_ROLE)
        if expanded:
            self.model.expanded_bodies.add(body)
        else:
            self.model.expanded_bodies.discard(body)
        _fitHeight(self.bodyTree, 260)

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
        if self.model.toggle_highlight(body, copy, shift=shift, ctrl=ctrl) and not self.chipCopies.isChecked():
            self.chipCopies.setChecked(True)
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
                show_atoms=self.chipAtoms.isChecked(),
                show_copies=self.chipCopies.isChecked(),
                show_backbone=self.chipBackbone.isChecked() or not self.chipAtoms.isChecked(),
                show_constraints=self.chipConstraints.isChecked(),
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

    def _homeView(self):
        """Reset the view to the auto-fit default."""
        self._preserveView = False
        self.axes.view_init()
        self._redraw()

    def _refreshClearChip(self):
        self.btnClearSelection.setVisible(bool(self.model.selected_residues or self.model.highlighted))

    def _clearAllSelection(self):
        """Drop both selections at once, the click-selected residues and the selected bodies: in the view they read as one."""
        self.model.clear_all_selection()
        self._refreshRowHighlight()
        self._refreshActionReadiness()
        self._scheduleRedraw()
        self._setStatus("Selection cleared.", ok=True)

    # ----- clickable view -----------------------------------------------------
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
        (a rotation) is ignored."""
        press, self._pressXY = self._pressXY, None
        if event.button != 1 or press is None or event.x is None or event.y is None:
            return
        if abs(event.x - press[0]) + abs(event.y - press[1]) > PICK_CLICK_DRAG_TOLERANCE:
            return
        hit = nearest_ca_residue(self.axes, self.model.data, event)
        if hit is not None:
            self._toggleSelectedResidue(hit["body"], hit["residue"])

    def _toggleSelectedResidue(self, body: int, resid: int):
        self._setStatus(self.model.toggle_selected_residue(body, resid), ok=True)
        self._scheduleRedraw()
        self._refreshActionReadiness()  # the residue selection stands in for an empty field, so it changes what is ready

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
        """Re-split the whole structure at the residues in the field, or at the selected residues if it is left empty."""
        result, shown = self.model.apply_splits(self.rowSplits.text())
        self.rowSplits.edit.setText(shown)
        if result.rebuilt:
            self._onRebuilt()
        elif result.ok:  # nothing to re-split, but a consumed residue selection still has to disappear from the view
            self._scheduleRedraw()
            self._refreshActionReadiness()
        if result.message:
            self._setStatus(result.message, ok=result.ok)

    def _runAction(self, field: ActionField, action: Callable[..., ActionResult], *args):
        result = action(*args)
        self._showResult(result)
        if result.ok:
            field.clear()
        self._refreshActionReadiness()
        return result

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
        if self._runAction(self.rowConvertSymmetry, self.model.apply_convert_symmetry, self.rowConvertSymmetry.text(),
                           self.txtTolerance.text()).ok:
            self.txtTolerance.clear()

    def _applyAutoconstrain(self):
        self._runAction(self.rowAutoconstrain, self.model.apply_autoconstrain, self.rowAutoconstrain.text())

    def _applyAddConstraint(self):
        self._runAction(self.rowConstraint, self.model.apply_add_constraint, self.rowConstraint.text())

    def _rebuildAppliedList(self):
        self.appliedTree.clear()
        n = len(self.model.elements)
        self.stagedSection.setTitle(f"Staged changes · {n}" if n else "Staged changes")
        self.lblNoChanges.setVisible(not n)
        self.appliedTree.setVisible(bool(n))
        for i, element in enumerate(self.model.elements):
            # a multi-line element (e.g. a constrain block) collapses to one line, elided to the width; the tooltip has it in full
            item = QtWidgets.QTreeWidgetItem([" ".join(element.split())])
            item.setToolTip(0, element)
            self.appliedTree.addTopLevelItem(item)
            remove = GlyphButton("✕", "Remove this change", hover=PALETTE["danger"], size=12)
            remove.clicked.connect(lambda _checked=False, i=i: self._removeElement(i))
            self.appliedTree.setItemWidget(item, 1, remove)
        _fitHeight(self.appliedTree, 160)
        self._refreshSendState()

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


def _fitHeight(tree: QtWidgets.QTreeWidget, cap: int):
    """Size a list to its visible rows, up to `cap` pixels, beyond which it scrolls; a short list then leaves no empty block behind it."""
    rows = 0
    iterator = QtWidgets.QTreeWidgetItemIterator(tree)
    while iterator.value() is not None:
        item = iterator.value()
        parent = item.parent()
        rows += parent is None or parent.isExpanded()
        iterator += 1
    row_height = tree.sizeHintForRow(0) if tree.topLevelItemCount() else tree.fontMetrics().height()
    tree.setFixedHeight(min(cap, max(1, rows) * max(row_height, 1) + 2 * tree.frameWidth() + 4))


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
        for one, other in ((self.original, self.changed), (self.changed, self.original)):
            one.verticalScrollBar().valueChanged.connect(other.verticalScrollBar().setValue)
            one.horizontalScrollBar().valueChanged.connect(other.horizontalScrollBar().setValue)

        buttons = QtWidgets.QDialogButtonBox()
        apply = buttons.addButton("Apply changes", QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        apply.setDefault(True)
        apply.setStyleSheet(PRIMARY_STYLE)
        buttons.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _side(grid: QtWidgets.QGridLayout, heading: str, column: int) -> QtWidgets.QPlainTextEdit:
        label = QtWidgets.QLabel(heading)
        label.setStyleSheet(MUTED_STYLE)
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
