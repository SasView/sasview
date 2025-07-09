from sys import argv

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)
from sasdata.metadata import MetaNode, Metadata
from sasdata.temp_xml_reader import load_data


def convert_raw_to_dict(to_convert: MetaNode, converted: dict = None) -> dict:
    if converted is None:
        converted = {}
    converted[to_convert.name] = {}
    for raw_content in to_convert.contents:
        if raw_content is MetaNode:
            to_add = convert_raw_to_dict(to_convert, converted[to_convert.name])
        else:
            to_add = raw_content
        converted[to_convert.name][to_add.name] = to_add
    return converted


def metadata_as_dict(to_convert: object):
    converted = to_convert.__dict__
    converted["raw"] = convert_raw_to_dict(converted["raw"])
    return converted


class MetadataExplorer(QDialog):
    def __init__(self, metadata: Metadata, filename: str | None):
        super().__init__()
        self.metadata_dict = metadata_as_dict(metadata)

        filename_known = filename if filename is not None else "Unknown"
        self.filenameLabel = QLabel(f"Filename: {filename_known}")

        self.metadataTreeWidget = QTreeWidget()
        self.buildTree()

        self.closeButton = QPushButton("Close")
        self.closeButton.clicked.connect(self.onClose)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.filenameLabel)
        self.layout.addWidget(self.metadataTreeWidget)
        self.layout.addWidget(self.closeButton)

        self.setWindowTitle("Metadata Explorer")

    def buildTree(
        self,
        table_root: QTreeWidgetItem | None = None,
        current_item: dict[str, object] | list[dict[str, object]] | None = None,
    ):
        tree = self.metadataTreeWidget
        tree.setColumnCount(2)
        if current_item is None:
            current_item = self.metadata_dict
        if table_root is None:
            table_root = QTreeWidgetItem(["Metadata"])
            tree.addTopLevelItem(table_root)
        if isinstance(current_item, list):
            dicts = current_item
        else:
            dicts = [current_item]
        for single_dict in dicts:
            for key, value in single_dict.items():
                if isinstance(value, dict) or (
                    isinstance(value, list)
                    and any([isinstance(member, dict) for member in value])
                ):
                    dict_root = QTreeWidgetItem([key])
                    table_root.addChild(dict_root)
                    self.buildTree(dict_root, value)
                elif isinstance(value, list):
                    node_item = QTreeWidgetItem([key, str(value)])
                    table_root.addChild(node_item)
                if isinstance(value, str):
                    node_item = QTreeWidgetItem([key, value])
                    table_root.addChild(node_item)
                if isinstance(value, MetaNode):
                    # TODO: Implement. Just show the contents for now.
                    node_item = QTreeWidgetItem([key, str(value.contents)])
                    table_root.addChild(node_item)

    def onClose(self):
        self.close()


if __name__ == "__main__":
    app = QApplication([])

    filename = argv[1]
    data_dict = load_data(filename)
    data = list(data_dict.items())[0][1]
    # This is only going to work on XML files for now.

    dialog = MetadataExplorer(data.metadata, data.name)
    status = dialog.exec()

    exit()
