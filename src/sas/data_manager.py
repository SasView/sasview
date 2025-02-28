from PySide6.QtCore import QObject, Signal
from sasdata.data import SasData

from src.sas.refactored import Perspective

# TODO: Add plots to this type.
TrackedData = SasData | Perspective

# TODO: Probably want to handle order, if that is even relevant.
valid_associations: list[tuple[str | type, str | type]] = [
    ('Perspective', SasData)
    # TODO: Include plots
]

# This is needed because the normal 'isinstance' builtin function annoyingly
# doesn't work properly on QObjects. So we need this workaround.

def isinstance_fix(obj: object, t: type | str) -> bool:
    if isinstance(t, str) and hasattr(obj, 'inherits'):
        return obj.inherits(t)
    elif isinstance(t, type):
        return isinstance(obj, t)
    else:
        return False

# Making this a QObject so it'll support events.
class NewDataManager(QObject):
    # Don't mutate these directly, or scary bad stuff will happen.
    _all_data_entries: list[TrackedData]
    associations: list[tuple[TrackedData, TrackedData]]
    new_data: Signal = Signal()
    data_removed: Signal = Signal()
    new_association: Signal = Signal()

    def __init__(self):
        super().__init__()
        self._all_data_entries = []
        self.associations = []

    def _number_perspective(self, to_number: Perspective):
        number = 1
        # TODO: Comparing titles might not be the best way to do this.
        relevant_perspective_numbers = [p.perspective_number for p in self._all_data_entries if hasattr(p, 'title') and p.title == to_number.title]
        while number in relevant_perspective_numbers:
            number += 1
        to_number.perspective_number = number

    def add_data(self, data: TrackedData):
        self._all_data_entries.append(data)
        # TODO: This is a bit of a dodgy way of checking for a perspective but isinstance won't work. I need to look
        # into using ABC.
        if hasattr(data, 'title'):
            self._number_perspective(data)
        self.new_data.emit()

    def remove_data(self, data: TrackedData):
        # We shouldn't be able to remove tracked data if its in an association
        # because it may be in a perspective etc.
        # TODO: Is it still ok to delete data in a plot if that plot is removed as well?
        if any([data in assoc for assoc in self.associations]):
            raise ValueError('Cannot remove data that is in an association.')
        self._all_data_entries.remove(data)
        self.data_removed.emit()
    # TODO: Remove data on a list. So that we could remove a perspective, and
    # data at the same time. So it doesn't matter that the perspective is
    # associated with the data becuase they will both be removed.

    # TODO: May want more rules to prevent associations being made twice.
    def make_association(self, data_1: TrackedData, data_2: TrackedData):
        if not (data_1 in self._all_data_entries or data_2 in self._all_data_entries):
            raise ValueError('Both data_1, and data_2 need to be tracked in the data manager.')
        if not any([isinstance_fix(data_1, x) and isinstance_fix(data_2, y) for x, y in valid_associations]):
            # TODO: Clearer error message.
            raise ValueError('Invalid association.')
        self.associations.append((data_1, data_2))
        self.new_association.emit()

    def get_association(self, data: TrackedData) -> TrackedData:
        for assoc in self.associations:
            if data in assoc:
                return assoc[0] if assoc[0] != data else assoc[1]
        raise ValueError('Association not found.')

    def get_all_associations(self, data: TrackedData) -> list[TrackedData]:
        return [assoc[0] if assoc[0] != data else assoc[1] for assoc in self.associations if data in assoc]

    @property
    def all_data(self) -> list[TrackedData]:
        return self._all_data_entries

    @property
    def all_perspectives(self) -> list[Perspective]:
        # TODO: This is a dodgy way of checking for a perspective but isinstance
        # doesn't work. Will need to look into this.
        return [item for item in self._all_data_entries if hasattr(item, 'title')]
