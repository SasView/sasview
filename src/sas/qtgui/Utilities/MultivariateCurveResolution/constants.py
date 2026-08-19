
""" UI and UX constants """

CURVE_LIST_COLUMN_WIDTHS = [30, 120, 50, 80, 50]
OUTLIER_TABLE_COLUMN_WIDTHS = [30, 200, 130]
ERRORS_LIST_COLUMN_WIDTHS = [50, 200]

CHI_TAG = "<χ²>="
REMOVED_TAG = " (removed)"

RESULTS_LIST_COMBINATION_LABELS = ["Absolute (A)", "Absolute + Holtzer (AH)", "Absolute + Kratky (AK)", "Absolute + Porod (AP)", "Absolute + Holtzer + Kratky (AHK)", "Absolute + Holtzer + Porod (AHP)", "Absolute + Kratky + Porod (AKP)", "All four (AHKP)"]
RESULTS_LIST_EXTRA_SIZE = (50, 2)

MAX_NUMBER_INPUT_DECIMALS = 20

UNITS = ["N", "A"]
DISPLAY_UNITS_TEXT = {
    "": "",
    "A": "1/Å",
    "N": "1/nm"
}
CYCLE_UNITS = {
    "": "N",
    "A": "N",
    "N": "A"
}

CONSTRAINTS_PRESETS = {
    "Amyloid filibration": [True, True, True, False, False, False],
    "Titration series": [True, True, False, True, False, False],
    "SEC-SAXS": [True, True, False, False, True, False]
}
"""
Constraints internal flags
1 : concentration non-negativity, 2 : spectra non-negativity, 3 : concentration unimodality, 4 : concentration closure, 5 : concentration equality, 6 : spectra equality
"""

A_DEF_COLOR = (0.9456327985739753 * .95,  0.029774872912127992 * .95,  0 * .95,                  1) #pl.cm.jet(.9) * .95
H_DEF_COLOR = (1 * .95,                   0.7705156136528688 * .95,    0 * .95,                  1) #pl.cm.jet(.7) * .95
K_DEF_COLOR = (0.4901960784313725 * .85,  1 * .85,                     0.4775458570524984 * .85, 1) #pl.cm.jet(.5) * .85
P_DEF_COLOR = (0 * .85,                   0.692156862745098 * .85,     1 * .85,                  1) #pl.cm.jet(.3) * .85

""" MCR-ALS constants """

MAX_NUMBER_SPECIES = 10
MAX_MCRALS_ITERATIONS = 10000
MAX_ERROR_ITERATIONS = 10000

INITIAL_ESTIMATE_METHOD_CURVE_REQUIREMENTS = {
    "Most dissimilar": 0,
    "Chi-rank": 1,
    "Manual selection": -1
}
INITIAL_ESTIMATE_MODE = {
    "Most dissimilar": 1,
    "Chi-rank": 2,
    "Manual selection": 0
}

EXPERIMENT_TYPES = {
    "Amyloid filibration": 1,
    "Titration series:": 2,
    "SEC-SAXS": 3,
    "Other": 4
}

ANGSTROM_UNIT_STRINGS = ["A", "1/A", "A-1", "A^-1", "A^{-1}", "Å", "1/Å", "Å-1", "Å^-1", "Å^{-1}"]
NANOMETER_UNIT_STRINGS = ["N", "1/N", "nm", "1/nm", "nm-1", "nm^-1", "nm^{-1}"]
XUNIT_FACTORS = {
    "A": 1,
    "N": 0.1,
    "": 1
}

RESULTS_LIST_COMBINATIONS = {
    "Absolute (A)": [True, False, False, False],
    "Absolute + Holtzer (AH)": [True, True, False, False],
    "Absolute + Kratky (AK)": [True, False, True, False],
    "Absolute + Porod (AP)": [True, False, False, True],
    "Absolute + Holtzer + Kratky (AHK)": [True, True, True, False],
    "Absolute + Holtzer + Porod (AHP)": [True, True, False, True],
    "Absolute + Kratky + Porod (AKP)": [True, False, True, True],
    "All four (AHKP)": [True, True, True, True]
}
