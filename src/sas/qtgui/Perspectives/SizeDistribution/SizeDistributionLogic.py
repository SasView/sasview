class SizeDistributionLogic:
    """
    All the data-related logic. This class deals exclusively with Data1D/2D
    No QStandardModelIndex here.
    """

    def __init__(self, data=None):
        self._data = data
        self.data_is_loaded = False
        if data is not None:
            self.data_is_loaded = True

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        """data setter"""
        self._data = value
        self.data_is_loaded = self._data is not None

    def isLoadedData(self):
        """accessor"""
        return self.data_is_loaded
