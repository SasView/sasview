import logging
from os.path import basename

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sasdata.temp_ascii_reader import load_data as load_advanced_ascii_data
from sasdata.temp_ascii_reader import load_data_default_params as load_ascii_data
from sasdata.temp_hdf5_reader import load_data as load_hdf5_data
from sasdata.temp_xml_reader import load_data as load_xml_data

from sas.ascii_dialog.dialog import AsciiDialog
from sas.data_explorer_error_message import DataExplorerErrorMessage
from sas.data_explorer_tree import DataExplorerTree
from sas.data_manager import NewDataManager as DataManager
from sas.dummy_perspective import DummyPerspective
from sas.refactored import Perspective

# TODO: Eventually, the values (should) never be None.
# FIXME: Linter is complaining about DummyPew
perspectives: dict[str, None | Perspective] = {
    "Corfunc": None,
    "Fitting": None,
    "Invariant": None,
    "Inversion": None,
    "Dummy": DummyPerspective,
    "Mumag": None,
}


# TODO: Just using the word 'new' to avoid conflicts. The final version
# shouldn't have that name.
class NewDataExplorer(QWidget):
    new_perspective = Signal(object)

    def __init__(self, data_manager: DataManager, parent: QWidget | None = ...) -> None:
        super().__init__(parent)
        self._data_manager = data_manager

        self.layout = QVBoxLayout(self)

        self.add_data_row = QHBoxLayout(self)

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

        self.filter_row = QHBoxLayout(self)
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

        # TODO: Is there a better name for this?
        self.final_row = QHBoxLayout(self)

        self.remove_button = QPushButton("Remove", self)
        self.remove_button.setToolTip("Remove the selected data from SasView")
        self.remove_button.clicked.connect(self.onRemove)
        self.plot_button = QPushButton("Plot", self)

        self.final_row.addWidget(self.remove_button)
        self.final_row.addWidget(self.plot_button)

        self.layout.addLayout(self.add_data_row)
        self.layout.addWidget(self.filter_label)
        self.layout.addLayout(self.filter_row)
        self.layout.addWidget(self.tree_view)
        self.layout.addLayout(self.final_row)

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
        if len(filenames) == 0:
            return
        for filename in filenames:
            # FIXME: This would probably break if there isn't an extension.

            # TODO: The logic for deciding which reader to use is temporary. It
            # won't work for all file extensions, and ultimately this logic probably
            # needs to be moved in sasdata.
            file_extension = filename.split(".")[-1].lower()
            match file_extension:
                case "xml":
                    loaded_data = load_xml_data(filename)
                case "h5" | "hdf":
                    loaded_data = load_hdf5_data(filename)
                case "txt" | "csv":
                    data_list = load_ascii_data(filename)
                    # Since we're only giving the load function one filename, we can
                    # assume only one data object is being loaded.
                    loaded_data = dict([(basename(filename), data_list[0])])
                case _:
                    QMessageBox.critical(
                        self,
                        "Data Loading Error",
                        f"Error loading {filename}. Extension not recognised.",
                    )
                    return

            for _, datum in loaded_data.items():
                self._data_manager.add_data(datum)

    @Slot()
    def onAdvancedLoad(self):
        dialog = AsciiDialog()
        status = dialog.exec()
        if status == 1:
            loaded = load_advanced_ascii_data(dialog.params)
            for datum in loaded:
                self._data_manager.add_data(datum)
