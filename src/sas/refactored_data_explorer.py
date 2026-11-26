import logging
import os.path
from collections.abc import Iterator

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

from sasdata.data import SasData
from sasdata.data_io.importer import Importer
from sasdata.data_io.importers import AsciiImporter

from sas.ascii_dialog.dialog import AsciiDialog
from sas.data_explorer_drop_hint import DropHint
from sas.data_explorer_error_message import DataExplorerRemoveMessage
from sas.data_explorer_tree import DataExplorerTree
from sas.data_manager import NewDataManager as DataManager
from sas.dummy_perspective import DummyPerspective
from sas.qtgui.Perspectives.Inversion.InversionWidget import InversionWidget
from sas.qtgui.Utilities.MuMag.MuMag import MuMag
from sas.refactored import Perspective, TrackedPlot

# TODO: Eventually, the values (should) never be None.
# FIXME: Linter is complaining about DummyPew
perspectives: dict[str, None | Perspective] = {
    "Corfunc": None,
    "Fitting": None,
    "Invariant": None,
    "Inversion": InversionWidget,
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
        self.filter_buttons: dict[str, QPushButton] = {name: QPushButton(name, self) for name in filter_names}
        for widget in self.filter_buttons.values():
            widget.setCheckable(True)
            self.filter_row.addWidget(widget)

        # TODO: I suspect this may end up being a separate widget. For now, just
        # use an empty tree view.
        self.tree_view = DataExplorerTree(self._data_manager, self)
        self.tree_view.current_datum_removed.connect(self.onRemove)
        self.tree_view.load_requested.connect(self.onLoadFile)

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
        self.plot_button.setToolTip("Plot the selected data.")
        self.plot_button.clicked.connect(self.onPlot)

        self.final_row.addWidget(self.remove_button)
        self.final_row.addWidget(self.plot_button)

        self.layout.addLayout(self.add_data_row)
        self.layout.addWidget(self.filter_label)
        self.layout.addLayout(self.filter_row)
        self.layout.addWidget(self.tree_stack)
        self.layout.addLayout(self.final_row)

    @Slot()
    def updateDropHint(self):
        empty = self.tree_view.dataItemCount() == 0
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
            box = DataExplorerRemoveMessage(self, errors)
            box.show()

    @Slot()
    def onPlot(self):
        to_plot = self.tree_view.currentTrackedDatum
        if isinstance(to_plot, SasData):
            plot_object = TrackedPlot(self._data_manager)
            self._data_manager.add_data(plot_object)
            self._data_manager.make_association(plot_object, to_plot)
            plot_object.update_plot()
        else:
            QMessageBox.critical(
                self, "Plotting Error", "The selected item is not a data object. Only data objects can be plotted."
            )

    @Slot()
    def onLoadFile(self):
        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "Open Data File",
        )
        self.loadPaths(filenames)

    @Slot()
    def onLoadFolder(self):
        folder = QFileDialog.getExistingDirectory(self, "Open Data Folder")
        if folder:
            self.loadPaths([folder])

    def loadPaths(self, paths: list[str]):
        """Load files and folders into the data manager. Anything that can't be
        loaded is reported together at the end."""
        if len(paths) == 0:
            return
        clean_paths = self._get_files_from_directories(paths)
        measurements, failures = Importer().import_data(clean_paths)
        for measurement in measurements:
            self._data_manager.add_data(measurement)

        if failures:
            QMessageBox.critical(
                self,
                "Data Loading Error",
                "The following files could not be loaded:\n\n" + "\n".join(failures),
            )
            logging.warning("The following files could not be loaded: " + "; ".join(failures))

    @staticmethod
    def _get_files_from_directories(paths):
        new_paths = []
        for path in paths:
            if os.path.isdir(path):
                with os.scandir(paths[0]) as entries:
                    new_paths.append(
                        sorted(entry.path for entry in entries if entry.is_file() and not entry.name.startswith(".")))
            elif os.path.isfile(path):
                new_paths.append(path)
        return new_paths

    @staticmethod
    def _droppedPaths(event: QDragEnterEvent | QDragMoveEvent | QDropEvent) -> Iterator[str]:
        """Local files and folders in a drag. Nothing is checked or opened here;
        whatever the user drops is attempted, and problems are reported on load."""
        for url in event.mimeData().urls():
            if path := url.toLocalFile():
                yield path

    @classmethod
    def _hasDroppablePaths(cls, event: QDragEnterEvent | QDragMoveEvent) -> bool:
        return any(cls._droppedPaths(event))

    def dragEnterEvent(self, event: QDragEnterEvent):
        # Accept any drag carrying local files or folders. Only drags without
        # any (e.g. text or web links) show the drop isn't allowed.
        if self._hasDroppablePaths(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self._setDropActive(True)
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if self._hasDroppablePaths(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def _setDropActive(self, active: bool):
        self.drop_hint.setActive(active)
        self.tree_view.setDropActive(active)

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self._setDropActive(False)

    def dropEvent(self, event: QDropEvent):
        self._setDropActive(False)
        filenames = list(self._droppedPaths(event))
        if not filenames:
            event.ignore()
            return
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()
        self.loadPaths(filenames)

    @Slot()
    def onAdvancedLoad(self):
        dialog = AsciiDialog()
        status = dialog.exec()
        if status == 1:
            try:
                loaded = AsciiImporter(params=dialog.params).load_data()
            except Exception as err:
                # A number of errors can be thrown here, a few examples include:
                #    TypeError: thrown when the ascii loader doesn't recognize the file
                #    FileNotFoundError: the file wasn't accessible
                #    ValueError: Unlikely, but could happen during loading on float() conversion
                logging.error(err)
                loaded = {}
            for datum in loaded.values():
                self._data_manager.add_data(datum)
