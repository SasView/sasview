"""Rigid-body refinement of a structure against SAXS data, driven by a pyAUSAXS sequencer script.

The script editor is the single source of truth: the input fields are shortcuts that each rewrite only their own line of the script's load
block. The script handling, the refinement runner and the structure previews come from pyausaxs.gui.core, which pyAUSAXS's own GUI shares,
so the two front-ends read and write scripts identically.
"""

import logging
import os

from pyausaxs.gui.core import script as rbscript
from pyausaxs.gui.core.files import SAXS_EXTENSIONS, STRUCTURE_EXTENSIONS, find_companion
from pyausaxs.gui.core.loads import LOAD_OPTIONS, RELAXED_LOADS, backend_message, structure_load_error
from pyausaxs.gui.core.plotting import draw_structure, fit_figure_from_curves, nearest_ca_residue
from pyausaxs.gui.core.preview import LiveStructure, PreviewCache, bare_structure_preview
from pyausaxs.gui.core.runner import RefinementWorker
from pyausaxs.gui.core.syntax import fetch_vocabulary
from PySide6 import QtCore, QtWidgets

import sas.qtgui.Calculators.RigidbodyRefinementUI as RigidBodyRefinementUI
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.system.user import get_app_dir, get_cache_dir

logger = logging.getLogger(__name__)

# milliseconds to wait after the last edit before rebuilding the structure preview, so typing stays smooth
_PREVIEW_DEBOUNCE_MS = 150


class RigidBodyRefinement:
    def __init__(self, *args):
        self.gui = RigidBodyRefinementUI.RigidBodyRefinementUI(*args)
        self._relaxed_loads = RELAXED_LOADS  # shared with every other user of pyAUSAXS in the process: grants are made per file
        self.worker = RefinementWorker()
        self.preview = PreviewCache(self._relaxed_loads)
        self.live = LiveStructure()
        self._backend_ready = False
        self._mode = "run"
        self._stop_requested = False      # set when the user stops a run, so the outcome can say so
        self._preview_key = None          # preview signature of what the structure tab currently shows
        self._last_valid_lims = None      # axis limits of the last drawn structure, kept across redraws
        self._pdb_changed_pending_fallback = False  # armed by a structure change: let the next failed preview retry it bare
        self._script_file_path = None     # last file the user saved the script to / loaded it from

        self._drainTimer = QtCore.QTimer(self.gui)
        self._drainTimer.setInterval(RefinementWorker.POLL_MS)
        self._drainTimer.timeout.connect(self._drain)
        self._liveTimer = QtCore.QTimer(self.gui)
        self._liveTimer.setInterval(LiveStructure.POLL_MS)
        self._liveTimer.timeout.connect(self._pollLive)
        self._previewTimer = QtCore.QTimer(self.gui)
        self._previewTimer.setSingleShot(True)
        self._previewTimer.setInterval(_PREVIEW_DEBOUNCE_MS)
        self._previewTimer.timeout.connect(self._updatePreview)

        gui = self.gui
        gui.structureField.committed.connect(self.onStructureCommitted)
        gui.saxsField.committed.connect(self.onSaxsCommitted)
        gui.txtSplits.textEdited.connect(lambda text: self._setLoadDirective("split", text))  # user edits only, never setText
        gui.editor.textChanged.connect(self._previewTimer.start)
        gui.btnValidate.clicked.connect(self.onValidate)
        gui.btnRun.clicked.connect(self.onRun)
        gui.btnStop.clicked.connect(self.onStop)
        gui.btnResetScript.clicked.connect(self.onResetScript)
        gui.btnLoadScript.clicked.connect(self.onLoadScript)
        gui.btnSaveScript.clicked.connect(self.onSaveScript)
        gui.btnHomeView.clicked.connect(self._homePreview)
        gui.structureCanvas.mpl_connect("motion_notify_event", self._onStructureHover)
        gui.closing.connect(self._saveCachedScript)

        cached = self._loadCachedScript()
        gui.replaceText(cached if cached is not None else self._defaultScript())
        self._populateInputsFromScript()

    def show(self):
        self._ensureBackend()
        self.gui.show()
        self.gui.raise_()
        self._previewTimer.start()

    def _ensureBackend(self):
        """Fetch the script vocabulary and register for live structures, once, on first use rather than at SasView start-up: both load the
        AUSAXS library, which a session that never opens this calculator has no need for."""
        if self._backend_ready:
            return
        self._backend_ready = True
        self.gui.highlighter.set_vocabulary(*fetch_vocabulary())
        try:
            # tell the backend a live-structure consumer exists, so `update` elements actually publish
            LiveStructure.register_consumer()
        except Exception as e:
            logger.warning(f"Rigid-body refinement: live structure view unavailable: {backend_message(e)}")

    # ----- script persistence -------------------------------------------------
    @staticmethod
    def _scriptCachePath() -> str:
        return str(get_cache_dir() / "rigidbody_script.txt")

    def _loadCachedScript(self) -> str | None:
        """The script from the last session, if there is one."""
        try:
            with open(self._scriptCachePath(), errors="replace") as f:
                text = f.read()
        except OSError:
            return None
        return text if text.strip() else None

    def _saveCachedScript(self):
        try:
            with open(self._scriptCachePath(), "w") as f:
                f.write(self.gui.getText())
        except OSError as e:
            logger.warning(f"Rigid-body refinement: could not save the script: {e}")

    @staticmethod
    def _defaultScript() -> str:
        """The default script, writing its output under SasView's app directory rather than wherever SasView happened to be started from."""
        output = os.path.join(str(get_app_dir()), "rigidbody") + os.sep
        return rbscript.OUTPUT_RE.sub(lambda m: m.group(1) + rbscript.quote_script_value(output), rbscript.DEFAULT_RIGIDBODY_SCRIPT, count=1)

    # ----- the load block and the input fields --------------------------------
    def _loadValue(self, directive: str) -> str | None:
        return rbscript.load_value(self.gui.getText(), directive)

    def _setLoadDirective(self, directive: str, value: str):
        """Write a single load directive (pdb/saxs/split) into the script, leaving the rest of it untouched."""
        if directive == "pdb" and value.strip() != (self._loadValue("pdb") or ""):
            # the script's splits/elements were written for whatever structure was loaded before; give the next preview one bare-load retry
            # rather than leaving the placeholder up with no explanation
            self._pdb_changed_pending_fallback = True
        new = rbscript.set_load_directive(self.gui.getText(), directive, value)
        if new is not None:
            self.gui.replaceText(new)

    def onStructureCommitted(self, path: str):
        self._setLoadDirective("pdb", path)
        if path and not self.gui.saxsField.valid():
            companion = find_companion(path, SAXS_EXTENSIONS)
            if companion:
                self.gui.saxsField.set(companion)
                self._setLoadDirective("saxs", companion)

    def onSaxsCommitted(self, path: str):
        self._setLoadDirective("saxs", path)
        if path and not self.gui.structureField.valid():
            companion = find_companion(path, STRUCTURE_EXTENSIONS)
            if companion:
                self.gui.structureField.set(companion)
                self._setLoadDirective("pdb", companion)

    def _populateInputsFromScript(self):
        """Mirror the script's load block into the input fields, after the script was replaced wholesale (restored, loaded or reset). A
        one-shot fill: later script edits don't propagate back, so the script stays the single source of truth."""
        self.gui.structureField.set(self._loadValue("pdb") or "")
        self.gui.saxsField.set(self._loadValue("saxs") or "")
        self.gui.txtSplits.setText(self._loadValue("split") or "")

    # ----- script actions -----------------------------------------------------
    def onResetScript(self):
        answer = QtWidgets.QMessageBox.question(
            self.gui, "Reset script", "Reset the script while keeping the current load element?")
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        reset = rbscript.reset_script(self.gui.getText())
        # a script without a load block of its own resets to the full default, output directory included
        self.gui.replaceText(reset if reset != rbscript.DEFAULT_RIGIDBODY_SCRIPT else self._defaultScript())
        self._populateInputsFromScript()

    def onLoadScript(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.gui, "Load refinement script", os.path.dirname(self._script_file_path or ""),
            "Script (*.conf);;All files (*)")
        if not path:
            return
        try:
            with open(path, errors="replace") as f:
                text = f.read()
        except OSError as e:
            QtWidgets.QMessageBox.critical(self.gui, "Load failed", f"Could not load the script:\n{e}")
            return
        self._script_file_path = path
        self.gui.replaceText(text)
        self._populateInputsFromScript()

    def onSaveScript(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.gui, "Save refinement script", self._script_file_path or "refinement.conf",
            "Script (*.conf);;All files (*)")
        if not path:
            return
        try:
            with open(path, "w") as f:
                f.write(self.gui.getText())
        except OSError as e:
            QtWidgets.QMessageBox.critical(self.gui, "Save failed", f"Could not save the script:\n{e}")
            return
        self._script_file_path = path

    # ----- structure preview --------------------------------------------------
    def _previewData(self, script: str) -> dict | None:
        """The script's preview structure, or None if it can't be built. Skipped while a refinement runs: the run owns the backend's
        process-wide settings until it finishes."""
        if self.worker.running():
            return None
        return self.preview.get(script)

    def _updatePreview(self):
        if self.live.active:
            return  # a live run owns the preview axis; don't draw the static preview over it
        script = self.gui.getText()
        sig = rbscript.preview_signature(script)
        if sig == self._preview_key:  # redraw only when something structural changed
            return
        self._preview_key = sig
        data = self._previewData(script)

        # a structure was just (re)chosen and the real script failed to build against it — most likely its splits/elements were written for
        # whatever was loaded before. Retry once with a bare load of just the new file, so the preview shows the structure itself rather than
        # an unexplained placeholder; the real error is still what Validate/Run act on.
        fallback_shown = False
        if data is None and self._pdb_changed_pending_fallback and self._loadValue("pdb"):
            data = bare_structure_preview(self._loadValue("pdb"), self._loadValue("saxs"), self._relaxed_loads)
            fallback_shown = data is not None
        self._pdb_changed_pending_fallback = False

        ax = self.gui.structureAxes
        view = (ax.elev, ax.azim, getattr(ax, "roll", 0.0))
        ax.clear()
        ax.set_axis_off()
        if data is None:
            ax.text2D(0.5, 0.5, "Set a structure to preview the splits", transform=ax.transAxes,
                      ha="center", va="center", color="#6b7785", fontsize=10)
        else:
            draw_structure(ax, data, rbscript.split_residues(script))
            if self._last_valid_lims is not None:  # keep the zoom and camera angle across redraws
                ax.set_xlim(self._last_valid_lims[0])
                ax.set_ylim(self._last_valid_lims[1])
                ax.set_zlim(self._last_valid_lims[2])
                ax.view_init(elev=view[0], azim=view[1], roll=view[2])
            self._last_valid_lims = [ax.get_xlim(), ax.get_ylim(), ax.get_zlim()]
        self.gui.structureFigure.set_layout_engine("tight")
        self.gui.structureCanvas.draw_idle()
        if fallback_shown:
            self.gui.appendOutput("Showing the new structure without the script's staged splits/elements — they were written for the "
                                  "previous one. Update or remove them, then Validate.\n", "warning")

    def _homePreview(self):
        """Reset the structure preview to the auto-fit default view."""
        self._last_valid_lims = None
        self._preview_key = None
        self.gui.structureAxes.view_init()
        self._updatePreview()

    def _onStructureHover(self, event):
        """Show the residue under the cursor (or clear the readout over empty space)."""
        data = None if self.live.active else self.preview.data
        hit = nearest_ca_residue(self.gui.structureAxes, data, event)
        self.gui.lblHover.setText("" if hit is None else f"b{hit['body'] + 1} · residue {hit['residue']}")

    # ----- validate / run -----------------------------------------------------
    def _structureLoads(self) -> bool:
        """Whether the script's structure can be read, offering a relaxed load if the backend refuses it. Called before Validate/Run, where
        a refused structure would otherwise surface as a bare backend message. Only offered once the bare file itself is confirmed refused:
        otherwise the problem is in the script's own splits/elements, which Validate/Run report better than a "relax the load" dialog."""
        path = self._loadValue("pdb")
        if not path or self._previewData(self.gui.getText()) is not None or self.preview.error is None:
            return True
        message = structure_load_error(path, self._relaxed_loads)
        if message is None:
            return True
        while True:
            option = self._offerRelaxedLoad(path, message)
            if option is None:
                self.gui.appendOutput(f"Could not read structure: {message}\n", "error")
                return False
            self._relaxed_loads.grant(path, option)
            message = structure_load_error(path, self._relaxed_loads)
            if message is None:
                # give the preview a fresh look now that the structure reads
                self.preview.invalidate()
                self._preview_key = None
                self._previewTimer.start()
                return True

    def _offerRelaxedLoad(self, path: str, message: str):
        """Ask whether to retry a refused structure with one of the relaxations on offer; returns the chosen option, or None."""
        box = QtWidgets.QMessageBox(self.gui)
        box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        box.setWindowTitle("Could not read structure")
        box.setText(f"The backend refused {os.path.basename(path)}:\n\n{message.strip() or 'Unknown error.'}")
        box.setInformativeText("\n\n".join(option.consequence for option in LOAD_OPTIONS))
        buttons = {box.addButton(option.label, QtWidgets.QMessageBox.ButtonRole.AcceptRole): option for option in LOAD_OPTIONS}
        box.addButton(QtWidgets.QMessageBox.StandardButton.Cancel)
        box.exec()
        return buttons.get(box.clickedButton())

    def onValidate(self):
        self._start(validate_only=True)

    def onRun(self):
        self._start(validate_only=False)

    def _start(self, *, validate_only: bool):
        if self.worker.running():
            return
        self._ensureBackend()
        self._mode = "validate" if validate_only else "run"
        self._stop_requested = False
        self.gui.clearOutput()
        # checked after the clear so the recovery dialog's own output survives, and before the busy state so a cancel leaves the buttons alone
        if not self._structureLoads():
            return
        script = self.gui.getText()
        self._saveCachedScript()
        self.gui.appendOutput("Validating script…\n\n" if validate_only else "Running rigid-body refinement…\n\n")
        if not validate_only:
            # if the script publishes its structure (`update structure`), follow it live. Must come before the run is started, so the
            # run's parse is the last to reset the live buffer.
            message = self.live.begin(script, self._relaxed_loads)
            if message:
                self.gui.appendOutput(message + "\n", "warning")
            if self.live.active:
                self.gui.showStructureTab()
                self._liveTimer.start()
        self.gui.setRunning(True, stoppable=not validate_only)
        self.worker.start(script, validate_only, structure_path=self._loadValue("pdb"), relaxed_loads=self._relaxed_loads)
        self._drainTimer.start()

    def onStop(self):
        """Ask the backend to end the run after its current iteration. The run then completes normally, so its (partial) results are
        reported as usual."""
        try:
            if not self.worker.request_stop():
                return
        except Exception as e:
            self.gui.appendOutput(f"\nCould not stop the refinement: {backend_message(e)}\n", "error")
            return
        self._stop_requested = True
        self.gui.setStopping()
        self.gui.appendOutput("\nStopping after the current iteration…\n")

    def _drain(self):
        if not self.worker.drain(self.gui.appendOutput, self._onDone):
            self._drainTimer.stop()

    def _pollLive(self):
        frame = self.live.poll()
        if frame is not None:
            self._drawLiveFrame(frame)

    def _drawLiveFrame(self, data: dict):
        ax = self.gui.structureAxes
        lims = [ax.get_xlim(), ax.get_ylim(), ax.get_zlim()]
        ax.clear()
        ax.set_axis_off()
        draw_structure(ax, data, rbscript.split_residues(self.gui.getText()))
        ax.set_xlim(lims[0])
        ax.set_ylim(lims[1])
        ax.set_zlim(lims[2])
        self.gui.structureCanvas.draw_idle()

    def _onDone(self, outcome):
        self._liveTimer.stop()
        frame = self.live.final()  # draw the final published frame, then release the preview axis
        if frame is not None:
            self._drawLiveFrame(frame)
        self.gui.setRunning(False)
        self._preview_key = None  # the preview was skipped while running; let it catch up with any edits made meanwhile
        self._previewTimer.start()

        if outcome.error is not None:
            # the backend already streamed run-time errors to the output; just note the failure
            if outcome.error_streamed:
                self.gui.appendOutput("\nRefinement failed.\n", "error")
            else:
                self.gui.appendOutput(f"\n{backend_message(outcome.error)}\n", "error")
            return
        if self._mode == "validate":
            self.gui.appendOutput("\nValidation successful.\n", "success")
            return
        if self._stop_requested:
            self.gui.appendOutput("\nRefinement stopped. The results are the best conformation found so far.\n", "success")
        else:
            self.gui.appendOutput("\nRefinement completed.\n", "success")
        if outcome.result is None or outcome.result.size == 0:
            self.gui.appendOutput("No fit curves were returned.\n")
            return
        try:
            self.gui.setFitFigures([
                (fit_figure_from_curves(outcome.result, logx=False), "Fit (log)"),
                (fit_figure_from_curves(outcome.result, logx=True), "Fit (log-log)"),
            ])
        except Exception as e:
            self.gui.appendOutput(f"Failed to plot results: {e}\n", "error")
        self._sendResultsToDataExplorer(outcome.result)

    def _sendResultsToDataExplorer(self, res):
        """Send the refinement results (q, I, I_err, I_model) to the Data Explorer."""
        q, intensity, intensity_err, model = res[:, 0], res[:, 1], res[:, 2], res[:, 3]

        data_exp = Data1D(x=q, y=intensity, dy=intensity_err)
        data_exp.title = "Rigidbody refinement (data)"
        data_exp.id = data_exp.title
        data_exp.xaxis(r'\rm{Q}', r'\AA^{-1}')
        data_exp.yaxis(r'\rm{Intensity}', 'cm^{-1}')

        data_model = Data1D(x=q, y=model)
        data_model.title = "Rigidbody refinement (model)"
        data_model.id = data_model.title
        data_model.xaxis(r'\rm{Q}', r'\AA^{-1}')
        data_model.yaxis(r'\rm{Intensity}', 'cm^{-1}')

        item_exp = GuiUtils.createModelItemWithPlot(data_exp, name=data_exp.title)
        GuiUtils.updateModelItemWithPlot(item_exp, data_model, name=data_model.title)
        GuiUtils.communicator.updateModelFromPerspectiveSignal.emit(item_exp)
        GuiUtils.communicator.forcePlotDisplaySignal.emit([item_exp, data_model])
