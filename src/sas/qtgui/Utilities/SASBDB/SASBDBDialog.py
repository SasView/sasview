"""SASBDB Export Dialog — review/edit export data before JSON/PDF/project export."""
import logging
import math
import os
import sys

import numpy as np
from dominate import tags
from dominate.util import raw
from PySide6 import QtCore, QtWidgets

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary
from sas.qtgui.Utilities.Reports.reports import ReportBase
from sas.qtgui.Utilities.SASBDB.guinier_plot_panel import GuinierPlotPanel
from sas.qtgui.Utilities.SASBDB.sasbdb_data import (
    SASBDBBuffer,
    SASBDBExportData,
    SASBDBFit,
    SASBDBGuinier,
    SASBDBInstrument,
    SASBDBModel,
    SASBDBMolecule,
    SASBDBProject,
    SASBDBSample,
)
from sas.qtgui.Utilities.SASBDB.sasbdb_data_collector import SASBDBDataCollector
from sas.qtgui.Utilities.SASBDB.sasbdb_exporter import SASBDBExporter
from sas.qtgui.Utilities.SASBDB.UI.SASBDBDialogUI import Ui_SASBDBDialogUI

logger = logging.getLogger(__name__)

_GUINIER_DERIVED_FIELD_NAMES = (
    "txtGuinierRangeStart",
    "txtGuinierRangeEnd",
    "txtGuinierRg",
    "txtGuinierRgError",
    "txtGuinierI0",
)
_GUINIER_FIELD_NAMES = _GUINIER_DERIVED_FIELD_NAMES + (
    "txtGuinierStartPoint",
    "txtGuinierEndPoint",
)
_PDF_CSS = (
    "body{font-size:11pt}"
    "table.sasbdb-table{font-size:11pt;width:100%;margin:10px 0}"
    "th.sasbdb-th{font-size:11pt;font-weight:bold;background:#f0f0f0;"
    "padding:8px;text-align:left}"
    "td.sasbdb-field{font-size:11pt;font-weight:bold;background:#f5f5f5;"
    "color:#666;padding:6px 8px}"
    "td.sasbdb-value{font-size:11pt;background:#fff;color:#000;padding:6px 8px}"
    "h3.sasbdb-section{margin:10px 0 8px;font-weight:bold;color:#2c3e50;"
    "font-size:13pt}"
    "hr.sasbdb-section-rule{margin-bottom:10px;border:1px solid #3498db}"
    "p.sasbdb-section-spacer{margin-top:15px}"
)


class SASBDBDialog(QtWidgets.QDialog, Ui_SASBDBDialogUI):
    """Dialog to review and export SASBDB submission data (JSON, PDF, project)."""

    def __init__(
        self,
        export_data: SASBDBExportData | None = None,
        parent: QtCore.QObject | None = None,
        guinier_source_data=None,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self._guinier_source_data = guinier_source_data
        self._guinier_plot_a: float | None = None
        self._guinier_plot_b: float | None = None
        self._guinier_suppress_range_signals = False
        self._guinier_plot_panel = None
        if hasattr(self, "widgetGuinierPlot"):
            if hasattr(self, "horizontalLayoutGuinierMain"):
                self.horizontalLayoutGuinierMain.setAlignment(
                    self.widgetGuinierPlot,
                    QtCore.Qt.AlignmentFlag.AlignTop
                    | QtCore.Qt.AlignmentFlag.AlignLeft,
                )
            plot_layout = QtWidgets.QVBoxLayout(self.widgetGuinierPlot)
            plot_layout.setContentsMargins(0, 0, 0, 0)
            self._guinier_plot_panel = GuinierPlotPanel(self.widgetGuinierPlot)
            plot_layout.addWidget(self._guinier_plot_panel)

        self.export_data = export_data or SASBDBExportData()
        self.save_location = ObjectLibrary.getObject('SASBDBDialog_directory')

        self.cmdExport.clicked.connect(self.onExport)
        self.cmdGeneratePDF.clicked.connect(self.onGeneratePDF)
        self.cmdHelp.clicked.connect(self.onHelp)
        self.cmdClose.clicked.connect(self.close)
        self.chkPublished.toggled.connect(self.onPublishedToggled)
        self._wire_guinier_controls()

        self.populateFromData()
        self._set_guinier_derived_fields_read_only(False)
        self.onPublishedToggled(self.chkPublished.isChecked())
        self._refresh_guinier_plot()

    def _style_action_button(self, btn) -> None:
        btn.setAutoDefault(False)
        btn.setDefault(False)
        if sys.platform == "darwin":
            btn.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

    def _wire_guinier_controls(self) -> None:
        if hasattr(self, 'btnGuinierEstimateFreeSAS'):
            self.btnGuinierEstimateFreeSAS.clicked.connect(
                self._on_guinier_estimate_clicked)
            self._style_action_button(self.btnGuinierEstimateFreeSAS)
        if hasattr(self, "btnGuinierReset"):
            self.btnGuinierReset.clicked.connect(self._on_guinier_reset_clicked)
            self._style_action_button(self.btnGuinierReset)
        if hasattr(self, "txtGuinierStartPoint"):
            self.txtGuinierStartPoint.editingFinished.connect(
                self._on_guinier_indices_editing_finished)
            self.txtGuinierEndPoint.editingFinished.connect(
                self._on_guinier_indices_editing_finished)
        if hasattr(self, "txtGuinierRangeStart"):
            self.txtGuinierRangeStart.editingFinished.connect(
                self._on_guinier_q_range_editing_finished)
            self.txtGuinierRangeEnd.editingFinished.connect(
                self._on_guinier_q_range_editing_finished)

    def _set_guinier_derived_fields_read_only(self, readonly: bool) -> None:
        for name in _GUINIER_DERIVED_FIELD_NAMES:
            if hasattr(self, name):
                getattr(self, name).setReadOnly(readonly)

    def _clear_guinier_fields(self) -> None:
        for name in _GUINIER_FIELD_NAMES:
            getattr(self, name).clear()
        self._guinier_plot_a = self._guinier_plot_b = None

    @staticmethod
    def _parse(text: str, cast):
        text = text.strip()
        if not text:
            return None
        try:
            return cast(text)
        except ValueError:
            return None

    def _parse_float(self, text: str) -> float | None:
        return self._parse(text, float)

    def _parse_int(self, text: str) -> int | None:
        return self._parse(text, int)

    def _parse_float_field(self, widget) -> float | None:
        return self._parse(widget.text(), float)

    def _parse_int_field(self, widget) -> int | None:
        return self._parse(widget.text(), int)

    @staticmethod
    def _set_text(widget, value, fmt=None) -> None:
        if value is None or value == "":
            return
        widget.setText(fmt.format(value) if fmt else str(value))

    @staticmethod
    def _set_plain(widget, value) -> None:
        if value:
            widget.setPlainText(value)

    @staticmethod
    def _set_combo(combo, text) -> None:
        if not text:
            return
        index = combo.findText(text)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _current_fitting_widget(self):
        parent = self.parent()
        if parent is None:
            return None
        perspective = getattr(parent, '_current_perspective', None)
        if perspective is None and hasattr(parent, 'guiManager'):
            perspective = getattr(parent.guiManager, '_current_perspective', None)
        if perspective is None:
            return None
        from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow
        if not isinstance(perspective, FittingWindow):
            return None
        return perspective.currentFittingWidget

    def _fit_guinier_over_q_range(
        self, q_lo: float, q_hi: float, *, clear_first: bool = False
    ) -> bool:
        if self._guinier_source_data is None or q_lo >= q_hi:
            return False
        guinier, fit_info = SASBDBDataCollector.collect_guinier_from_q_range(
            self._guinier_source_data, q_lo, q_hi
        )
        if guinier is None:
            return False
        self._apply_guinier_to_fields(
            guinier, clear_first=clear_first, fit_info=fit_info)
        return True

    def _on_guinier_reset_clicked(self) -> None:
        self._clear_guinier_fields()
        self._set_guinier_derived_fields_read_only(False)
        self._refresh_guinier_plot()

    def _sync_guinier_plot_ab_from_rg_i0(self, guinier: SASBDBGuinier) -> None:
        if guinier.rg is None or guinier.i0 is None or guinier.i0 <= 0:
            self._guinier_plot_a = self._guinier_plot_b = None
            return
        scale = SASBDBDataCollector._guinier_native_q_to_nm_scale(
            self._guinier_source_data)
        rg_native = float(guinier.rg) * scale
        self._guinier_plot_b = -(rg_native**2) / 3.0
        self._guinier_plot_a = math.log(float(guinier.i0))

    def _apply_guinier_to_fields(
        self,
        guinier: SASBDBGuinier,
        clear_first: bool = False,
        fit_info: dict | None = None,
    ) -> None:
        self._guinier_suppress_range_signals = True
        try:
            if clear_first:
                self._clear_guinier_fields()
            pairs = (
                (self.txtGuinierRg, guinier.rg, "{:.2g}"),
                (self.txtGuinierRgError, guinier.rg_error, "{:.2g}"),
                (self.txtGuinierI0, guinier.i0, "{:.2g}"),
                (self.txtGuinierRangeStart, guinier.range_start, None),
                (self.txtGuinierRangeEnd, guinier.range_end, None),
                (self.txtGuinierStartPoint, guinier.start_point, None),
                (self.txtGuinierEndPoint, guinier.end_point, None),
            )
            for widget, value, fmt in pairs:
                if value is not None:
                    self._set_text(widget, value, fmt)
            if fit_info is not None:
                self._guinier_plot_a = fit_info.get("a")
                self._guinier_plot_b = fit_info.get("b")
            elif guinier.rg is not None and guinier.i0 is not None and guinier.i0 > 0:
                self._sync_guinier_plot_ab_from_rg_i0(guinier)
            else:
                self._guinier_plot_a = self._guinier_plot_b = None
        finally:
            self._guinier_suppress_range_signals = False
        self._refresh_guinier_plot()

    def _refresh_guinier_plot(self) -> None:
        if self._guinier_plot_panel is None:
            return

        data = self._guinier_source_data
        q = (np.asarray(data.x, dtype=float)
             if data is not None and hasattr(data, "x") else None)
        iy = (np.asarray(data.y, dtype=float)
              if data is not None and hasattr(data, "y") else None)
        q_start = q_end = None
        rs = self.txtGuinierRangeStart.text().strip()
        re = self.txtGuinierRangeEnd.text().strip()
        if rs and re:
            try:
                q_start, q_end = float(rs), float(re)
            except ValueError:
                pass
        self._guinier_plot_panel.update_plot(
            q, iy, q_start, q_end, self._guinier_plot_a, self._guinier_plot_b)

    def _guinier_any_field_nonempty(self) -> bool:
        return any(
            hasattr(self, name) and getattr(self, name).text().strip()
            for name in _GUINIER_FIELD_NAMES
        )

    def _q_lo_q_hi_from_guinier_indices(
        self, i_start: int, i_end: int
    ) -> tuple[float, float] | None:
        data = self._guinier_source_data
        if data is None or not hasattr(data, "x"):
            return None

        x = np.asarray(data.x, dtype=float)
        n = len(x)
        if n == 0:
            return None
        ia, ib = int(min(i_start, i_end)), int(max(i_start, i_end))
        if ia < 0 or ib >= n:
            return None
        return float(x[ia]), float(x[ib])

    def _on_guinier_indices_editing_finished(self) -> None:
        if self._guinier_suppress_range_signals:
            return
        i_s = self._parse_int_field(self.txtGuinierStartPoint)
        i_e = self._parse_int_field(self.txtGuinierEndPoint)
        if i_s is None or i_e is None:
            self._refresh_guinier_plot()
            return
        qr = self._q_lo_q_hi_from_guinier_indices(i_s, i_e)
        if qr is None or not self._fit_guinier_over_q_range(qr[0], qr[1]):
            self._refresh_guinier_plot()

    def _on_guinier_q_range_editing_finished(self) -> None:
        if self._guinier_suppress_range_signals:
            return
        q_lo = self._parse_float_field(self.txtGuinierRangeStart)
        q_hi = self._parse_float_field(self.txtGuinierRangeEnd)
        if q_lo is None or q_hi is None or not self._fit_guinier_over_q_range(q_lo, q_hi):
            self._refresh_guinier_plot()

    def _guinier_msg(self, warning: bool, text: str) -> None:
        box = (QtWidgets.QMessageBox.warning if warning
               else QtWidgets.QMessageBox.information)
        box(self, "Guinier estimate", text)

    def _on_guinier_estimate_clicked(self) -> None:
        """FreeSAS auto_guinier, or WLS fit by indices / by Q range."""
        sp = self.txtGuinierStartPoint.text().strip()
        ep = self.txtGuinierEndPoint.text().strip()
        rs = self.txtGuinierRangeStart.text().strip()
        re = self.txtGuinierRangeEnd.text().strip()

        if sp and ep:
            if self._guinier_source_data is None:
                self._guinier_msg(False,
                    "No 1D scattering data is available for a fit by indices.\n\n"
                    "Load 1D data or clear start/end point to use FreeSAS.")
                return
            i_s, i_e = self._parse_int(sp), self._parse_int(ep)
            if i_s is None or i_e is None:
                self._guinier_msg(True, "Start and end point must be integers.")
                return
            qr = self._q_lo_q_hi_from_guinier_indices(i_s, i_e)
            if qr is None:
                self._guinier_msg(
                    True, "Indices are out of range for the current 1D dataset.")
                return
            q_lo, q_hi = qr
            if q_lo >= q_hi:
                self._guinier_msg(True,
                    "Start and end point must span at least two distinct q values.")
                return
            if not self._fit_guinier_over_q_range(q_lo, q_hi):
                self._guinier_msg(True,
                    "Could not fit ln(I) vs q² for the selected indices.\n\n"
                    "Need at least two points with I > 0 and a negative slope.")
                return
            self._set_guinier_derived_fields_read_only(True)
            return

        if sp or ep:
            self._guinier_msg(False,
                "Enter both start and end point for a fit by indices, or clear "
                "both to use FreeSAS or Q start / Q end.")
            return

        if rs and re:
            if self._guinier_source_data is None:
                self._guinier_msg(False,
                    "No 1D scattering data is available for a range fit.\n\n"
                    "Load 1D data or clear Q start and Q end to use FreeSAS "
                    "auto_guinier.")
                return
            q_lo, q_hi = self._parse_float(rs), self._parse_float(re)
            if q_lo is None or q_hi is None:
                self._guinier_msg(True, "Q start and Q end must be valid numbers.")
                return
            if q_lo >= q_hi:
                self._guinier_msg(True, "Q start must be less than Q end.")
                return
            if not self._fit_guinier_over_q_range(q_lo, q_hi):
                self._guinier_msg(True,
                    "Could not fit ln(I) vs q² in the selected range.\n\n"
                    "Need at least two points with I > 0 and a negative slope "
                    "(check q range and data).")
                return
            self._set_guinier_derived_fields_read_only(True)
            return

        if rs or re:
            self._guinier_msg(False,
                "Enter both Q start and Q end to fit by q, or clear both for "
                "FreeSAS auto_guinier.")
            return

        if self._guinier_source_data is None:
            self._guinier_msg(False,
                "No 1D scattering data is available for FreeSAS.\n\n"
                "Open SASBDB from the Fitting perspective with 1D data loaded, "
                "or load 1D data in the Data Explorer first.")
            return

        guinier = SASBDBDataCollector.collect_guinier_from_freesas(
            self._guinier_source_data)
        if guinier is None:
            self._guinier_msg(True,
                "FreeSAS auto_guinier did not return a result.\n\n"
                "Ensure the freesas package is installed and the curve is suitable "
                "for Guinier analysis.")
            return
        self._apply_guinier_to_fields(guinier, clear_first=True, fit_info=None)
        self._set_guinier_derived_fields_read_only(True)

    def populateFromData(self):
        """Fill UI fields from export_data."""
        if self.export_data.project:
            project = self.export_data.project
            self.chkPublished.setChecked(project.published)
            self._set_text(self.txtPubmedPMID, project.pubmed_pmid)
            self._set_text(self.txtDOI, project.doi)
            self._set_text(self.txtProjectTitle, project.project_title)

        if not self.export_data.samples:
            instruments = self.export_data.instruments
            if instruments:
                self._populate_instrument(instruments[0])
            return

        sample = self.export_data.samples[0]
        self._set_text(self.txtSampleTitle, sample.sample_title)
        self._set_combo(self.cmbCurveType, sample.curve_type)
        self._set_combo(self.cmbAngularUnits, sample.angular_units)
        self._set_combo(self.cmbIntensityUnits, sample.intensity_units)
        self._set_text(self.txtExpMW, sample.experimental_molecular_weight)
        self._set_text(self.txtExperimentDate, sample.experiment_date)
        self._set_text(self.txtBeamline, sample.beamline_instrument)
        self._set_text(self.txtWavelength, sample.wavelength)
        self._set_text(self.txtDistance, sample.sample_detector_distance)
        self._set_text(self.txtTemperature, sample.cell_temperature)
        self._set_text(self.txtConcentration, sample.concentration)

        if sample.molecule:
            mol = sample.molecule
            self._set_combo(self.cmbMoleculeType, mol.type)
            self._set_text(self.txtLongName, mol.long_name)
            self._set_text(self.txtShortName, mol.short_name)
            self._set_plain(self.txtFastaSequence, mol.fasta_sequence)
            self._set_text(self.txtMonomerMW, mol.monomer_mw_kda)
            self._set_combo(self.cmbOligomericState, mol.oligomeric_state)
            if mol.number_of_molecules:
                self.spnNumberOfMolecules.setValue(mol.number_of_molecules)
            self._set_text(self.txtUniProt, mol.uniprot_accession)
            self._set_text(self.txtSourceOrganism, mol.source_organism)

        if sample.buffer:
            buf = sample.buffer
            self._set_plain(self.txtBufferDescription, buf.description)
            self._set_text(self.txtBufferPH, buf.ph)
            self._set_plain(self.txtBufferComment, buf.comment)

        if sample.guinier:
            self._apply_guinier_to_fields(sample.guinier, clear_first=False)

        if sample.fits:
            fit = sample.fits[0]
            self._set_text(self.txtFitSoftware, fit.software)
            self._set_text(self.txtFitVersion, fit.software_version)
            if fit.chi_squared:
                self.txtChiSquared.setText(f"{fit.chi_squared:.2f}")
            if fit.cormap_pvalue:
                self.txtCorMapPValue.setText(f"{fit.cormap_pvalue:.2g}")
            if fit.models:
                model = fit.models[0]
                self._set_text(self.txtModelName, model.software_or_db)
                self._set_plain(self.txtModelParameters, model.log)

        if self.export_data.instruments:
            self._populate_instrument(self.export_data.instruments[0])

    def _populate_instrument(self, instrument: SASBDBInstrument) -> None:
        self._set_combo(self.cmbSourceType, instrument.source_type)
        self._set_text(self.txtBeamlineName, instrument.beamline_name)
        self._set_text(self.txtSynchrotronName, instrument.synchrotron_name)
        self._set_text(self.txtDetectorManufacturer, instrument.detector_manufacturer)
        self._set_text(self.txtDetectorType, instrument.detector_type)
        self._set_text(self.txtDetectorResolution, instrument.detector_resolution)
        self._set_text(self.txtCity, instrument.city)
        self._set_text(self.txtCountry, instrument.country)

    def collectFromUI(self) -> SASBDBExportData:
        """Build SASBDBExportData from UI fields."""
        export_data = SASBDBExportData()
        project = SASBDBProject()
        project.published = self.chkPublished.isChecked()
        project.pubmed_pmid = self.txtPubmedPMID.text().strip() or None
        project.doi = self.txtDOI.text().strip() or None
        project.project_title = self.txtProjectTitle.text().strip() or None
        export_data.project = project

        sample = SASBDBSample()
        sample.sample_title = self.txtSampleTitle.text().strip() or None
        sample.curve_type = self.cmbCurveType.currentText() or None
        sample.angular_units = self.cmbAngularUnits.currentText() or None
        sample.intensity_units = self.cmbIntensityUnits.currentText() or None
        sample.experimental_molecular_weight = self._parse_float_field(self.txtExpMW)
        sample.experiment_date = self.txtExperimentDate.text().strip() or None
        sample.beamline_instrument = self.txtBeamline.text().strip() or None
        sample.wavelength = self._parse_float_field(self.txtWavelength)
        sample.sample_detector_distance = self._parse_float_field(self.txtDistance)
        sample.cell_temperature = self._parse_float_field(self.txtTemperature)
        sample.concentration = self._parse_float_field(self.txtConcentration)

        molecule = SASBDBMolecule()
        molecule.type = self.cmbMoleculeType.currentText() or None
        molecule.long_name = self.txtLongName.text().strip() or None
        molecule.short_name = self.txtShortName.text().strip() or None
        molecule.fasta_sequence = self.txtFastaSequence.toPlainText().strip() or None
        molecule.monomer_mw_kda = self._parse_float_field(self.txtMonomerMW)
        molecule.oligomeric_state = self.cmbOligomericState.currentText() or None
        molecule.number_of_molecules = self.spnNumberOfMolecules.value()
        molecule.uniprot_accession = self.txtUniProt.text().strip() or None
        molecule.source_organism = self.txtSourceOrganism.text().strip() or None
        sample.molecule = molecule

        buffer = SASBDBBuffer()
        buffer.description = self.txtBufferDescription.toPlainText().strip() or None
        buffer.ph = self._parse_float_field(self.txtBufferPH)
        buffer.comment = self.txtBufferComment.toPlainText().strip() or None
        sample.buffer = buffer

        guinier = SASBDBGuinier(
            rg=self._parse_float_field(self.txtGuinierRg),
            rg_error=self._parse_float_field(self.txtGuinierRgError),
            i0=self._parse_float_field(self.txtGuinierI0),
            range_start=self._parse_float_field(self.txtGuinierRangeStart),
            range_end=self._parse_float_field(self.txtGuinierRangeEnd),
            start_point=self._parse_int_field(self.txtGuinierStartPoint),
            end_point=self._parse_int_field(self.txtGuinierEndPoint),
        )
        if any(v is not None for v in (
                guinier.rg, guinier.rg_error, guinier.i0, guinier.range_start,
                guinier.range_end, guinier.start_point, guinier.end_point)):
            sample.guinier = guinier

        fit = SASBDBFit(
            software=self.txtFitSoftware.text().strip() or None,
            software_version=self.txtFitVersion.text().strip() or None,
            chi_squared=self._parse_float_field(self.txtChiSquared),
            cormap_pvalue=self._parse_float_field(self.txtCorMapPValue),
        )
        model_name = self.txtModelName.text().strip()
        model_parameters = self.txtModelParameters.toPlainText().strip()
        if model_name or model_parameters:
            model = SASBDBModel()
            if model_name:
                model.software_or_db = model_name
            if model_parameters:
                model.log = model_parameters
            fit.models.append(model)
        if fit.software or fit.chi_squared is not None or fit.models:
            sample.fits.append(fit)
        export_data.samples.append(sample)

        instrument = SASBDBInstrument(
            source_type=self.cmbSourceType.currentText() or None,
            beamline_name=self.txtBeamlineName.text().strip() or None,
            synchrotron_name=self.txtSynchrotronName.text().strip() or None,
            detector_manufacturer=self.txtDetectorManufacturer.text().strip() or None,
            detector_type=self.txtDetectorType.text().strip() or None,
            detector_resolution=self.txtDetectorResolution.text().strip() or None,
            city=self.txtCity.text().strip() or None,
            country=self.txtCountry.text().strip() or None,
        )
        if any((instrument.source_type, instrument.beamline_name,
                instrument.synchrotron_name, instrument.detector_manufacturer,
                instrument.city, instrument.country)):
            export_data.instruments.append(instrument)
        return export_data

    def validateData(self) -> tuple[bool, str]:
        """Return (ok, error_message) for required SASBDB fields."""
        checks = []
        if self.chkPublished.isChecked():
            if not self.txtPubmedPMID.text().strip() and not self.txtDOI.text().strip():
                return False, "If published, either PubMed PMID or DOI is required"
        else:
            checks.append((self.txtProjectTitle.text().strip(),
                           "Project Title is required if not published"))
        checks.extend([
            (self.txtSampleTitle.text().strip(), "Sample Title is required"),
            (self.txtExpMW.text().strip(),
             "Experimental Molecular Weight is required"),
            (self.txtExperimentDate.text().strip(), "Experiment Date is required"),
            (self.txtBeamline.text().strip(), "Beamline/Instrument is required"),
            (self.txtLongName.text().strip(), "Molecule Long Name is required"),
            (self.txtFastaSequence.toPlainText().strip(),
             "FASTA Sequence is required"),
            (self.txtMonomerMW.text().strip(), "Monomer MW (kDa) is required"),
            (self.txtBufferDescription.toPlainText().strip(),
             "Buffer Description is required"),
            (self.txtBufferPH.text().strip(), "Buffer pH is required"),
        ])
        for ok, msg in checks:
            if not ok:
                return False, msg

        if hasattr(self, "txtGuinierStartPoint") and self._guinier_any_field_nonempty():
            sp = self.txtGuinierStartPoint.text().strip()
            ep = self.txtGuinierEndPoint.text().strip()
            if not sp or not ep:
                return False, (
                    "Guinier: start and end point are required when any Guinier "
                    "field is filled.")
            try:
                i_s, i_e = int(sp), int(ep)
            except ValueError:
                return False, "Guinier: start and end point must be integers."
            if i_s < 0 or i_e < 0:
                return False, "Guinier: indices must be non-negative."
            if i_s >= i_e:
                return False, (
                    "Guinier: start point index must be less than end point index.")
            data = self._guinier_source_data
            if data is not None and hasattr(data, "x"):
                n = len(np.asarray(data.x))
                if n and (i_s >= n or i_e >= n):
                    return False, (
                        "Guinier: start and end point must be within the 1D data "
                        "length.")
        return True, ""

    def onPublishedToggled(self, checked: bool):
        self.txtPubmedPMID.setEnabled(checked)
        self.txtDOI.setEnabled(checked)
        self.txtProjectTitle.setEnabled(not checked)

    def onHelp(self):
        help_url = "/user/qtgui/Utilities/SASBDB/sasbdb_help.html"
        parent_window = self.parent()
        if parent_window is not None:
            if hasattr(parent_window, 'showHelp'):
                parent_window.showHelp(help_url)
                return
            gui = getattr(parent_window, 'guiManager', None)
            if gui is not None and hasattr(gui, 'showHelp'):
                gui.showHelp(help_url)
                return
        from sas.qtgui.Utilities.GuiUtils import showHelp
        showHelp(help_url)

    def _choose_save_path(self, title: str, default_name: str, filt: str) -> str | None:
        location = (self.save_location if self.save_location is not None
                    else os.path.expanduser('~'))
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, title, os.path.join(str(location), default_name), filt, "")
        if not path:
            return None
        self.save_location = os.path.dirname(path)
        ObjectLibrary.addObject('SASBDBDialog_directory', self.save_location)
        return path

    def onExport(self):
        """Validate, then write JSON + PDF + project beside the chosen JSON path."""
        is_valid, error_msg = self.validateData()
        if not is_valid:
            QtWidgets.QMessageBox.warning(self, "Validation Error", error_msg)
            return

        export_data = self.collectFromUI()
        json_filename = self._choose_save_path(
            'Export SASBDB Data', 'sasbdb_export.json', 'JSON file (*.json)')
        if not json_filename:
            return
        if not json_filename.endswith('.json'):
            json_filename += '.json'

        base_name = os.path.splitext(os.path.basename(json_filename))[0]
        directory = os.path.dirname(json_filename)
        pdf_filename = os.path.join(directory, f"{base_name}.pdf")
        project_filename = os.path.join(directory, f"{base_name}_project.json")

        results = {'json': False, 'pdf': False, 'project': False}
        errors = {'json': None, 'pdf': None, 'project': None}

        try:
            results['json'] = SASBDBExporter(export_data).export_to_json(json_filename)
            if not results['json']:
                errors['json'] = "Failed to export JSON file"
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}", exc_info=True)
            errors['json'] = str(e)

        try:
            self._generatePDFReport(export_data, pdf_filename)
            results['pdf'] = True
        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            errors['pdf'] = str(e)

        try:
            results['project'] = self._saveProjectFile(project_filename)
            if not results['project']:
                errors['project'] = (
                    "Failed to save project file "
                    "(GuiManager not accessible or no data available)")
        except Exception as e:
            logger.error(f"Error saving project file: {e}", exc_info=True)
            errors['project'] = str(e)

        success_count = sum(1 for v in results.values() if v)
        paths = {'json': json_filename, 'pdf': pdf_filename, 'project': project_filename}
        labels = {'json': 'JSON', 'pdf': 'PDF', 'project': 'Project'}
        if success_count == 3:
            msg = "All files exported successfully:\n\n" + "\n".join(
                f"• {labels[k]}: {paths[k]}" for k in paths)
            QtWidgets.QMessageBox.information(self, "Export Successful", msg)
            self.close()
        elif success_count > 0:
            lines = []
            for key in paths:
                if results[key]:
                    lines.append(f"✓ {labels[key]}: {paths[key]}")
                else:
                    lines.append(f"✗ {labels[key]}: {errors[key] or 'Failed'}")
            QtWidgets.QMessageBox.warning(
                self, "Partial Export Success",
                f"Export completed with {success_count} of 3 files saved:\n\n"
                + "\n".join(lines))
        else:
            QtWidgets.QMessageBox.critical(
                self, "Export Failed",
                "Failed to export all files:\n\n"
                + "\n".join(f"• {labels[k]}: {errors[k] or 'Failed'}" for k in paths)
                + "\n\nPlease check the logs for details.")

    def _saveProjectFile(self, filepath: str) -> bool:
        """Save current session project to filepath without a file dialog."""
        try:
            parent_window = self.parent()
            if parent_window is None:
                logger.warning("Cannot save project file: dialog has no parent window")
                return False
            gui_manager = (getattr(parent_window, 'guiManager', None)
                           or getattr(parent_window, 'gui_manager', None))
            if gui_manager is None:
                logger.warning(
                    "Cannot save project file: GuiManager not accessible from parent")
                return False
            if not getattr(gui_manager, 'filesWidget', None):
                logger.warning("Cannot save project file: filesWidget not available")
                return False

            all_data = gui_manager.filesWidget.getSerializedData()
            final_data = {id_: {'fit_data': data} for id_, data in all_data.items()}
            analysis = {}
            for _name, per in getattr(gui_manager, 'loadedPerspectives', {}).items():
                if getattr(per, 'isSerializable', lambda: False)():
                    perspective_data = per.serializeAll()
                    for key, value in perspective_data.items():
                        if key in final_data:
                            final_data[key].update(value)
                        elif 'cs_tab' in key:
                            final_data[key] = value
                    analysis.update(perspective_data)

            grid = getattr(gui_manager, 'grid_window', None)
            final_data['batch_grid'] = getattr(grid, 'data_dict', {}) if grid else {}
            final_data['is_batch'] = analysis.get('is_batch', 'False')
            current = getattr(gui_manager, '_current_perspective', None)
            final_data['visible_perspective'] = current.name if current else ''

            import sas.qtgui.Utilities.GuiUtils as GuiUtils
            with open(filepath, 'w') as outfile:
                GuiUtils.saveData(outfile, final_data)
            logger.info(f"Project file saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving project file: {e}", exc_info=True)
            return False

    def onGeneratePDF(self):
        export_data = self.collectFromUI()
        filename = self._choose_save_path(
            'Save PDF Report', 'sasbdb_report.pdf', 'PDF file (*.pdf)')
        if not filename:
            return
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        try:
            self._generatePDFReport(export_data, filename)
            QtWidgets.QMessageBox.information(
                self, "PDF Generated",
                f"PDF report generated successfully:\n{filename}")
        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self, "PDF Generation Failed",
                f"Failed to generate PDF report:\n{str(e)}")

    def _addCustomStyles(self, report: ReportBase):
        with report._html_doc.head:
            tags.style(raw(_PDF_CSS))

    def _addStyledTable(self, report: ReportBase, data: dict,
                        titles: tuple = ("Field", "Value")):
        with report._html_doc.getElementById("model-parameters"):
            with tags.table(cls="sasbdb-table"):
                with tags.tr():
                    tags.th(titles[0], cls="sasbdb-th")
                    tags.th(titles[1], cls="sasbdb-th")
                for key in sorted(data.keys()):
                    with tags.tr():
                        tags.td(key, cls="sasbdb-field")
                        tags.td(str(data[key]), cls="sasbdb-value")

    def _addSectionHeader(self, report: ReportBase, title: str):
        with report._html_doc.getElementById("model-parameters"):
            tags.p("", cls="sasbdb-section-spacer")
            tags.h3(title, cls="sasbdb-section")
            tags.hr(cls="sasbdb-section-rule")

    def _pdf_section(self, report: ReportBase, title: str, items: list) -> None:
        """Add a PDF section from (label, value) pairs; skip empty values."""
        data = {label: value for label, value in items if value not in (None, "", False)}
        if data:
            self._addSectionHeader(report, title)
            self._addStyledTable(report, data)

    def _generatePDFReport(self, export_data: SASBDBExportData, filename: str):
        report = ReportBase("SASBDB Export Report")
        self._addCustomStyles(report)

        if export_data.project:
            p = export_data.project
            self._pdf_section(report, "Project Information", [
                ("Published", "Yes" if p.published else "No"),
                ("PubMed PMID", p.pubmed_pmid),
                ("DOI", p.doi),
                ("Project Title", p.project_title),
            ])

        if export_data.samples:
            s = export_data.samples[0]
            self._pdf_section(report, "Sample/Data Information", [
                ("Sample Title", s.sample_title),
                ("Curve Type", s.curve_type),
                ("Angular Units", s.angular_units),
                ("Intensity Units", s.intensity_units),
                ("Experimental MW",
                 f"{s.experimental_molecular_weight} kDa"
                 if s.experimental_molecular_weight else None),
                ("Experiment Date", s.experiment_date),
                ("Beamline/Instrument", s.beamline_instrument),
                ("Wavelength", f"{s.wavelength} nm" if s.wavelength else None),
                ("Sample-Detector Distance",
                 f"{s.sample_detector_distance} m"
                 if s.sample_detector_distance else None),
                ("Cell Temperature",
                 f"{s.cell_temperature} °C" if s.cell_temperature else None),
                ("Concentration",
                 f"{s.concentration} mg/ml" if s.concentration else None),
            ])

            if s.molecule:
                m = s.molecule
                seq = m.fasta_sequence
                if seq and len(seq) > 100:
                    seq = seq[:100] + "..."
                self._pdf_section(report, "Molecule Information", [
                    ("Type", m.type),
                    ("Long Name", m.long_name),
                    ("Short Name", m.short_name),
                    ("UniProt Accession", m.uniprot_accession),
                    ("FASTA Sequence", seq),
                    ("Monomer MW",
                     f"{m.monomer_mw_kda} kDa" if m.monomer_mw_kda else None),
                    ("Number of Molecules",
                     str(m.number_of_molecules) if m.number_of_molecules else None),
                    ("Oligomeric State", m.oligomeric_state),
                    ("Total MW", f"{m.total_mw_kda} kDa" if m.total_mw_kda else None),
                ])

            if s.buffer:
                b = s.buffer
                self._pdf_section(report, "Buffer Information", [
                    ("Description", b.description),
                    ("pH", str(b.ph) if b.ph else None),
                    ("Comment", b.comment),
                ])

            if s.guinier:
                g = s.guinier
                self._pdf_section(report, "Guinier Analysis", [
                    ("Q Start", str(g.range_start) if g.range_start is not None else None),
                    ("Q End", str(g.range_end) if g.range_end is not None else None),
                    ("Start point",
                     str(g.start_point) if g.start_point is not None else None),
                    ("End point",
                     str(g.end_point) if g.end_point is not None else None),
                    ("Rg", f"{g.rg} nm" if g.rg is not None else None),
                    ("Rg Error", f"{g.rg_error} nm" if g.rg_error is not None else None),
                    ("I(0)", str(g.i0) if g.i0 is not None else None),
                ])

            for fit_i, fit in enumerate(s.fits):
                title = ("Fit Information" if fit_i == 0
                         else f"Fit Information ({fit_i + 1})")
                self._pdf_section(report, title, [
                    ("Software", fit.software),
                    ("Software Version", fit.software_version),
                    ("Chi-squared",
                     f"{fit.chi_squared:.4f}" if fit.chi_squared is not None else None),
                    ("CorMap p-value",
                     f"{fit.cormap_pvalue:.4f}"
                     if fit.cormap_pvalue is not None else None),
                    ("Angular Units", fit.angular_units),
                    ("Description", fit.description),
                ])
                for model_i, model in enumerate(fit.models):
                    mtitle = ("Model Information" if model_i == 0
                              else f"Model Information ({model_i + 1})")
                    self._pdf_section(report, mtitle, [
                        ("Software/DB", model.software_or_db),
                        ("Software Version", model.software_version),
                        ("Symmetry", model.symmetry),
                        ("Model Data", model.model_data),
                        ("Comment", model.comment),
                    ])

        if export_data.instruments:
            inst = export_data.instruments[0]
            self._pdf_section(report, "Instrument Information", [
                ("Source Type", inst.source_type),
                ("Beamline/Instrument", inst.beamline_name),
                ("Synchrotron/Facility", inst.synchrotron_name),
                ("Detector Manufacturer/Model", inst.detector_manufacturer),
                ("Detector Type", inst.detector_type),
                ("Detector Resolution", inst.detector_resolution),
                ("City", inst.city),
                ("Country", inst.country),
            ])

        self._add_plots_to_report(report)
        report.save_pdf(filename)

    def _add_plots_to_report(self, report: ReportBase) -> None:
        plot_fig = self._getPlotFigureWithModel()
        if plot_fig:
            try:
                report.add_plot(
                    plot_fig, image_type="png", figure_title="Data and Model Fit")
            except Exception as e:
                logger.warning(f"Could not add plot to PDF: {e}")
        else:
            try:
                plot_fig = self._getPlotFigure()
                if plot_fig:
                    report.add_plot(
                        plot_fig, image_type="png", figure_title="Data Plot")
            except Exception as e:
                logger.warning(f"Could not add plot to PDF: {e}")

        residual_fig = self._getResidualPlotFigure()
        if residual_fig:
            try:
                report.add_plot(
                    residual_fig, image_type="png", figure_title="Residuals")
            except Exception as e:
                logger.warning(f"Could not add residual plot to PDF: {e}")

    def _getPlotFigureWithModel(self):
        try:
            fitting_widget = self._current_fitting_widget()
            if fitting_widget is None:
                return None
            from sas.qtgui.Perspectives.Fitting import FittingUtilities
            from sas.qtgui.Perspectives.Fitting.ReportPageLogic import ReportPageLogic

            index = None
            if getattr(fitting_widget, 'all_data', None):
                index = fitting_widget.all_data[fitting_widget.data_index]
            elif hasattr(fitting_widget, 'theory_item'):
                index = fitting_widget.theory_item
            if index is None or fitting_widget.logic.kernel_module is None:
                return None

            params = FittingUtilities.getStandardParam(fitting_widget._model_model)
            poly_params = magnet_params = []
            if (getattr(fitting_widget, 'chkPolydispersity', None)
                    and fitting_widget.chkPolydispersity.isChecked()
                    and fitting_widget.polydispersity_widget.poly_model.rowCount() > 0):
                poly_params = FittingUtilities.getStandardParam(
                    fitting_widget.polydispersity_widget.poly_model)
            if (getattr(fitting_widget, 'chkMagnetism', None)
                    and fitting_widget.chkMagnetism.isChecked()
                    and hasattr(fitting_widget, 'canHaveMagnetism')
                    and fitting_widget.canHaveMagnetism()
                    and fitting_widget.magnetism_widget._magnet_model.rowCount() > 0):
                magnet_params = FittingUtilities.getStandardParam(
                    fitting_widget.magnetism_widget._magnet_model)

            images = ReportPageLogic(
                fitting_widget,
                kernel_module=fitting_widget.logic.kernel_module,
                data=fitting_widget.data,
                index=index,
                params=params + poly_params + magnet_params,
            ).getImages()
            return images[0] if images else None
        except Exception as e:
            logger.warning(f"Error getting plot figure with model: {e}")
            return None

    def _getPlotFigure(self):
        try:
            if not self.export_data.samples:
                return None
            sample = self.export_data.samples[0]
            if not (sample.experimental_curve
                    and os.path.exists(sample.experimental_curve)):
                return None
            import matplotlib.pyplot as plt
            from sasdata.dataloader.loader import Loader

            data_list = Loader().load(sample.experimental_curve)
            if not data_list:
                return None
            data = data_list[0]
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.errorbar(data.x, data.y, yerr=data.dy, fmt='o', markersize=3, capsize=2)
            ax.set_xlabel(f"Q ({sample.angular_units or '1/nm'})")
            ax.set_ylabel(f"I ({sample.intensity_units or 'arbitrary'})")
            ax.set_title(sample.sample_title or "SAS Data")
            ax.set_yscale('log')
            ax.set_xscale('log')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            return fig
        except Exception as e:
            logger.warning(f"Error getting plot figure: {e}")
            return None

    def _getResidualPlotFigure(self):
        try:
            fitting_widget = self._current_fitting_widget()
            if fitting_widget is None or fitting_widget.logic.kernel_module is None:
                return None
            import sas.qtgui.Plotting.PlotHelper as PlotHelper

            modelname = fitting_widget.logic.kernel_module.name
            data = getattr(fitting_widget, 'data', None)
            if not modelname or not data:
                return None
            data_id = data.id
            data_name = getattr(data, 'name', None)
            expected_residual_id = f"Residual res{data_id}"
            expected_original_id = f"res{data_id}"

            best_score, best_figure = 0, None
            for name in PlotHelper.currentPlotIds():
                try:
                    plotter = PlotHelper.plotById(name)
                    if not plotter or not plotter.data:
                        continue
                    for data_item in plotter.data:
                        score = self._score_residual_plot_match(
                            data_item, data_id=data_id,
                            expected_residual_id=expected_residual_id,
                            expected_original_id=expected_original_id,
                            modelname=modelname, data_name=data_name)
                        if score > best_score:
                            best_score, best_figure = score, plotter.figure
                except Exception as e:
                    logger.warning(f"Error checking plot {name}: {e}")
            return best_figure
        except Exception as e:
            logger.warning(f"Error getting residual plot figure: {e}")
            return None

    @staticmethod
    def _score_residual_plot_match(
        data_item, *, data_id, expected_residual_id, expected_original_id,
        modelname, data_name,
    ) -> int:
        from sas.qtgui.Plotting.PlotterData import DataRole

        if getattr(data_item, 'plot_role', None) != DataRole.ROLE_RESIDUAL:
            return 0
        residual_id = getattr(data_item, 'id', '')
        residual_name = getattr(data_item, 'name', '')
        if residual_id == expected_residual_id:
            return 100
        if residual_id == expected_original_id:
            return 90
        if str(data_id) in residual_id:
            return 80
        if residual_name and "Residual" in residual_name and (
                modelname in residual_name
                or (data_name and data_name in residual_name)):
            return 70
        return 10
