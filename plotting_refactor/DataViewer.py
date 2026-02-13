from DataCollector import DataCollector
from DataTreeItems import DataItem, PlotPageItem
from DataTreeWidget import DataTreeWidget
from PlotModifiers import ModifierColormap, ModifierLinecolor, ModifierLinestyle
from PlotTreeItems import PlotItem, PlottableItem, SubTabItem, TabItem
from PlotTreeWidget import PlotTreeWidget
from PlotWidget import PlotWidget
from PySide6 import QtWidgets
from UI.DataViewerUI import Ui_DataViewer


class DataViewer(QtWidgets.QWidget, Ui_DataViewer):
    """
    Class for interface between Plotwidget and Datacollector. Processing of signals for plotting,
    redrawing of existing plots, adding new plot modifiers ends here.
    """
    def __init__(self, main_window):
        """
        Main Window is used as a parameter in the constructor to be able to hand it further to the Datacollector which
        can then directly read values from checkboxes and spinboxes for new model calculations.

        self.dataTreeWidget and self.plotTreeWidget represent data that exists in the DataCollector or existing plots
        in the plot widget, respectively.
        """
        super(DataViewer, self).__init__()
        self.setupUi(self)

        self.main_window = main_window
        self.datacollector = DataCollector()

        self.dataTreeWidget = DataTreeWidget(self, self.datacollector)
        self.plotTreeWidget = PlotTreeWidget(self)

        self.cmdClose.clicked.connect(self.onShowDataViewer)
        self.cmdAddModifier.clicked.connect(self.onAddModifier)
        self.plotTreeWidget.dropSignal.connect(self.redraw)

        self.setupMofifierCombobox()
        self.plot_widget = PlotWidget(self, self.datacollector)

    def create_plot(self, fitpage_index):
        self.update_plot_tree(fitpage_index)
        self.plot_widget.show()
        self.plot_widget.activateWindow()

    def update_datasets_from_collector(self, fitpage_index: int):
        """
        Collects datasets from the datacollector and adds them to the dataTreeWidget. Is called upon a plot or
        calculation request from the mainwindow. Only adds the dataset with the corresponding fitpage_index.
        """
        datasets = self.datacollector.datasets
        already_exists = False
        for i in range(self.dataTreeWidget.topLevelItemCount()):
            if fitpage_index == self.dataTreeWidget.topLevelItem(i).data(0, 1).fitpage_index:
                already_exists = True

        if not already_exists:
            for dataset in datasets:
                if fitpage_index == dataset.fitpage_index:
                    name = "Data from Fitpage " + str(fitpage_index)
                    data_id = dataset.data_id
                    item = PlotPageItem(self.dataTreeWidget, [name], fitpage_index, data_id)
                    item.setData(0, 1, item)
                    subitem_data = DataItem(item, ["Data"], fitpage_index, data_id, 1)
                    subitem_data.setData(0, 1, subitem_data)
                    if dataset.has_y_fit():
                        subitem_fit = DataItem(item, ["Fit"], fitpage_index, data_id, 2)
                        subitem_fit.setData(0, 1, subitem_fit)

            self.dataTreeWidget.expandAll()

    def onShowDataViewer(self):
        """
        Function for handling showing and hiding of the data viewer and the button for that in the main window
        """
        if self.isVisible():
            self.hide()
            self.main_window.cmdShowDataViewer.setText("Show Data Viewer")
        else:
            self.show()
            self.main_window.cmdShowDataViewer.setText("Hide Data Viewer")

    def update_dataset(self, fitpage_index, create_fit, checked_2d):
        """
        Updates existing or non-existing datasets in the datacollector for a fitpage in the mainwindow
        """
        self.datacollector.update_dataset(self.main_window, fitpage_index, create_fit, checked_2d)
        self.update_datasets_from_collector(fitpage_index)

    def update_plot_tree(self, fitpage_index):
        """
        Function to populate the plotTreeWidget for a certain fitpage. Checks if a plot for the given fitpage already
        exists and recreates it if so. Therefore it collects all the data for the given fitpage from the datacollector
        and creates the Tabs, Subtabs, Plots, Plottables for the plotTreeWidget. This mechanism also checks, if a
        dataitem that comes from the datacollector is 2d. If it is 2d, the type_num for this PlottableItem will be
        different (4 instead of 1) and the SubTabs.py can recognize, that only this 2d data can be plotted in one
        actual plot.
        """
        # check if an item for the fitpage index already exists
        # if one is found - remove from tree
        for i in range(self.plotTreeWidget.topLevelItemCount()):
            if isinstance(self.plotTreeWidget.topLevelItem(i), TabItem):
                if fitpage_index == self.plotTreeWidget.topLevelItem(i).data(0, 1).fitpage_index:
                    self.plotTreeWidget.takeTopLevelItem(i)

        # add tab
        tab_name = "Plot for Fitpage " + str(fitpage_index)
        tab_item = TabItem(self.plotTreeWidget, [tab_name], fitpage_index)
        tab_item.setData(0, 1, tab_item)

        # add data child and corresponding plot children in every case
        subtab_data = SubTabItem(tab_item, ["Data"], fitpage_index, 0)
        subplot_data = PlotItem(subtab_data, ["Data Plot"], fitpage_index, 0, 0,
                                self.datacollector.get_data_by_fp(fitpage_index).is_data_2d)
        fitpage_id = self.datacollector.get_data_by_fp(fitpage_index).data_id

        # create plottables in the plottreewidget with indicators (type_nums) to identify what kind of plot it is while
        # plotting in subtabs.py: type_num = 1 : 1d data, type_num = 2 : 1d fit, type_num = 3 : 1d residuals
        # type_num = 4 : 2d data, type_num = 5 : 2d fit, type_num = 6 : 2d residuals
        # 2d plots cannot overlap each other as curves can do
        # for every 2d data an additional plot is added and 1 plottable is inserted
        if self.datacollector.get_data_by_fp(fitpage_index).is_data_2d:
            plottable_data = PlottableItem(subplot_data, ["2d " + str(fitpage_id)], fitpage_id, 4)
        else:
            plottable_data = PlottableItem(subplot_data, [str(fitpage_id)], fitpage_id, 1)

        #add fit and residuals in case it was generated
        if self.datacollector.get_data_by_fp(fitpage_index).has_y_fit():
            # on the fit tab: one central plot that shows the dataset and the according fit curve
            # create tab for fit and residual plot
            subtab_fit = SubTabItem(tab_item, ["Fit"], fitpage_index, 1)
            subtab_residuals = SubTabItem(tab_item, ["Residuals"], fitpage_index, 2)
            # if the data is 2d, then every plot contains only one plottable
            if self.datacollector.get_data_by_fp(fitpage_index).is_data_2d:
                subplot_data_subtab_fit = PlotItem(subtab_fit, ["Data"], fitpage_index, 1, 0, True)
                plottable_subplot_data_subtab_fit = PlottableItem(subplot_data_subtab_fit, ["2d Plottable Fit Data"], fitpage_id, 4)

                subplot_fit_subtab_fit = PlotItem(subtab_fit, ["Fit"], fitpage_index, 1, 1, True)
                plottable_subplot_fit_subtab_fit = PlottableItem(subplot_fit_subtab_fit, ["2d Plottable Fit Fit"], fitpage_id, 5)


                subplot_data_subtab_residuals = PlotItem(subtab_residuals, ["Data"], fitpage_index, 2, 0, True)
                plottable_subplot_data_subtab_residuals = PlottableItem(subplot_data_subtab_residuals, ["2d Plottable Residuals Data"], fitpage_id, 4)

                subplot_fit_subtab_residuals = PlotItem(subtab_residuals, ["Fit"], fitpage_index, 2, 1, True)
                plottable_subplot_fit_subtab_residuals = PlottableItem(subplot_fit_subtab_residuals, ["2d Plottable Residuals Fit"], fitpage_id, 5)

                subplot_residuals_subtab_residuals = PlotItem(subtab_residuals, ["Residuals"], fitpage_index, 2, 2, True)
                plottable_subplot_residuals_subtab_residuals = PlottableItem(subplot_residuals_subtab_residuals, ["2d Plottable Residuals Residuals"], fitpage_id, 6)

            else:  # if the data is 1d, multiple plottables can be plotted in one plot
                subplot_fit = PlotItem(subtab_fit, ["Fit Plot"], fitpage_index, 1, 0, False)
                plottable_fit_data = PlottableItem(subplot_fit, ["Plottable Fit Data"], fitpage_id, 1)
                plottable_fit_fit = PlottableItem(subplot_fit, ["Plottable Fit Fit"], fitpage_id, 2)

                # on the residuals subtab: create 2 plots with 3 datasets: on the top plot is the data and the fit,
                # on the bottom plot is the residuals displayed with the same x-axis for comparison
                subplot_residuals_fit = PlotItem(subtab_residuals, ["Fit Plot"], fitpage_index, 2, 0, False)
                plottable_res_data = PlottableItem(subplot_residuals_fit, ["Plottable Res Data"], fitpage_id, 1)
                plottable_res_fit = PlottableItem(subplot_residuals_fit, ["Plottable Res Fit"], fitpage_id, 2)

                subplot_res = PlotItem(subtab_residuals, ["Residuals Plot"], fitpage_index, 2, 1, False)
                plottable_res = PlottableItem(subplot_res, ["Plottable Residuals"], fitpage_id, 3)

        self.plotTreeWidget.expandAll()
        self.redraw(fitpage_index, 0)

    def redraw(self, redraw_fitpage_index, redraw_subtab_index):
        """
        Redraws all tabs in the plotTreeWidget. parameters redraw_fitpage_index and redraw_subtab_index are used to show
        the subtab for which the redrawAll was invoked, because a modifier was dragged onto a child plot or plottable
        item in the plotTreeWidget.
        If redrawing is invoked from the update_plot_tree method, only the fitpage_index will be used but 0 for
        the subplot.
        """
        if self.plotTreeWidget.topLevelItemCount() != 0:
            for i in range(self.plotTreeWidget.topLevelItemCount()):
                if isinstance(self.plotTreeWidget.topLevelItem(i).data(0, 1), TabItem):
                    self.plot_widget.redrawTab(self.plotTreeWidget.topLevelItem(i))

        plotpage_index = self.datacollector.get_plotpage_index(redraw_fitpage_index)
        self.plot_widget.setCurrentIndex(plotpage_index)
        self.plot_widget.widget(plotpage_index).setCurrentIndex(redraw_subtab_index)

    def remove_plottree_item(self, index: int):
        """
        Remove toplevelitem from plottreeitem upon closing a tab in the plottreewidget.
        """
        # search for the existing dataset with the right plotpage index
        datasets = self.datacollector.datasets
        for dataset in datasets:
            if dataset.plotpage_index == index:
                fitpage_index_tab = dataset.fitpage_index

        # look through the toplevel items for the item with the right fitpage_index, that needs to be deleted.
        for i in range(self.plotTreeWidget.topLevelItemCount()):
            if self.plotTreeWidget.topLevelItem(i).data(0, 1).fitpage_index == fitpage_index_tab:
                self.plotTreeWidget.takeTopLevelItem(i)


    def onAddModifier(self):
        """
        Add modifiers via button press to the plotTreeWidget. These can then be dragged around on PlotItems and
        PlottableItems. Logic for dragging is in the PlotTreeWidget.py.
        """
        currentmodifier = self.comboBoxModifier.currentText()
        if 'color' in currentmodifier:
            mod = ModifierLinecolor(self.plotTreeWidget, [currentmodifier])
        if 'linestyle' in currentmodifier:
            mod = ModifierLinestyle(self.plotTreeWidget, [currentmodifier])
        if 'scheme' in currentmodifier:
            mod = ModifierColormap(self.plotTreeWidget, [currentmodifier])
    def setupMofifierCombobox(self):
        """
        Gives all the different available modifiers to the combobox so that they can be created by user selection.
        """
        self.comboBoxModifier.addItem("color=r")
        self.comboBoxModifier.addItem("color=g")
        self.comboBoxModifier.addItem("color=b")
        self.comboBoxModifier.addItem("linestyle=solid")
        self.comboBoxModifier.addItem("linestyle=dashed")
        self.comboBoxModifier.addItem("linestyle=dotted")
        self.comboBoxModifier.addItem("scheme=jet")
        self.comboBoxModifier.addItem("scheme=spring")
        self.comboBoxModifier.addItem("scheme=gray")

