from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTreeView, QVBoxLayout, QWidget

# TODO: Just using the word 'new' to avoid conflicts. The final version
# shouldn't have that name.
class NewDataExplorer(QWidget):
    def __init__(self, parent: QWidget | None = ...) -> None:
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        self.add_data_row = QHBoxLayout(self)

        self.load_data_row = QPushButton("Load Data", self)
        self.add_perspective = QPushButton("+ New Perspective", self)

        self.add_data_row.addWidget(self.load_data_row)
        self.add_data_row.addWidget(self.add_perspective)

        self.filter_row = QHBoxLayout(self)
        filter_names = ['Data', 'Perspective', 'Theory', 'Plot']
        self.filter_buttons: dict[str, QPushButton] = {name: QPushButton(name, self) for name in filter_names}
        for widget in self.filter_buttons.values():
            widget.setCheckable(True)
            self.filter_row.addWidget(widget)

        # TODO: I suspect this may end up being a separate widget. For now, just
        # use an empty tree view.
        self.tree_view = QTreeView()

        # TODO: Is there a better name for this?
        self.final_row = QHBoxLayout(self)

        self.remove_button = QPushButton('Remove', self)
        self.remove_button.setToolTip('Remove the selected data from SasView')
        self.plot_button = QPushButton('Plot', self)

        self.final_row.addWidget(self.remove_button)
        self.final_row.addWidget(self.plot_button)


        self.layout.addLayout(self.add_data_row)
        self.layout.addLayout(self.filter_row)
        self.layout.addWidget(self.tree_view)
        self.layout.addLayout(self.final_row)
