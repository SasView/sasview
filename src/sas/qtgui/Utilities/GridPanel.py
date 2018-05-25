import os
import sys
import time
import logging
import webbrowser

from PyQt5 import QtCore, QtWidgets, QtGui

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Utilities.UI.GridPanelUI import Ui_GridPanelUI


class BatchOutputPanel(QtWidgets.QMainWindow, Ui_GridPanelUI):
    """
    Class for stateless grid-like printout of model parameters for mutiple models
    """
    ERROR_COLUMN_CAPTION = " (Err)"
    IS_WIN = (sys.platform == 'win32')
    def __init__(self, parent = None, output_data=None):

        super(BatchOutputPanel, self).__init__(parent._parent)
        self.setupUi(self)

        self.parent = parent
        if hasattr(self.parent, "communicate"):
            self.communicate = parent.communicate

        self.addToolbarActions()

        # file name for the dataset
        self.grid_filename = ""

        self.has_data = False if output_data is None else True
        # Tab numbering
        self.tab_number = 1

        # System dependent menu items
        if not self.IS_WIN:
            self.actionOpen_with_Excel.setVisible(False)

        # list of QTableWidgets, indexed by tab number
        self.tables = []
        self.tables.append(self.tblParams)

        # context menu on the table
        self.tblParams.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tblParams.customContextMenuRequested.connect(self.showContextMenu)

        # Command buttons
        self.cmdHelp.clicked.connect(self.onHelp)
        self.cmdPlot.clicked.connect(self.onPlot)

        # Fill in the table from input data
        self.setupTable(widget=self.tblParams, data=output_data)
        if output_data is not None:
            # Set a table tooltip describing the model
            model_name = output_data[0][0].model.id
            self.tabWidget.setTabToolTip(0, model_name)

    def closeEvent(self, event):
        """
        Overwrite QDialog close method to allow for custom widget close
        """
        # Maybe we should just minimize
        self.setWindowState(QtCore.Qt.WindowMinimized)
        event.ignore()

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
        self.has_data = True

    def currentTable(self):
        """
        Returns the currently shown QTabWidget
        """
        return self.tables[self.tabWidget.currentIndex()]

    def showContextMenu(self, position):
        """
        Show context specific menu in the tab table widget.
        """
        menu = QtWidgets.QMenu()
        rows = [s.row() for s in self.currentTable().selectionModel().selectedRows()]
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
        self.actionPlotResults.triggered.connect(self.onPlot)
        try:
            menu.exec_(self.currentTable().viewport().mapToGlobal(position))
        except AttributeError as ex:
            logging.error("Error generating context menu: %s" % ex)
        return

    def addTabPage(self):
        """
        Add new tab page with QTableWidget
        """
        layout = QtWidgets.QVBoxLayout()
        tab_widget = QtWidgets.QTableWidget(parent=self)
        # Same behaviour as the original tblParams
        tab_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        tab_widget.setAlternatingRowColors(True)
        tab_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        tab_widget.setLayout(layout)
        # Simple naming here.
        # One would think naming the tab with current model name would be good.
        # However, some models have LONG names, which doesn't look well on the tab bar.
        self.tab_number += 1
        tab_name = "Tab " + str(self.tab_number)
        # each table needs separate slots.
        tab_widget.customContextMenuRequested.connect(self.showContextMenu)
        self.tables.append(tab_widget)
        self.tabWidget.addTab(tab_widget, tab_name)
        # Make the new tab active
        self.tabWidget.setCurrentIndex(self.tab_number-1)

    def addFitResults(self, results):
        """
        Create a new tab with batch fitting results
        """
        self.addTabPage()
        # Update the new widget
        # Fill in the table from input data in the last/newest page
        assert(self.tables)
        self.setupTable(widget=self.tables[-1], data=results)
        self.has_data = True

        # Set a table tooltip describing the model
        model_name = results[0][0].model.id
        self.tabWidget.setTabToolTip(self.tabWidget.count()-1, model_name)


    @classmethod
    def onHelp(cls):
        """
        Open a local url in the default browser
        """
        location = GuiUtils.HELP_DIRECTORY_LOCATION
        url = "/user/qtgui/Perspectives/Fitting/fitting_help.html#batch-fit-mode"
        try:
            webbrowser.open('file://' + os.path.realpath(location+url))
        except webbrowser.Error as ex:
            logging.warning("Cannot display help. %s" % ex)

    def onPlot(self):
        """
        Plot selected fits by sending signal to the parent
        """
        rows = [s.row() for s in self.currentTable().selectionModel().selectedRows()]
        if not rows:
            msg = "Nothing to plot!"
            self.parent.communicate.statusBarUpdateSignal.emit(msg)
            return
        data = self.dataFromTable(self.currentTable())
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

    @classmethod
    def dataFromTable(cls, table):
        """
        Creates a dictionary {<parameter>:[list of values]} from the parameter table
        """
        assert(isinstance(table, QtWidgets.QTableWidget))
        params = {}
        for column in range(table.columnCount()):
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
            data = self.dataFromTable(self.currentTable())
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
        data = self.dataFromTable(self.currentTable())
        details = "File generated by SasView\n"
        with open(filename, 'w') as csv_file:
            self.writeBatchToFile(data=data, tmpfile=csv_file, details=details)

    def setupTableFromCSV(self, csv_data):
        """
        Create tablewidget items and show them, based on params
        """
        # Is this an empty grid?
        if self.has_data:
            # Add a new page
            self.addTabPage()
            # Access the newly created QTableWidget
            current_page = self.tables[-1]
        else:
            current_page = self.tblParams
        # headers
        param_list = csv_data[1].rstrip().split(',')
        # need to remove the 2 header rows to get the total data row number
        rows = len(csv_data) -2
        assert(rows > -1)
        columns = len(param_list)
        current_page.setColumnCount(columns)
        current_page.setRowCount(rows)

        for i, param in enumerate(param_list):
            current_page.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(param))

        # first - Chi2 and data filename
        for i_row, row in enumerate(csv_data[2:]):
            for i_col, col in enumerate(row.rstrip().split(',')):
                current_page.setItem(i_row, i_col, QtWidgets.QTableWidgetItem(col))

        current_page.resizeColumnsToContents()

    def setupTable(self, widget=None, data=None):
        """
        Create tablewidget items and show them, based on params
        """
        # quietly leave is nothing to show
        if data is None or widget is None:
            return

        # Figure out the headers
        model = data[0][0]

        # TODO: add a conditional for magnetic models
        param_list = [m for m in model.model.params.keys() if ":" not in m]

        # Check if 2D model. If not, remove theta/phi
        if isinstance(model.data.sas_data, Data1D):
            param_list.remove('theta')
            param_list.remove('phi')

        rows = len(data)
        columns = len(param_list)

        widget.setColumnCount(columns+2) # add 2 initial columns defined below
        widget.setRowCount(rows)

        # Insert two additional columns
        param_list.insert(0, "Data")
        param_list.insert(0, "Chi2")
        for i, param in enumerate(param_list):
            widget.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(param))

        # dictionary of parameter errors for post-processing
        # [param_name] = [param_column_nr, error_for_row_1, error_for_row_2,...]
        error_columns = {}
        # first - Chi2 and data filename
        for i_row, row in enumerate(data):
            # each row corresponds to a single fit
            chi2 = row[0].fitness
            filename = ""
            if hasattr(row[0].data, "sas_data"):
                filename = row[0].data.sas_data.filename
            widget.setItem(i_row, 0, QtWidgets.QTableWidgetItem(GuiUtils.formatNumber(chi2, high=True)))
            widget.setItem(i_row, 1, QtWidgets.QTableWidgetItem(str(filename)))
            # Now, all the parameters
            for i_col, param in enumerate(param_list[2:]):
                if param in row[0].param_list:
                    # parameter is on the to-optimize list - get the optimized value
                    par_value = row[0].pvec[row[0].param_list.index(param)]
                    # parse out errors and store them for later use
                    err_value = row[0].stderr[row[0].param_list.index(param)]
                    if param in error_columns:
                        error_columns[param].append(err_value)
                    else:
                        error_columns[param] = [i_col, err_value]
                else:
                    # parameter was not varied
                    par_value = row[0].model.params[param]

                widget.setItem(i_row, i_col+2, QtWidgets.QTableWidgetItem(
                    GuiUtils.formatNumber(par_value, high=True)))

        # Add errors
        error_list = list(error_columns.keys())
        for error_param in error_list[::-1]: # must be reverse to keep column indices
            # the offset for the err column: +2 from the first two extra columns, +1 to append this column
            error_column = error_columns[error_param][0]+3
            error_values = error_columns[error_param][1:]
            widget.insertColumn(error_column)

            column_name = error_param + self.ERROR_COLUMN_CAPTION
            widget.setHorizontalHeaderItem(error_column, QtWidgets.QTableWidgetItem(column_name))

            for i_row, error in enumerate(error_values):
                item = QtWidgets.QTableWidgetItem(GuiUtils.formatNumber(error, high=True))
                # Fancy, italic font for errors
                font = QtGui.QFont()
                font.setItalic(True)
                item.setFont(font)
                widget.setItem(i_row, error_column, item)

        # resize content
        widget.resizeColumnsToContents()

    @classmethod
    def writeBatchToFile(cls, data, tmpfile, details=""):
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


class BatchInversionOutputPanel(BatchOutputPanel):
    """
        Class for stateless grid-like printout of P(r) parameters for any number
        of data sets
    """
    def __init__(self, parent = None, output_data=None):

        super(BatchInversionOutputPanel, self).__init__(parent, output_data)
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("GridPanelUI", "Batch P(r) Results"))

    def setupTable(self, data):
        """
        Create tablewidget items and show them, based on params
        """
        # headers
        param_list = ['Filename', 'Rg [Å]', 'Chi^2/dof', 'I(Q=0)', 'Oscillations',
                      'Background [Å^-1]', 'P+ Fraction', 'P+1-theta Fraction',
                      'Calc. Time [sec]']

        keys = data.keys()
        rows = len(keys)
        columns = len(param_list)
        self.tblParams.setColumnCount(columns)
        self.tblParams.setRowCount(rows)

        for i, param in enumerate(param_list):
            self.tblParams.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(param))

        # first - Chi2 and data filename
        for i_row, (filename, pr) in enumerate(data.items()):
            out = pr.out
            cov = pr.cov
            if out is None:
                logging.warning("P(r) for {} did not converge.".format(filename))
                continue
            self.tblParams.setItem(i_row, 0, QtWidgets.QTableWidgetItem(
                "{}".format(filename)))
            self.tblParams.setItem(i_row, 1, QtWidgets.QTableWidgetItem(
                "{:.3g}".format(pr.rg(out))))
            self.tblParams.setItem(i_row, 2, QtWidgets.QTableWidgetItem(
                "{:.3g}".format(pr.chi2[0])))
            self.tblParams.setItem(i_row, 3, QtWidgets.QTableWidgetItem(
                "{:.3g}".format(pr.iq0(out))))
            self.tblParams.setItem(i_row, 4, QtWidgets.QTableWidgetItem(
                "{:.3g}".format(pr.oscillations(out))))
            self.tblParams.setItem(i_row, 5, QtWidgets.QTableWidgetItem(
                "{:.3g}".format(pr.background)))
            self.tblParams.setItem(i_row, 6, QtWidgets.QTableWidgetItem(
                "{:.3g}".format(pr.get_positive(out))))
            self.tblParams.setItem(i_row, 7, QtWidgets.QTableWidgetItem(
                "{:.3g}".format(pr.get_pos_err(out, cov))))
            self.tblParams.setItem(i_row, 8, QtWidgets.QTableWidgetItem(
                "{:.2g}".format(pr.elapsed)))

        self.tblParams.resizeColumnsToContents()

    @classmethod
    def onHelp(cls):
        """
        Open a local url in the default browser
        """
        location = GuiUtils.HELP_DIRECTORY_LOCATION
        url = "/user/sasgui/perspectives/pr/pr_help.html#batch-pr-mode"
        try:
            webbrowser.open('file://' + os.path.realpath(location + url))
        except webbrowser.Error as ex:
            logging.warning("Cannot display help. %s" % ex)

    def closeEvent(self, event):
        """Tell the parent window the window closed"""
        self.parent.batchResultsWindow = None
        event.accept()
