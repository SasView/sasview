import logging
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QTreeView, QVBoxLayout, QWidget
from sasdata.data import Group, NamedQuantity, SasData
import sasdata.quantities.units as units
import numpy as np

from sas.data_explorer_tree import DataExplorerTree
from sas.dummy_perspective import DummyPerspective
from sas.refactored import Perspective
from sas.data_manager import NewDataManager as DataManager

# TODO: Eventually, the values (should) never be None.
# FIXME: Linter is complaining about DummyPew
perspectives: dict[str, None | Perspective] = {
    'Corfunc': None,
    'Fitting': None,
    'Invariant': None,
    'Inversion': None,
    'Dummy': DummyPerspective,
    'Mumag': None
}

# TODO: Just using the word 'new' to avoid conflicts. The final version
# shouldn't have that name.
class NewDataExplorer(QWidget):

    new_perspective: Signal = Signal(QDialog)
    removed_perspective: Signal = Signal(QDialog)

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
        self.add_perspective_button.addItem('+ New Perspectives')
        for p in perspectives.keys():
            self.add_perspective_button.addItem(p)
        self.add_perspective_button.currentTextChanged.connect(self.add_perspective)

        self.add_data_row.addWidget(self.load_data_row)
        self.add_data_row.addWidget(self.add_perspective_button)

        self.filter_label = QLabel('Filters')

        self.filter_row = QHBoxLayout(self)
        filter_names = ['Data', 'Perspective', 'Theory', 'Plot']
        self.filter_buttons: dict[str, QPushButton] = {name: QPushButton(name, self) for name in filter_names}
        for widget in self.filter_buttons.values():
            widget.setCheckable(True)
            self.filter_row.addWidget(widget)

        # TODO: I suspect this may end up being a separate widget. For now, just
        # use an empty tree view.
        self.tree_view = DataExplorerTree(self._data_manager, self)
        self.tree_view.current_datum_removed.connect(self.onRemove)

        # TODO: Is there a better name for this?
        self.final_row = QHBoxLayout(self)

        self.remove_button = QPushButton('Remove', self)
        self.remove_button.setToolTip('Remove the selected data from SasView')
        self.remove_button.clicked.connect(self.onRemove)
        self.plot_button = QPushButton('Plot', self)

        self.final_row.addWidget(self.remove_button)
        self.final_row.addWidget(self.plot_button)


        self.layout.addLayout(self.add_data_row)
        self.layout.addWidget(self.filter_label)
        self.layout.addLayout(self.filter_row)
        self.layout.addWidget(self.tree_view)
        self.layout.addLayout(self.final_row)

    @Slot()
    def add_perspective(self):
        # This is here because, when we reset the index to 0, this evert gets
        # triggered again which we don't want.
        if self.add_perspective_button.currentIndex() == 0:
            return
        to_add = self.add_perspective_button.currentText()
        # TODO: Placeholder
        new_perspective_dialog = perspectives[to_add](self._data_manager)
        self._data_manager.add_data(new_perspective_dialog)
        self.new_perspective.emit(new_perspective_dialog)
        logging.info(to_add)
        self.add_perspective_button.setCurrentIndex(0)

    @Slot()
    def onRemove(self):
        to_remove = self.tree_view.currentTrackedDatum
        # We need to try to remove this from the data manager because there is a
        # chance that operation may fail if we violate one of the association
        # rules.
        self._data_manager.remove_data(to_remove)
        if isinstance(to_remove, Perspective):
            self.removed_perspective.emit(to_remove)

    @Slot()
    def onLoadFile(self):
        # TODO: At the moment, the readers are not hooked up properly. Just create some random dummy data for now.
        quantities: list[NamedQuantity] = []
        for column in ['Q', 'I']:
            quantities.append(NamedQuantity(column, 100 * np.random.rand(100),  units.angstroms))
        dummy = SasData('Dummy Data', quantities, Group('root', {}))
        self._data_manager.add_data(dummy)
