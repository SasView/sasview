from sas.qtgui.Utilities.GuiUtils import enum

WIDGETS = enum(
    "W_NAME",
    "W_QMIN",
    "W_QMAX",
    "W_BACKGROUND",
    "W_SCALE",
    "W_CONTRAST",
    "W_CONTRAST_ERR",
    "W_POROD_CST",
    "W_VOLFRAC1",
    "W_VOLFRAC1_ERR",
    "W_VOLFRAC2",
    "W_ENABLE_CONTRAST",
    "W_ENABLE_VOLFRAC",
    "W_VOLUME_FRACTION",
    "W_VOLUME_FRACTION_ERR",
    # results
    "W_CONTRAST_OUT",
    "W_CONTRAST_OUT_ERR",
    "W_SPECIFIC_SURFACE",
    "W_SPECIFIC_SURFACE_ERR",
    "W_INVARIANT",
    "W_INVARIANT_ERR",
    "D_DATA_QSTAR",
    "D_DATA_QSTAR_ERR",
    "D_LOW_QSTAR",
    "D_LOW_QSTAR_ERR",
    "D_HIGH_QSTAR",
    "D_HIGH_QSTAR_ERR",
    #extrapolation tab
    "W_GUINIER_END_EX",
    "W_POROD_START_EX",
    "W_POROD_END_EX",
    "W_LOWQ_POWER_VALUE_EX",
    "W_HIGHQ_POWER_VALUE_EX",
    "W_ENABLE_LOWQ_EX",
    "W_ENABLE_HIGHQ_EX",
    "W_LOWQ_GUINIER_EX",
    "W_LOWQ_POWER_EX",
    "W_LOWQ_FIT_EX",
    "W_LOWQ_FIX_EX",
    "W_HIGHQ_FIT_EX",
    "W_HIGHQ_FIX_EX",
    "D_PROGRESS_LOW_QSTAR",
    "D_PROGRESS_DATA_QSTAR",
    "D_PROGRESS_HIGH_QSTAR"
)

def safe_float(x: str):
    """ String to float method that returns zero if parsing failed """

    try:
        return float(x)
    except (ValueError, TypeError):
        return 0.0
