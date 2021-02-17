"""
    Generic multi-column ASCII data reader
"""

import logging
from sas.sascalc.dataloader.readers.ascii_reader import Reader as ASCIIReader

logger = logging.getLogger(__name__)


class Reader(ASCIIReader):
    """
    Class to load ascii files (2, 3 or 4 columns).
    """
    # File type
    type_name = "CSV"
    # Wildcards
    type = ["CSV files (*.csv)|*.csv"]
    # List of allowed extensions
    ext = ['.csv']
    # data unless that is the only data
    min_data_pts = 5

    def write(self, filename, dataset, sep=""):
        ASCIIReader.write(self, filename=filename, dataset=dataset, sep=", ")
