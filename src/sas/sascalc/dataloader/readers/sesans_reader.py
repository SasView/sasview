"""
    SESANS reader (based on ASCII reader)
    
    Reader for .ses or .sesans file format
    
    Jurrian Bakker 
"""
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
    ## File type
    type_name = "SESANS"
    
    ## Wildcards
    type = ["SESANS files (*.ses)|*.ses",
            "SESANS files (*..sesans)|*.sesans"]
    ## List of allowed extensions
    ext = ['.ses', '.SES', '.sesans', '.SESANS']
    
    ## Flag to bypass extension check
    allow_all = True
    
    def read(self, path):
        
#        print "reader triggered"
        
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
            if self.allow_all or extension.lower() in self.ext:
                with open(path, 'r') as input_f:
                    # Read in binary mode since GRASP frequently has no-ascii
                    # characters that brakes the open operation
                    line = input_f.readline()
                    params = {}
                    while line.strip() != "":
                        if line.strip() == "":
                            break
                        terms = line.strip().split("\t")
                        params[terms[0].strip()] = " ".join(terms[1:]).strip()
                        line = input_f.readline()
                    headers_temp = input_f.readline().strip().split("\t")
                    headers = {}
                    for h in headers_temp:
                        temp = h.strip().split()
                        headers[h[:-1].strip()] = temp[-1][1:-1]
                    data = np.loadtxt(input_f)
                    x = data[:, 0]
                    dx = data[:, 3]
                    lam = data[:, 4]
                    dlam = data[:, 5]
                    y = data[:, 1]
                    dy = data[:, 2]

                    lam_unit = _header_fetch(headers, "wavelength")
                    if lam_unit == "AA":
                        lam_unit = "A"
                    p_unit = headers["polarisation"]

                    x, x_unit = self._unit_conversion(x, lam_unit,
                                                      _fetch_unit(headers,
                                                                  "spin echo length"))
                    dx, dx_unit = self._unit_conversion(dx, lam_unit,
                                                        _fetch_unit(headers,
                                                                    "error SEL"))
                    dlam, dlam_unit = self._unit_conversion(dlam, lam_unit,
                                                            _fetch_unit(headers,
                                                                        "error wavelength"))
                    y_unit = r'\AA^{-2} cm^{-1}'

                    output = Data1D(x=x, y=y, lam=lam, dy = dy, dx=dx, dlam=dlam, isSesans=True)
                    self.filename = output.filename = basename
                    output.xaxis(r"\rm{z}", x_unit)
                    output.yaxis(r"\rm{ln(P)/(t \lambda^2)}", y_unit)  # Adjust label to ln P/(lam^2 t), remove lam column refs
                    # Store loading process information
                    output.meta_data['loader'] = self.type_name
                    #output.sample.thickness = float(paramvals[6])
                    output.sample.name = params["Sample"]
                    output.sample.ID = params["DataFileTitle"]

                    output.sample.zacceptance = (float(_header_fetch(params, "Q_zmax")),
                                                 _fetch_unit(params, "Q_zmax"))

                    output.sample.yacceptance = (float(_header_fetch(params, "Q_ymax")),
                                                 _fetch_unit(params, "Q_ymax"))

                if len(output.x) < 1:
                    raise RuntimeError, "%s is empty" % path
                return output

        else:
            raise RuntimeError, "%s is not a file" % path
        return None

    def _unit_conversion(self, value, value_unit, default_unit):
        if has_converter == True and value_unit != default_unit:
            data_conv_q = Converter(value_unit)
            value = data_conv_q(value, units=default_unit)
            new_unit = default_unit
        else:
            new_unit = value_unit
        return value, new_unit


def _header_fetch(headers, key):
    index = [k for k in headers.keys()
             if k.startswith(key)][0]
    return headers[index]

def _fetch_unit(params, key):
    index = [k for k in params.keys()
             if k.startswith(key)][0]
    unit = index.strip().split()[-1][1:-1]
    if unit.startswith(r"\A"):
        unit = "1/A"
    return unit
