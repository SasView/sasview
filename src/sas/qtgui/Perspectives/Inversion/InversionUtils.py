from sas.qtgui.Utilities.GuiUtils import enum

WIDGETS = enum(
    'W_FILENAME',
    'W_BACKGROUND_INPUT',
    'W_ESTIMATE',
    'W_MANUAL_INPUT',
    'W_Q_MIN',
    'W_Q_MAX',
    'W_SLIT_HEIGHT',
    'W_SLIT_WIDTH',
    'W_NO_TERMS',
    'W_NO_TERMS_SUGGEST',
    'W_REGULARIZATION',
    'W_REGULARIZATION_SUGGEST',
    'W_MAX_DIST',
    'W_EXPLORE',
    # results
    'W_RG',
    'W_I_ZERO',
    'W_BACKGROUND_OUTPUT',
    'W_COMP_TIME',
    'W_CHI_SQUARED',
    'W_OSCILLATION',
    'W_POS_FRACTION',
    'W_SIGMA_POS_FRACTION',
    # bottom buttons
    'W_REMOVE',
    'W_CALCULATE_ALL',
    'W_CALCULATE_VISIBLE',
    'W_HELP'
)
