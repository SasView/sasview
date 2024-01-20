from typing import Union, TypeVar, Generic
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections import defaultdict

from sas.qtgui.Plotting2.Plots.FormattingOptions import FormattingOptions

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sas.qtgui.Plotting2.Plots.NotionalPlot import NotionalPlot
    from sas.qtgui.Plotting2.Plots.NotionalSubplot import NotionalSubplot
    from sas.qtgui.Plotting2.Plots.NotionalAxis import NotionalAxis
    from sas.qtgui.Plotting2.Plots.PlotSeriesGroup import PlotSeriesGroup
    from sas.qtgui.Plotting2.Plots.PlotSeries import PlotSeries
    from sas.qtgui.Plotting2.Plots.PlotSeriesComponent import PlotSeriesComponent
    from sas.qtgui.Plotting2.Plots.PlotGroup import PlotGroup

    NonRootPlotComponent = Union[
        NotionalPlot, NotionalSubplot, NotionalAxis, PlotSeriesGroup, PlotSeries, PlotSeriesComponent]

# What are we using to identify things?
Identifier = int
GroupIdentifier = int


class NoParent(Exception):
    pass

@dataclass
class PlotLocationConcrete:
    plot: Identifier
    subplot: Identifier
    axis: Identifier
    series_group: Identifier
    series: Identifier
    series_component: Identifier


T = TypeVar("T")
S = TypeVar("S")
class PlotCommon(ABC, Generic[S, T]):
    def __init__(self):
        self._identifier = PlotRecord.new_identifier()
        self._formatting_options = FormattingOptions()

    @property
    def identifier(self) -> Identifier:
        """ Unique ID for this object"""
        return self._identifier

    def parent(self) -> S:
        """ Get the parent object """

    def children(self) -> list[T]:
        """ Get the children of this object """

    def formatting_options(self):
        return self._formatting_options.override(self.parent().formatting_options)


class PlotRoot(PlotCommon[None, NotionalPlot]):
    def __init__(self):
        super().__init__()

        self.default_formatting = FormattingOptions(
            color="black",
            marker_style=None)

    def children(self) -> list[NotionalPlot]:
        return PlotRecord.plots()

    def formatting_options(self):
        """ Get the formatting options - Overrides parent class"""
        return self.default_formatting

class PlotRecord:
    """ Central place that keeps track of the various plot, groups, and plot components """
    _root = PlotRoot()

    _plots: dict[Identifier, NotionalPlot] = {}
    _subplots: dict[Identifier, NotionalSubplot] = {}
    _axes: dict[Identifier, NotionalAxis] = {}
    _series_groups: dict[Identifier, PlotSeriesGroup] = {}
    _series: dict[Identifier, PlotSeries] = {}
    _series_components: dict[Identifier, PlotSeriesComponent] = {}

    _plot_groups: dict[GroupIdentifier, PlotGroup] = {}

    _names: dict[Identifier, str] = {}

    _child_parent_links: dict[Identifier, Identifier] = {}
    _parent_child_links: dict[Identifier, list[Identifier]] = defaultdict(list[int])

    # Unique ID stuff - maybe replace with UID system
    _identifiers: set[int] = set() # The only purpose of this is to assure unique ids, don't use for anything else
    _current_identifier = 0

    _plot_group_identifiers: set[int] = set()
    _current_plot_group_identifier = 0

    @staticmethod
    def new_identifier():
        while PlotRecord._current_identifier in PlotRecord._identifiers:
            PlotRecord._current_identifier += 1

        PlotRecord._identifiers.add(PlotRecord._current_identifier)

        return PlotRecord._current_identifier


    @staticmethod
    def new_plot_group_identifier() -> GroupIdentifier:
        while PlotRecord._current_plot_group_identifier in PlotRecord._plot_group_identifiers:
            PlotRecord._current_plot_group_identifier += 1

        PlotRecord._identifiers.add(PlotRecord._current_plot_group_identifier)

        return PlotRecord._current_identifier


    @staticmethod
    def _iterate_plot_object_lookups():
        """ Helper method to iterate though all the different kinds of plot record"""

        yield PlotRecord._plots
        yield PlotRecord._subplots
        yield PlotRecord._axes
        yield PlotRecord._series_groups
        yield PlotRecord._series
        yield PlotRecord._series_components
        yield PlotRecord._names

    @staticmethod
    def remove_id(identifier: Identifier):
        # Remove from list
        PlotRecord._identifiers.remove(identifier)

        # Remove associated objects
        for dictionary in PlotRecord._iterate_plot_object_lookups():
            if identifier in dictionary:
                del dictionary[identifier]

        # Remove all references to it from parent to child links
        for parent_key in PlotRecord._parent_child_links:

            if parent_key == identifier:
                del PlotRecord._parent_child_links[parent_key]

            else:
                PlotRecord._parent_child_links[parent_key] = \
                    [i for i in PlotRecord._parent_child_links[parent_key] if i != identifier]

        # Remove all references to it from the child to parent links
        for child_key in PlotRecord._child_parent_links:
            if child_key == identifier:
                del PlotRecord._child_parent_links[child_key]

            else:
                if PlotRecord._child_parent_links[child_key] == identifier:
                    del PlotRecord._child_parent_links[child_key]

        # Remove from plot groups

        for group_id in PlotRecord._plot_groups:
            PlotRecord._plot_groups[group_id].remove_plot_by_identifier(identifier)

        PlotRecord._current_identifier = identifier # Re-use ID


    @staticmethod
    def remove_component(plot_component: NonRootPlotComponent):
        # Remove from list
        PlotRecord.remove_id(plot_component.identifier)

    #
    #
    # Adding of components
    #
    #

    @staticmethod
    def add_group(group: PlotGroup):
        PlotRecord._plot_groups[group.identifier] = group

    @staticmethod
    def add_plot(plot: NotionalPlot):
        """ Add a plot to the system """
        PlotRecord._plots[plot.identifier] = plot

    @staticmethod
    def add_subplot(subplot: NotionalSubplot):
        """ Add a subplot to the system """
        PlotRecord._subplots[subplot.identifier] = subplot

    @staticmethod
    def add_axis(axis: NotionalAxis):
        """ Add an axis to the system """
        PlotRecord._axes[axis.identifier] = axis

    @staticmethod
    def add_series_group(series_group: PlotSeriesGroup):
        """ Add a series group to the system """
        PlotRecord._series_groups[series_group.identifier] = series_group

    @staticmethod
    def add_series(series: PlotSeries):
        """ Add a plot series to the system """
        PlotRecord._series[series.identifier] = series

    @staticmethod
    def add_series_component(series_component: PlotSeriesComponent):
        """ Add a plot series component to the system """
        PlotRecord._series_components[series_component.identifier] = series_component

    #
    #
    # Getters
    #
    #

    @staticmethod
    def plot_group(identifier: GroupIdentifier):
        """ Get a plot group by its ID"""
        return PlotRecord._plot_groups[identifier]

    @staticmethod
    def plots():
        """ All the current plots"""
        return [PlotRecord._plots[identifier] for identifier in PlotRecord._plots]

    @staticmethod
    def plot(identifier: Identifier) -> NotionalPlot:
        """ Get a plot by identifier """
        return PlotRecord._plots[identifier]

    @staticmethod
    def subplot(identifier: Identifier) -> NotionalSubplot:
        """ Get a subplot by identifier """
        return PlotRecord._subplots[identifier]

    @staticmethod
    def axis(identifier: Identifier) -> NotionalAxis:
        """ Get an axis by identifier """
        return PlotRecord._axes[identifier]

    @staticmethod
    def series_group(identifier: Identifier) -> PlotSeriesGroup:
        """ Get a series group by identifier """
        return PlotRecord._series_groups[identifier]

    @staticmethod
    def series_group(identifier: Identifier) -> PlotSeriesGroup:
        """ Get a series by identifier """
        return PlotRecord._series_groups[identifier]

    @staticmethod
    def series_group(identifier: Identifier) -> PlotSeriesGroup:
        """ Get a series component by identifier """
        return PlotRecord._series_groups[identifier]



    @staticmethod
    def root():
        """ Root of all plots, base of the plotting heirarcy"""
        return PlotRecord._root

    #
    #
    #   Parent Getters
    #
    #


    @staticmethod
    def parent_plot(identifier: Identifier) -> NotionalPlot:
        """ Get the parent plot from the identifier of a subplot."""
        parent_identifier = PlotRecord._child_parent_links[identifier]
        if parent_identifier in PlotRecord._plots:
            return PlotRecord._plots[parent_identifier]
        else:
            raise NoParent(f"No parent for identifier {identifier}")

    @staticmethod
    def parent_subplot(identifier: Identifier) -> NotionalSubplot:
        """ Get the parent subplot from the identifier of an axis."""
        parent_identifier = PlotRecord._child_parent_links[identifier]
        if parent_identifier in PlotRecord._subplots:
            return PlotRecord._subplots[parent_identifier]
        else:
            raise NoParent(f"No parent for identifier {identifier}")

    @staticmethod
    def parent_axis(identifier: Identifier) -> NotionalAxis:
        """ Get the parent axis from the identifier of a series group."""
        parent_identifier = PlotRecord._child_parent_links[identifier]
        if parent_identifier in PlotRecord._axes:
            return PlotRecord._axes[parent_identifier]
        else:
            raise NoParent(f"No parent for identifier {identifier}")


    @staticmethod
    def parent_series_group(identifier: Identifier) -> PlotSeriesGroup:
        """ Get the parent series group from the identifier of a series."""
        parent_identifier = PlotRecord._child_parent_links[identifier]
        if parent_identifier in PlotRecord._series_groups:
            return PlotRecord._series_groups[parent_identifier]
        else:
            raise NoParent(f"No parent for identifier {identifier}")


    @staticmethod
    def parent_series(identifier: Identifier) -> PlotSeries:
        """ Get the parent series from the identifier of a series component."""
        parent_identifier = PlotRecord._child_parent_links[identifier]
        if parent_identifier in PlotRecord._series:
            return PlotRecord._series[parent_identifier]
        else:
            raise NoParent(f"No parent for identifier {identifier}")

    #
    #
    #    Child getters
    #
    #

    @staticmethod
    def child_plots(identifier: Identifier) -> list[NotionalPlot]:
        child_identifiers = PlotRecord._parent_child_links[identifier]
        return [PlotRecord._plots[child_identifier] for child_identifier in child_identifiers]

    @staticmethod
    def child_subplots(identifier: Identifier) -> list[NotionalSubplot]:
        child_identifiers = PlotRecord._parent_child_links[identifier]
        return [PlotRecord._subplots[child_identifier] for child_identifier in child_identifiers]

    @staticmethod
    def child_axes(identifier: Identifier) -> list[NotionalAxis]:
        child_identifiers = PlotRecord._parent_child_links[identifier]
        return [PlotRecord._axes[child_identifier] for child_identifier in child_identifiers]

    @staticmethod
    def child_series_group(identifier: Identifier) -> list[PlotSeriesGroup]:
        child_identifiers = PlotRecord._parent_child_links[identifier]
        return [PlotRecord._series_groups[child_identifier] for child_identifier in child_identifiers]

    @staticmethod
    def child_series(identifier: Identifier) -> list[PlotSeries]:
        child_identifiers = PlotRecord._parent_child_links[identifier]
        return [PlotRecord._series[child_identifier] for child_identifier in child_identifiers]

    @staticmethod
    def child_series_component(identifier: Identifier) -> list[PlotSeriesComponent]:
        child_identifiers = PlotRecord._parent_child_links[identifier]
        return [PlotRecord._series_components[child_identifier] for child_identifier in child_identifiers]




    def __new__(cls, *args, **kwargs):
        """Lock it down!!!!"""
        raise RuntimeError("Don't create me!")

class PlotLocationPattern:

    def get_matches(self) -> PlotLocationConcrete:
        pass
