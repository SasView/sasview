from sys import argv

from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from sasdata.ascii_reader_metadata import AsciiReaderMetadata

from metadata_filename_gui.metadata_tree_widget import MetadataTreeWidget


def build_font(text: str, classname: str = '') -> str:
    match classname:
        case 'token':
            return f"<font color='red'>{text}</font>"
        case 'separator':
            return f"<font color='grey'>{text}</font>"
        case _:
            return text
    return f'<span class="{classname}">{text}</span>'

class MetadataFilenameDialog(QDialog):
    def __init__(self, filename: str, initial_metadata: AsciiReaderMetadata):
        super().__init__()

        # TODO: Will probably change this default later (or a more sophisticated way of getting this default from the
        # filename.)
        initial_separator_text = initial_metadata.filename_separator[filename]

        self.setWindowTitle('Metadata')

        self.filename = filename
        # Key is the metadatum, value is the component selected for it.
        self.internal_metadata = initial_metadata

        self.filename_line_label = QLabel()
        self.separate_on_group = QButtonGroup()
        self.character_radio = QRadioButton("Character")
        self.separate_on_group.addButton(self.character_radio)
        self.casing_radio = QRadioButton("Casing")
        self.separate_on_group.addButton(self.casing_radio)
        if isinstance(initial_separator_text, str):
            self.character_radio.setChecked(True)
        else: # if bool
            self.casing_radio.setChecked(True)
        self.separate_on_layout = QHBoxLayout()
        self.separate_on_group.buttonToggled.connect(self.update_filename_separation)
        self.separate_on_layout.addWidget(self.filename_line_label)
        self.separate_on_layout.addWidget(self.character_radio)
        self.separate_on_layout.addWidget(self.casing_radio)

        if not any([char.isupper() for char in self.filename]):
            self.casing_radio.setDisabled(True)

        self.seperator_chars_label = QLabel('Seperators')
        if isinstance(initial_separator_text, str):
            self.separator_chars = QLineEdit(initial_separator_text)
        else:
            self.separator_chars = QLineEdit()
        self.separator_chars.textChanged.connect(self.update_filename_separation)

        self.filename_separator_layout = QHBoxLayout()
        self.filename_separator_layout.addWidget(self.seperator_chars_label)
        self.filename_separator_layout.addWidget(self.separator_chars)

        self.metadata_tree = MetadataTreeWidget(self.internal_metadata)

        # Have to update this now because it relies on the value of the separator, and tree.
        self.update_filename_separation()

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.on_save)

        self.layout = QVBoxLayout(self)
        self.layout.addLayout(self.separate_on_layout)
        self.layout.addLayout(self.filename_separator_layout)
        self.layout.addWidget(self.metadata_tree)
        self.layout.addWidget(self.save_button)

    def formatted_filename(self) -> str:
        sep_str = self.separator_chars.text()
        if sep_str == '' or self.casing_radio.isChecked():
            return f'<span>{self.filename}</span>'
        # TODO: Won't escape characters; I'll handle that later.
        separated = self.internal_metadata.filename_components(self.filename, False, True)
        font_elements = ''
        for i, token in enumerate(separated):
            classname = 'token' if i % 2 == 0 else 'separator'
            font_elements += build_font(token, classname)
        return font_elements

    def update_filename_separation(self):
        if self.casing_radio.isChecked():
            self.separator_chars.setDisabled(True)
        else:
            self.separator_chars.setDisabled(False)
        self.internal_metadata.filename_separator[self.filename] = self.separator_chars.text() if self.character_radio.isChecked() else True
        self.internal_metadata.purge_unreachable(self.filename)
        self.filename_line_label.setText(f'Filename: {self.formatted_filename()}')
        self.metadata_tree.draw_tree(self.filename)

    def on_save(self):
        self.accept()
        # Don't really need to do anything else. Anyone using this dialog can access the component_metadata dict.



if __name__ == "__main__":
    app = QApplication([])
    if len(argv) < 2:
        filename = input('Input filename to test: ')
    else:
        filename = argv[1]
    dialog = MetadataFilenameDialog(filename)
    status = dialog.exec()
    if status == 1:
        print(dialog.component_metadata)
