from PySide6.QtWidgets import QApplication, QDialog

class MetadataExplorer(QDialog):
    def __init__(self):
        super().__init__()

if __name__ == '__main__':
    app = QApplication([])

    dialog = MetadataExplorer()
    status = dialog.exec()

    exit()
