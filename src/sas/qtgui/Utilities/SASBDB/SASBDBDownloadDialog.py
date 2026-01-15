"""
SASBDB Dataset Download Dialog.

Provides a dialog interface for downloading datasets from SASBDB
and loading them into SasView.
"""

import logging
import os
import tempfile
from typing import Optional

from PySide6 import QtWidgets

from .sasbdb_api import downloadDataset, SASBDBDatasetInfo
from .UI.SASBDBDownloadDialogUI import Ui_SASBDBDownloadDialogUI

logger = logging.getLogger(__name__)


class SASBDBDownloadDialog(QtWidgets.QDialog, Ui_SASBDBDownloadDialogUI):
    """
    Dialog for downloading datasets from SASBDB.
    
    Allows users to enter a SASBDB dataset identifier, downloads
    the dataset, and loads it into SasView.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the download dialog.
        
        :param parent: Parent widget
        """
        super().__init__(parent)
        self.setupUi(self)
        
        # Store downloaded file path and metadata
        self.downloaded_filepath: Optional[str] = None
        self.dataset_info: Optional[SASBDBDatasetInfo] = None
        
        # Connect signals
        self.cmdDownload.clicked.connect(self.onDownload)
        self.cmdCancel.clicked.connect(self.reject)
        self.cmdHelp.clicked.connect(self.onHelp)
        self.txtDatasetId.returnPressed.connect(self.onDownload)
        
        # Set focus on dataset ID input
        self.txtDatasetId.setFocus()
    
    def onDownload(self):
        """
        Handle download button click.
        
        Validates the dataset ID, downloads the dataset,
        and loads it into SasView.
        """
        dataset_id = self.txtDatasetId.text().strip()
        
        if not dataset_id:
            self._showError("Please enter a dataset identifier.")
            return
        
        # Disable download button during download
        self.cmdDownload.setEnabled(False)
        self.cmdCancel.setEnabled(False)
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 0)  # Indeterminate progress
        self.lblStatus.setText("Downloading dataset...")
        QtWidgets.QApplication.processEvents()
        
        try:
            # Download the dataset
            output_dir = tempfile.gettempdir()
            filepath, dataset_info = downloadDataset(dataset_id, output_dir)
            
            # Store the metadata
            self.dataset_info = dataset_info
            
            if filepath and os.path.exists(filepath):
                self.downloaded_filepath = filepath
                
                # Build success message with metadata summary
                success_msg = f"Successfully downloaded dataset {dataset_id}"
                if dataset_info:
                    details = self._formatMetadataSummary(dataset_info)
                    if details:
                        success_msg += f"\n{details}"
                
                self.lblStatus.setText(success_msg)
                self.progressBar.setVisible(False)
                
                # Log detailed metadata
                if dataset_info:
                    self._logMetadata(dataset_info)
                
                self.accept()  # Close dialog and return success
            else:
                self._showError(f"Failed to download dataset {dataset_id}.\n"
                              "Please check the dataset identifier and try again.")
                self.progressBar.setVisible(False)
                self.cmdDownload.setEnabled(True)
                self.cmdCancel.setEnabled(True)
                
        except Exception as e:
            logger.error(f"Error downloading dataset {dataset_id}: {e}", exc_info=True)
            self._showError(f"Error downloading dataset:\n{str(e)}")
            self.progressBar.setVisible(False)
            self.cmdDownload.setEnabled(True)
            self.cmdCancel.setEnabled(True)
    
    def _formatMetadataSummary(self, info: SASBDBDatasetInfo) -> str:
        """
        Format a brief summary of the dataset metadata.
        
        :param info: Parsed dataset info
        :return: Formatted summary string
        """
        parts = []
        
        if info.title:
            parts.append(f"Title: {info.title}")
        if info.sample_name:
            parts.append(f"Sample: {info.sample_name}")
        if info.rg is not None:
            rg_str = f"Rg: {info.rg:.2f}"
            if info.rg_error:
                rg_str += f" ± {info.rg_error:.2f}"
            rg_str += " Å"
            parts.append(rg_str)
        if info.molecular_weight is not None:
            parts.append(f"MW: {info.molecular_weight:.1f} kDa")
        
        return "\n".join(parts)
    
    def _logMetadata(self, info: SASBDBDatasetInfo):
        """
        Log detailed metadata information.
        
        :param info: Parsed dataset info
        """
        logger.info(f"SASBDB Dataset: {info.code or info.entry_id}")
        if info.title:
            logger.info(f"  Title: {info.title}")
        if info.sample_name:
            logger.info(f"  Sample: {info.sample_name}")
        if info.molecule_name:
            logger.info(f"  Molecule: {info.molecule_name}")
        if info.concentration:
            logger.info(f"  Concentration: {info.concentration} {info.concentration_unit}")
        if info.buffer_description:
            logger.info(f"  Buffer: {info.buffer_description}")
        if info.instrument:
            logger.info(f"  Instrument: {info.instrument}")
        if info.wavelength:
            logger.info(f"  Wavelength: {info.wavelength} {info.wavelength_unit}")
        if info.temperature:
            logger.info(f"  Temperature: {info.temperature} {info.temperature_unit}")
        if info.rg is not None:
            logger.info(f"  Rg: {info.rg} ± {info.rg_error or 0} Å")
        if info.i0 is not None:
            logger.info(f"  I(0): {info.i0} ± {info.i0_error or 0}")
        if info.dmax is not None:
            logger.info(f"  Dmax: {info.dmax} Å")
        if info.molecular_weight is not None:
            logger.info(f"  MW: {info.molecular_weight} kDa")
        if info.publication_doi:
            logger.info(f"  DOI: {info.publication_doi}")
    
    def _showError(self, message: str):
        """
        Display an error message to the user.
        
        :param message: Error message to display
        """
        self.lblStatus.setText(f"<span style='color: red;'>{message}</span>")
        QtWidgets.QMessageBox.warning(self, "Download Error", message)
    
    def getDownloadedFilepath(self) -> Optional[str]:
        """
        Get the path to the downloaded file.
        
        :return: Path to downloaded file, or None if download failed
        """
        return self.downloaded_filepath
    
    def getDatasetInfo(self) -> Optional[SASBDBDatasetInfo]:
        """
        Get the parsed dataset metadata.
        
        :return: SASBDBDatasetInfo object, or None if metadata not available
        """
        return self.dataset_info
    
    def onHelp(self):
        """
        Show the SASBDB download help documentation.
        """
        from sas.qtgui.Utilities import GuiUtils
        help_location = "user/qtgui/Utilities/SASBDB/sasbdb_download_help.html"
        try:
            # Try to get guiManager from parent workspace
            parent = self.parent()
            if parent:
                # Check if parent has guiManager attribute
                if hasattr(parent, 'guiManager') and hasattr(parent.guiManager, 'showHelp'):
                    parent.guiManager.showHelp(help_location)
                    return
                # Check if parent itself has showHelp
                elif hasattr(parent, 'showHelp'):
                    parent.showHelp(help_location)
                    return
            
            # Fallback to GuiUtils
            GuiUtils.showHelp(help_location)
        except Exception as e:
            logger.warning(f"Could not display help: {e}")
            # Final fallback to GuiUtils
            try:
                GuiUtils.showHelp(help_location)
            except Exception as e2:
                logger.error(f"Failed to display help: {e2}")

