"""
    SESANS reader (based on ASCII reader)

    Reader for .ses or .sesans file format

    Jurrian Bakker
"""
import numpy as np
import os
from sas.sascalc.dataloader.file_reader_base_class import FileReader
from sas.sascalc.dataloader.data_info import plottable_1D, DataInfo
from sas.sascalc.dataloader.loader_exceptions import FileContentsException, DataReaderException

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
    ## File type
    type_name = "SESANS"

    ## Wildcards
    type = ["SESANS files (*.ses)|*.ses",
            "SESANS files (*..sesans)|*.sesans"]
    ## List of allowed extensions
    ext = ['.ses', '.SES', '.sesans', '.SESANS']

    ## Flag to bypass extension check
    allow_all = False

    def get_file_contents(self):
        self.current_datainfo = DataInfo()
        self.current_dataset = plottable_1D(np.array([]), np.array([]))
        self.current_datainfo.isSesans = True
        self.output = []

        error_message = ""
        loaded_correctly = True

        import pdb; pdb.set_trace()

        buff = self.f_open.read()
        lines = buff.splitlines()

        self.current_datainfo.filename = os.path.basename(self.f_open.name)

        paramnames=[]
        paramvals=[]
        zvals=[]
        dzvals=[]
        lamvals=[]
        dlamvals=[]
        Pvals=[]
        dPvals=[]

        for line in lines:
            # Initial try for CSV (split on ,)
            line=line.strip()
            toks = line.split('\t')
            if len(toks)==2:
                paramnames.append(toks[0])
                paramvals.append(toks[1])
            elif len(toks)>5:
                zvals.append(toks[0])
                dzvals.append(toks[3])
                lamvals.append(toks[4])
                dlamvals.append(toks[5])
                Pvals.append(toks[1])
                dPvals.append(toks[2])
            else:
                continue

        x=[]
        y=[]
        lam=[]
        dx=[]
        dy=[]
        dlam=[]
        lam_header = lamvals[0].split()
        data_conv_z = None
        default_z_unit = "A"
        data_conv_P = None
        default_p_unit = " " # Adjust unit for axis (L^-3)
        lam_unit = lam_header[1].replace("[","").replace("]","")
        if lam_unit == 'AA':
            lam_unit = 'A'
        varheader=[zvals[0],dzvals[0],lamvals[0],dlamvals[0],Pvals[0],dPvals[0]]
        valrange=range(1, len(zvals))
        try:
            for i in valrange:
                x.append(float(zvals[i]))
                y.append(float(Pvals[i]))
                lam.append(float(lamvals[i]))
                dy.append(float(dPvals[i]))
                dx.append(float(dzvals[i]))
                dlam.append(float(dlamvals[i]))
        except ValueError as val_err:
            err_msg = "Invalid float"
            err_msg += ":".join(val_err.message.split(":")[1:])
            raise FileContentsException(err_msg)

        x, y, lam, dy, dx, dlam = [
            np.asarray(v, 'double')
           for v in (x, y, lam, dy, dx, dlam)
        ]

        self.f_open.close()

        self.current_dataset.x, self.current_dataset._xunit = self._unit_conversion(x, lam_unit, default_z_unit)
        self.current_dataset.y = y
        self.current_dataset._yunit = r'\AA^{-2} cm^{-1}'  # output y_unit added
        self.current_dataset.dx, _ = self._unit_conversion(dx, lam_unit, default_z_unit)
        self.current_dataset.dy = dy
        self.current_dataset.lam, _ = self._unit_conversion(lam, lam_unit, default_z_unit)
        self.current_dataset.dlam, _ = self._unit_conversion(dlam, lam_unit, default_z_unit)

        self.current_dataset.xaxis(r"\rm{z}", self.current_dataset._xunit)
        self.current_dataset.yaxis(r"\rm{ln(P)/(t \lambda^2)}", self.current_dataset._yunit)  # Adjust label to ln P/(lam^2 t), remove lam column refs

        # Store loading process information
        self.current_datainfo.meta_data['loader'] = self.type_name
        try:
            self.current_datainfo.sample.thickness = float(paramvals[6])
        except ValueError as val_err:
            loaded_correctly = False
            error_message += "\nInvalid sample thickness '{}'".format(paramvals[6])

        self.current_datainfo.sample.name = paramvals[1]
        self.current_datainfo.sample.ID = paramvals[0]
        zaccept_unit_split = paramnames[7].split("[")
        zaccept_unit = zaccept_unit_split[1].replace("]","")
        if zaccept_unit.strip() == r'\AA^-1' or zaccept_unit.strip() == r'\A^-1':
            zaccept_unit = "1/A"
        self.current_datainfo.sample.zacceptance=(float(paramvals[7]),zaccept_unit)

        self.current_datainfo.vars = varheader

        if len(self.current_dataset.x) < 1:
            raise FileContentsException("No data points in file.")

        self.send_to_output()

        if not loaded_correctly:
            raise DataReaderException(error_message)

    def _unit_conversion(self, value, value_unit, default_unit):
        if has_converter == True and value_unit != default_unit:
            data_conv_q = Converter(value_unit)
            value = data_conv_q(value, units=default_unit)
            new_unit = default_unit
        else:
            new_unit = value_unit
        return value, new_unit
