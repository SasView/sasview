import logging
import os
from os.path import basename

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from sasdata.data_io.importers.import_ascii import load_data as load_advanced_ascii_data
from sasdata.data_io.importers.import_ascii import load_data_default_params as load_ascii_data
from sasdata.data_io.importers.import_hdf5 import load_data as load_hdf5_data
from sasdata.data_io.importers.import_xml import load_data as load_xml_data

from sas.ascii_dialog.dialog import AsciiDialog
from sas.data_explorer_drop_hint import DropHint
from sas.data_explorer_error_message import DataExplorerErrorMessage
from sas.data_explorer_tree import DataExplorerTree
from sas.data_manager import NewDataManager as DataManager
from sas.dummy_perspective import DummyPerspective
from sas.qtgui.Utilities.MuMag.MuMag import MuMag
from sas.refactored import Perspective

# TODO: Eventually, the values (should) never be None.
# FIXME: Linter is complaining about DummyPew
perspectives: dict[str, None | Perspective] = {
    "Corfunc": None,
    "Fitting": None,
    "Invariant": None,
    "Inversion": None,
    "Dummy": DummyPerspective,
    "Mumag": MuMag,
}


# TODO: Just using the word 'new' to avoid conflicts. The final version
# shouldn't have that name.
class NewDataExplorer(QWidget):
    new_perspective = Signal(object)

    def __init__(self, data_manager: DataManager, parent: QWidget | None = ...) -> None:
        super().__init__(parent)
        self._data_manager = data_manager
        # Files dropped anywhere on the explorer (the tree included, since it
        # doesn't accept drops itself) are loaded.
        self.setAcceptDrops(True)

        self.layout = QVBoxLayout(self)

        self.add_data_row = QHBoxLayout()

        self.load_data_row = QPushButton("Load Data", self)
        _ = self.load_data_row.clicked.connect(self.onLoadFile)
        # self.add_perspective = QPushButton("+ New Perspective", self)
        #
        # TODO: This list is temporary. We should have all the perspectives
        # registered somewhere so its easy to add a new one.
        self.add_perspective_button = QComboBox(self)
        self.add_perspective_button.addItem("+ New Perspectives")
        for p in perspectives:
            self.add_perspective_button.addItem(p)
        self.add_perspective_button.currentTextChanged.connect(self.add_perspective)

        self.add_data_row.addWidget(self.load_data_row)
        self.add_data_row.addWidget(self.add_perspective_button)

        self.filter_label = QLabel("Filters")

        self.filter_row = QHBoxLayout()
        filter_names = ["Data", "Perspective", "Theory", "Plot"]
        self.filter_buttons: dict[str, QPushButton] = {
            name: QPushButton(name, self) for name in filter_names
        }
        for widget in self.filter_buttons.values():
            widget.setCheckable(True)
            self.filter_row.addWidget(widget)

        # TODO: I suspect this may end up being a separate widget. For now, just
        # use an empty tree view.
        self.tree_view = DataExplorerTree(self._data_manager, self)
        self.tree_view.current_datum_removed.connect(self.onRemove)

        # While the tree is empty, show a hint that files can be loaded or dropped.
        self.drop_hint = DropHint(self)
        self.drop_hint.load_requested.connect(self.onLoadFile)
        self.tree_stack = QStackedWidget(self)
        self.tree_stack.addWidget(self.drop_hint)
        self.tree_stack.addWidget(self.tree_view)
        self.tree_view.model().rowsInserted.connect(self.updateDropHint)
        self.tree_view.model().rowsRemoved.connect(self.updateDropHint)
        self.tree_view.model().modelReset.connect(self.updateDropHint)

        # TODO: Is there a better name for this?
        self.final_row = QHBoxLayout()

        self.remove_button = QPushButton("Remove", self)
        self.remove_button.setToolTip("Remove the selected data from SasView")
        self.remove_button.clicked.connect(self.onRemove)
        self.plot_button = QPushButton("Plot", self)

        self.final_row.addWidget(self.remove_button)
        self.final_row.addWidget(self.plot_button)

        self.layout.addLayout(self.add_data_row)
        self.layout.addWidget(self.filter_label)
        self.layout.addLayout(self.filter_row)
        self.layout.addWidget(self.tree_stack)
        self.layout.addLayout(self.final_row)

    @Slot()
    def updateDropHint(self):
        empty = self.tree_view.topLevelItemCount() == 0
        self.tree_stack.setCurrentWidget(self.drop_hint if empty else self.tree_view)

    @Slot()
    def add_perspective(self):
        # This is here because, when we reset the index to 0, this event gets
        # triggered again which we don't want.
        if self.add_perspective_button.currentIndex() == 0:
            return
        to_add = self.add_perspective_button.currentText()
        # TODO: temporary fix for errors until perspectives are re-enabled
        if not perspectives[to_add]:
            return
        # TODO: Placeholder
        new_perspective_dialog = perspectives[to_add](self._data_manager)
        self._data_manager.add_data(new_perspective_dialog)
        logging.info(to_add)
        self.add_perspective_button.setCurrentIndex(0)

    @Slot()
    def onRemove(self):
        items_to_remove = self.tree_view.currentTrackedData
        errors: list[ValueError] = []
        for item in items_to_remove:
            # We need to try to remove this from the data manager because there is a
            # chance that operation may fail if we violate one of the association
            # rules.
            try:
                self._data_manager.remove_data(item)
            except ValueError as err:
                errors.append(err)
        if len(errors) > 0:
            box = DataExplorerErrorMessage(self, errors)
            box.show()

    @Slot()
    def onLoadFile(self):
        # TODO: Probably want to add filters.
        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "Open Data File",
        )
        self.loadFiles(filenames)

    def loadFiles(self, filenames: list[str]):
        """Load each file into the data manager. Files that can't be loaded are
        skipped, and all failures are reported together at the end."""
        failures: list[str] = []
        for filename in filenames:
            # TODO: The logic for deciding which reader to use is temporary. It
            # won't work for all file extensions, and ultimately this logic probably
            # needs to be moved in sasdata.
            _, file_extension = os.path.splitext(filename)
            try:
                match file_extension.lower():
                    case ".xml":
                        loaded_data = load_xml_data(filename)
                    case ".h5" | ".hdf":
                        loaded_data = load_hdf5_data(filename)
                    case ".txt" | ".csv":
                        data_list = load_ascii_data(filename)
                        # Since we're only giving the load function one filename, we can
                        # assume only one data object is being loaded.
                        loaded_data = dict([(basename(filename), data_list[0])])
                    case _:
                        failures.append(f"{basename(filename)}: extension not recognised.")
                        continue
            except Exception as err:
                logging.exception(f"Error loading {filename}")
                failures.append(f"{basename(filename)}: {err}")
                continue

            for _, datum in loaded_data.items():
                self._data_manager.add_data(datum)

        if failures:
            QMessageBox.critical(
                self,
                "Data Loading Error",
                "The following files could not be loaded:\n\n" + "\n".join(failures),
            )

    @staticmethod
    def _droppedFiles(event: QDragEnterEvent | QDragMoveEvent | QDropEvent) -> list[str]:
        """Local file paths in a drag, with folders expanded to the files
        directly inside them (not recursive)."""
        if not event.mimeData().hasUrls():
            return []
        filenames: list[str] = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if not path:
                continue
            if os.path.isdir(path):
                filenames += sorted(
                    os.path.join(path, name)
                    for name in os.listdir(path)
                    if os.path.isfile(os.path.join(path, name))
                )
            else:
                filenames.append(path)
        return filenames

    @staticmethod
    def _hasLocalFiles(event: QDragEnterEvent | QDragMoveEvent) -> bool:
        return event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls())

    def dragEnterEvent(self, event: QDragEnterEvent):
        if self._hasLocalFiles(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self.drop_hint.setActive(True)
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if self._hasLocalFiles(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.drop_hint.setActive(False)

    def dropEvent(self, event: QDropEvent):
        self.drop_hint.setActive(False)
        filenames = self._droppedFiles(event)
        if not filenames:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()
        self.loadFiles(filenames)

    @Slot()
    def onAdvancedLoad(self):
        dialog = AsciiDialog()
        status = dialog.exec()
        if status == 1:
            loaded = load_advanced_ascii_data(dialog.params)
            for datum in loaded:
                self._data_manager.add_data(datum)
