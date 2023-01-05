"""
Container class for fitting widget state storage
"""
class FitPage(object):
    """
    Container for all data related to the current fit page
    """
    MIN_RANGE = 0
    MAX_RANGE = 1
    NPTS = 2
    NPTS_FIT = 3
    LOG_POINTS = 4
    WEIGHTING = 5
    SMEARING_OPTION = 6
    SMEARING_ACCURACY = 7
    SMEARING_MIN = 8
    SMEARING_MAX = 9
    def __init__(self):
        """
        Define the dictionary
        """
        # Main tab
        self.current_category = ""
        self.current_model = ""
        self.current_factor = ""

        self.page_id = 0
        self.data_is_loaded = False
        self.name = ""
        self.data = None
        self.parameters_to_fit = []
        self.kernel_module = None

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
        # Smearing options - tab #3
        # Should this be just part of self.fit_options?
        self.smearing_options = {}

        # Polydispersity - tab #4
        #self.poly

        # Magnetism - tab #5
        #self.magnetism

        # Algorithm
        self.algorithm = None
        self.algorithm_options = {}

    def save(self):
        """
        Serialize the current state
        """
        pass

    def load(self, location):
        """
        Retrieve serialized state from specified location
        """
        pass

    def saveAsXML(self):
        """
        Serialize the current state
        """
        # Connect to PageState.to_xml(), which serializes
        # to the existing XML with file I(Q)
        pass

