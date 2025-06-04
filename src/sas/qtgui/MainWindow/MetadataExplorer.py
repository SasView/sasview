from PySide6.QtWidgets import QApplication, QDialog
from sasdata.metadata import Metadata
from sys import argv
from sasdata.temp_xml_reader import load_data


class MetadataExplorer(QDialog):
    def __init__(self, metadata: Metadata):
        super().__init__()
        self.metadata = metadata


if __name__ == "__main__":
    app = QApplication([])

    filename = argv[1]
    data_dict = load_data(filename)
    data = list(data_dict.items())[0][1]
    # This is only going to work on XML files for now.

    dialog = MetadataExplorer(data.metadata)
    status = dialog.exec()

    exit()
