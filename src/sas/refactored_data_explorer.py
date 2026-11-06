import logging
import os
from collections.abc import Callable, Iterator
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


def _load_ascii(filename: str) -> dict:
    # Since we're only giving the load function one filename, we can assume only
    # one data object is being loaded.
    return {basename(filename): load_ascii_data(filename)[0]}


# TODO: The logic for deciding which reader to use is temporary. It won't work
# for all file extensions, and ultimately this logic probably needs to be moved
# into sasdata.
# The file formats SasView can load: name -> (extensions, loader). The file
# dialog filters and drag and drop are both derived from this, so only files
# with these extensions can be picked or dropped.
SUPPORTED_FORMATS: dict[str, tuple[tuple[str, ...], Callable[[str], dict]]] = {
    "XML": ((".xml",), load_xml_data),
    "HDF5": ((".h5", ".hdf"), load_hdf5_data),
    "ASCII": ((".txt", ".csv"), _load_ascii),
}


def _loaders_by_extension() -> dict[str, Callable[[str], dict]]:
    loaders = {}
    for extensions, loader in SUPPORTED_FORMATS.values():
        for extension in extensions:
            loaders[extension] = loader
    return loaders


_LOADERS = _loaders_by_extension()


def _loader_for(filename: str) -> Callable[[str], dict] | None:
    return _LOADERS.get(os.path.splitext(filename)[1].lower())


def _file_dialog_filters() -> str:
    def patterns(extensions) -> str:
        return " ".join(f"*{ext}" for ext in extensions)

    filters = [f"All supported files ({patterns(_LOADERS)})"]
    for name, (extensions, _) in SUPPORTED_FORMATS.items():
        filters.append(f"{name} files ({patterns(extensions)})")
    return ";;".join(filters)


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
        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "Open Data File",
            filter=_file_dialog_filters(),
        )
        self.loadFiles(filenames)

    def loadFiles(self, filenames: list[str]):
        """Load each file into the data manager. Files in an unsupported format
        are skipped; files that fail to load are skipped and reported together
        at the end."""
        failures: list[str] = []
        for filename in filenames:
            loader = _loader_for(filename)
            if loader is None:
                continue
            try:
                loaded_data = loader(filename)
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
    def _droppedFiles(event: QDragEnterEvent | QDragMoveEvent | QDropEvent) -> Iterator[str]:
        """Local files in a supported format in a drag, with folders expanded
        to the files directly inside them (not recursive)."""
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if not path:
                continue
            if os.path.isdir(path):
                candidates = (os.path.join(path, name) for name in sorted(os.listdir(path)))
            else:
                candidates = (path,)
            for candidate in candidates:
                if _loader_for(candidate) is not None and os.path.isfile(candidate):
                    yield candidate

    @classmethod
    def _hasSupportedFiles(cls, event: QDragEnterEvent | QDragMoveEvent) -> bool:
        return any(cls._droppedFiles(event))

    def dragEnterEvent(self, event: QDragEnterEvent):
        # Only accept drags carrying something we can load, so the cursor shows
        # the drop isn't allowed otherwise.
        if self._hasSupportedFiles(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            self.drop_hint.setActive(True)
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if self._hasSupportedFiles(event):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.drop_hint.setActive(False)

    def dropEvent(self, event: QDropEvent):
        self.drop_hint.setActive(False)
        filenames = list(self._droppedFiles(event))
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
