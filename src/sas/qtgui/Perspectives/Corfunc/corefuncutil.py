from dataclasses import dataclass
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
                'W_FILENAME',
                )

@dataclass
class ExtractedParameters:
    long_period: float
    long_block_thickness: float
    polydispersity_ryan: float
    polydispersity_stribeck: float
    local_crystallinity: float