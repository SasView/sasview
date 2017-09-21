from sas.sasview.sasview import run_gui
# force inclusion of readers in the distribution
from sas.sascalc.dataloader.readers import (
    abs_reader, anton_paar_saxs_reader, ascii_reader, cansas_reader_HDF5,
    cansas_reader, danse_reader, red2d_reader, sesans_reader, tiff_reader,
    xml_reader,
)
run_gui()