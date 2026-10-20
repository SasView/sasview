from abc import ABC, abstractmethod
from typing import Literal, get_args
from matplotlib.axes import Axes

LineStyleType = Literal['solid', 'dotted', 'dashed', 'dashdot']
# TODO: This should probably be an RGB value. The current value is just a placeholder.
ColourType = Literal['red', 'green', 'blue']

class PlotModifier(ABC):
    @abstractmethod
    def __init__(self, value):
        pass

    @property
    @abstractmethod
    def modifier_value(self):
        pass

    @property
    @abstractmethod
    def explorer_item_name(self) -> str:
        pass

    @abstractmethod
    def modify_axes(self, axes: Axes):
        pass

    @staticmethod
    @abstractmethod
    def options() -> list:
        pass


class ModifierLinestyle(PlotModifier):
    def __init__(self, line_style: LineStyleType):
        self.line_style = line_style

    @property
    def modifier_value(self) -> LineStyleType:
        return self.line_style

    @property
    def explorer_item_name(self) -> str:
        return f"Line Style: {self.line_style}"

    def modify_axes(self, axes: Axes):
        axes.get_lines()[-1].set_linestyle(self.modifier_value)

    @staticmethod
    def options() -> list[str]:
        return get_args(LineStyleType)



class ModifierLinecolor(PlotModifier):
    def __init__(self, line_colour: ColourType):
        self.line_colour = line_colour

    @property
    def modifier_value(self) -> ColourType:
        return self.line_colour

    @property
    def explorer_item_name(self) -> str:
        return f"Line Colour: {self.line_colour}"

    def modify_axes(self, axes: Axes):
        axes.get_lines()[-1].set_color(self.modifier_value)

    @staticmethod
    def options() -> list[str]:
        return get_args(ColourType)



class ModifierColormap(PlotModifier):
    def __init__(self, colour: ColourType):
        self.colour = colour

    @property
    def modifier_value(self) -> ColourType:
        return self.colour

    @property
    def explorer_item_name(self) -> str:
        return f"Plot Colour: {self.colour}"

    def modify_axes(self, axes: Axes):
        raise NotImplementedError("Color map is not implemented for plots.")

    @staticmethod
    def options() -> list[str]:
        return get_args(ColourType)

