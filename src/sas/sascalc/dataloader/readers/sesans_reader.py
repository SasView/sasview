"""
    SESANS reader (based on ASCII reader)

    Reader for .ses or .sesans file format

    Jurrian Bakker
"""
import logging
import numpy as np
import os
from sas.sascalc.dataloader.data_info import Data1D

# Check whether we have a converter available
has_converter = True
try:
    from sas.sascalc.data_util.nxsunit import Converter
except:
    has_converter = False
_ZERO = 1e-16


class Reader:
    """
    Class to load sesans files (6 columns).
    """
    # File type
    type_name = "SESANS"

    # Wildcards
    type = ["SESANS files (*.ses)|*.ses",
            "SESANS files (*..sesans)|*.sesans"]
    # List of allowed extensions
    ext = ['.ses', '.SES', '.sesans', '.SESANS']

    # Flag to bypass extension check
    allow_all = True

    def read(self, path):
        """
        Load data file

        :param path: file path

        :return: SESANSData1D object, or None

        :raise RuntimeError: when the file can't be opened
        :raise ValueError: when the length of the data vectors are inconsistent
        """
        if os.path.isfile(path):
            basename = os.path.basename(path)
            _, extension = os.path.splitext(basename)
            if not (self.allow_all or extension.lower() in self.ext):
                raise RuntimeError(
                    "{} has an unrecognized file extension".format(path))
        else:
            raise RuntimeError("{} is not a file".format(path))
        with open(path, 'r') as input_f:
            # Read in binary mode since GRASP frequently has no-ascii
            # characters that brakes the open operation
            line = input_f.readline()
            params = {}
            while not line.startswith("BEGIN_DATA"):
                terms = line.split()
                if len(terms) >= 2:
                    params[terms[0]] = " ".join(terms[1:])
                line = input_f.readline()
            self.params = params

            if "FileFormatVersion" not in self.params:
                raise RuntimeError("SES file missing FileFormatVersion")

            if "SpinEchoLength_unit" not in self.params:
                raise RuntimeError("SpinEchoLength has no units")
            if "Wavelength_unit" not in self.params:
                raise RuntimeError("Wavelength has no units")
            if params["SpinEchoLength_unit"] != params["Wavelength_unit"]:
                raise RuntimeError("The spin echo data has rudely used "
                                   "different units for the spin echo length "
                                   "and the wavelength.  While sasview could "
                                   "handle this instance, it is a violation "
                                   "of the file format and will not be "
                                   "handled by other software.")

            headers = input_f.readline().split()

            data = np.loadtxt(input_f)
            if data.size < 1:
                raise RuntimeError("{} is empty".format(path))
            x = data[:, headers.index("SpinEchoLength")]
            if "SpinEchoLength_error" in headers:
                dx = data[:, headers.index("SpinEchoLength_error")]
            else:
                dx = x*0.05
            lam = data[:, headers.index("Wavelength")]
            if "Wavelength_error" in headers:
                dlam = data[:, headers.index("Wavelength_error")]
            else:
                dlam = lam*0.05
            y = data[:, headers.index("Depolarisation")]
            dy = data[:, headers.index("Depolarisation_error")]

            lam_unit = self._unit_fetch("Wavelength")
            x, x_unit = self._unit_conversion(x, "A", self._unit_fetch("SpinEchoLength"))
            dx, dx_unit = self._unit_conversion(
                dx, lam_unit,
                self._unit_fetch("SpinEchoLength"))
            dlam, dlam_unit = self._unit_conversion(
                dlam, lam_unit,
                self._unit_fetch("Wavelength"))
            y_unit = self._unit_fetch("Depolarisation")

            output = Data1D(x=x, y=y, lam=lam, dy=dy, dx=dx, dlam=dlam,
                            isSesans=True)

            output.y_unit = y_unit
            output.x_unit = x_unit
            output.source.wavelength_unit = lam_unit
            output.source.wavelength = lam
            self.filename = output.filename = basename
            output.xaxis(r"\rm{z}", x_unit)
            # Adjust label to ln P/(lam^2 t), remove lam column refs
            output.yaxis(r"\rm{ln(P)/(t \lambda^2)}", y_unit)
            # Store loading process information
            output.meta_data['loader'] = self.type_name
            output.sample.name = params["Sample"]
            output.sample.ID = params["DataFileTitle"]
            output.sample.thickness = self._unit_conversion(
                float(params["Thickness"]), "cm",
                self._unit_fetch("Thickness"))[0]

            output.sample.zacceptance = (
                float(params["Theta_zmax"]),
                self._unit_fetch("Theta_zmax"))

            output.sample.yacceptance = (
                float(params["Theta_ymax"]),
                self._unit_fetch("Theta_ymax"))
            return output

    @staticmethod
    def _unit_conversion(value, value_unit, default_unit):
        """
        Performs unit conversion on a measurement.

        :param value: The magnitude of the measurement
        :param value_unit: a string containing the final desired unit
        :param default_unit: a string containing the units of the original measurement
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
