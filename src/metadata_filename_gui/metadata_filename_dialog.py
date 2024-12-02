from PySide6.QtWidgets import QWidget, QApplication, QVBoxLayout, QLineEdit, QHBoxLayout, QLabel, QDialog, QPushButton
from metadata_filename_gui.metadata_tree_widget import MetadataTreeWidget
from sys import argv
import re

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
    def __init__(self, filename: str, initial_component_metadata: dict[str, str]={},
                 master_metadata: dict[str, dict[str, int]]={}, initial_separator_text=''):
        super().__init__()

        self.setWindowTitle('Metadata')

        self.filename = filename
        # Key is the metadatum, value is the component selected for it.
        self.component_metadata = initial_component_metadata
        self.master_metadata = master_metadata

        self.filename_line_label = QLabel()
        self.seperator_chars_label = QLabel('Seperators')
        self.separator_chars = QLineEdit(initial_separator_text)
        self.separator_chars.textChanged.connect(self.update_filename_separation)

        self.filename_separator_layout = QHBoxLayout()
        self.filename_separator_layout.addWidget(self.filename_line_label)
        self.filename_separator_layout.addWidget(self.seperator_chars_label)
        self.filename_separator_layout.addWidget(self.separator_chars)

        self.metadata_tree = MetadataTreeWidget(self.component_metadata)

        # Have to update this now because it relies on the value of the separator, and tree.
        self.update_filename_separation()

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.on_save)

        self.layout = QVBoxLayout(self)
        self.layout.addLayout(self.filename_separator_layout)
        self.layout.addWidget(self.metadata_tree)
        self.layout.addWidget(self.save_button)

    @property
    def separator_text(self) -> str:
        return self.separator_chars.text()

    def split_filename(self) -> list[str]:
        return re.split(f'([{self.separator_text}])', self.filename)

    def filename_components(self) -> list[str]:
        splitted = re.split(f'{self.separator_chars.text()}', self.filename)
        # If the last component has a file extensions, remove it.
        last_component = splitted[-1]
        if '.' in last_component:
            pos = last_component.index('.')
            last_component = last_component[:pos]
            splitted[-1] = last_component
        return splitted

    def formatted_filename(self) -> str:
        sep_str = self.separator_chars.text()
        if sep_str == '':
            return f'<span>{self.filename}</span>'
        # TODO: Won't escape characters; I'll handle that later.
        separated = self.split_filename()
        font_elements = ''
        for i, token in enumerate(separated):
            classname = 'token' if i % 2 == 0 else 'separator'
            font_elements += build_font(token, classname)
        return font_elements

    def update_filename_separation(self):
        self.filename_line_label.setText(f'Filename: {self.formatted_filename()}')
        self.metadata_tree.draw_tree(self.filename_components(), self.component_metadata)

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
