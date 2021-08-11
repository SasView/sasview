"""
    CSV-specific multi-column ASCII data reader
"""

import logging
from sas.sascalc.dataloader.readers.ascii_reader import Reader as ASCIIReader

logger = logging.getLogger(__name__)


class Reader(ASCIIReader):
    """
    Class to load CSV files (2, 3 or 4 columns) built off the ASCII reader.

    All reading is done by the ASCIIReader. The writer calls the ASCII writer with a different separator.
    """
    # File type
    type_name = "CSV"
    # Wildcards
    type = ["CSV files (*.csv)|*.csv"]
    # List of allowed extensions
    ext = ['.csv']
    # data unless that is the only data
    min_data_pts = 5

    def write(self, filename, dataset, sep=", "):
        """
        Output data csv format using the ASCII reader

        :param filename: Full file name and path where the file will be saved
        :param dataset: Data1D object that will be saved
        :param sep: Separator between data items, default is a comma followed by a single space
        """
        ASCIIReader.write(self, filename=filename, dataset=dataset, sep=sep)
