import os
import time
import logging
import webbrowser

from PyQt5 import QtCore, QtGui, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils

from sas.qtgui.Utilities.UI.GridPanelUI import Ui_GridPanelUI


class BatchOutputPanel(QtWidgets.QMainWindow, Ui_GridPanelUI):
    """
    Class for stateless grid-like printout of model parameters for mutiple models
    """
    def __init__(self, parent = None, output_data=None):

        super(BatchOutputPanel, self).__init__()
        self.setupUi(self)

        self.data = output_data
        self.parent = parent
        if hasattr(self.parent, "communicate"):
            self.communicate = parent.communicate

        self.addToolbarActions()

        # file name for the dataset
        self.grid_filename = ""

        # context menu on the table
        self.tblParams.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tblParams.customContextMenuRequested.connect(self.showContextMenu)

        # Fill in the table from input data
        self.setupTable(output_data)

        # Command buttons
        self.cmdHelp.clicked.connect(self.onHelp)

    def addToolbarActions(self):
        """
        Assing actions and callbacks to the File menu items
        """
        self.actionOpen.triggered.connect(self.actionLoadData)
        self.actionOpen_with_Excel.triggered.connect(self.actionSendToExcel)
        self.actionSave.triggered.connect(self.actionSaveFile)

    def actionLoadData(self):
        """
        Open file load dialog and load a .csv file
        """
        datafile = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose a file with results", "", "CSV files (*.csv)", None,
            QtWidgets.QFileDialog.DontUseNativeDialog)[0]

        if not datafile:
            logging.info("No data file chosen.")
            return

        with open(datafile, 'r') as csv_file:
            lines = csv_file.readlines()

        self.setupTableFromCSV(lines)

    def showContextMenu(self, position):
        """
        Show context specific menu in the tab table widget.
        """
        menu = QtWidgets.QMenu()
        rows = [s.row() for s in self.tblParams.selectionModel().selectedRows()]
        num_rows = len(rows)
        if num_rows <= 0:
            return
        # Find out which items got selected and in which row
        # Select for fitting

        self.actionPlotResults = QtWidgets.QAction(self)
        self.actionPlotResults.setObjectName("actionPlot")
        self.actionPlotResults.setText(QtCore.QCoreApplication.translate("self", "Plot selected fits."))

        menu.addAction(self.actionPlotResults)

        # Define the callbacks
        self.actionPlotResults.triggered.connect(self.plotFits)
        try:
            menu.exec_(self.tblParams.viewport().mapToGlobal(position))
        except AttributeError as ex:
            logging.error("Error generating context menu: %s" % ex)
        return

    def onHelp(self):
        """
        Open a local url in the default browser
        """
        location = GuiUtils.HELP_DIRECTORY_LOCATION
        url = "/user/sasgui/perspectives/fitting/fitting_help.html#batch-fit-mode"
        try:
            webbrowser.open('file://' + os.path.realpath(location+url))
        except webbrowser.Error as ex:
            logging.warning("Cannot display help. %s" % ex)

    def plotFits(self):
        """
        Plot selected fits by sending signal to the parent
        """
        rows = [s.row() for s in self.tblParams.selectionModel().selectedRows()]
        data = self.dataFromTable(self.tblParams)
        # data['Data'] -> ['filename1', 'filename2', ...]
        # look for the 'Data' column and extract the filename
        for row in rows:
            try:
                filename = data['Data'][row]
                # emit a signal so the plots are being shown
                self.communicate.plotFromFilenameSignal.emit(filename)
            except (IndexError, AttributeError):
                # data messed up.
                return

    def dataFromTable(self, table):
        """
        Creates a dictionary {<parameter>:[list of values]} from the parameter table
        """
        assert(isinstance(table, QtWidgets.QTableWidget))
        params = {}
        #return {"sld_solvent":[1.2, 2.0, 0.0], "scale":[1.0, 2.0, 3.0]}
        for column in range(table.columnCount()):
            #pass
            value = [table.item(row, column).data(0) for row in range(table.rowCount())]
            key = table.horizontalHeaderItem(column).data(0)
            params[key] = value
        return params

    def actionSendToExcel(self):
        """
        Generates a .csv file and opens the default CSV reader
        """
        if not self.grid_filename:
            import tempfile
            tmpfile = tempfile.NamedTemporaryFile(delete=False, mode="w+", suffix=".csv")
            self.grid_filename = tmpfile.name
            data = self.dataFromTable(self.tblParams)
            t = time.localtime(time.time())
            time_str = time.strftime("%b %d %H:%M of %Y", t)
            details = "File Generated by SasView " 
            details += "on %s.\n" % time_str
            self.writeBatchToFile(data=data, tmpfile=tmpfile, details=details)
            tmpfile.close()

        try:
            from win32com.client import Dispatch
            excel_app = Dispatch('Excel.Application')
            excel_app.Workbooks.Open(self.grid_filename)
            excel_app.Visible = 1
        except Exception as ex:
            msg = "Error occured when calling Excel.\n"
            msg += ex
            self.parent.communicate.statusBarUpdateSignal.emit(msg)

    def actionSaveFile(self):
        """
        Generate a .csv file and dump it do disk
        """
        t = time.localtime(time.time())
        time_str = time.strftime("%b %d %H %M of %Y", t)
        default_name = "Batch_Fitting_"+time_str+".csv"

        wildcard = "CSV files (*.csv);;"
        kwargs = {
            'caption'   : 'Save As',
            'directory' : default_name,
            'filter'    : wildcard,
            'parent'    : None,
        }
        # Query user for filename.
        filename_tuple = QtWidgets.QFileDialog.getSaveFileName(**kwargs)
        filename = filename_tuple[0]

        # User cancelled.
        if not filename:
            return
        data = self.dataFromTable(self.tblParams)
        details = "File generated by SasView\n"
        with open(filename, 'w') as csv_file:
            self.writeBatchToFile(data=data, tmpfile=csv_file, details=details)

    def setupTableFromCSV(self, csv_data):
        """
        Create tablewidget items and show them, based on params
        """
        # Clear existing display
        self.tblParams.clear()
        # headers
        param_list = csv_data[1].rstrip().split(',')
        for i, param in enumerate(param_list):
            self.tblParams.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(param))

        # first - Chi2 and data filename
        for i_row, row in enumerate(csv_data[2:]):
            for i_col, col in enumerate(row.rstrip().split(',')):
                self.tblParams.setItem(i_row, i_col, QtWidgets.QTableWidgetItem(col))

        self.tblParams.resizeColumnsToContents()

    def setupTable(self, data):
        """
        Create tablewidget items and show them, based on params
        """
        # headers
        model = data[0][0]
        param_list = [m for m in model.model.params.keys() if ":" not in m]

        # Check if 2D model. If not, remove theta/phi

        rows = len(data)
        columns = len(param_list)
        self.tblParams.setColumnCount(columns+2)
        self.tblParams.setRowCount(rows)

        param_list.insert(0, "Data")
        param_list.insert(0, "Chi2")
        for i, param in enumerate(param_list):
            self.tblParams.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(param))

        # first - Chi2 and data filename
        for i_row, row in enumerate(data):
            # each row corresponds to a single fit
            chi2 = row[0].fitness
            filename = ""
            if hasattr(row[0].data, "sas_data"):
                filename = row[0].data.sas_data.filename
            self.tblParams.setItem(i_row, 0, QtWidgets.QTableWidgetItem(GuiUtils.formatNumber(chi2, high=True)))
            self.tblParams.setItem(i_row, 1, QtWidgets.QTableWidgetItem(str(filename)))
            # Now, all the parameters
            for i_col, param in enumerate(param_list[2:]):
                if param in row[0].param_list:
                    # parameter is on the to-optimize list - get the optimized value
                    par_value = row[0].pvec[row[0].param_list.index(param)]
                    # should we parse out errors here and store them?
                else:
                    # parameter was not varied
                    par_value = row[0].model.params[param]
                self.tblParams.setItem(i_row, i_col+2, QtWidgets.QTableWidgetItem(
                    GuiUtils.formatNumber(par_value, high=True)))

        self.tblParams.resizeColumnsToContents()

    def writeBatchToFile(self, data, tmpfile, details=""):
        """
        Helper to write result from batch into cvs file
        """
        name = tmpfile.name
        if data is None or name is None or name.strip() == "":
            return
        _, ext = os.path.splitext(name)
        separator = "\t"
        if ext.lower() == ".csv":
            separator = ","
        tmpfile.write(details)
        for col_name in data.keys():
            tmpfile.write(col_name)
            tmpfile.write(separator)
        tmpfile.write('\n')
        max_list = [len(value) for value in data.values()]
        if len(max_list) == 0:
            return
        max_index = max(max_list)
        index = 0
        while index < max_index:
            for value_list in data.values():
                if index < len(value_list):
                    tmpfile.write(str(value_list[index]))
                    tmpfile.write(separator)
                else:
                    tmpfile.write('')
                    tmpfile.write(separator)
            tmpfile.write('\n')
            index += 1

