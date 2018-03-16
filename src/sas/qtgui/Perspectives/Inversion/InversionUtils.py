from sas.qtgui.Utilities.GuiUtils import enum

WIDGETS = enum( 'W_FILENAME',               #0
                'W_BACKGROUND_INPUT',             #1
                'W_ESTIMATE',               #2
                'W_MANUAL_INPUT',           #3
                'W_QMIN',                   #4
                'W_QMAX',                   #5
                'W_SLIT_HEIGHT',            #6
                'W_SLIT_WIDTH',             #7
                'W_NO_TERMS',               #8
                'W_NO_TERMS_SUGGEST',       #9
                'W_REGULARIZATION',         #10
                'W_REGULARIZATION_SUGGEST', #11
                'W_MAX_DIST',               #12
                'W_EXPLORE',                #13
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
