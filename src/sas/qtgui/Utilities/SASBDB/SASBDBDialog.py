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
            # Try to import sasmodels shape visualizer
            from sasmodels.shape_visualizer import generate_shape_image, SASModelsLoader, SASModelsShapeDetector
            
            # Normalize model name (remove any path or module prefixes)
            normalized_name = model_name
            if '.' in normalized_name:
                # Extract just the model name if it's a module path
                normalized_name = normalized_name.split('.')[-1]
            
            # Load model info - try both original and normalized names
            model_info = SASModelsLoader.load_model_info(normalized_name)
            if model_info is None and normalized_name != model_name:
                # Try original name if normalized didn't work
                model_info = SASModelsLoader.load_model_info(model_name)
            
            if model_info is None:
                if hasattr(self, 'lblShapeImage'):
                    self.lblShapeImage.setText(f"Model '{model_name}' not found in sasmodels")
                return
            
            # Check if model supports visualization
            visualizer = SASModelsShapeDetector.create_visualizer(model_info)
            if visualizer is None:
                if hasattr(self, 'lblShapeImage'):
                    self.lblShapeImage.setText(f"Model '{normalized_name}' does not support shape visualization")
                return
            
            # Generate visualization image
            # Use visualization params if available, otherwise use defaults
            params = viz_params if viz_params else None
            
            # Generate image as BytesIO - use normalized name
            image_buffer = generate_shape_image(
                normalized_name, 
                params=params, 
                output_file=None,
                show_cross_sections=True,  # Include cross-section views
                show_wireframe=False
            )
            
            if image_buffer:
                # Convert BytesIO to QPixmap
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(image_buffer.getvalue())
                
                # Display the image at a good size
                if hasattr(self, 'lblShapeImage'):
                    # Scale to fit the available space while maintaining aspect ratio
                    # With cross-sections, the image is larger (16x10 inches at 300 DPI = 4800x3000 pixels)
                    # Scale it down to fit the 600x400 minimum size label
                    target_width = 580
                    target_height = int(target_width * pixmap.height() / pixmap.width()) if pixmap.width() > 0 else 380
                    # Ensure it fits within the label bounds
                    if target_height > 380:
                        target_height = 380
                        target_width = int(target_height * pixmap.width() / pixmap.height()) if pixmap.height() > 0 else 580
                    
                    target_size = QtCore.QSize(target_width, target_height)
                    
                    scaled_pixmap = pixmap.scaled(
                        target_size,
                        QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                        QtCore.Qt.TransformationMode.SmoothTransformation
                    )
                    self.lblShapeImage.setPixmap(scaled_pixmap)
                    self.lblShapeImage.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            else:
                if hasattr(self, 'lblShapeImage'):
                    self.lblShapeImage.setText(f"Failed to generate visualization for '{model_name}'")
                    
        except ImportError:
            logger.warning("sasmodels.shape_visualizer not available")
            if hasattr(self, 'lblShapeImage'):
                self.lblShapeImage.setText("Shape visualization not available\n(sasmodels not installed)")
        except Exception as e:
            logger.warning(f"Error generating model visualization: {e}")
            if hasattr(self, 'lblShapeImage'):
                self.lblShapeImage.setText(f"Error generating visualization:\n{str(e)[:50]}")
    
    def onExport(self):
        """
        Handle export button click
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
        filename = filename_tuple[0]
        if not filename:
            return
        
        # Update save location
        self.save_location = os.path.dirname(filename)
        ObjectLibrary.addObject('SASBDBDialog_directory', self.save_location)
        
        # Ensure .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        # Export
        exporter = SASBDBExporter(export_data)
        success = exporter.export_to_json(filename)
        
        if success:
            QtWidgets.QMessageBox.information(
                self,
                "Export Successful",
                f"SASBDB data exported to:\n{filename}"
            )
            self.close()
        else:
            QtWidgets.QMessageBox.critical(
                self,
                "Export Failed",
                "Failed to export SASBDB data. Please check the logs for details."
            )
    
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
            
            # Fallback: Try to generate shape visualization from model data
            if not self.export_data.samples:
                return None
            
            sample = self.export_data.samples[0]
            if not sample.fits:
                return None
            
            # Look for model with visualization params
            for fit in sample.fits:
                if fit.models:
                    for model in fit.models:
                        if hasattr(model, 'visualization_params') and model.visualization_params:
                            # Try to generate shape visualization
                            try:
                                import sys
                                import os
                                # Add parent directory to path to access sasmodels
                                parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
                                if parent_dir not in sys.path:
                                    sys.path.insert(0, parent_dir)
                                
                                from sasmodels.shape_visualizer import generate_shape_image
                                from matplotlib.figure import Figure
                                from matplotlib.backends.backend_agg import FigureCanvasAgg
                                import numpy as np
                                
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
                                
                                if not model_name:
                                    return None
                                
                                # Generate shape image
                                fig = Figure(figsize=(8, 6))
                                canvas = FigureCanvasAgg(fig)
                                
                                # Generate the shape visualization
                                img_array = generate_shape_image(
                                    model_name=model_name,
                                    params=model.visualization_params,
                                    show_cross_sections=True
                                )
                                
                                if img_array is not None:
                                    ax = fig.add_subplot(111)
                                    ax.imshow(img_array)
                                    ax.axis('off')
                                    ax.set_title(f"Shape Visualization: {model_name}", fontsize=12)
                                    fig.tight_layout()
                                    return fig
                            except Exception as e:
                                logger.warning(f"Could not generate model shape visualization: {e}")
                                return None
            
            return None
        except Exception as e:
            logger.warning(f"Error getting model shape figure: {e}")
            return None

