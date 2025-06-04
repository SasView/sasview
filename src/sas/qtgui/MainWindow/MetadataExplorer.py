from sys import argv
from pprint import pp

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPushButton,
    QTreeWidget,
    QVBoxLayout,
)
from sasdata.metadata import MetaNode, Metadata
from sasdata.temp_xml_reader import load_data


def metadata_as_dict(to_convert: object):
    """This is a custom implementation of asdict from dataclasses. The key difference is that MetaNode class objects are
    preserved, but everything else is converted into a dict. This makes it easier to iterate over."""
    if not hasattr(to_convert, "__dict__"):
        return to_convert
    converted_dict = to_convert.__dict__
    for key, value in converted_dict.items():
        # This if statement looks for a meta node that is a child node, and leaves it as is (i.e. it doesn't turn it
        # into a dict). Some meta nodes contain other meta nodes, so we need to add a condition for this.
        if not (
            value is dict
            or (
                isinstance(value, MetaNode)
                and [isinstance(content, MetaNode) for content in value.contents]
            )
        ):
            converted_dict[key] = metadata_as_dict(value)
    return converted_dict


class MetadataExplorer(QDialog):
    def __init__(self, metadata: Metadata, filename: str | None):
        super().__init__()
        self.metadata_dict = metadata_as_dict(metadata)
        # TODO: Temp get rid of later.
        pp(self.metadata_dict)

        filename_known = filename if filename is not None else "Unknown"
        self.filenameLabel = QLabel(f"Filename: {filename_known}")

        self.metadataTreeWidget = QTreeWidget()
        self.buildTree()

        self.closeButton = QPushButton("Close")

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.filenameLabel)
        self.layout.addWidget(self.metadataTreeWidget)
        self.layout.addWidget(self.closeButton)

        self.setWindowTitle("Metadata Explorer")

    def buildTree(self):
        tree = self.metadataTreeWidget
        # TODO: Implement


if __name__ == "__main__":
    app = QApplication([])

    filename = argv[1]
    data_dict = load_data(filename)
    data = list(data_dict.items())[0][1]
    # This is only going to work on XML files for now.

    dialog = MetadataExplorer(data.metadata, data.name)
    status = dialog.exec()

    exit()
