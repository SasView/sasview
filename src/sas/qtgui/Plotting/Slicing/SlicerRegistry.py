from dataclasses import dataclass
from typing import Generator


@dataclass
class RegistryEntry:
    """ Data kept on each slicer """
    name: str
    cls: type
    priority: int

class SlicerRegistry:
    """ Keeps track of all the possible slicers for the menu and stuff """

    _slicers: list[RegistryEntry] = []
    _initialised = False

    @staticmethod
    def _register(name: str, cls: type, priority: int=0):
        """ Register a slicer with the registry

        :param name: name that will show on the menu
        :param cls: class name
        :param priority: priority (used to determine the order on menus, higher number first)
        """

        print(f"Registering '{name}, {cls}' (priority={priority})")

        SlicerRegistry._slicers.append(RegistryEntry(name, cls, priority))

    @staticmethod
    def name_class_pairs() -> Generator[tuple[str, type], None, None]:
        """ Generator over priority sorted """

        if not SlicerRegistry._initialised:
            SlicerRegistry._register_slicers()
            SlicerRegistry._initialised = True

        for slicer in SlicerRegistry._slicers:
            yield slicer.name, slicer.cls

    @staticmethod
    def _register_slicers():

        from sas.qtgui.Plotting.Slicing.Slicers.BoxSlicer import BoxInteractorX, BoxInteractorY
        from sas.qtgui.Plotting.Slicing.Slicers.AnnulusSlicer import AnnulusInteractor
        from sas.qtgui.Plotting.Slicing.Slicers.WedgeSlicer import WedgeInteractorQ, WedgeInteractorPhi

        # self.actionSectorView = plot_slicer_menu.addAction("&Sector [Q View]")
        # self.actionSectorView.triggered.connect(self.onSectorView)
        # self.actionBoxSum = plot_slicer_menu.addAction("&Box Sum")
        # self.actionBoxSum.triggered.connect(self.onBoxSum)
        


        # Register slicers

        SlicerRegistry._register("Box Slice (X)", BoxInteractorX, priority=10)
        SlicerRegistry._register("Box Slice (Y)", BoxInteractorY, priority=20)
        SlicerRegistry._register("Full Annulus (Phi)", AnnulusInteractor, priority=30)
        SlicerRegistry._register("Wedge (Phi)", WedgeInteractorPhi, priority=40)
        SlicerRegistry._register("Wedge (Q)", WedgeInteractorQ, priority=50)


        SlicerRegistry._slicers.sort(
            key=lambda x: (x.priority, x.name))  # Sort by priority, lexographical name tiebreak
