"""
SASBDB Export Dialog

This dialog allows users to review and edit SASBDB export data before exporting.
"""
import logging
import os
from typing import Optional

from PySide6 import QtCore, QtWidgets

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
        self.cmdClose.clicked.connect(self.close)
        self.chkPublished.toggled.connect(self.onPublishedToggled)
        
        # Populate UI with data
        self.populateFromData()
        
        # Set up initial state
        self.onPublishedToggled(self.chkPublished.isChecked())
    
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
                    self.txtCorMapPValue.setText(str(fit.cormap_pvalue))
                
                # Model section (use first model if available)
                if fit.models:
                    model = fit.models[0]
                    if model.software_or_db:
                        self.txtModelName.setText(model.software_or_db)
                    if model.comment:
                        self.txtModelComment.setPlainText(model.comment)
                    
                    # Format parameters if available
                    # Parameters are stored as a formatted string in comment or log
                    # We'll extract them from the model if available
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
        model_comment = self.txtModelComment.toPlainText().strip()
        
        if model_name or model_parameters or model_comment:
            model = SASBDBModel()
            if model_name:
                model.software_or_db = model_name
            if model_parameters:
                # Store parameters in log field
                model.log = model_parameters
            if model_comment:
                model.comment = model_comment
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

