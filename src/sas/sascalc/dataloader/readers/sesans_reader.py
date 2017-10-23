"""
    SESANS reader (based on ASCII reader)

    Reader for .ses or .sesans file format

    Jurrian Bakker
"""
import os

import numpy as np

from ..file_reader_base_class import FileReader
from ..data_info import plottable_1D, DataInfo
from ..loader_exceptions import FileContentsException, DataReaderException

# Check whether we have a converter available
has_converter = True
try:
    from sas.sascalc.data_util.nxsunit import Converter
except:
    has_converter = False
_ZERO = 1e-16

class Reader(FileReader):
    """
    Class to load sesans files (6 columns).
    """
    # File type
    type_name = "SESANS"

    ## Wildcards
    type = ["SESANS files (*.ses)|*.ses",
            "SESANS files (*..sesans)|*.sesans"]
    # List of allowed extensions
    ext = ['.ses', '.SES', '.sesans', '.SESANS']

    # Flag to bypass extension check
    allow_all = True

    def get_file_contents(self):
        self.current_datainfo = DataInfo()
        self.current_dataset = plottable_1D(np.array([]), np.array([]))
        self.current_datainfo.isSesans = True
        self.output = []

        line = self.nextline()
        params = {}
        while not line.startswith("BEGIN_DATA"):
            terms = line.split()
            if len(terms) >= 2:
                params[terms[0]] = " ".join(terms[1:])
            line = self.nextline()
        self.params = params

        if "FileFormatVersion" not in self.params:
            raise FileContentsException("SES file missing FileFormatVersion")
        if float(self.params["FileFormatVersion"]) >= 2.0:
            raise FileContentsException("SASView only supports SES version 1")

        if "SpinEchoLength_unit" not in self.params:
            raise FileContentsException("SpinEchoLength has no units")
        if "Wavelength_unit" not in self.params:
            raise FileContentsException("Wavelength has no units")
        if params["SpinEchoLength_unit"] != params["Wavelength_unit"]:
            raise FileContentsException("The spin echo data has rudely used "
                               "different units for the spin echo length "
                               "and the wavelength.  While sasview could "
                               "handle this instance, it is a violation "
                               "of the file format and will not be "
                               "handled by other software.")

        headers = self.nextline().split()

        self._insist_header(headers, "SpinEchoLength")
        self._insist_header(headers, "Depolarisation")
        self._insist_header(headers, "Depolarisation_error")
        self._insist_header(headers, "Wavelength")

        data = np.loadtxt(self.f_open)

        if data.shape[1] != len(headers):
            raise FileContentsException(
                "File has {} headers, but {} columns".format(
                    len(headers),
                    data.shape[1]))

        if not data.size:
            raise FileContentsException("{} is empty".format(path))
        x = data[:, headers.index("SpinEchoLength")]
        if "SpinEchoLength_error" in headers:
            dx = data[:, headers.index("SpinEchoLength_error")]
        else:
            dx = x * 0.05
        lam = data[:, headers.index("Wavelength")]
        if "Wavelength_error" in headers:
            dlam = data[:, headers.index("Wavelength_error")]
        else:
            dlam = lam * 0.05
        y = data[:, headers.index("Depolarisation")]
        dy = data[:, headers.index("Depolarisation_error")]

        lam_unit = self._unit_fetch("Wavelength")
        x, x_unit = self._unit_conversion(x, "A",
                                          self._unit_fetch(
                                              "SpinEchoLength"))
        dx, dx_unit = self._unit_conversion(
            dx, lam_unit,
            self._unit_fetch("SpinEchoLength"))
        dlam, dlam_unit = self._unit_conversion(
            dlam, lam_unit,
            self._unit_fetch("Wavelength"))
        y_unit = self._unit_fetch("Depolarisation")

        self.current_dataset.x = x
        self.current_dataset.y = y
        self.current_dataset.lam = lam
        self.current_dataset.dy = dy
        self.current_dataset.dx = dx
        self.current_dataset.dlam = dlam
        self.current_datainfo.isSesans = True

        self.current_datainfo._yunit = y_unit
        self.current_datainfo._xunit = x_unit
        self.current_datainfo.source.wavelength_unit = lam_unit
        self.current_datainfo.source.wavelength = lam
        self.current_datainfo.filename = os.path.basename(self.f_open.name)
        self.current_dataset.xaxis(r"\rm{z}", x_unit)
        # Adjust label to ln P/(lam^2 t), remove lam column refs
        self.current_dataset.yaxis(r"\rm{ln(P)/(t \lambda^2)}", y_unit)
        # Store loading process information
        self.current_datainfo.meta_data['loader'] = self.type_name
        self.current_datainfo.sample.name = params["Sample"]
        self.current_datainfo.sample.ID = params["DataFileTitle"]
        self.current_datainfo.sample.thickness = self._unit_conversion(
            float(params["Thickness"]), "cm",
            self._unit_fetch("Thickness"))[0]

        self.current_datainfo.sample.zacceptance = (
            float(params["Theta_zmax"]),
            self._unit_fetch("Theta_zmax"))

        self.current_datainfo.sample.yacceptance = (
            float(params["Theta_ymax"]),
            self._unit_fetch("Theta_ymax"))

        self.send_to_output()

    @staticmethod
    def _insist_header(headers, name):
        if name not in headers:
            raise FileContentsException(
                "Missing {} column in spin echo data".format(name))

    @staticmethod
    def _unit_conversion(value, value_unit, default_unit):
        """
        Performs unit conversion on a measurement.

        :param value: The magnitude of the measurement
        :param value_unit: a string containing the final desired unit
        :param default_unit: string with the units of the original measurement
        :return: The magnitude of the measurement in the new units
        """
        # (float, string, string) -> float
        if has_converter and value_unit != default_unit:
            data_conv_q = Converter(default_unit)
            value = data_conv_q(value, units=value_unit)
            new_unit = default_unit
        else:
            new_unit = value_unit
        return value, new_unit

    def _unit_fetch(self, unit):
        return self.params[unit+"_unit"]
