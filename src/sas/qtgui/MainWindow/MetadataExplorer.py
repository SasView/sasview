from sys import argv
from pprint import pp

from PySide6.QtWidgets import QApplication, QDialog
from sasdata.metadata import MetaNode, Metadata
from sasdata.temp_xml_reader import load_data


def metadata_as_dict(to_convert: object):
    """This is a custom implementation of asdict from dataclasses. The key difference is that MetaNode class objects are
    preserved, but everything else is converted into a dict. This makes it easier to iterate over."""
    converted_dict = to_convert.__dict__
    for key, value in converted_dict.items():
        if not (value is dict or isinstance(value, MetaNode)):
            converted_dict[key] = metadata_as_dict(value)
    return converted_dict


class MetadataExplorer(QDialog):
    def __init__(self, metadata: Metadata):
        super().__init__()
        self.metadata_dict = asdict(metadata)
        # TODO: Temp get rid of later.
        pp(self.metadata_dict)

        self.setWindowTitle("Metadata Explorer")


if __name__ == "__main__":
    app = QApplication([])

    filename = argv[1]
    data_dict = load_data(filename)
    data = list(data_dict.items())[0][1]
    # This is only going to work on XML files for now.

    dialog = MetadataExplorer(data.metadata)
    status = dialog.exec()

    exit()
