from dataclasses import dataclass
from typing import Generator

@dataclass
class RegistryEntry:
    """ Data kept on each slicer """
    name: str
    cls: type
    priority: int

class SlicerRegistry:
    """ Keeps track of all the possible slicers """

    _slicers: list[RegistryEntry] = []

    @staticmethod
    def register(name: str, cls: type, priority: int=0):
        """ Register a slicer with the registry

        :param name: name that will show on the menu
        :param cls: class name
        :param priority: priority (used to determine the order on menus, higher number first)
        """

        SlicerRegistry._slicers.append(RegistryEntry(name, cls, priority))
        SlicerRegistry._slicers.sort(key=lambda x: (x.priority, x.name)) # Sort by priority, lexographical name tiebreak

    @staticmethod
    def name_class_pairs() -> Generator[tuple[str, type], None, None]:
        """ Generator over priority sorted """
        for slicer in SlicerRegistry._slicers:
            yield slicer.name, slicer.cls

