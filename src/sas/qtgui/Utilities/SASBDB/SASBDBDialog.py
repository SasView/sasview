"""
SASBDB Export Dialog

This dialog allows users to review and edit SASBDB export data before exporting.
"""
import logging
import math
import os
import sys

from dominate import tags
from dominate.util import raw
from PySide6 import QtCore, QtWidgets

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary
from sas.qtgui.Utilities.Reports.reports import ReportBase
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
from sas.qtgui.Utilities.SASBDB.sasbdb_exporter import SASBDBExporter
from sas.qtgui.Utilities.SASBDB.UI.SASBDBDialogUI import Ui_SASBDBDialogUI

logger = logging.getLogger(__name__)

# Guinier Q / Rg / I(0) fields locked after a successful Estimate (indices stay editable).
_GUINIER_DERIVED_FIELD_NAMES = (
    "txtGuinierRangeStart",
    "txtGuinierRangeEnd",
    "txtGuinierRg",
    "txtGuinierRgError",
    "txtGuinierI0",
)


class SASBDBDialog(QtWidgets.QDialog, Ui_SASBDBDialogUI):
    """
    Dialog for SASBDB export functionality.
    
    This dialog provides a user interface for reviewing and editing SASBDB export data
    before exporting to JSON, PDF, and project file formats. It collects data from
    the current SasView session (loaded datasets, fit results, metadata) and allows
    users to complete missing information.
    
    The dialog includes multiple tabs for organizing different types of information:
    - Project: Publication status and identification
    - Sample: Experimental sample and data parameters
    - Molecule: Biological molecule details
    - Buffer: Buffer composition and conditions
    - Guinier: Guinier analysis results (if available)
    - Fit: Fit results and model information
    - Instrument: Instrument and facility details
    
    :param export_data: Pre-collected SASBDB export data (optional). If not provided,
                        an empty SASBDBExportData object will be created.
    :param parent: Parent widget for the dialog
    :param guinier_source_data: Optional 1D dataset for optional FreeSAS Guinier estimate
    """

    def __init__(
        self,
        export_data: SASBDBExportData | None = None,
        parent: QtCore.QObject | None = None,
        guinier_source_data=None,
    ):
        """
        Initialize the SASBDB dialog

        :param export_data: Pre-collected SASBDB export data (optional)
        :param parent: Parent widget
        :param guinier_source_data: 1D data used when the user runs FreeSAS from the Guinier tab
        """
        super().__init__(parent)
        self.setupUi(self)

        self._guinier_source_data = guinier_source_data
        self._guinier_plot_a: float | None = None
        self._guinier_plot_b: float | None = None
        self._guinier_suppress_range_signals: bool = False
        self._guinier_plot_panel = None
        if hasattr(self, "widgetGuinierPlot"):
            from sas.qtgui.Utilities.SASBDB.guinier_plot_panel import GuinierPlotPanel

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

        # Store export data
        self.export_data = export_data or SASBDBExportData()

        # Get save location from object library
        self.save_location = ObjectLibrary.getObject('SASBDBDialog_directory')

        # Connect signals
        self.cmdExport.clicked.connect(self.onExport)
        self.cmdGeneratePDF.clicked.connect(self.onGeneratePDF)
        self.cmdHelp.clicked.connect(self.onHelp)
        self.cmdClose.clicked.connect(self.close)
        self.chkPublished.toggled.connect(self.onPublishedToggled)
        if hasattr(self, 'btnGuinierEstimateFreeSAS'):
            self.btnGuinierEstimateFreeSAS.clicked.connect(
                self._on_guinier_estimate_clicked)
            # Not a dialog default: stay neutral until pressed; avoid default-button
            # chrome (autoDefault) like the footer Export/Close actions.
            est_btn = self.btnGuinierEstimateFreeSAS
            est_btn.setAutoDefault(False)
            est_btn.setDefault(False)
            if sys.platform == "darwin":
                est_btn.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        if hasattr(self, "btnGuinierReset"):
            self.btnGuinierReset.clicked.connect(self._on_guinier_reset_clicked)
            reset_btn = self.btnGuinierReset
            reset_btn.setAutoDefault(False)
            reset_btn.setDefault(False)
            if sys.platform == "darwin":
                reset_btn.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        if hasattr(self, "txtGuinierStartPoint"):
            self.txtGuinierStartPoint.editingFinished.connect(
                self._on_guinier_indices_editing_finished
            )
            self.txtGuinierEndPoint.editingFinished.connect(
                self._on_guinier_indices_editing_finished
            )
        if hasattr(self, "txtGuinierRangeStart"):
            self.txtGuinierRangeStart.editingFinished.connect(
                self._on_guinier_q_range_editing_finished
            )
            self.txtGuinierRangeEnd.editingFinished.connect(
                self._on_guinier_q_range_editing_finished
            )

        # Populate UI with data
        self.populateFromData()
        self._set_guinier_derived_fields_read_only(False)

        # Set up initial state
        self.onPublishedToggled(self.chkPublished.isChecked())

        self._refresh_guinier_plot()

    def _set_guinier_derived_fields_read_only(self, readonly: bool) -> None:
        """
        Lock or unlock Q start/end, Rg, Rg error, and I(0).

        Start and end point indices stay editable so the user can re-range and
        use Estimate again; Reset clears everything and unlocks.
        """
        for name in _GUINIER_DERIVED_FIELD_NAMES:
            if hasattr(self, name):
                getattr(self, name).setReadOnly(readonly)

    def _clear_guinier_fields(self) -> None:
        """Clear all Guinier line edits."""
        self.txtGuinierRg.clear()
        self.txtGuinierRgError.clear()
        self.txtGuinierI0.clear()
        self.txtGuinierRangeStart.clear()
        self.txtGuinierRangeEnd.clear()
        self.txtGuinierStartPoint.clear()
        self.txtGuinierEndPoint.clear()
        self._guinier_plot_a = None
        self._guinier_plot_b = None

    def _on_guinier_reset_clicked(self) -> None:
        """Clear all Guinier line edits and reset the plot panel."""
        self._clear_guinier_fields()
        self._set_guinier_derived_fields_read_only(False)
        self._refresh_guinier_plot()

    def _sync_guinier_plot_ab_from_rg_i0(self, guinier: SASBDBGuinier) -> None:
        """Set ln(I)=a+b q² line parameters from Rg (nm) and I(0) for plotting."""
        from sas.qtgui.Utilities.SASBDB.sasbdb_data_collector import SASBDBDataCollector

        if guinier.rg is None or guinier.i0 is None or guinier.i0 <= 0:
            self._guinier_plot_a = None
            self._guinier_plot_b = None
            return
        coll = SASBDBDataCollector()
        scale = coll._guinier_native_q_to_nm_scale(self._guinier_source_data)
        rg_native = float(guinier.rg) * scale
        self._guinier_plot_b = -(rg_native**2) / 3.0
        self._guinier_plot_a = math.log(float(guinier.i0))

    def _apply_guinier_to_fields(
        self,
        guinier: SASBDBGuinier,
        clear_first: bool = False,
        fit_info: dict | None = None,
    ) -> None:
        """Fill Guinier tab fields from a SASBDBGuinier object."""
        self._guinier_suppress_range_signals = True
        try:
            if clear_first:
                self._clear_guinier_fields()
            if guinier.rg is not None:
                self.txtGuinierRg.setText(f"{guinier.rg:.2g}")
            if guinier.rg_error is not None:
                self.txtGuinierRgError.setText(f"{guinier.rg_error:.2g}")
            if guinier.i0 is not None:
                self.txtGuinierI0.setText(f"{guinier.i0:.2g}")
            if guinier.range_start is not None:
                self.txtGuinierRangeStart.setText(str(guinier.range_start))
            if guinier.range_end is not None:
                self.txtGuinierRangeEnd.setText(str(guinier.range_end))
            if guinier.start_point is not None:
                self.txtGuinierStartPoint.setText(str(guinier.start_point))
            if guinier.end_point is not None:
                self.txtGuinierEndPoint.setText(str(guinier.end_point))

            if fit_info is not None:
                self._guinier_plot_a = fit_info.get("a")
                self._guinier_plot_b = fit_info.get("b")
            elif guinier.rg is not None and guinier.i0 is not None and guinier.i0 > 0:
                self._sync_guinier_plot_ab_from_rg_i0(guinier)
            else:
                self._guinier_plot_a = None
                self._guinier_plot_b = None
        finally:
            self._guinier_suppress_range_signals = False
        self._refresh_guinier_plot()

    def _refresh_guinier_plot(self) -> None:
        """Redraw the Guinier ln(I) vs q² panel."""
        if self._guinier_plot_panel is None:
            return
        import numpy as np

        data = self._guinier_source_data
        q = (
            np.asarray(data.x, dtype=float)
            if data is not None and hasattr(data, "x")
            else None
        )
        iy = (
            np.asarray(data.y, dtype=float)
            if data is not None and hasattr(data, "y")
            else None
        )
        q_start = q_end = None
        rs = self.txtGuinierRangeStart.text().strip()
        re = self.txtGuinierRangeEnd.text().strip()
        if rs and re:
            try:
                q_start = float(rs)
                q_end = float(re)
            except ValueError:
                pass
        self._guinier_plot_panel.update_plot(
            q,
            iy,
            q_start,
            q_end,
            self._guinier_plot_a,
            self._guinier_plot_b,
        )

    def _guinier_any_field_nonempty(self) -> bool:
        """True if any Guinier line edit has text (export validation)."""
        for name in (
            "txtGuinierRg",
            "txtGuinierRgError",
            "txtGuinierI0",
            "txtGuinierRangeStart",
            "txtGuinierRangeEnd",
            "txtGuinierStartPoint",
            "txtGuinierEndPoint",
        ):
            if hasattr(self, name) and getattr(self, name).text().strip():
                return True
        return False

    def _q_lo_q_hi_from_guinier_indices(
        self, i_start: int, i_end: int
    ) -> tuple[float, float] | None:
        """
        Map inclusive data indices to q-range endpoints (uses sorted index order).

        :return: ``(q_lo, q_hi)`` at ``x[min(i)]`` and ``x[max(i)]``, or ``None``
        """
        data = self._guinier_source_data
        if data is None or not hasattr(data, "x"):
            return None
        import numpy as np

        x = np.asarray(data.x, dtype=float)
        n = len(x)
        if n == 0:
            return None
        ia = int(min(i_start, i_end))
        ib = int(max(i_start, i_end))
        if ia < 0 or ib >= n:
            return None
        return float(x[ia]), float(x[ib])

    def _on_guinier_indices_editing_finished(self) -> None:
        """Refit when both start and end point indices are set."""
        if self._guinier_suppress_range_signals:
            return
        sp = self.txtGuinierStartPoint.text().strip()
        ep = self.txtGuinierEndPoint.text().strip()
        if not sp or not ep:
            self._refresh_guinier_plot()
            return
        try:
            i_s = int(sp)
            i_e = int(ep)
        except ValueError:
            self._refresh_guinier_plot()
            return
        if self._guinier_source_data is None:
            self._refresh_guinier_plot()
            return
        qr = self._q_lo_q_hi_from_guinier_indices(i_s, i_e)
        if qr is None:
            self._refresh_guinier_plot()
            return
        q_lo, q_hi = qr
        if q_lo >= q_hi:
            self._refresh_guinier_plot()
            return

        from sas.qtgui.Utilities.SASBDB.sasbdb_data_collector import SASBDBDataCollector

        collector = SASBDBDataCollector()
        guinier, fit_info = collector.collect_guinier_from_q_range(
            self._guinier_source_data, q_lo, q_hi
        )
        if guinier is None:
            self._refresh_guinier_plot()
            return
        self._apply_guinier_to_fields(guinier, clear_first=False, fit_info=fit_info)

    def _on_guinier_q_range_editing_finished(self) -> None:
        """Refit ln(I) vs q² when both Q start and Q end are set."""
        if self._guinier_suppress_range_signals:
            return
        rs = self.txtGuinierRangeStart.text().strip()
        re = self.txtGuinierRangeEnd.text().strip()
        if not rs or not re:
            self._refresh_guinier_plot()
            return
        try:
            q_lo = float(rs)
            q_hi = float(re)
        except ValueError:
            self._refresh_guinier_plot()
            return
        if q_lo >= q_hi:
            self._refresh_guinier_plot()
            return
        if self._guinier_source_data is None:
            self._refresh_guinier_plot()
            return

        from sas.qtgui.Utilities.SASBDB.sasbdb_data_collector import SASBDBDataCollector

        collector = SASBDBDataCollector()
        guinier, fit_info = collector.collect_guinier_from_q_range(
            self._guinier_source_data, q_lo, q_hi
        )
        if guinier is None:
            self._refresh_guinier_plot()
            return
        self._apply_guinier_to_fields(guinier, clear_first=False, fit_info=fit_info)

    def _on_guinier_estimate_clicked(self) -> None:
        """Estimate: FreeSAS when range empty; fit by indices or by Q when set."""
        self._run_free_sas_guinier_estimate()

    def _run_free_sas_guinier_estimate(self) -> None:
        """FreeSAS auto_guinier, or WLS fit by indices / by Q range."""
        from sas.qtgui.Utilities.SASBDB.sasbdb_data_collector import SASBDBDataCollector

        sp = self.txtGuinierStartPoint.text().strip()
        ep = self.txtGuinierEndPoint.text().strip()
        rs = self.txtGuinierRangeStart.text().strip()
        re = self.txtGuinierRangeEnd.text().strip()

        if sp and ep:
            if self._guinier_source_data is None:
                QtWidgets.QMessageBox.information(
                    self,
                    "Guinier estimate",
                    "No 1D scattering data is available for a fit by indices.\n\n"
                    "Load 1D data or clear start/end point to use FreeSAS.",
                )
                return
            try:
                i_s = int(sp)
                i_e = int(ep)
            except ValueError:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Guinier estimate",
                    "Start and end point must be integers.",
                )
                return
            qr = self._q_lo_q_hi_from_guinier_indices(i_s, i_e)
            if qr is None:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Guinier estimate",
                    "Indices are out of range for the current 1D dataset.",
                )
                return
            q_lo, q_hi = qr
            if q_lo >= q_hi:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Guinier estimate",
                    "Start and end point must span at least two distinct q values.",
                )
                return

            collector = SASBDBDataCollector()
            guinier, fit_info = collector.collect_guinier_from_q_range(
                self._guinier_source_data, q_lo, q_hi
            )
            if guinier is None:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Guinier estimate",
                    "Could not fit ln(I) vs q² for the selected indices.\n\n"
                    "Need at least two points with I > 0 and a negative slope.",
                )
                return
            self._apply_guinier_to_fields(guinier, clear_first=False, fit_info=fit_info)
            self._set_guinier_derived_fields_read_only(True)
            return

        if sp or ep:
            QtWidgets.QMessageBox.information(
                self,
                "Guinier estimate",
                "Enter both start and end point for a fit by indices, or clear "
                "both to use FreeSAS or Q start / Q end.",
            )
            return

        if rs and re:
            if self._guinier_source_data is None:
                QtWidgets.QMessageBox.information(
                    self,
                    "Guinier estimate",
                    "No 1D scattering data is available for a range fit.\n\n"
                    "Load 1D data or clear Q start and Q end to use FreeSAS "
                    "auto_guinier.",
                )
                return
            try:
                q_lo = float(rs)
                q_hi = float(re)
            except ValueError:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Guinier estimate",
                    "Q start and Q end must be valid numbers.",
                )
                return
            if q_lo >= q_hi:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Guinier estimate",
                    "Q start must be less than Q end.",
                )
                return

            collector = SASBDBDataCollector()
            guinier, fit_info = collector.collect_guinier_from_q_range(
                self._guinier_source_data, q_lo, q_hi
            )
            if guinier is None:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Guinier estimate",
                    "Could not fit ln(I) vs q² in the selected range.\n\n"
                    "Need at least two points with I > 0 and a negative slope "
                    "(check q range and data).",
                )
                return
            self._apply_guinier_to_fields(guinier, clear_first=False, fit_info=fit_info)
            self._set_guinier_derived_fields_read_only(True)
            return

        if rs or re:
            QtWidgets.QMessageBox.information(
                self,
                "Guinier estimate",
                "Enter both Q start and Q end to fit by q, or clear both for "
                "FreeSAS auto_guinier.",
            )
            return

        if self._guinier_source_data is None:
            QtWidgets.QMessageBox.information(
                self,
                "Guinier estimate",
                "No 1D scattering data is available for FreeSAS.\n\n"
                "Open SASBDB from the Fitting perspective with 1D data loaded, "
                "or load 1D data in the Data Explorer first.",
            )
            return

        collector = SASBDBDataCollector()
        guinier = collector.collect_guinier_from_freesas(self._guinier_source_data)
        if guinier is None:
            QtWidgets.QMessageBox.warning(
                self,
                "Guinier estimate",
                "FreeSAS auto_guinier did not return a result.\n\n"
                "Ensure the freesas package is installed and the curve is suitable "
                "for Guinier analysis.",
            )
            return

        self._apply_guinier_to_fields(guinier, clear_first=True, fit_info=None)
        self._set_guinier_derived_fields_read_only(True)

    def populateFromData(self):
        """
        Populate UI fields from export_data.
        
        This method reads the export_data object and fills in all UI form fields
        with the available data. It handles all tabs including Project, Sample,
        Molecule, Buffer, Guinier, Fit, and Instrument information.
        
        If export_data is empty or fields are missing, the corresponding UI fields
        will remain empty for manual entry.
        """
        # Project tab
        if self.export_data.project:
            project = self.export_data.project
            self.chkPublished.setChecked(project.published)
            if project.pubmed_pmid:
                self.txtPubmedPMID.setText(project.pubmed_pmid)
            if project.doi:
                self.txtDOI.setText(project.doi)
            if project.project_title:
                self.txtProjectTitle.setText(project.project_title)

        # Sample tab (use first sample if available)
        if self.export_data.samples:
            sample = self.export_data.samples[0]
            if sample.sample_title:
                self.txtSampleTitle.setText(sample.sample_title)
            if sample.curve_type:
                index = self.cmbCurveType.findText(sample.curve_type)
                if index >= 0:
                    self.cmbCurveType.setCurrentIndex(index)
            if sample.angular_units:
                index = self.cmbAngularUnits.findText(sample.angular_units)
                if index >= 0:
                    self.cmbAngularUnits.setCurrentIndex(index)
            if sample.intensity_units:
                index = self.cmbIntensityUnits.findText(sample.intensity_units)
                if index >= 0:
                    self.cmbIntensityUnits.setCurrentIndex(index)
            if sample.experimental_molecular_weight:
                self.txtExpMW.setText(str(sample.experimental_molecular_weight))
            if sample.experiment_date:
                self.txtExperimentDate.setText(sample.experiment_date)
            if sample.beamline_instrument:
                self.txtBeamline.setText(sample.beamline_instrument)
            if sample.wavelength:
                self.txtWavelength.setText(str(sample.wavelength))
            if sample.sample_detector_distance:
                self.txtDistance.setText(str(sample.sample_detector_distance))
            if sample.cell_temperature:
                self.txtTemperature.setText(str(sample.cell_temperature))
            if sample.concentration:
                self.txtConcentration.setText(str(sample.concentration))

            # Molecule tab
            if sample.molecule:
                molecule = sample.molecule
                if molecule.type:
                    index = self.cmbMoleculeType.findText(molecule.type)
                    if index >= 0:
                        self.cmbMoleculeType.setCurrentIndex(index)
                if molecule.long_name:
                    self.txtLongName.setText(molecule.long_name)
                if molecule.short_name:
                    self.txtShortName.setText(molecule.short_name)
                if molecule.fasta_sequence:
                    self.txtFastaSequence.setPlainText(molecule.fasta_sequence)
                if molecule.monomer_mw_kda:
                    self.txtMonomerMW.setText(str(molecule.monomer_mw_kda))
                if molecule.oligomeric_state:
                    index = self.cmbOligomericState.findText(molecule.oligomeric_state)
                    if index >= 0:
                        self.cmbOligomericState.setCurrentIndex(index)
                if molecule.number_of_molecules:
                    self.spnNumberOfMolecules.setValue(molecule.number_of_molecules)
                if molecule.uniprot_accession:
                    self.txtUniProt.setText(molecule.uniprot_accession)
                if molecule.source_organism:
                    self.txtSourceOrganism.setText(molecule.source_organism)

            # Buffer tab
            if sample.buffer:
                buffer = sample.buffer
                if buffer.description:
                    self.txtBufferDescription.setPlainText(buffer.description)
                if buffer.ph:
                    self.txtBufferPH.setText(str(buffer.ph))
                if buffer.comment:
                    self.txtBufferComment.setPlainText(buffer.comment)

            # Guinier tab (manual entry by default; optional FreeSAS via Estimate button)
            if sample.guinier:
                self._apply_guinier_to_fields(sample.guinier, clear_first=False)

            # Fit tab (use first fit if available)
            if sample.fits:
                fit = sample.fits[0]
                if fit.software:
                    self.txtFitSoftware.setText(fit.software)
                if fit.software_version:
                    self.txtFitVersion.setText(fit.software_version)
                if fit.chi_squared:
                    # Format chi-squared to 2 decimal places
                    self.txtChiSquared.setText(f"{fit.chi_squared:.2f}")
                if fit.cormap_pvalue:
                    # Format to 2 significant digits
                    self.txtCorMapPValue.setText(f"{fit.cormap_pvalue:.2g}")

                # Model section (use first model if available)
                if fit.models:
                    model = fit.models[0]
                    if model.software_or_db:
                        self.txtModelName.setText(model.software_or_db)

                    # Format parameters if available
                    # Parameters are stored as a formatted string in log
                    if model.log:
                        self.txtModelParameters.setPlainText(model.log)

        # Instrument tab (use first instrument if available)
        if self.export_data.instruments:
            instrument = self.export_data.instruments[0]
            if instrument.source_type:
                index = self.cmbSourceType.findText(instrument.source_type)
                if index >= 0:
                    self.cmbSourceType.setCurrentIndex(index)
            if instrument.beamline_name:
                self.txtBeamlineName.setText(instrument.beamline_name)
            if instrument.synchrotron_name:
                self.txtSynchrotronName.setText(instrument.synchrotron_name)
            if instrument.detector_manufacturer:
                self.txtDetectorManufacturer.setText(instrument.detector_manufacturer)
            if instrument.detector_type:
                self.txtDetectorType.setText(instrument.detector_type)
            if instrument.detector_resolution:
                self.txtDetectorResolution.setText(instrument.detector_resolution)
            if instrument.city:
                self.txtCity.setText(instrument.city)
            if instrument.country:
                self.txtCountry.setText(instrument.country)

    def collectFromUI(self) -> SASBDBExportData:
        """
        Collect data from UI fields and create SASBDBExportData.
        
        This method reads all UI form fields and constructs a complete SASBDBExportData
        object containing all the information entered by the user. It handles parsing
        of numeric fields, text fields, and dropdown selections across all tabs.
        
        :return: SASBDBExportData object containing all collected data from the UI
        """
        export_data = SASBDBExportData()

        # Project
        project = SASBDBProject()
        project.published = self.chkPublished.isChecked()
        project.pubmed_pmid = self.txtPubmedPMID.text().strip() or None
        project.doi = self.txtDOI.text().strip() or None
        project.project_title = self.txtProjectTitle.text().strip() or None
        export_data.project = project

        # Sample
        sample = SASBDBSample()
        sample.sample_title = self.txtSampleTitle.text().strip() or None
        sample.curve_type = self.cmbCurveType.currentText() or None
        sample.angular_units = self.cmbAngularUnits.currentText() or None
        sample.intensity_units = self.cmbIntensityUnits.currentText() or None

        # Parse numeric fields
        try:
            mw_text = self.txtExpMW.text().strip()
            if mw_text:
                sample.experimental_molecular_weight = float(mw_text)
        except ValueError:
            pass

        sample.experiment_date = self.txtExperimentDate.text().strip() or None
        sample.beamline_instrument = self.txtBeamline.text().strip() or None

        try:
            wavelength_text = self.txtWavelength.text().strip()
            if wavelength_text:
                sample.wavelength = float(wavelength_text)
        except ValueError:
            pass

        try:
            distance_text = self.txtDistance.text().strip()
            if distance_text:
                sample.sample_detector_distance = float(distance_text)
        except ValueError:
            pass

        try:
            temp_text = self.txtTemperature.text().strip()
            if temp_text:
                sample.cell_temperature = float(temp_text)
        except ValueError:
            pass

        try:
            conc_text = self.txtConcentration.text().strip()
            if conc_text:
                sample.concentration = float(conc_text)
        except ValueError:
            pass

        # Molecule
        molecule = SASBDBMolecule()
        molecule.type = self.cmbMoleculeType.currentText() or None
        molecule.long_name = self.txtLongName.text().strip() or None
        molecule.short_name = self.txtShortName.text().strip() or None
        molecule.fasta_sequence = self.txtFastaSequence.toPlainText().strip() or None

        try:
            monomer_mw_text = self.txtMonomerMW.text().strip()
            if monomer_mw_text:
                molecule.monomer_mw_kda = float(monomer_mw_text)
        except ValueError:
            pass

        molecule.oligomeric_state = self.cmbOligomericState.currentText() or None
        molecule.number_of_molecules = self.spnNumberOfMolecules.value()
        molecule.uniprot_accession = self.txtUniProt.text().strip() or None
        molecule.source_organism = self.txtSourceOrganism.text().strip() or None
        sample.molecule = molecule

        # Buffer
        buffer = SASBDBBuffer()
        buffer.description = self.txtBufferDescription.toPlainText().strip() or None

        try:
            ph_text = self.txtBufferPH.text().strip()
            if ph_text:
                buffer.ph = float(ph_text)
        except ValueError:
            pass

        buffer.comment = self.txtBufferComment.toPlainText().strip() or None
        sample.buffer = buffer

        # Guinier
        guinier = SASBDBGuinier()
        try:
            rg_text = self.txtGuinierRg.text().strip()
            if rg_text:
                guinier.rg = float(rg_text)
        except ValueError:
            pass

        try:
            rg_error_text = self.txtGuinierRgError.text().strip()
            if rg_error_text:
                guinier.rg_error = float(rg_error_text)
        except ValueError:
            pass

        try:
            i0_text = self.txtGuinierI0.text().strip()
            if i0_text:
                guinier.i0 = float(i0_text)
        except ValueError:
            pass

        try:
            range_start_text = self.txtGuinierRangeStart.text().strip()
            if range_start_text:
                guinier.range_start = float(range_start_text)
        except ValueError:
            pass

        try:
            range_end_text = self.txtGuinierRangeEnd.text().strip()
            if range_end_text:
                guinier.range_end = float(range_end_text)
        except ValueError:
            pass

        try:
            start_point_text = self.txtGuinierStartPoint.text().strip()
            if start_point_text:
                guinier.start_point = int(start_point_text)
        except ValueError:
            pass

        try:
            end_point_text = self.txtGuinierEndPoint.text().strip()
            if end_point_text:
                guinier.end_point = int(end_point_text)
        except ValueError:
            pass

        if any([guinier.rg, guinier.i0, guinier.range_start, guinier.range_end,
                guinier.start_point is not None, guinier.end_point is not None]):
            sample.guinier = guinier

        # Fit
        fit = SASBDBFit()
        fit.software = self.txtFitSoftware.text().strip() or None
        fit.software_version = self.txtFitVersion.text().strip() or None

        try:
            chi2_text = self.txtChiSquared.text().strip()
            if chi2_text:
                fit.chi_squared = float(chi2_text)
        except ValueError:
            pass

        try:
            cormap_text = self.txtCorMapPValue.text().strip()
            if cormap_text:
                fit.cormap_pvalue = float(cormap_text)
        except ValueError:
            pass

        # Model section
        model_name = self.txtModelName.text().strip()
        model_parameters = self.txtModelParameters.toPlainText().strip()

        if model_name or model_parameters:
            model = SASBDBModel()
            if model_name:
                model.software_or_db = model_name
            if model_parameters:
                # Store parameters in log field
                model.log = model_parameters
            fit.models.append(model)

        if any([fit.software, fit.chi_squared, fit.models]):
            sample.fits.append(fit)

        export_data.samples.append(sample)

        # Collect instrument data
        instrument = SASBDBInstrument()
        instrument.source_type = self.cmbSourceType.currentText() or None
        instrument.beamline_name = self.txtBeamlineName.text().strip() or None
        instrument.synchrotron_name = self.txtSynchrotronName.text().strip() or None
        instrument.detector_manufacturer = self.txtDetectorManufacturer.text().strip() or None
        instrument.detector_type = self.txtDetectorType.text().strip() or None
        instrument.detector_resolution = self.txtDetectorResolution.text().strip() or None
        instrument.city = self.txtCity.text().strip() or None
        instrument.country = self.txtCountry.text().strip() or None

        if any([instrument.source_type, instrument.beamline_name, instrument.synchrotron_name,
                instrument.detector_manufacturer, instrument.city, instrument.country]):
            export_data.instruments.append(instrument)

        return export_data

    def validateData(self) -> tuple[bool, str]:
        """
        Validate that all required fields are filled.
        
        This method checks all required fields according to SASBDB submission requirements:
        - Project: Either PMID/DOI (if published) or Title (if not published)
        - Sample: Title, Experimental MW, Experiment Date, Beamline/Instrument
        - Molecule: Long Name, FASTA Sequence, Monomer MW
        - Buffer: Description, pH
        
        :return: Tuple of (is_valid, error_message). If is_valid is False, error_message
                 contains a description of which required fields are missing.
        """
        # Project validation
        if self.chkPublished.isChecked():
            if not self.txtPubmedPMID.text().strip() and not self.txtDOI.text().strip():
                return False, "If published, either PubMed PMID or DOI is required"
        else:
            if not self.txtProjectTitle.text().strip():
                return False, "Project Title is required if not published"

        # Sample validation
        if not self.txtSampleTitle.text().strip():
            return False, "Sample Title is required"

        if not self.txtExpMW.text().strip():
            return False, "Experimental Molecular Weight is required"

        if not self.txtExperimentDate.text().strip():
            return False, "Experiment Date is required"

        if not self.txtBeamline.text().strip():
            return False, "Beamline/Instrument is required"

        # Molecule validation
        if not self.txtLongName.text().strip():
            return False, "Molecule Long Name is required"

        if not self.txtFastaSequence.toPlainText().strip():
            return False, "FASTA Sequence is required"

        if not self.txtMonomerMW.text().strip():
            return False, "Monomer MW (kDa) is required"

        # Buffer validation
        if not self.txtBufferDescription.toPlainText().strip():
            return False, "Buffer Description is required"

        if not self.txtBufferPH.text().strip():
            return False, "Buffer pH is required"

        if hasattr(self, "txtGuinierStartPoint") and self._guinier_any_field_nonempty():
            sp = self.txtGuinierStartPoint.text().strip()
            ep = self.txtGuinierEndPoint.text().strip()
            if not sp or not ep:
                return (
                    False,
                    "Guinier: start and end point are required when any Guinier "
                    "field is filled.",
                )
            try:
                i_s = int(sp)
                i_e = int(ep)
            except ValueError:
                return False, "Guinier: start and end point must be integers."
            if i_s < 0 or i_e < 0:
                return False, "Guinier: indices must be non-negative."
            if i_s >= i_e:
                return (
                    False,
                    "Guinier: start point index must be less than end point index.",
                )
            data = self._guinier_source_data
            if data is not None and hasattr(data, "x"):
                import numpy as np

                n = len(np.asarray(data.x))
                if n and (i_s >= n or i_e >= n):
                    return (
                        False,
                        "Guinier: start and end point must be within the 1D data "
                        "length.",
                    )

        return True, ""

    def onPublishedToggled(self, checked: bool):
        """
        Enable/disable published-related fields
        
        :param checked: Whether published checkbox is checked
        """
        self.txtPubmedPMID.setEnabled(checked)
        self.txtDOI.setEnabled(checked)
        self.txtProjectTitle.setEnabled(not checked)

    def onHelp(self):
        """
        Show the SASBDB Export help documentation.
        
        Opens the help window with the SASBDB Export documentation.
        The help file is located at /user/qtgui/Utilities/SASBDB/sasbdb_help.html
        """
        help_url = "/user/qtgui/Utilities/SASBDB/sasbdb_help.html"

        # Try to use parent's showHelp method if available (GuiManager)
        parent_window = self.parent()
        if parent_window is not None:
            if hasattr(parent_window, 'showHelp'):
                parent_window.showHelp(help_url)
                return
            elif hasattr(parent_window, 'guiManager') and hasattr(parent_window.guiManager, 'showHelp'):
                parent_window.guiManager.showHelp(help_url)
                return

        # Fallback to GuiUtils.showHelp
        from sas.qtgui.Utilities.GuiUtils import showHelp
        showHelp(help_url)

    def onExport(self):
        """
        Handle export button click.
        
        This method performs the complete export process:
        1. Validates that all required fields are filled
        2. Collects data from the UI
        3. Prompts user to select a location and filename for the JSON file
        4. Saves three files to the selected directory:
           - JSON file (user-selected filename): Main SASBDB export data
           - PDF file (auto-named): PDF report with all export information
           - Project file (auto-named): SasView project file for the current session
        
        The PDF and project files are automatically named based on the JSON filename.
        For example, if the JSON file is "my_export.json", the other files will be
        "my_export.pdf" and "my_export_project.json".
        
        After export, displays a success/failure message and closes the dialog if
        all files were saved successfully.
        """
        # Validate data
        is_valid, error_msg = self.validateData()
        if not is_valid:
            QtWidgets.QMessageBox.warning(
                self,
                "Validation Error",
                error_msg
            )
            return

        # Collect data from UI
        export_data = self.collectFromUI()

        # Choose save location
        if self.save_location is None:
            location = os.path.expanduser('~')
        else:
            location = self.save_location

        default_name = os.path.join(str(location), 'sasbdb_export.json')

        filename_tuple = QtWidgets.QFileDialog.getSaveFileName(
            self,
            'Export SASBDB Data',
            default_name,
            'JSON file (*.json)',
            ""
        )
        json_filename = filename_tuple[0]
        if not json_filename:
            return

        # Update save location
        self.save_location = os.path.dirname(json_filename)
        ObjectLibrary.addObject('SASBDBDialog_directory', self.save_location)

        # Ensure .json extension
        if not json_filename.endswith('.json'):
            json_filename += '.json'

        # Extract base name (without extension) and directory
        base_name = os.path.splitext(os.path.basename(json_filename))[0]
        directory = os.path.dirname(json_filename)

        # Generate filenames for PDF and project
        pdf_filename = os.path.join(directory, f"{base_name}.pdf")
        project_filename = os.path.join(directory, f"{base_name}_project.json")

        # Track success/failure for each file
        results = {
            'json': False,
            'pdf': False,
            'project': False
        }
        errors = {
            'json': None,
            'pdf': None,
            'project': None
        }

        # 1. Export JSON file
        try:
            exporter = SASBDBExporter(export_data)
            results['json'] = exporter.export_to_json(json_filename)
            if not results['json']:
                errors['json'] = "Failed to export JSON file"
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}", exc_info=True)
            errors['json'] = str(e)

        # 2. Generate PDF file
        try:
            self._generatePDFReport(export_data, pdf_filename)
            results['pdf'] = True
        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            errors['pdf'] = str(e)

        # 3. Save project file
        try:
            results['project'] = self._saveProjectFile(project_filename)
            if not results['project']:
                errors['project'] = "Failed to save project file (GuiManager not accessible or no data available)"
        except Exception as e:
            logger.error(f"Error saving project file: {e}", exc_info=True)
            errors['project'] = str(e)

        # Show results message
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)

        if success_count == total_count:
            # All files saved successfully
            message = "All files exported successfully:\n\n"
            message += f"• JSON: {json_filename}\n"
            message += f"• PDF: {pdf_filename}\n"
            message += f"• Project: {project_filename}"
            QtWidgets.QMessageBox.information(
                self,
                "Export Successful",
                message
            )
            self.close()
        elif success_count > 0:
            # Partial success
            message = f"Export completed with {success_count} of {total_count} files saved:\n\n"
            if results['json']:
                message += f"✓ JSON: {json_filename}\n"
            else:
                message += f"✗ JSON: {errors['json'] or 'Failed'}\n"

            if results['pdf']:
                message += f"✓ PDF: {pdf_filename}\n"
            else:
                message += f"✗ PDF: {errors['pdf'] or 'Failed'}\n"

            if results['project']:
                message += f"✓ Project: {project_filename}\n"
            else:
                message += f"✗ Project: {errors['project'] or 'Failed'}\n"

            QtWidgets.QMessageBox.warning(
                self,
                "Partial Export Success",
                message
            )
        else:
            # All failed
            message = "Failed to export all files:\n\n"
            message += f"• JSON: {errors['json'] or 'Failed'}\n"
            message += f"• PDF: {errors['pdf'] or 'Failed'}\n"
            message += f"• Project: {errors['project'] or 'Failed'}\n\n"
            message += "Please check the logs for details."
            QtWidgets.QMessageBox.critical(
                self,
                "Export Failed",
                message
            )

    def _saveProjectFile(self, filepath: str) -> bool:
        """
        Save SasView project file programmatically without showing file dialog.
        
        This method replicates the functionality of GuiManager.actionSave_Project()
        but saves to a specified filepath without user interaction. It collects
        data from the current SasView session including:
        - All loaded data files from filesWidget
        - All serializable perspectives and their data
        - Current perspective state
        
        :param filepath: Full path where the project file should be saved
        :return: True if the project file was saved successfully, False otherwise.
                 Returns False if GuiManager is not accessible, filesWidget is missing,
                 or if an error occurs during saving.
        This replicates the functionality of GuiManager.actionSave_Project() but
        saves to a specified filepath instead of prompting the user.
        
        :param filepath: Full path where the project file should be saved
        :return: True if successful, False otherwise
        """
        try:
            # Access GuiManager via parent window
            parent_window = self.parent()
            if parent_window is None:
                logger.warning("Cannot save project file: dialog has no parent window")
                return False

            # Try to get guiManager from parent
            gui_manager = None
            if hasattr(parent_window, 'guiManager'):
                gui_manager = parent_window.guiManager
            elif hasattr(parent_window, 'gui_manager'):
                gui_manager = parent_window.gui_manager

            if gui_manager is None:
                logger.warning("Cannot save project file: GuiManager not accessible from parent window")
                return False

            # Get serialized data from filesWidget
            if not hasattr(gui_manager, 'filesWidget') or gui_manager.filesWidget is None:
                logger.warning("Cannot save project file: filesWidget not available")
                return False

            all_data = gui_manager.filesWidget.getSerializedData()
            final_data = {}
            for id, data in all_data.items():
                final_data[id] = {'fit_data': data}

            # Get serialized data from all perspectives
            analysis = {}
            if hasattr(gui_manager, 'loadedPerspectives'):
                for name, per in gui_manager.loadedPerspectives.items():
                    if hasattr(per, 'isSerializable') and per.isSerializable():
                        perspective_data = per.serializeAll()
                        for key, value in perspective_data.items():
                            if key in final_data:
                                final_data[key].update(value)
                            elif 'cs_tab' in key:
                                final_data[key] = value
                        # Merge analysis data
                        analysis.update(perspective_data)

            # Add batch and grid data if available
            if hasattr(gui_manager, 'grid_window') and hasattr(gui_manager.grid_window, 'data_dict'):
                final_data['batch_grid'] = gui_manager.grid_window.data_dict
            else:
                final_data['batch_grid'] = {}

            final_data['is_batch'] = analysis.get('is_batch', 'False')

            # Add visible perspective if available
            if hasattr(gui_manager, '_current_perspective') and gui_manager._current_perspective:
                final_data['visible_perspective'] = gui_manager._current_perspective.name
            else:
                final_data['visible_perspective'] = ''

            # Save using GuiUtils.saveData()
            import sas.qtgui.Utilities.GuiUtils as GuiUtils
            with open(filepath, 'w') as outfile:
                GuiUtils.saveData(outfile, final_data)

            logger.info(f"Project file saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error saving project file: {e}", exc_info=True)
            return False

    def onGeneratePDF(self):
        """
        Handle Generate PDF button click
        """
        # Collect data from UI
        export_data = self.collectFromUI()

        # Choose save location
        if self.save_location is None:
            location = os.path.expanduser('~')
        else:
            location = self.save_location

        default_name = os.path.join(str(location), 'sasbdb_report.pdf')

        filename_tuple = QtWidgets.QFileDialog.getSaveFileName(
            self,
            'Save PDF Report',
            default_name,
            'PDF file (*.pdf)',
            ""
        )
        filename = filename_tuple[0]
        if not filename:
            return

        # Update save location
        self.save_location = os.path.dirname(filename)
        ObjectLibrary.addObject('SASBDBDialog_directory', self.save_location)

        # Ensure .pdf extension
        if not filename.endswith('.pdf'):
            filename += '.pdf'

        # Generate PDF
        try:
            self._generatePDFReport(export_data, filename)
            QtWidgets.QMessageBox.information(
                self,
                "PDF Generated",
                f"PDF report generated successfully:\n{filename}"
            )
        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            QtWidgets.QMessageBox.critical(
                self,
                "PDF Generation Failed",
                f"Failed to generate PDF report:\n{str(e)}"
            )

    def _addCustomStyles(self, report: ReportBase):
        """
        Add custom CSS styles for better PDF formatting
        
        :param report: ReportBase instance
        """
        custom_css = """
        body {
            font-size: 11pt;
        }
        table {
            font-size: 11pt;
            width: 100%;
            margin: 10px 0;
        }
        th {
            font-size: 11pt;
            font-weight: bold;
            background-color: #f0f0f0;
            padding: 8px;
            text-align: left;
        }
        td {
            font-size: 11pt;
            padding: 6px 8px;
        }
        td.column-0 {
            font-weight: bold;
            background-color: #ffffff;
            color: #000000;
        }
        td.column-1 {
            background-color: #f5f5f5;
            color: #666666;
        }
        h3 {
            font-size: 13pt;
        }
        """
        with report._html_doc.head:
            tags.style(raw(custom_css))

    def _addStyledTable(self, report: ReportBase, data: dict, titles: tuple = ("Field", "Value")):
        """
        Add a styled table with larger font and grey field names
        
        :param report: ReportBase instance
        :param data: Dictionary of field-value pairs
        :param titles: Tuple of (field_title, value_title)
        """
        with report._html_doc.getElementById("model-parameters"):
            with tags.table(style="font-size: 11pt; width: 100%; margin: 10px 0;"):
                # Header row
                with tags.tr():
                    tags.th(titles[0], style="font-size: 11pt; font-weight: bold; background-color: #f0f0f0; padding: 8px; text-align: left;")
                    tags.th(titles[1], style="font-size: 11pt; font-weight: bold; background-color: #f0f0f0; padding: 8px; text-align: left;")

                # Data rows
                for key in sorted(data.keys()):
                    with tags.tr():
                        # Field name (left column) - bold, grey background and text
                        tags.td(key, style="font-size: 11pt; font-weight: bold; background-color: #f5f5f5; color: #666666; padding: 6px 8px;")
                        # Value (right column) - white background, black text
                        tags.td(str(data[key]), style="font-size: 11pt; background-color: #ffffff; color: #000000; padding: 6px 8px;")

    def _addSectionHeader(self, report: ReportBase, title: str):
        """
        Add a section header to the report
        
        :param report: ReportBase instance
        :param title: Section title
        """
        with report._html_doc.getElementById("model-parameters"):
            # Add spacing before header
            tags.p("", style="margin-top: 15px;")
            tags.h3(title, style="margin-top: 10px; margin-bottom: 8px; font-weight: bold; color: #2c3e50;")
            tags.hr(style="margin-bottom: 10px; border: 1px solid #3498db;")

    def _generatePDFReport(self, export_data: SASBDBExportData, filename: str):
        """
        Generate a PDF report with all entries and plot
        
        :param export_data: SASBDB export data
        :param filename: Output PDF filename
        """
        # Create report
        report = ReportBase("SASBDB Export Report")

        # Add custom styles for better formatting
        self._addCustomStyles(report)

        # Add project information
        if export_data.project:
            project = export_data.project
            project_data = {
                "Published": "Yes" if project.published else "No",
            }
            if project.pubmed_pmid:
                project_data["PubMed PMID"] = project.pubmed_pmid
            if project.doi:
                project_data["DOI"] = project.doi
            if project.project_title:
                project_data["Project Title"] = project.project_title

            if project_data:
                self._addSectionHeader(report, "Project Information")
                self._addStyledTable(report, project_data)

        # Add sample information
        if export_data.samples:
            sample = export_data.samples[0]
            sample_data = {}
            if sample.sample_title:
                sample_data["Sample Title"] = sample.sample_title
            if sample.curve_type:
                sample_data["Curve Type"] = sample.curve_type
            if sample.angular_units:
                sample_data["Angular Units"] = sample.angular_units
            if sample.intensity_units:
                sample_data["Intensity Units"] = sample.intensity_units
            if sample.experimental_molecular_weight:
                sample_data["Experimental MW"] = f"{sample.experimental_molecular_weight} kDa"
            if sample.experiment_date:
                sample_data["Experiment Date"] = sample.experiment_date
            if sample.beamline_instrument:
                sample_data["Beamline/Instrument"] = sample.beamline_instrument
            if sample.wavelength:
                sample_data["Wavelength"] = f"{sample.wavelength} nm"
            if sample.sample_detector_distance:
                sample_data["Sample-Detector Distance"] = f"{sample.sample_detector_distance} m"
            if sample.cell_temperature:
                sample_data["Cell Temperature"] = f"{sample.cell_temperature} °C"
            if sample.concentration:
                sample_data["Concentration"] = f"{sample.concentration} mg/ml"

            if sample_data:
                self._addSectionHeader(report, "Sample/Data Information")
                self._addStyledTable(report, sample_data)

            # Add molecule information
            if sample.molecule:
                mol = sample.molecule
                mol_data = {}
                if mol.type:
                    mol_data["Type"] = mol.type
                if mol.long_name:
                    mol_data["Long Name"] = mol.long_name
                if mol.short_name:
                    mol_data["Short Name"] = mol.short_name
                if mol.uniprot_accession:
                    mol_data["UniProt Accession"] = mol.uniprot_accession
                if mol.fasta_sequence:
                    # Truncate long sequences for display
                    seq = mol.fasta_sequence
                    if len(seq) > 100:
                        seq = seq[:100] + "..."
                    mol_data["FASTA Sequence"] = seq
                if mol.monomer_mw_kda:
                    mol_data["Monomer MW"] = f"{mol.monomer_mw_kda} kDa"
                if mol.number_of_molecules:
                    mol_data["Number of Molecules"] = str(mol.number_of_molecules)
                if mol.oligomeric_state:
                    mol_data["Oligomeric State"] = mol.oligomeric_state
                if mol.total_mw_kda:
                    mol_data["Total MW"] = f"{mol.total_mw_kda} kDa"

                if mol_data:
                    self._addSectionHeader(report, "Molecule Information")
                    self._addStyledTable(report, mol_data)

            # Add buffer information
            if sample.buffer:
                buffer = sample.buffer
                buffer_data = {}
                if buffer.description:
                    buffer_data["Description"] = buffer.description
                if buffer.ph:
                    buffer_data["pH"] = str(buffer.ph)
                if buffer.comment:
                    buffer_data["Comment"] = buffer.comment

                if buffer_data:
                    self._addSectionHeader(report, "Buffer Information")
                    self._addStyledTable(report, buffer_data)

            # Add Guinier information
            if sample.guinier:
                guinier = sample.guinier
                guinier_data = {}
                # Q range start and end at top
                if guinier.range_start is not None:
                    guinier_data["Q Start"] = str(guinier.range_start)
                if guinier.range_end is not None:
                    guinier_data["Q End"] = str(guinier.range_end)
                if guinier.start_point is not None:
                    guinier_data["Start point"] = str(guinier.start_point)
                if guinier.end_point is not None:
                    guinier_data["End point"] = str(guinier.end_point)
                if guinier.rg is not None:
                    guinier_data["Rg"] = f"{guinier.rg} nm"
                if guinier.rg_error is not None:
                    guinier_data["Rg Error"] = f"{guinier.rg_error} nm"
                if guinier.i0 is not None:
                    guinier_data["I(0)"] = str(guinier.i0)

                if guinier_data:
                    self._addSectionHeader(report, "Guinier Analysis")
                    self._addStyledTable(report, guinier_data)

            # Add fit information
            if sample.fits:
                fit_count = 0
                for fit in sample.fits:
                    fit_data = {}
                    if fit.software:
                        fit_data["Software"] = fit.software
                    if fit.software_version:
                        fit_data["Software Version"] = fit.software_version
                    if fit.chi_squared is not None:
                        fit_data["Chi-squared"] = f"{fit.chi_squared:.4f}"
                    if fit.cormap_pvalue is not None:
                        fit_data["CorMap p-value"] = f"{fit.cormap_pvalue:.4f}"
                    if fit.angular_units:
                        fit_data["Angular Units"] = fit.angular_units
                    if fit.description:
                        fit_data["Description"] = fit.description

                    if fit_data:
                        fit_title = "Fit Information" if fit_count == 0 else f"Fit Information ({fit_count + 1})"
                        self._addSectionHeader(report, fit_title)
                        self._addStyledTable(report, fit_data)

                    # Add model information
                    if fit.models:
                        model_count = 0
                        for model in fit.models:
                            model_data = {}
                            if model.software_or_db:
                                model_data["Software/DB"] = model.software_or_db
                            if model.software_version:
                                model_data["Software Version"] = model.software_version
                            if model.symmetry:
                                model_data["Symmetry"] = model.symmetry
                            if model.model_data:
                                model_data["Model Data"] = model.model_data
                            if model.comment:
                                model_data["Comment"] = model.comment

                            if model_data:
                                model_title = "Model Information" if model_count == 0 else f"Model Information ({model_count + 1})"
                                self._addSectionHeader(report, model_title)
                                self._addStyledTable(report, model_data)
                            model_count += 1
                    fit_count += 1

        # Add instrument information
        if export_data.instruments:
            instrument = export_data.instruments[0]
            inst_data = {}
            if instrument.source_type:
                inst_data["Source Type"] = instrument.source_type
            if instrument.beamline_name:
                inst_data["Beamline/Instrument"] = instrument.beamline_name
            if instrument.synchrotron_name:
                inst_data["Synchrotron/Facility"] = instrument.synchrotron_name
            if instrument.detector_manufacturer:
                inst_data["Detector Manufacturer/Model"] = instrument.detector_manufacturer
            if instrument.detector_type:
                inst_data["Detector Type"] = instrument.detector_type
            if instrument.detector_resolution:
                inst_data["Detector Resolution"] = instrument.detector_resolution
            if instrument.city:
                inst_data["City"] = instrument.city
            if instrument.country:
                inst_data["Country"] = instrument.country

            if inst_data:
                self._addSectionHeader(report, "Instrument Information")
                self._addStyledTable(report, inst_data)

        # Try to add plot with model from fitting widget
        plot_fig = self._getPlotFigureWithModel()
        if plot_fig:
            try:
                report.add_plot(plot_fig, image_type="png", figure_title="Data and Model Fit")
            except Exception as e:
                logger.warning(f"Could not add plot to PDF: {e}")
        else:
            # Fallback: try to get simple data plot
            try:
                plot_fig = self._getPlotFigure()
                if plot_fig:
                    report.add_plot(plot_fig, image_type="png", figure_title="Data Plot")
            except Exception as e:
                logger.warning(f"Could not add plot to PDF: {e}")

        # Try to add residual plot
        residual_fig = self._getResidualPlotFigure()
        if residual_fig:
            try:
                report.add_plot(residual_fig, image_type="png", figure_title="Residuals")
            except Exception as e:
                logger.warning(f"Could not add residual plot to PDF: {e}")

        # Try to add model shape visualization if available
        model_shape_fig = self._getModelShapeFigure()
        if model_shape_fig:
            try:
                report.add_plot(model_shape_fig, image_type="png", figure_title="Model 3D Shape")
            except Exception as e:
                logger.warning(f"Could not add model shape to PDF: {e}")

        # Save PDF
        report.save_pdf(filename)

    def _getPlotFigureWithModel(self):
        """
        Try to get a matplotlib figure with data and model from the fitting widget
        
        :return: matplotlib.figure.Figure or None
        """
        try:
            # Try to access the fitting widget through parent
            parent = self.parent()
            if parent is None:
                return None

            # Try to get current perspective (FittingPerspective)
            current_perspective = None
            if hasattr(parent, '_current_perspective'):
                current_perspective = parent._current_perspective
            elif hasattr(parent, 'guiManager') and hasattr(parent.guiManager, '_current_perspective'):
                current_perspective = parent.guiManager._current_perspective

            if current_perspective is None:
                return None

            # Check if it's a FittingPerspective
            from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow
            if not isinstance(current_perspective, FittingWindow):
                return None

            # Get current fitting widget
            fitting_widget = current_perspective.currentFittingWidget
            if fitting_widget is None:
                return None

            # Use ReportPageLogic to get plot images (same as Report Results)
            from sas.qtgui.Perspectives.Fitting import FittingUtilities
            from sas.qtgui.Perspectives.Fitting.ReportPageLogic import ReportPageLogic

            # Get the index (same way as getReport does)
            index = None
            if hasattr(fitting_widget, 'all_data') and fitting_widget.all_data:
                index = fitting_widget.all_data[fitting_widget.data_index]
            elif hasattr(fitting_widget, 'theory_item'):
                index = fitting_widget.theory_item

            if index is None or fitting_widget.logic.kernel_module is None:
                return None

            # Create ReportPageLogic instance
            params = FittingUtilities.getStandardParam(fitting_widget._model_model)
            poly_params = []
            magnet_params = []
            if (hasattr(fitting_widget, 'chkPolydispersity') and
                fitting_widget.chkPolydispersity.isChecked() and
                fitting_widget.polydispersity_widget.poly_model.rowCount() > 0):
                poly_params = FittingUtilities.getStandardParam(fitting_widget.polydispersity_widget.poly_model)
            if (hasattr(fitting_widget, 'chkMagnetism') and
                fitting_widget.chkMagnetism.isChecked() and
                hasattr(fitting_widget, 'canHaveMagnetism') and
                fitting_widget.canHaveMagnetism() and
                fitting_widget.magnetism_widget._magnet_model.rowCount() > 0):
                magnet_params = FittingUtilities.getStandardParam(fitting_widget.magnetism_widget._magnet_model)

            report_logic = ReportPageLogic(
                fitting_widget,
                kernel_module=fitting_widget.logic.kernel_module,
                data=fitting_widget.data,
                index=index,
                params=params + poly_params + magnet_params
            )

            # Get plot figures
            images = report_logic.getImages()
            if images and len(images) > 0:
                # Return the first plot figure
                return images[0]

            return None
        except Exception as e:
            logger.warning(f"Error getting plot figure with model: {e}")
            return None

    def _getPlotFigure(self):
        """
        Try to get a matplotlib figure from the current data/plot (fallback)
        
        :return: matplotlib.figure.Figure or None
        """
        try:
            # Try to get data from export_data and create a simple plot
            if self.export_data.samples:
                sample = self.export_data.samples[0]
                # Try to load data from experimental_curve file if available
                if sample.experimental_curve and os.path.exists(sample.experimental_curve):
                    try:
                        import matplotlib.pyplot as plt

                        from sasdata.dataloader.loader import Loader

                        loader = Loader()
                        data_list = loader.load(sample.experimental_curve)
                        if data_list:
                            data = data_list[0]
                            # Create plot
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
                        logger.warning(f"Could not load data file for plotting: {e}")

            return None
        except Exception as e:
            logger.warning(f"Error getting plot figure: {e}")
            return None

    def _getResidualPlotFigure(self):
        """
        Try to get a matplotlib figure of the residual plot from the fitting widget
        
        :return: matplotlib.figure.Figure or None
        """
        try:
            logger.info("Starting residual plot search...")

            # Try to access the fitting widget through parent
            parent = self.parent()
            if parent is None:
                logger.warning("No parent found for residual plot search")
                return None

            # Try to get current perspective (FittingPerspective)
            current_perspective = None
            if hasattr(parent, '_current_perspective'):
                current_perspective = parent._current_perspective
            elif hasattr(parent, 'guiManager') and hasattr(parent.guiManager, '_current_perspective'):
                current_perspective = parent.guiManager._current_perspective

            if current_perspective is None:
                logger.warning("No current perspective found")
                return None

            # Check if it's a FittingPerspective
            from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow
            if not isinstance(current_perspective, FittingWindow):
                logger.warning(f"Current perspective is not FittingWindow: {type(current_perspective)}")
                return None

            # Get current fitting widget
            fitting_widget = current_perspective.currentFittingWidget
            if fitting_widget is None:
                logger.warning("No current fitting widget found")
                return None

            logger.info(f"Found fitting widget: {fitting_widget}")

            # Get residual plots using PlotHelper
            import sas.qtgui.Plotting.PlotHelper as PlotHelper
            from sas.qtgui.Plotting.PlotterData import DataRole

            if fitting_widget.logic.kernel_module is None:
                logger.warning("No kernel module found")
                return None

            modelname = fitting_widget.logic.kernel_module.name
            if not modelname:
                logger.warning("No model name found")
                return None

            logger.info(f"Model name: {modelname}")

            # Get the data ID - residuals are linked to the original data, not the model
            data_id = None
            if hasattr(fitting_widget, 'data') and fitting_widget.data:
                data_id = fitting_widget.data.id
                logger.info(f"Data ID: {data_id}")

            if data_id is None:
                logger.warning("No data ID found")
                return None

            # Get all shown plots
            shown_plot_names = PlotHelper.currentPlotIds()
            logger.info(f"Found {len(shown_plot_names)} active plots")

            # Find residual plots related to this dataset
            # Residual plot ID format: "Residual res" + str(data_id)
            # The original ID from FittingUtilities.plotResiduals is "res" + str(data_id)
            # Then it gets prefixed with "Residual " in calculateResiduals()
            expected_residual_id = f"Residual res{data_id}"
            expected_original_id = f"res{data_id}"
            logger.info(f"Looking for residual ID: {expected_residual_id} or {expected_original_id}")

            residual_plots = []
            data_name = None
            if hasattr(fitting_widget, 'data') and fitting_widget.data:
                data_name = getattr(fitting_widget.data, 'name', None)
                logger.info(f"Data name: {data_name}")

            # First pass: look for exact matches
            for name in shown_plot_names:
                try:
                    plotter = PlotHelper.plotById(name)
                    if plotter and plotter.data:
                        logger.info(f"Checking plot {name} with {len(plotter.data)} data items")
                        # Check if this is a residual plot for our data
                        for data_item in plotter.data:
                            # Check if it's a residual plot
                            if hasattr(data_item, 'plot_role'):
                                role = data_item.plot_role
                                logger.info(f"  Data item role: {role}, ID: {getattr(data_item, 'id', 'N/A')}, Name: {getattr(data_item, 'name', 'N/A')}")

                                if role == DataRole.ROLE_RESIDUAL:
                                    residual_id = getattr(data_item, 'id', '')
                                    residual_name = getattr(data_item, 'name', '')
                                    logger.info(f"  Found residual plot! ID: {residual_id}, Name: {residual_name}")

                                    # Check by exact ID match
                                    if residual_id == expected_residual_id:
                                        logger.info(f"  Matched by exact ID: {expected_residual_id}")
                                        residual_plots.append(plotter.figure)
                                        break

                                    # Check by original ID (without "Residual " prefix)
                                    if residual_id == expected_original_id:
                                        logger.info(f"  Matched by original ID: {expected_original_id}")
                                        residual_plots.append(plotter.figure)
                                        break

                                    # Check if ID contains our data ID
                                    if str(data_id) in residual_id:
                                        logger.info("  Matched by data ID in residual ID")
                                        residual_plots.append(plotter.figure)
                                        break

                                    # Fallback: check by name pattern
                                    if residual_name and "Residual" in residual_name:
                                        if (modelname in residual_name or
                                            (data_name and data_name in residual_name)):
                                            logger.info("  Matched by name pattern")
                                            residual_plots.append(plotter.figure)
                                            break
                except Exception as e:
                    logger.warning(f"Error checking plot {name}: {e}")
                    import traceback
                    logger.warning(traceback.format_exc())
                    continue

            # Return the first residual plot found
            if residual_plots:
                logger.info(f"Found {len(residual_plots)} residual plot(s), returning first one")
                return residual_plots[0]

            # Last resort: return any residual plot if we can't match by ID/name
            logger.info("No exact match found, trying fallback: any residual plot")
            for name in shown_plot_names:
                try:
                    plotter = PlotHelper.plotById(name)
                    if plotter and plotter.data:
                        for data_item in plotter.data:
                            if (hasattr(data_item, 'plot_role') and
                                data_item.plot_role == DataRole.ROLE_RESIDUAL):
                                # Return any residual plot as fallback
                                logger.info(f"Found residual plot by role only: {getattr(data_item, 'id', 'unknown')}")
                                return plotter.figure
                except Exception as e:
                    logger.warning(f"Error in fallback residual search: {e}")
                    continue

            logger.warning("No residual plot found after exhaustive search")
            return None
        except Exception as e:
            logger.warning(f"Error getting residual plot figure: {e}")
            import traceback
            logger.warning(traceback.format_exc())
            return None

    def _getModelShapeFigure(self):
        # TODO: sasmodels shape visualization
        return None

