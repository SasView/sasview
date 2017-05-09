class FitPage(object):
    """
    Container for all data related to the current fit page
    """
    MIN_RANGE=0
    MAX_RANGE=1
    NPTS=2
    NPTS_FIT=3
    LOG_POINTS=4
    WEIGHTING=5
    SMEARING_OPTION=6
    SMEARING_ACCURACY=7
    SMEARING_MIN=8
    SMEARING_MAX=9
    def __init__(self, parent=None):
        """
        Define the dictionary
        """
        # Main tab
        self.current_category = ""
        self.current_model = ""
        self.current_factor = ""

        self.page_id = 0
        self.is_data_loaded = False
        self.filename = ""
        
        # QModels
        self.param_model = None
        self.poly_model = None
        self.magnetism_model = None

        # Displayed values - tab #1
        self.is_polydisperse = False
        self.is2D = False
        self.is_magnetism = False
        self.displayed_values = {}
        self.chi2 = None

        # Fit options - tab #2
        self.fit_options = {}
        # Weight options - tab #2
        #self.weighting_options = {}
        # Smearing options - tab #3
        self.smearing_options = {}

