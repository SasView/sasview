import time
import logging
import re
import copy

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.Plotter import PlotterWidget
from sas.qtgui.Plotting.PlotterData import Data2D
from sas.qtgui.Plotting.Plotter2D import Plotter2DWidget
import sas.qtgui.Utilities.GuiUtils as GuiUtils

from .UI.DataOperationUtilityUI import Ui_DataOperationUtility

BG_WHITE = "background-color: rgb(255, 255, 255);"
BG_RED = "background-color: rgb(244, 170, 164);"


class DataOperationUtilityPanel(QtWidgets.QDialog, Ui_DataOperationUtility):
    def __init__(self, parent=None):
        super(DataOperationUtilityPanel, self).__init__()
        self.setupUi(self)
        self.manager = parent
        self.communicator = self.manager.communicator()

        # To store input datafiles
        self.filenames = None
        self.list_data_items = []
        self.data1 = None
        self.data2 = None
        # To store the result
        self.output = None

        # To update content of comboboxes with files loaded in DataExplorer
        self.communicator.sendDataToPanelSignal.connect(self.updateCombobox)

        # change index of comboboxes
        self.cbData1.currentIndexChanged.connect(self.onSelectData1)
        self.cbData2.currentIndexChanged.connect(self.onSelectData2)
        self.cbOperator.currentIndexChanged.connect(self.onSelectOperator)

        # edit Coefficient text edit
        self.txtNumber.textChanged.connect(self.onInputCoefficient)
        self.txtOutputData.textChanged.connect(self.onCheckOutputName)

        # push buttons
        self.cmdClose.clicked.connect(self.onClose)
        self.cmdHelp.clicked.connect(self.onHelp)
        self.cmdCompute.clicked.connect(self.onCompute)
        self.cmdReset.clicked.connect(self.onReset)

        self.cmdCompute.setEnabled(False)

        # validator for coefficient
        self.txtNumber.setValidator(GuiUtils.DoubleValidator())

        self.layoutOutput = QtWidgets.QHBoxLayout()
        self.layoutData1 = QtWidgets.QHBoxLayout()
        self.layoutData2 = QtWidgets.QHBoxLayout()

        # Create default layout for initial graphs (when they are still empty)
        self.newPlot(self.graphOutput, self.layoutOutput)
        self.newPlot(self.graphData1, self.layoutData1)
        self.newPlot(self.graphData2, self.layoutData2)

        # Flag to enable Compute pushbutton
        self.data2OK = False
        self.data1OK = False

    def updateCombobox(self, filenames):
        """ Function to fill comboboxes with names of datafiles loaded in
         DataExplorer. For Data2, there is the additional option of choosing
         a number to apply to data1 """
        self.filenames = filenames

        if list(filenames.keys()):
            # clear contents of comboboxes
            self.cbData1.clear()
            self.cbData1.addItems(['Select Data'])
            self.cbData2.clear()
            self.cbData2.addItems(['Select Data', 'Number'])

            list_datafiles = []

            for key_id in list(filenames.keys()):
                if filenames[key_id].get_data().title:
                    # filenames with titles
                    new_title = filenames[key_id].get_data().title
                    list_datafiles.append(new_title)
                    self.list_data_items.append(new_title)

                else:
                    # filenames without titles by removing time.time()
                    new_title = re.sub('\d{10}\.\d{2}', '', str(key_id))
                    self.list_data_items.append(new_title)
                    list_datafiles.append(new_title)

            # update contents of comboboxes
            self.cbData1.addItems(list_datafiles)
            self.cbData2.addItems(list_datafiles)

    def onHelp(self):
        """
        Bring up the Data Operation Utility Documentation whenever
        the HELP button is clicked.
        Calls Documentation Window with the path of the location within the
        documentation tree (after /doc/ ....".
        """
        location = "/user/sasgui/perspectives/calculator/data_operator_help.html"
        self.manager.showHelp(location)

    def onClose(self):
        """ Close dialog """
        self.onReset()

        self.cbData1.clear()
        self.cbData1.addItems(['No Data Available'])
        self.cbData2.clear()
        self.cbData2.addItems(['No Data Available'])
        self.close()


    def onCompute(self):
        """ perform calculation """
        # set operator to be applied
        operator = self.cbOperator.currentText()
        # calculate and send data to DataExplorer
        output = None
        try:
            data1 = self.data1
            data2 = self.data2
            output = eval("data1 %s data2" % operator)
        except Exception as ex:
            logging.error(ex)
            return

        self.output = output

        # if outputname was unused, write output result to it
        # and display plot
        if self.onCheckOutputName():
            # add outputname to self.filenames
            self.list_data_items.append(str(self.txtOutputData.text()))
            # send result to DataExplorer
            self.onPrepareOutputData()
            # plot result
            self.updatePlot(self.graphOutput, self.layoutOutput, self.output)

    def onPrepareOutputData(self):
        """ Prepare datasets to be added to DataExplorer and DataManager """
        new_item = GuiUtils.createModelItemWithPlot(
            self.output,
            name=self.txtOutputData.text())

        new_datalist_item = {str(self.txtOutputData.text()) + str(time.time()):
                                 self.output}
        self.communicator. \
            updateModelFromDataOperationPanelSignal.emit(new_item, new_datalist_item)

    def onSelectOperator(self):
        """ Change GUI when operator changed """
        self.lblOperatorApplied.setText(self.cbOperator.currentText())
        self.newPlot(self.graphOutput, self.layoutOutput)

    def onReset(self):
        """
        Reset Panel to its initial state (default values) keeping
        the names of loaded data
        """
        self.txtNumber.setText('1.0')
        self.txtOutputData.setText('MyNewDataName')

        self.txtNumber.setEnabled(False)
        self.cmdCompute.setEnabled(False)

        self.cbData1.setCurrentIndex(0)
        self.cbData2.setCurrentIndex(0)
        self.cbOperator.setCurrentIndex(0)

        self.output = None
        self.data1 = None
        self.data2 = None
        self.filenames = None
        self.list_data_items = []

        self.data1OK = False
        self.data2OK = False

        # Empty graphs
        self.newPlot(self.graphOutput, self.layoutOutput)
        self.newPlot(self.graphData1, self.layoutData1)
        self.newPlot(self.graphData2, self.layoutData2)

    def onSelectData1(self):
        """ Plot for selection of Data1 """
        choice_data1 = str(self.cbData1.currentText())

        wrong_choices = ['No Data Available', 'Select Data', '']

        if choice_data1 in wrong_choices:
            # check validity of choice: input = filename
            self.newPlot(self.graphData1, self.layoutData1)
            self.data1 = None
            self.data1OK = False
            self.cmdCompute.setEnabled(False) # self.onCheckChosenData())
            return

        else:
            self.data1OK = True
            # get Data1
            key_id1 = self._findId(choice_data1)
            self.data1 = self._extractData(key_id1)
            # plot Data1
            self.updatePlot(self.graphData1, self.layoutData1, self.data1)
            # plot default for output graph
            self.newPlot(self.graphOutput, self.layoutOutput)
            # Enable Compute button only if Data2 is defined and data compatible
            self.cmdCompute.setEnabled(self.onCheckChosenData())

    def onSelectData2(self):
        """ Plot for selection of Data2 """
        choice_data2 = str(self.cbData2.currentText())
        wrong_choices = ['No Data Available', 'Select Data', '']

        if choice_data2 in wrong_choices:
            self.newPlot(self.graphData2, self.layoutData2)
            self.txtNumber.setEnabled(False)
            self.data2OK = False
            self.onCheckChosenData()
            self.cmdCompute.setEnabled(False)
            return

        elif choice_data2 == 'Number':
            self.data2OK = True
            self.txtNumber.setEnabled(True)
            self.data2 = float(self.txtNumber.text())

            # Enable Compute button only if Data1 defined and compatible data
            self.cmdCompute.setEnabled(self.onCheckChosenData())
            # Display value of coefficient in graphData2
            self.updatePlot(self.graphData2, self.layoutData2, self.data2)
            # plot default for output graph
            self.newPlot(self.graphOutput, self.layoutOutput)
            self.onCheckChosenData()

        else:
            self.txtNumber.setEnabled(False)
            self.data2OK = True
            key_id2 = self._findId(choice_data2)
            self.data2 = self._extractData(key_id2)
            self.cmdCompute.setEnabled(self.onCheckChosenData())

            # plot Data2
            self.updatePlot(self.graphData2, self.layoutData2, self.data2)
            # plot default for output graph
            self.newPlot(self.graphOutput, self.layoutOutput)

    def onInputCoefficient(self):
        """ Check input of number when a coefficient is required
        for operation """
        if self.txtNumber.isModified():
            input_to_check = str(self.txtNumber.text())

            if input_to_check is None or input_to_check is '':
                msg = 'DataOperation: Number requires a float number'
                logging.warning(msg)
                self.txtNumber.setStyleSheet(BG_RED)

            elif float(self.txtNumber.text()) == 0.:
                # should be check that 0 is not chosen
                msg = 'DataOperation: Number requires a non zero number'
                logging.warning(msg)
                self.txtNumber.setStyleSheet(BG_RED)

            else:
                self.txtNumber.setStyleSheet(BG_WHITE)
                self.data2 = float(self.txtNumber.text())
                self.updatePlot(self.graphData2, self.layoutData2, self.data2)

    def onCheckChosenData(self):
        """ check that data1 and data2 are compatible """

        if not all([self.data1OK, self.data2OK]):
            return False
        else:
            if self.cbData2.currentText() == 'Number':
                self.cbData1.setStyleSheet(BG_WHITE)
                self.cbData2.setStyleSheet(BG_WHITE)
                return True

            elif self.data1.__class__.__name__ != self.data2.__class__.__name__:
                self.cbData1.setStyleSheet(BG_RED)
                self.cbData2.setStyleSheet(BG_RED)
                print(self.data1.__class__.__name__ != self.data2.__class__.__name__)
                logging.warning('Cannot compute data of different dimensions')
                return False

            elif self.data1.__class__.__name__ == 'Data1D'\
                    and (len(self.data2.x) != len(self.data1.x) or
                             not all(i == j for i, j in zip(self.data1.x, self.data2.x))):
                logging.warning('Cannot compute 1D data of different lengths')
                self.cbData1.setStyleSheet(BG_RED)
                self.cbData2.setStyleSheet(BG_RED)
                return False

            elif self.data1.__class__.__name__ == 'Data2D' \
                    and (len(self.data2.qx_data) != len(self.data1.qx_data) \
                    or len(self.data2.qy_data) != len(self.data1.qy_data)
                    or not all(i == j for i, j in
                                     zip(self.data1.qx_data, self.data2.qx_data))
                    or not all(i == j for i, j in
                                zip(self.data1.qy_data, self.data2.qy_data))
                         ):
                self.cbData1.setStyleSheet(BG_RED)
                self.cbData2.setStyleSheet(BG_RED)
                logging.warning('Cannot compute 2D data of different lengths')
                return False

            else:
                self.cbData1.setStyleSheet(BG_WHITE)
                self.cbData2.setStyleSheet(BG_WHITE)
                return True

    def onCheckOutputName(self):
        """ Check that name of output does not already exist """
        name_to_check = str(self.txtOutputData.text())
        self.txtOutputData.setStyleSheet(BG_WHITE)

        if name_to_check is None or name_to_check == '':
            self.txtOutputData.setStyleSheet(BG_RED)
            logging.warning('No output name')
            return False

        elif name_to_check in self.list_data_items:
            self.txtOutputData.setStyleSheet(BG_RED)
            logging.warning('The Output data name already exists')
            return False

        else:
            self.txtOutputData.setStyleSheet(BG_WHITE)
            return True

    # ########
    # Modification of inputs
    # ########
    def _findId(self, name):
        """ find id of name in list of filenames """
        isinstance(name, str)

        for key_id in list(self.filenames.keys()):
            # data with title
            if self.filenames[key_id].get_data().title:
                input = self.filenames[key_id].get_data().title
            # data without title
            else:
                input = str(key_id)
            if name in input:
                return key_id

    def _extractData(self, key_id):
        """ Extract data from file with id contained in list of filenames """
        data_complete = self.filenames[key_id].get_data()
        dimension = data_complete.__class__.__name__

        if dimension in ('Data1D', 'Data2D'):
            return copy.deepcopy(data_complete)

        else:
            logging.warning('Error with data format')
            return

    # ########
    # PLOTS
    # ########
    def newPlot(self, graph, layout):
        """ Create template for graphs with default '?' layout"""
        assert isinstance(graph, QtWidgets.QGraphicsView)
        assert isinstance(layout, QtWidgets.QHBoxLayout)

        # clear layout
        if layout.count() > 0:
            item = layout.takeAt(0)
            layout.removeItem(item)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.prepareSubgraphWithData("?"))

        graph.setLayout(layout)

    def updatePlot(self, graph, layout, data):
        """ plot data in graph after clearing its layout """

        assert isinstance(graph, QtWidgets.QGraphicsView)
        assert isinstance(layout, QtWidgets.QHBoxLayout)

        # clear layout
        if layout.count() > 0:
            item = layout.takeAt(0)
            layout.removeItem(item)

        layout.setContentsMargins(0, 0, 0, 0)

        if isinstance(data, Data2D):
            # plot 2D data
            plotter2D = Plotter2DWidget(self, quickplot=True)
            plotter2D.data = data
            plotter2D.scale = 'linear'

            plotter2D.ax.tick_params(axis='x', labelsize=8)
            plotter2D.ax.tick_params(axis='y', labelsize=8)

            # Draw zero axis lines.
            plotter2D.ax.axhline(linewidth=1)
            plotter2D.ax.axvline(linewidth=1)

            graph.setLayout(layout)
            layout.addWidget(plotter2D)
            # remove x- and ylabels
            plotter2D.y_label = ''
            plotter2D.x_label = ''
            plotter2D.plot(show_colorbar=False)
            plotter2D.show()

        elif isinstance(data, Data1D):
            # plot 1D data
            plotter = PlotterWidget(self, quickplot=True)
            plotter.data = data

            graph.setLayout(layout)
            layout.addWidget(plotter)

            plotter.ax.tick_params(axis='x', labelsize=8)
            plotter.ax.tick_params(axis='y', labelsize=8)

            plotter.plot(hide_error=True, marker='.')
            # plotter.legend = None

            plotter.show()

        elif float(data) and self.cbData2.currentText() == 'Number':
            # display value of coefficient (to be applied to Data1)
            # in graphData2
            layout.addWidget(self.prepareSubgraphWithData(data))

            graph.setLayout(layout)

    def prepareSubgraphWithData(self, data):
        """ Create graphics view containing scene with string """
        scene = QtWidgets.QGraphicsScene()
        scene.addText(str(data))

        subgraph = QtWidgets.QGraphicsView()
        subgraph.setScene(scene)

        return subgraph
