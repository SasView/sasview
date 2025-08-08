from sas.qtgui.Utilities.GuiUtils import enum

WIDGETS = enum( 'W_QMIN',
                'W_QMAX',
                'W_QCUTOFF',
                'W_BACKGROUND',
                'W_TRANSFORM',
                'W_GUINIERA',
                'W_GUINIERB',
                'W_PORODK',
                'W_PORODSIGMA',
                'W_CORETHICK',
                'W_INTTHICK',
                'W_HARDBLOCK',
                'W_SOFTBLOCK',
                'W_CRYSTAL',
                'W_POLY_RYAN',
                'W_POLY_STRIBECK',
                'W_PERIOD',
                'W_FILENAME'
                )


def safe_float(x: str):
    """ String to float method that returns zero if parsing failed """

    try:
        return float(x)
    except:
        return 0.0
