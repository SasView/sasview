"""
SASBDB Export Dialog

This dialog allows users to review and edit SASBDB export data before exporting.
"""
import logging
import os
from typing import Optional

from PySide6 import QtCore, QtWidgets, QtGui

import sas.qtgui.Utilities.ObjectLibrary as ObjectLibrary
from sas.qtgui.Utilities.SASBDB.sasbdb_data import (
    SASBDBExportData,
    SASBDBProject,
    SASBDBSample,
    SASBDBMolecule,
    SASBDBBuffer,
    SASBDBGuinier,
    SASBDBFit,
    SASBDBInstrument,
    SASBDBModel,
)
from sas.qtgui.Utilities.SASBDB.sasbdb_data_collector import SASBDBDataCollector
from sas.qtgui.Utilities.SASBDB.sasbdb_exporter import SASBDBExporter
from sas.qtgui.Utilities.SASBDB.UI.SASBDBDialogUI import Ui_SASBDBDialogUI
from sas.qtgui.Utilities.Reports.reports import ReportBase
from dominate import tags
from dominate.util import raw

logger = logging.getLogger(__name__)


class SASBDBDialog(QtWidgets.QDialog, Ui_SASBDBDialogUI):
    """
    Dialog for SASBDB export functionality
    """
    
    def __init__(self, export_data: Optional[SASBDBExportData] = None, parent: Optional[QtCore.QObject] = None):
        """
        Initialize the SASBDB dialog
        
        :param export_data: Pre-collected SASBDB export data (optional)
        :param parent: Parent widget
        """
        super().__init__(parent)
        self.setupUi(self)

        # Cache for the original (unscaled) shape pixmap; used to rescale efficiently on resize
        self._shape_pixmap_original = None
        if hasattr(self, 'lblShapeImage'):
            self.lblShapeImage.installEventFilter(self)
            self.lblShapeImage.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        
        # Store export data
        self.export_data = export_data or SASBDBExportData()
        
        # Get save location from object library
        self.save_location = ObjectLibrary.getObject('SASBDBDialog_directory')
        
        # Connect signals
        self.cmdExport.clicked.connect(self.onExport)
        self.cmdGeneratePDF.clicked.connect(self.onGeneratePDF)
        self.cmdClose.clicked.connect(self.close)
        self.chkPublished.toggled.connect(self.onPublishedToggled)
        
        # Populate UI with data
        self.populateFromData()
        
        # Set up initial state
        self.onPublishedToggled(self.chkPublished.isChecked())
        
        # Generate model visualization if available
        self.updateModelVisualization()

    def eventFilter(self, obj, event):
        """Keep the shape visualization filling the available label size on resize (no re-render)."""
        if hasattr(self, 'lblShapeImage') and obj is self.lblShapeImage:
            if event.type() == QtCore.QEvent.Type.Resize:
                if self._shape_pixmap_original is not None and not self._shape_pixmap_original.isNull():
                    scaled = self._shape_pixmap_original.scaled(
                        self.lblShapeImage.size(),
                        QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                        QtCore.Qt.TransformationMode.SmoothTransformation,
                    )
                    self.lblShapeImage.setPixmap(scaled)
                    self.lblShapeImage.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        return super().eventFilter(obj, event)
    
    def populateFromData(self):
        """
        Populate UI fields from export_data
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
            
            # Guinier tab
            if sample.guinier:
                guinier = sample.guinier
                if guinier.rg:
                    # Format to 2 significant digits
                    self.txtGuinierRg.setText(f"{guinier.rg:.2g}")
                if guinier.rg_error:
                    # Format to 2 significant digits
                    self.txtGuinierRgError.setText(f"{guinier.rg_error:.2g}")
                if guinier.i0:
                    # Format to 2 significant digits
                    self.txtGuinierI0.setText(f"{guinier.i0:.2g}")
                if guinier.range_start:
                    self.txtGuinierRangeStart.setText(str(guinier.range_start))
                if guinier.range_end:
                    self.txtGuinierRangeEnd.setText(str(guinier.range_end))
            
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
        Collect data from UI fields and create SASBDBExportData
        
        :return: SASBDBExportData object
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
        
        if any([guinier.rg, guinier.i0, guinier.range_start, guinier.range_end]):
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
        Validate that required fields are filled
        
        :return: Tuple of (is_valid, error_message)
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
        
        return True, ""
    
    def onPublishedToggled(self, checked: bool):
        """
        Enable/disable published-related fields
        
        :param checked: Whether published checkbox is checked
        """
        self.txtPubmedPMID.setEnabled(checked)
        self.txtDOI.setEnabled(checked)
        self.txtProjectTitle.setEnabled(not checked)
    
    def updateModelVisualization(self):
        """
        Generate and display model shape visualization if available
        Uses built-in matplotlib rendering for common sasmodels shapes
        """
        # Check if we have model data with visualization parameters
        model_name = None
        viz_params = None
        
        if self.export_data.samples:
            sample = self.export_data.samples[0]
            if sample.fits:
                fit = sample.fits[0]
                if fit.models:
                    model = fit.models[0]
                    model_name = model.software_or_db
                    viz_params = model.visualization_params
        
        if not model_name:
            # No model available
            if hasattr(self, 'lblShapeImage'):
                self.lblShapeImage.setText("No model visualization available")
            return
        
        try:
            # Generate visualization using built-in matplotlib rendering
            if hasattr(self, 'lblShapeImage'):
                label_size = self.lblShapeImage.size()
                # When the dialog is first shown, the label may not be laid out yet
                if label_size.width() < 50 or label_size.height() < 50:
                    label_size = self.lblShapeImage.minimumSize()
            else:
                label_size = None

            pixmap = self._generateModelShapePixmap(model_name, viz_params, target_size=label_size)
            
            if pixmap and not pixmap.isNull():
                # Display the image at a good size
                if hasattr(self, 'lblShapeImage'):
                    # Pixmap is generated to fit the label; no hard-coded downscaling here
                    self._shape_pixmap_original = pixmap
                    # Scale once now (future resizes are handled by eventFilter)
                    scaled = pixmap.scaled(
                        self.lblShapeImage.size(),
                        QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                        QtCore.Qt.TransformationMode.SmoothTransformation,
                    )
                    self.lblShapeImage.setPixmap(scaled)
                    self.lblShapeImage.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            else:
                if hasattr(self, 'lblShapeImage'):
                    self.lblShapeImage.setText(f"Visualization not available for '{model_name}'")
                    
        except Exception as e:
            logger.warning(f"Error generating model visualization: {e}")
            import traceback
            logger.warning(traceback.format_exc())
            if hasattr(self, 'lblShapeImage'):
                self.lblShapeImage.setText(f"Error generating visualization:\n{str(e)[:80]}")
    
    def _generateModelShapePixmap(self, model_name: str, params: dict = None, target_size: QtCore.QSize = None) -> QtGui.QPixmap:
        """
        Generate a QPixmap visualization of the model shape using matplotlib
        
        :param model_name: Name of the sasmodel (e.g., 'sphere', 'cylinder', 'core_shell_sphere')
        :param params: Dictionary of model parameters
        :param target_size: Target size for the pixmap (typically the QLabel size)
        :return: QPixmap with the visualization
        """
        import numpy as np
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from mpl_toolkits.mplot3d import Axes3D
        import io
        
        # Normalize model name
        normalized_name = model_name.lower().replace(' ', '_')
        if '.' in normalized_name:
            normalized_name = normalized_name.split('.')[-1]
        
        # Create figure sized to the actual target widget size (fills the available space)
        dpi = 100
        if target_size is not None:
            w_px = max(int(target_size.width()), 1)
            h_px = max(int(target_size.height()), 1)
            # Cap to avoid excessive memory usage on very large screens
            w_px = min(w_px, 2200)
            h_px = min(h_px, 1800)
            fig = Figure(figsize=(w_px / dpi, h_px / dpi), dpi=dpi)
        else:
            fig = Figure(figsize=(20, 12), dpi=dpi)
        canvas = FigureCanvasAgg(fig)
        
        # Use GridSpec efficiently: 3D view takes ~70% width, cross-sections take ~30% width
        from matplotlib.gridspec import GridSpec
        from matplotlib.ticker import MaxNLocator
        gs = GridSpec(
            3, 3,
            figure=fig,
            width_ratios=[2.2, 2.2, 1.8],
            height_ratios=[1, 1, 1],
            hspace=0.08,
            wspace=0.08,
        )
        
        # Main 3D view spans first 2 columns and all 3 rows
        ax_main = fig.add_subplot(gs[:, :2], projection='3d')
        
        # Cross-sections stacked in rightmost column (made wider)
        ax1 = fig.add_subplot(gs[0, 2])  # XY view (top)
        ax2 = fig.add_subplot(gs[1, 2])  # XZ view (front)
        ax3 = fig.add_subplot(gs[2, 2])  # YZ view (side)
        
        # Get default parameters if none provided
        if params is None:
            params = {}
        
        # Define shape drawing functions for common models
        try:
            if 'sphere' in normalized_name and 'core_shell' in normalized_name:
                self._draw_core_shell_sphere(ax1, ax2, ax3, params)
                self._draw_3d_core_shell_sphere(ax_main, params)
            elif 'sphere' in normalized_name:
                self._draw_sphere(ax1, ax2, ax3, params)
                self._draw_3d_sphere(ax_main, params)
            elif 'cylinder' in normalized_name and 'core_shell' in normalized_name:
                self._draw_core_shell_cylinder(ax1, ax2, ax3, params)
                self._draw_3d_core_shell_cylinder(ax_main, params)
            elif 'cylinder' in normalized_name:
                self._draw_cylinder(ax1, ax2, ax3, params)
                self._draw_3d_cylinder(ax_main, params)
            elif 'ellipsoid' in normalized_name:
                self._draw_ellipsoid(ax1, ax2, ax3, params)
                self._draw_3d_ellipsoid(ax_main, params)
            elif 'parallelepiped' in normalized_name or 'rectangular' in normalized_name:
                self._draw_parallelepiped(ax1, ax2, ax3, params)
                self._draw_3d_parallelepiped(ax_main, params)
            else:
                # Generic visualization - show model name
                self._draw_generic_shape(ax1, ax2, ax3, normalized_name, params)
                self._draw_3d_generic(ax_main, normalized_name, params)
            
            # Remove axes from main 3D plot
            ax_main.set_axis_off()

            # Keep cross-section axes but make them clean: few ticks, small labels, subtle spines
            def _style_cross_section_ax(ax):
                ax.tick_params(axis='both', which='major', labelsize=7, length=2, pad=1)
                ax.xaxis.set_major_locator(MaxNLocator(nbins=3))
                ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
                for spine in ax.spines.values():
                    spine.set_linewidth(0.6)
                    spine.set_alpha(0.6)
                ax.grid(True, alpha=0.15, linewidth=0.6)

            for ax in (ax1, ax2, ax3):
                _style_cross_section_ax(ax)
            
            # Set titles
            #ax_main.set_title('3D View', fontsize=16, fontweight='bold', pad=6)
            # Put cross-section titles inside the axes to avoid overlapping with ticks
            for ax, label in (
                (ax1, 'XY (Top)'),
                (ax2, 'XZ (Front)'),
                (ax3, 'YZ (Side)'),
            ):
                ax.set_title("")
                ax.text(
                    0.02, 0.98, label,
                    transform=ax.transAxes,
                    ha='left', va='top',
                    fontsize=10, color='0.2',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='none', alpha=0.85),
                )
            
            # Add main title
            fig.suptitle(f'Model: {model_name}', fontsize=14, fontweight='bold', y=0.99)
            # Use manual spacing (tight_layout can shrink axes in dense grids)
            fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.94, wspace=0.06, hspace=0.10)
            
            # Convert figure to QPixmap
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=dpi, facecolor='white', edgecolor='none')
            buf.seek(0)
            
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(buf.getvalue())
            
            return pixmap
            
        except Exception as e:
            logger.warning(f"Error drawing shape for {model_name}: {e}")
            import traceback
            logger.warning(traceback.format_exc())
            return None
    
    def _draw_sphere(self, ax1, ax2, ax3, params):
        """Draw a sphere in three views"""
        import numpy as np
        
        radius = params.get('radius', 50.0)
        
        # Create circle for all views (sphere looks like circle from all angles)
        theta = np.linspace(0, 2*np.pi, 100)
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        
        for ax in [ax1, ax2, ax3]:
            ax.fill(x, y, alpha=0.6, color='steelblue', edgecolor='darkblue', linewidth=2)
            ax.set_xlim(-radius*1.5, radius*1.5)
            ax.set_ylim(-radius*1.5, radius*1.5)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='k', linewidth=0.5)
            ax.axvline(x=0, color='k', linewidth=0.5)
        
        ax1.set_xlabel('X (Å)')
        ax1.set_ylabel('Y (Å)')
        ax2.set_xlabel('X (Å)')
        ax2.set_ylabel('Z (Å)')
        ax3.set_xlabel('Y (Å)')
        ax3.set_ylabel('Z (Å)')
    
    def _draw_core_shell_sphere(self, ax1, ax2, ax3, params):
        """Draw a core-shell sphere in three views"""
        import numpy as np
        
        # Try multiple parameter name variations for core radius
        core_radius = params.get('radius', params.get('radius_core', params.get('core_radius', 40.0)))
        # Try multiple parameter name variations for thickness  
        thickness = params.get('thickness', params.get('shell_thickness', params.get('thick_shell', 10.0)))
        outer_radius = core_radius + thickness
        
        logger.info(f"Drawing core_shell_sphere with core_radius={core_radius}, thickness={thickness}")
        
        theta = np.linspace(0, 2*np.pi, 100)
        
        for ax in [ax1, ax2, ax3]:
            # Draw outer shell
            x_outer = outer_radius * np.cos(theta)
            y_outer = outer_radius * np.sin(theta)
            ax.fill(x_outer, y_outer, alpha=0.5, color='lightcoral', 
                   edgecolor='darkred', linewidth=2, label='Shell')
            
            # Draw core
            x_core = core_radius * np.cos(theta)
            y_core = core_radius * np.sin(theta)
            ax.fill(x_core, y_core, alpha=0.7, color='steelblue', 
                   edgecolor='darkblue', linewidth=2, label='Core')
            
            ax.set_xlim(-outer_radius*1.5, outer_radius*1.5)
            ax.set_ylim(-outer_radius*1.5, outer_radius*1.5)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            ax.axhline(y=0, color='k', linewidth=0.5)
            ax.axvline(x=0, color='k', linewidth=0.5)
        
        ax1.legend(loc='upper right', fontsize=8)
        ax1.set_xlabel('X (Å)')
        ax1.set_ylabel('Y (Å)')
        ax2.set_xlabel('X (Å)')
        ax2.set_ylabel('Z (Å)')
        ax3.set_xlabel('Y (Å)')
        ax3.set_ylabel('Z (Å)')
    
    def _draw_cylinder(self, ax1, ax2, ax3, params):
        """Draw a cylinder in three views"""
        import numpy as np
        
        radius = params.get('radius', 20.0)
        length = params.get('length', 100.0)
        half_length = length / 2
        
        theta = np.linspace(0, 2*np.pi, 100)
        
        # XY view (top) - circle
        x_circle = radius * np.cos(theta)
        y_circle = radius * np.sin(theta)
        ax1.fill(x_circle, y_circle, alpha=0.6, color='steelblue', 
                edgecolor='darkblue', linewidth=2)
        ax1.set_xlim(-radius*2, radius*2)
        ax1.set_ylim(-radius*2, radius*2)
        ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3)
        ax1.set_xlabel('X (Å)')
        ax1.set_ylabel('Y (Å)')
        
        # XZ view (front) - rectangle
        rect_x = [-radius, radius, radius, -radius, -radius]
        rect_z = [-half_length, -half_length, half_length, half_length, -half_length]
        ax2.fill(rect_x, rect_z, alpha=0.6, color='steelblue', 
                edgecolor='darkblue', linewidth=2)
        max_dim = max(radius*2, half_length*2)
        ax2.set_xlim(-max_dim*0.7, max_dim*0.7)
        ax2.set_ylim(-max_dim*0.7, max_dim*0.7)
        ax2.set_aspect('equal')
        ax2.grid(True, alpha=0.3)
        ax2.set_xlabel('X (Å)')
        ax2.set_ylabel('Z (Å)')
        
        # YZ view (side) - rectangle
        ax3.fill(rect_x, rect_z, alpha=0.6, color='steelblue', 
                edgecolor='darkblue', linewidth=2)
        ax3.set_xlim(-max_dim*0.7, max_dim*0.7)
        ax3.set_ylim(-max_dim*0.7, max_dim*0.7)
        ax3.set_aspect('equal')
        ax3.grid(True, alpha=0.3)
        ax3.set_xlabel('Y (Å)')
        ax3.set_ylabel('Z (Å)')
    
    def _draw_core_shell_cylinder(self, ax1, ax2, ax3, params):
        """Draw a core-shell cylinder in three views"""
        import numpy as np
        
        core_radius = params.get('radius', 20.0)
        shell_thickness = params.get('thickness', 5.0)
        outer_radius = core_radius + shell_thickness
        length = params.get('length', 100.0)
        half_length = length / 2
        
        theta = np.linspace(0, 2*np.pi, 100)
        
        # XY view (top) - concentric circles
        for ax in [ax1]:
            x_outer = outer_radius * np.cos(theta)
            y_outer = outer_radius * np.sin(theta)
            ax.fill(x_outer, y_outer, alpha=0.5, color='lightcoral', 
                   edgecolor='darkred', linewidth=2)
            x_core = core_radius * np.cos(theta)
            y_core = core_radius * np.sin(theta)
            ax.fill(x_core, y_core, alpha=0.7, color='steelblue', 
                   edgecolor='darkblue', linewidth=2)
            ax.set_xlim(-outer_radius*2, outer_radius*2)
            ax.set_ylim(-outer_radius*2, outer_radius*2)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
        ax1.set_xlabel('X (Å)')
        ax1.set_ylabel('Y (Å)')
        
        # XZ and YZ views - nested rectangles
        for ax, xlabel in [(ax2, 'X (Å)'), (ax3, 'Y (Å)')]:
            # Shell rectangle
            shell_x = [-outer_radius, outer_radius, outer_radius, -outer_radius, -outer_radius]
            shell_z = [-half_length, -half_length, half_length, half_length, -half_length]
            ax.fill(shell_x, shell_z, alpha=0.5, color='lightcoral', 
                   edgecolor='darkred', linewidth=2)
            # Core rectangle
            core_x = [-core_radius, core_radius, core_radius, -core_radius, -core_radius]
            ax.fill(core_x, shell_z, alpha=0.7, color='steelblue', 
                   edgecolor='darkblue', linewidth=2)
            max_dim = max(outer_radius*2, half_length*2)
            ax.set_xlim(-max_dim*0.7, max_dim*0.7)
            ax.set_ylim(-max_dim*0.7, max_dim*0.7)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            ax.set_xlabel(xlabel)
            ax.set_ylabel('Z (Å)')
    
    def _draw_ellipsoid(self, ax1, ax2, ax3, params):
        """Draw an ellipsoid in three views"""
        import numpy as np
        
        radius_a = params.get('radius_equatorial', params.get('radius_a', 50.0))
        radius_b = params.get('radius_polar', params.get('radius_b', 30.0))
        radius_c = params.get('radius_c', radius_a)  # Often prolate/oblate
        
        theta = np.linspace(0, 2*np.pi, 100)
        
        # XY view
        x1 = radius_a * np.cos(theta)
        y1 = radius_c * np.sin(theta)
        ax1.fill(x1, y1, alpha=0.6, color='steelblue', edgecolor='darkblue', linewidth=2)
        max_r1 = max(radius_a, radius_c) * 1.5
        ax1.set_xlim(-max_r1, max_r1)
        ax1.set_ylim(-max_r1, max_r1)
        ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3)
        ax1.set_xlabel('X (Å)')
        ax1.set_ylabel('Y (Å)')
        
        # XZ view
        x2 = radius_a * np.cos(theta)
        z2 = radius_b * np.sin(theta)
        ax2.fill(x2, z2, alpha=0.6, color='steelblue', edgecolor='darkblue', linewidth=2)
        max_r2 = max(radius_a, radius_b) * 1.5
        ax2.set_xlim(-max_r2, max_r2)
        ax2.set_ylim(-max_r2, max_r2)
        ax2.set_aspect('equal')
        ax2.grid(True, alpha=0.3)
        ax2.set_xlabel('X (Å)')
        ax2.set_ylabel('Z (Å)')
        
        # YZ view
        y3 = radius_c * np.cos(theta)
        z3 = radius_b * np.sin(theta)
        ax3.fill(y3, z3, alpha=0.6, color='steelblue', edgecolor='darkblue', linewidth=2)
        max_r3 = max(radius_c, radius_b) * 1.5
        ax3.set_xlim(-max_r3, max_r3)
        ax3.set_ylim(-max_r3, max_r3)
        ax3.set_aspect('equal')
        ax3.grid(True, alpha=0.3)
        ax3.set_xlabel('Y (Å)')
        ax3.set_ylabel('Z (Å)')
    
    def _draw_parallelepiped(self, ax1, ax2, ax3, params):
        """Draw a parallelepiped/rectangular prism in three views"""
        import numpy as np
        
        a = params.get('length_a', params.get('a', 50.0))
        b = params.get('length_b', params.get('b', 40.0))
        c = params.get('length_c', params.get('c', 30.0))
        
        # XY view
        rect1 = [[-a/2, -b/2], [a/2, -b/2], [a/2, b/2], [-a/2, b/2], [-a/2, -b/2]]
        ax1.fill([p[0] for p in rect1], [p[1] for p in rect1], alpha=0.6, 
                color='steelblue', edgecolor='darkblue', linewidth=2)
        max_dim1 = max(a, b) * 0.8
        ax1.set_xlim(-max_dim1, max_dim1)
        ax1.set_ylim(-max_dim1, max_dim1)
        ax1.set_aspect('equal')
        ax1.grid(True, alpha=0.3)
        ax1.set_xlabel('X (Å)')
        ax1.set_ylabel('Y (Å)')
        
        # XZ view
        rect2 = [[-a/2, -c/2], [a/2, -c/2], [a/2, c/2], [-a/2, c/2], [-a/2, -c/2]]
        ax2.fill([p[0] for p in rect2], [p[1] for p in rect2], alpha=0.6, 
                color='steelblue', edgecolor='darkblue', linewidth=2)
        max_dim2 = max(a, c) * 0.8
        ax2.set_xlim(-max_dim2, max_dim2)
        ax2.set_ylim(-max_dim2, max_dim2)
        ax2.set_aspect('equal')
        ax2.grid(True, alpha=0.3)
        ax2.set_xlabel('X (Å)')
        ax2.set_ylabel('Z (Å)')
        
        # YZ view
        rect3 = [[-b/2, -c/2], [b/2, -c/2], [b/2, c/2], [-b/2, c/2], [-b/2, -c/2]]
        ax3.fill([p[0] for p in rect3], [p[1] for p in rect3], alpha=0.6, 
                color='steelblue', edgecolor='darkblue', linewidth=2)
        max_dim3 = max(b, c) * 0.8
        ax3.set_xlim(-max_dim3, max_dim3)
        ax3.set_ylim(-max_dim3, max_dim3)
        ax3.set_aspect('equal')
        ax3.grid(True, alpha=0.3)
        ax3.set_xlabel('Y (Å)')
        ax3.set_ylabel('Z (Å)')
    
    def _draw_generic_shape(self, ax1, ax2, ax3, model_name, params):
        """Draw a generic representation for unsupported models"""
        for ax in [ax1, ax2, ax3]:
            ax.text(0.5, 0.5, f'{model_name}', 
                   transform=ax.transAxes,
                   ha='center', va='center', fontsize=10,
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_aspect('equal')
            
            # Show parameters if available
            if params:
                param_text = '\n'.join([f'{k}: {v:.2f}' if isinstance(v, float) else f'{k}: {v}' 
                                       for k, v in list(params.items())[:5]])
                ax.text(0.5, 0.2, param_text, 
                       transform=ax.transAxes,
                       ha='center', va='center', fontsize=8,
                       family='monospace')
        
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax2.set_xlabel('X')
        ax2.set_ylabel('Z')
        ax3.set_xlabel('Y')
        ax3.set_ylabel('Z')
    
    # ========== 3D Drawing Functions ==========
    
    def _draw_3d_sphere(self, ax, params):
        """Draw a 3D sphere"""
        import numpy as np
        
        radius = params.get('radius', 50.0)
        
        # Create sphere mesh
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi, 20)
        x = radius * np.outer(np.cos(u), np.sin(v))
        y = radius * np.outer(np.sin(u), np.sin(v))
        z = radius * np.outer(np.ones(np.size(u)), np.cos(v))
        
        ax.plot_surface(x, y, z, alpha=0.7, color='steelblue', edgecolor='darkblue', linewidth=0.3)
        
        self._set_3d_axes(ax, radius * 1.3)
    
    def _draw_3d_core_shell_sphere(self, ax, params):
        """Draw a 3D core-shell sphere with cutaway"""
        import numpy as np
        
        # Try multiple parameter name variations for core radius
        core_radius = params.get('radius', params.get('radius_core', params.get('core_radius', 40.0)))
        # Try multiple parameter name variations for thickness  
        thickness = params.get('thickness', params.get('shell_thickness', params.get('thick_shell', 10.0)))
        outer_radius = core_radius + thickness
        
        # Create meshes
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi, 20)
        
        # Draw shell (with partial transparency to show core)
        x_shell = outer_radius * np.outer(np.cos(u), np.sin(v))
        y_shell = outer_radius * np.outer(np.sin(u), np.sin(v))
        z_shell = outer_radius * np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_surface(x_shell, y_shell, z_shell, alpha=0.3, color='lightcoral', 
                       edgecolor='darkred', linewidth=0.2)
        
        # Draw core (visible through shell)
        x_core = core_radius * np.outer(np.cos(u), np.sin(v))
        y_core = core_radius * np.outer(np.sin(u), np.sin(v))
        z_core = core_radius * np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_surface(x_core, y_core, z_core, alpha=0.8, color='steelblue', 
                       edgecolor='darkblue', linewidth=0.2)
        
        self._set_3d_axes(ax, outer_radius * 1.3)
    
    def _draw_3d_cylinder(self, ax, params):
        """Draw a 3D cylinder"""
        import numpy as np
        
        radius = params.get('radius', 20.0)
        length = params.get('length', 100.0)
        half_length = length / 2
        
        # Create cylinder mesh
        theta = np.linspace(0, 2 * np.pi, 30)
        z_cyl = np.linspace(-half_length, half_length, 20)
        theta_grid, z_grid = np.meshgrid(theta, z_cyl)
        x = radius * np.cos(theta_grid)
        y = radius * np.sin(theta_grid)
        
        ax.plot_surface(x, y, z_grid, alpha=0.7, color='steelblue', 
                       edgecolor='darkblue', linewidth=0.3)
        
        # Draw top and bottom caps
        r_cap = np.linspace(0, radius, 10)
        theta_cap = np.linspace(0, 2 * np.pi, 30)
        r_grid, theta_grid = np.meshgrid(r_cap, theta_cap)
        x_cap = r_grid * np.cos(theta_grid)
        y_cap = r_grid * np.sin(theta_grid)
        
        # Top cap
        z_top = np.ones_like(x_cap) * half_length
        ax.plot_surface(x_cap, y_cap, z_top, alpha=0.7, color='steelblue', 
                       edgecolor='darkblue', linewidth=0.2)
        # Bottom cap
        z_bottom = np.ones_like(x_cap) * (-half_length)
        ax.plot_surface(x_cap, y_cap, z_bottom, alpha=0.7, color='steelblue', 
                       edgecolor='darkblue', linewidth=0.2)
        
        max_dim = max(radius, half_length) * 1.3
        self._set_3d_axes(ax, max_dim)
    
    def _draw_3d_core_shell_cylinder(self, ax, params):
        """Draw a 3D core-shell cylinder"""
        import numpy as np
        
        core_radius = params.get('radius', 20.0)
        shell_thickness = params.get('thickness', 5.0)
        outer_radius = core_radius + shell_thickness
        length = params.get('length', 100.0)
        half_length = length / 2
        
        theta = np.linspace(0, 2 * np.pi, 30)
        z_cyl = np.linspace(-half_length, half_length, 20)
        theta_grid, z_grid = np.meshgrid(theta, z_cyl)
        
        # Shell
        x_shell = outer_radius * np.cos(theta_grid)
        y_shell = outer_radius * np.sin(theta_grid)
        ax.plot_surface(x_shell, y_shell, z_grid, alpha=0.3, color='lightcoral', 
                       edgecolor='darkred', linewidth=0.2)
        
        # Core
        x_core = core_radius * np.cos(theta_grid)
        y_core = core_radius * np.sin(theta_grid)
        ax.plot_surface(x_core, y_core, z_grid, alpha=0.8, color='steelblue', 
                       edgecolor='darkblue', linewidth=0.2)
        
        max_dim = max(outer_radius, half_length) * 1.3
        self._set_3d_axes(ax, max_dim)
    
    def _draw_3d_ellipsoid(self, ax, params):
        """Draw a 3D ellipsoid"""
        import numpy as np
        
        radius_a = params.get('radius_equatorial', params.get('radius_a', 50.0))
        radius_b = params.get('radius_polar', params.get('radius_b', 30.0))
        radius_c = params.get('radius_c', radius_a)
        
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi, 20)
        
        x = radius_a * np.outer(np.cos(u), np.sin(v))
        y = radius_c * np.outer(np.sin(u), np.sin(v))
        z = radius_b * np.outer(np.ones(np.size(u)), np.cos(v))
        
        ax.plot_surface(x, y, z, alpha=0.7, color='steelblue', 
                       edgecolor='darkblue', linewidth=0.3)
        
        max_dim = max(radius_a, radius_b, radius_c) * 1.3
        self._set_3d_axes(ax, max_dim)
    
    def _draw_3d_parallelepiped(self, ax, params):
        """Draw a 3D parallelepiped/box"""
        import numpy as np
        
        a = params.get('length_a', params.get('a', 50.0))
        b = params.get('length_b', params.get('b', 40.0))
        c = params.get('length_c', params.get('c', 30.0))
        
        # Define vertices
        vertices = np.array([
            [-a/2, -b/2, -c/2], [a/2, -b/2, -c/2], [a/2, b/2, -c/2], [-a/2, b/2, -c/2],
            [-a/2, -b/2, c/2], [a/2, -b/2, c/2], [a/2, b/2, c/2], [-a/2, b/2, c/2]
        ])
        
        # Define faces
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],  # bottom
            [vertices[4], vertices[5], vertices[6], vertices[7]],  # top
            [vertices[0], vertices[1], vertices[5], vertices[4]],  # front
            [vertices[2], vertices[3], vertices[7], vertices[6]],  # back
            [vertices[0], vertices[3], vertices[7], vertices[4]],  # left
            [vertices[1], vertices[2], vertices[6], vertices[5]]   # right
        ]
        
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        ax.add_collection3d(Poly3DCollection(faces, alpha=0.7, facecolor='steelblue', 
                                             edgecolor='darkblue', linewidth=1))
        
        max_dim = max(a, b, c) * 0.8
        self._set_3d_axes(ax, max_dim)
    
    def _draw_3d_generic(self, ax, model_name, params):
        """Draw a generic 3D representation for unsupported models"""
        # Just draw a simple sphere as placeholder
        import numpy as np
        
        radius = 50.0
        u = np.linspace(0, 2 * np.pi, 20)
        v = np.linspace(0, np.pi, 15)
        x = radius * np.outer(np.cos(u), np.sin(v))
        y = radius * np.outer(np.sin(u), np.sin(v))
        z = radius * np.outer(np.ones(np.size(u)), np.cos(v))
        
        ax.plot_surface(x, y, z, alpha=0.5, color='gray', edgecolor='darkgray', linewidth=0.3)
        ax.text2D(0.5, 0.95, model_name, transform=ax.transAxes, ha='center', fontsize=9)
        
        self._set_3d_axes(ax, radius * 1.3)
    
    def _set_3d_axes(self, ax, max_dim):
        """Set up 3D axes with equal aspect ratio"""
        ax.set_xlim(-max_dim, max_dim)
        ax.set_ylim(-max_dim, max_dim)
        ax.set_zlim(-max_dim, max_dim)
        ax.set_xlabel('X (Å)', fontsize=8)
        ax.set_ylabel('Y (Å)', fontsize=8)
        ax.set_zlabel('Z (Å)', fontsize=8)
        ax.tick_params(labelsize=7)
        # Set viewing angle
        ax.view_init(elev=20, azim=45)
    
    def _generateModelShapeFigure(self, model_name: str, params: dict = None):
        """
        Generate a matplotlib Figure visualization of the model shape
        Similar to _generateModelShapePixmap but returns a Figure for PDF generation
        
        :param model_name: Name of the sasmodel (e.g., 'sphere', 'cylinder', 'core_shell_sphere')
        :param params: Dictionary of model parameters
        :return: matplotlib.figure.Figure with the visualization
        """
        import numpy as np
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from mpl_toolkits.mplot3d import Axes3D
        
        # Normalize model name
        normalized_name = model_name.lower().replace(' ', '_')
        if '.' in normalized_name:
            normalized_name = normalized_name.split('.')[-1]
        
        # Create figure with large 3D view + cross-sections (PDF rendering)
        fig = Figure(figsize=(24, 12), dpi=100)
        canvas = FigureCanvasAgg(fig)
        
        # Use GridSpec efficiently: 3D view takes ~70% width, cross-sections take ~30% width
        from matplotlib.gridspec import GridSpec
        from matplotlib.ticker import MaxNLocator
        gs = GridSpec(
            3, 3,
            figure=fig,
            width_ratios=[2.2, 2.2, 1.8],
            height_ratios=[1, 1, 1],
            hspace=0.08,
            wspace=0.08,
        )
        
        # Main 3D view spans first 2 columns and all 3 rows
        ax_main = fig.add_subplot(gs[:, :2], projection='3d')
        
        # Cross-sections stacked in rightmost column (made wider)
        ax1 = fig.add_subplot(gs[0, 2])  # XY view (top)
        ax2 = fig.add_subplot(gs[1, 2])  # XZ view (front)
        ax3 = fig.add_subplot(gs[2, 2])  # YZ view (side)
        
        # Get default parameters if none provided
        if params is None:
            params = {}
        
        # Define shape drawing functions for common models
        try:
            if 'sphere' in normalized_name and 'core_shell' in normalized_name:
                self._draw_core_shell_sphere(ax1, ax2, ax3, params)
                self._draw_3d_core_shell_sphere(ax_main, params)
            elif 'sphere' in normalized_name:
                self._draw_sphere(ax1, ax2, ax3, params)
                self._draw_3d_sphere(ax_main, params)
            elif 'cylinder' in normalized_name and 'core_shell' in normalized_name:
                self._draw_core_shell_cylinder(ax1, ax2, ax3, params)
                self._draw_3d_core_shell_cylinder(ax_main, params)
            elif 'cylinder' in normalized_name:
                self._draw_cylinder(ax1, ax2, ax3, params)
                self._draw_3d_cylinder(ax_main, params)
            elif 'ellipsoid' in normalized_name:
                self._draw_ellipsoid(ax1, ax2, ax3, params)
                self._draw_3d_ellipsoid(ax_main, params)
            elif 'parallelepiped' in normalized_name or 'rectangular' in normalized_name:
                self._draw_parallelepiped(ax1, ax2, ax3, params)
                self._draw_3d_parallelepiped(ax_main, params)
            else:
                # Generic visualization - show model name
                self._draw_generic_shape(ax1, ax2, ax3, normalized_name, params)
                self._draw_3d_generic(ax_main, normalized_name, params)
            
            # Remove axes from main 3D plot
            ax_main.set_axis_off()

            # Keep cross-section axes but make them clean: few ticks, small labels, subtle spines
            def _style_cross_section_ax(ax):
                ax.tick_params(axis='both', which='major', labelsize=7, length=2, pad=1)
                ax.xaxis.set_major_locator(MaxNLocator(nbins=3))
                ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
                for spine in ax.spines.values():
                    spine.set_linewidth(0.6)
                    spine.set_alpha(0.6)
                ax.grid(True, alpha=0.15, linewidth=0.6)

            for ax in (ax1, ax2, ax3):
                _style_cross_section_ax(ax)
            
            # Set titles
            ax_main.set_title('3D View', fontsize=16, fontweight='bold', pad=6)
            # Put cross-section titles inside the axes to avoid overlapping with ticks
            for ax, label in (
                (ax1, 'XY (Top)'),
                (ax2, 'XZ (Front)'),
                (ax3, 'YZ (Side)'),
            ):
                ax.set_title("")
                ax.text(
                    0.02, 0.98, label,
                    transform=ax.transAxes,
                    ha='left', va='top',
                    fontsize=10, color='0.2',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='none', alpha=0.85),
                )
            
            # Add main title
            fig.suptitle(f'Model: {model_name}', fontsize=14, fontweight='bold', y=0.99)
            # Use manual spacing (tight_layout can shrink axes in dense grids)
            fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.94, wspace=0.06, hspace=0.10)
            
            return fig
            
        except Exception as e:
            logger.warning(f"Error drawing shape for {model_name}: {e}")
            import traceback
            logger.warning(traceback.format_exc())
            return None
    
    def onExport(self):
        """
        Handle export button click
        Saves three files to the selected folder:
        1. JSON file (user-selected filename)
        2. PDF file (auto-named based on JSON filename)
        3. Project file (auto-named based on JSON filename)
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
            message = f"All files exported successfully:\n\n"
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
            if not hasattr(gui_manager, 'filesWidget'):
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
                if guinier.rg is not None:
                    guinier_data["Rg"] = f"{guinier.rg} nm"
                if guinier.rg_error is not None:
                    guinier_data["Rg Error"] = f"{guinier.rg_error} nm"
                if guinier.i0 is not None:
                    guinier_data["I(0)"] = str(guinier.i0)
                if guinier.range_start is not None and guinier.range_end is not None:
                    guinier_data["Q Range"] = f"{guinier.range_start} - {guinier.range_end}"
                
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
            from sas.qtgui.Perspectives.Fitting.ReportPageLogic import ReportPageLogic
            import sas.qtgui.Utilities.GuiUtils as GuiUtils
            from sas.qtgui.Perspectives.Fitting import FittingUtilities
            
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
                        from sasdata.dataloader.loader import Loader
                        import matplotlib.pyplot as plt
                        import numpy as np
                        
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
            import sas.qtgui.Utilities.GuiUtils as GuiUtils
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
                                        logger.info(f"  Matched by data ID in residual ID")
                                        residual_plots.append(plotter.figure)
                                        break
                                    
                                    # Fallback: check by name pattern
                                    if residual_name and "Residual" in residual_name:
                                        if (modelname in residual_name or 
                                            (data_name and data_name in residual_name)):
                                            logger.info(f"  Matched by name pattern")
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
        """
        Try to get a matplotlib figure of the model 3D shape from the Fit tab
        
        :return: matplotlib.figure.Figure or None
        """
        try:
            # First, try to get the pixmap directly from the label in the Fit tab
            if hasattr(self, 'lblShapeImage'):
                pixmap = self.lblShapeImage.pixmap()
                if pixmap and not pixmap.isNull():
                    # Convert QPixmap to matplotlib figure
                    from matplotlib.figure import Figure
                    from matplotlib.backends.backend_agg import FigureCanvasAgg
                    import numpy as np
                    
                    # Convert QPixmap to bytes, then load with PIL/matplotlib
                    from io import BytesIO
                    buffer = QtCore.QBuffer()
                    buffer.open(QtCore.QBuffer.OpenModeFlag.ReadWrite)
                    pixmap.save(buffer, "PNG")
                    byte_data = buffer.data()
                    buffer.close()
                    
                    # Load image from bytes using PIL
                    try:
                        from PIL import Image
                        pil_image = Image.open(BytesIO(byte_data))
                        rgb_array = np.array(pil_image)
                    except ImportError:
                        # Fallback: convert QImage directly
                        qimage = pixmap.toImage()
                        qimage = qimage.convertToFormat(QtGui.QImage.Format.Format_RGB32)
                        width = qimage.width()
                        height = qimage.height()
                        byte_array = qimage.bits().tobytes()
                        # Use frombuffer (correct spelling: from + buffer)
                        arr = np.frombuffer(byte_array, dtype=np.uint8).reshape(height, width, 4)
                        rgb_array = arr[:, :, [2, 1, 0]]
                    
                    # Create matplotlib figure
                    fig = Figure(figsize=(10, 6.67))  # Maintain aspect ratio
                    canvas = FigureCanvasAgg(fig)
                    ax = fig.add_subplot(111)
                    ax.imshow(rgb_array)
                    ax.axis('off')
                    
                    # Get model name for title if available
                    model_name = ""
                    if hasattr(self, 'txtModelName') and self.txtModelName.text():
                        model_name = self.txtModelName.text()
                    elif self.export_data.samples:
                        sample = self.export_data.samples[0]
                        if sample.fits and sample.fits[0].models:
                            model_name = sample.fits[0].models[0].software_or_db or ""
                    
                    if model_name:
                        ax.set_title(f"Shape Visualization: {model_name}", fontsize=12, pad=10)
                    else:
                        ax.set_title("Shape Visualization", fontsize=12, pad=10)
                    
                    fig.tight_layout()
                    return fig
            
            # Fallback: Try to generate shape visualization from model data using built-in rendering
            if not self.export_data.samples:
                return None
            
            sample = self.export_data.samples[0]
            if not sample.fits:
                return None
            
            # Look for model with visualization params
            for fit in sample.fits:
                if fit.models:
                    for model in fit.models:
                        # Get model name from software_or_db or model_data
                        model_name = model.software_or_db or ""
                        if not model_name and model.model_data:
                            # Try to extract model name from model_data
                            import json
                            try:
                                model_data_dict = json.loads(model.model_data)
                                model_name = model_data_dict.get('name', '')
                            except:
                                pass
                        
                        if model_name:
                            # Generate visualization using built-in matplotlib rendering
                            viz_params = getattr(model, 'visualization_params', None)
                            return self._generateModelShapeFigure(model_name, viz_params)
            
            return None
        except Exception as e:
            logger.warning(f"Error getting model shape figure: {e}")
            return None

