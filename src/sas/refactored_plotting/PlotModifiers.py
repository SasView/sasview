from typing import Literal
from PySide6.QtWidgets import QTreeWidgetItem
from abc import ABC, abstractmethod

LineStyleType = Literal['solid', 'dotted', 'dashed', 'dashdot']
# TODO: This should probably be an RGB value. The current value is just a placeholder.
LineColourType = Literal['red', 'green', 'blue'] 

class PlotModifier(ABC):
    @abstractmethod
    @property
    def modifier_value(self):
        pass


class ModifierLinestyle(PlotModifier):
    def __init__(self, line_style: LineStyleType):
        self.line_style = line_style

    @property
    def modifier_value(self) -> LineStyleType:
        return self.line_style
        


class ModifierLinecolor(PlotModifier):
    def __init__(self, parent, name):
        


class ModifierColormap(PlotModifier):
    def __init__(self, parent, name):
        super().__init__(parent, name)

    def clone(self):
        copy = super().clone()
        return ModifierColormap(copy.parent(), [copy.text(0)])
