from PySide6.QtWidgets import QTreeWidgetItem


class TabItem(QTreeWidgetItem):
    """
    Class for representation in the PlotTreeWidget. Saves the fitpage index to know, which data needs to be plotted
    in the redrawing process of this tab.
    """
    def __init__(self, parent, name, fitpage_index):
        super().__init__(parent, name)
        self._fitpage_index = fitpage_index
        super().setData(0, 1, self)

    @property
    def fitpage_index(self):
        return self._fitpage_index

class SubTabItem(TabItem):
    """
    Class for representation in the PlotTreeWidget. Has both fitpage index (from the parent TabItem) and subtab_index
    for plotting purposes in the redrawing process.
    """
    def __init__(self, parent, name, fitpage_index, subtab_index):
        super().__init__(parent, name, fitpage_index)
        self._subtab_index = subtab_index

    @property
    def subtab_index(self):
        return self._subtab_index

class PlotItem(SubTabItem):
    """
    Class for representation in the PlotTreeWidget. Has fitpage_index and subtab_index from the parent items. _ax_index
    and _is_plot_2d class attributes are used when the PlotTreeWidget item is drawn for redrawing.
    """
    def __init__(self, parent, name, fitpage_index, subtab_index, ax_index, is_plot_2d):
        super().__init__(parent, name, fitpage_index, subtab_index)
        self._ax_index = ax_index
        self._is_plot_2d = is_plot_2d

    @property
    def ax_index(self):
        return self._ax_index

    @property
    def is_plot_2d(self):
        return self._is_plot_2d

class PlottableItem(QTreeWidgetItem):
    """
    Class for representation in the PlotTreeWidget. Has _data_id and _type_num for replotting purposes in the redrawing
    process.
    """
    def __init__(self, parent, name, data_id, type_num):
        super().__init__(parent, name)
        self._data_id = data_id
        # type serves the same purpose as in DataTreeItems - knowing if the item is a data item or a fit item, so that
        # for example the axes can be scaled accordingly
        self._type_num = type_num
        super().setData(0, 1, self)

    @property
    def data_id(self):
        return self._data_id

    @property
    def type_num(self):
        # type_num = 1: 1d data,
        # type_num = 2: 1d fit,
        # type_num = 3: 1d residuals,
        # type_num = 4 : 2d data,
        # type_num = 5 : 2d fit,
        # type_num = 6 : 2d residuals
        return self._type_num



