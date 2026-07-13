"""
SASBDB Dataset Download Dialog.
"""

import logging
import os
import tempfile

from PySide6 import QtWidgets

from .sasbdb_api import SASBDBDatasetInfo, downloadDataset, validateDatasetId
from .sasbdb_loader import metadata_summary
from .UI.SASBDBDownloadDialogUI import Ui_SASBDBDownloadDialogUI

logger = logging.getLogger(__name__)


class SASBDBDownloadDialog(QtWidgets.QDialog, Ui_SASBDBDownloadDialogUI):
    """Dialog for downloading datasets from SASBDB."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.downloaded_filepath: str | None = None
        self.dataset_info: SASBDBDatasetInfo | None = None

        self.cmdDownload.clicked.connect(self.onDownload)
        self.cmdCancel.clicked.connect(self.reject)
        self.cmdHelp.clicked.connect(self.onHelp)
        self.txtDatasetId.returnPressed.connect(self.onDownload)
        self.txtDatasetId.setFocus()

    def onDownload(self):
        dataset_id = self.txtDatasetId.text().strip()
        if not dataset_id:
            self._showError("Please enter a dataset identifier.")
            return

        normalized_id, validation_error = validateDatasetId(dataset_id)
        if validation_error:
            self._showError(validation_error)
            return

        self._set_busy(True)
        self.lblStatus.setText("Downloading dataset...")

        try:
            filepath, dataset_info = downloadDataset(normalized_id, tempfile.gettempdir())
            self.dataset_info = dataset_info

            if filepath and os.path.exists(filepath):
                self.downloaded_filepath = filepath
                summary = metadata_summary(dataset_info) if dataset_info else ""
                status = f"Successfully downloaded dataset {normalized_id}"
                if summary:
                    status += f"\n{summary}"
                self.lblStatus.setText(status)
                self.accept()
            else:
                self._showError(
                    f"Failed to download dataset {normalized_id}.\n"
                    "Please check the dataset identifier and try again."
                )
        except Exception as e:
            logger.error(f"Error downloading dataset {normalized_id}: {e}", exc_info=True)
            self._showError(f"Error downloading dataset:\n{e}")
        finally:
            self._set_busy(False)

    def _set_busy(self, busy: bool):
        self.cmdDownload.setEnabled(not busy)
        self.cmdCancel.setEnabled(not busy)
        self.progressBar.setVisible(busy)
        if busy:
            self.progressBar.setRange(0, 0)
            QtWidgets.QApplication.processEvents()

    def _showError(self, message: str):
        self.lblStatus.setText(f"<span style='color: red;'>{message}</span>")
        QtWidgets.QMessageBox.warning(self, "Download Error", message)

    def getDownloadedFilepath(self) -> str | None:
        return self.downloaded_filepath

    def getDatasetInfo(self) -> SASBDBDatasetInfo | None:
        return self.dataset_info

    def onHelp(self):
        from sas.qtgui.Utilities import GuiUtils
        GuiUtils.showHelp("user/qtgui/Utilities/SASBDB/sasbdb_download_help.html")
