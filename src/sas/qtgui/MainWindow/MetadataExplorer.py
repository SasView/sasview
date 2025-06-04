from PySide6.QtWidgets import QApplication, QDialog

from sasdata.metadata import Metadata


class MetadataExplorer(QDialog):
    def __init__(self, metadata: Metadata):
        super().__init__()
        self.metadata = metadata


if __name__ == "__main__":
    app = QApplication([])

    dialog = MetadataExplorer()
    status = dialog.exec()

    exit()
