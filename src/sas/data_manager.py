from sasdata.data import SasData

from src.sas.refactored import Perspective

# TODO: Add plots to this type.
TrackedData = SasData | Perspective

# TODO: Probably want to handle order, if that is even relevant.
valid_associations = [
    (Perspective, SasData)
    # TODO: Include plots
]


class DataManager():
    # Don't mutate these directly, or scary bad stuff will happen.
    _all_data_entries: set[TrackedData]
    _association: list[tuple[TrackedData, TrackedData]]

    def __init__(self):
        self._all_data_entries = set()
        self._association = []

    def add_data(self, data: TrackedData):
        self._all_data_entries.add(data)

    # TODO: May want more rules to prevent associations being made twice.
    def make_association(self, data_1: TrackedData, data_2: TrackedData):
        if not (data_1 in self._all_data_entries or data_2 in self._all_data_entries):
            raise ValueError('Both data_1, and data_2 need to be tracked in the data manager.')
        if not any([isinstance(data_1, x) and isinstance(data_2, y) for x, y in valid_associations]):
            # TODO: Clearer error message.
            raise ValueError('Invalid association.')
