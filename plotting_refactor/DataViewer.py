from PySide6 import QtWidgets

from DataViewerUI import Ui_DataViewer
from PlotWidget import PlotWidget
from DataTreeWidget import DataTreeWidget
from PlotTreeWidget import PlotTreeWidget
from DataCollector import DataCollector
from DataTreeItems import PlotPageItem, DataItem
from PlotTreeItems import TabItem, SubTabItem, PlotItem, PlottableItem
from PlotModifiers import ModifierLinecolor, ModifierLinestyle, ModifierColormap, PlotModifier


class DataViewer(QtWidgets.QWidget, Ui_DataViewer):
    def __init__(self, main_window):
        super(DataViewer, self).__init__()
        self.setupUi(self)

        self.main_window = main_window
        self.datacollector = DataCollector()

        self.dataTreeWidget = DataTreeWidget(self, self.datacollector)
        self.plotTreeWidget = PlotTreeWidget(self)

        self.cmdClose.clicked.connect(self.onShowDataViewer)
        self.cmdAddModifier.clicked.connect(self.onAddModifier)
        self.plotTreeWidget.dropSignal.connect(self.redrawAll)

        self.setupMofifierCombobox()
        self.plot_widget = PlotWidget(self.datacollector)
        self.data_origin_fitpage_index = None

    def create_plot(self, fitpage_index):
        self.update_plot_tree(fitpage_index)
        self.plot_widget.show()
        self.plot_widget.activateWindow()

    def update_datasets_from_collector(self):
        # block signals to prevent currentItemChanged to be called. otherwise the program crashes, because it tries
        # to access the current item.
        self.dataTreeWidget.blockSignals(True)
        self.dataTreeWidget.clear()
        self.dataTreeWidget.blockSignals(False)

        datasets = self.datacollector.get_datasets()
        for i in range(len(datasets)):
            fitpage_index = datasets[i].get_fitpage_index()
            name = "Data from Fitpage " + str(fitpage_index)
            data_id = datasets[i].get_data_id()
            item = PlotPageItem(self.dataTreeWidget, [name], fitpage_index, data_id)
            item.setData(0, 1, item)
            subitem_data = DataItem(item, ["Data"], fitpage_index, data_id, 1)
            subitem_data.setData(0, 1, subitem_data)
            if datasets[i].has_y_fit():
                subitem_fit = DataItem(item, ["Fit"], fitpage_index, data_id, 2)
                subitem_fit.setData(0, 1, subitem_fit)

        self.dataTreeWidget.expandAll()

    def onShowDataViewer(self):
        if self.isVisible():
            self.hide()
            self.main_window.cmdShowDataViewer.setText("Show Data Viewer")
        else:
            self.update_datasets_from_collector()
            self.show()
            self.main_window.cmdShowDataViewer.setText("Hide Data Viewer")

    def update_dataset(self, main_window, fitpage_index, create_fit):
        self.datacollector.update_dataset(main_window, fitpage_index, create_fit)

    def update_plot_tree(self, fitpage_index):
        # check if an item for the fitpage index already exists
        # if one is found - remove from tree
        for i in range(self.plotTreeWidget.topLevelItemCount()):
            if isinstance(self.plotTreeWidget.topLevelItem(i), TabItem):
                if fitpage_index == self.plotTreeWidget.topLevelItem(i).data(0, 1).get_fitpage_index():
                    self.plotTreeWidget.takeTopLevelItem(i)

        #add tab
        tab_name = "Plot for Fitpage " + str(fitpage_index)
        tab_item = TabItem(self.plotTreeWidget, [tab_name], fitpage_index)
        tab_item.setData(0, 1, tab_item)

        #add data child and corresponding plot children in every case
        subtab_data = SubTabItem(tab_item, ["Data"], fitpage_index, 0)
        subplot_data = PlotItem(subtab_data, ["Data Plot"], fitpage_index, 0, 0)
        plottable_data = PlottableItem(subplot_data, [str(self.datacollector.get_data_fp(fitpage_index).get_data_id())],
                                       self.datacollector.get_data_fp(fitpage_index).get_data_id(), 1)
        #add fit and residuals in case it was generated
        if self.datacollector.get_data_fp(fitpage_index).has_y_fit():
            subtab_fit = SubTabItem(tab_item, ["Fit"], fitpage_index, 1)
            subplot_fit = PlotItem(subtab_fit, ["Fit Plot"], fitpage_index, 1, 0)
            plottable_fit_data = PlottableItem(subplot_fit, ["Plottable Fit Data"],
                                               self.datacollector.get_data_fp(fitpage_index).get_data_id(), 1)
            plottable_fit_fit = PlottableItem(subplot_fit, ["Plottable Fit Fit"],
                                          self.datacollector.get_data_fp(fitpage_index).get_data_id(), 2)

            subtab_res = SubTabItem(tab_item, ["Residuals"], fitpage_index, 2)
            subplot_res_fit = PlotItem(subtab_res, ["Fit Plot"], fitpage_index, 2, 0)
            plottable_res_data = PlottableItem(subplot_res_fit, ["Plottable Res Data"],
                                               self.datacollector.get_data_fp(fitpage_index).get_data_id(), 1)
            plottable_res_fit = PlottableItem(subplot_res_fit, ["Plottable Res Fit"],
                                               self.datacollector.get_data_fp(fitpage_index).get_data_id(), 2)
            subplot_res = PlotItem(subtab_res, ["Residuals Plot"], fitpage_index, 2, 1)
            plottable_res = PlottableItem(subplot_res, ["Plottable Residuals"],
                                          self.datacollector.get_data_fp(fitpage_index).get_data_id(), 3)
        self.plotTreeWidget.expandAll()
        self.redrawAll()

    def redrawAll(self):
        if self.plotTreeWidget.topLevelItemCount() != 0:
            for i in range(self.plotTreeWidget.topLevelItemCount()):
                if isinstance(self.plotTreeWidget.topLevelItem(i).data(0, 1), TabItem):
                    self.plot_widget.redrawTab(self.plotTreeWidget.topLevelItem(i))

    def onAddModifier(self):
        currentmodifier = self.comboBoxModifier.currentText()
        if 'color' in currentmodifier:
            mod = ModifierLinecolor(self.plotTreeWidget, [currentmodifier])
        if 'linestyle' in currentmodifier:
            mod = ModifierLinestyle(self.plotTreeWidget, [currentmodifier])
        if 'scheme' in currentmodifier:
            mod = ModifierColormap(self.plotTreeWidget, [currentmodifier])
    def setupMofifierCombobox(self):
        self.comboBoxModifier.addItem("color=r")
        self.comboBoxModifier.addItem("color=g")
        self.comboBoxModifier.addItem("color=b")
        self.comboBoxModifier.addItem("linestyle=solid")
        self.comboBoxModifier.addItem("linestyle=dashed")
        self.comboBoxModifier.addItem("linestyle=dotted")
        self.comboBoxModifier.addItem("scheme=jet")
        self.comboBoxModifier.addItem("scheme=spring")
        self.comboBoxModifier.addItem("scheme=gray")

