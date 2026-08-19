import random  # for testing
import sys  # for testing
from copy import deepcopy
from logging import getLogger

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  # SasView MuMag uses .backend_qt5agg
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QCursor, QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableWidgetItem,
    QWidget,
)

from sas.qtgui.Utilities.MultivariateCurveResolution.MultivariateCurveResolutionLib import (
    Curve,
    CurveContainer,
    MCRALSLib,
    ProcessContainer,
)
from sas.qtgui.Utilities.MultivariateCurveResolution.UI.MultivariateCurveResolutionUI import Ui_MCRTool

log = getLogger("MCRALS")

import sas.qtgui.Utilities.MultivariateCurveResolution.constants as const

""" Utility functions """

def stringToFloatWithCommas(x: str) -> float:
    try:
        return float(x.replace(',', '.'))
    except:
        raise ValueError


""" Main class """

class MCRTool(QMainWindow, Ui_MCRTool):
    """ Main window for the MCR-ALS tool """

    selected_known_species: list[int] = []

    def __init__(self, parent=None):
        super().__init__()

        self.parent = parent
        self.setupUi(self)

        # Data
        self.MCRprocess = ProcessContainer()
        self.curve_container = self.MCRprocess.curve_container
        self.curves = self.curve_container.curves

        self.curve_item_container = CurveItemContainer(self.curve_container)
        self.curve_items = self.curve_item_container.curve_items

        # Connect buttons
        self.ImportDataButton.clicked.connect(self.onImportData)
        self.ImportDataButton.clicked.connect(self.refreshPrepareDataTab)
        self.ResetUnitsButton.clicked.connect(self.curve_item_container.resetUnits)
        self.ResetUnitsButton.clicked.connect(self.refreshPrepareDataTab)
        self.ClearGraphsViewButton.clicked.connect(self.GraphsViewList.clear)
        self.SelectCurvesButton.clicked.connect(self.onRunPCA)

        self.InitialEstimatesNextButton.clicked.connect(self.onNextFromInitialEstimates)
        self.PreviewEstimateButton.clicked.connect(self.previewInitialEstimateCurve)
        self.MostDissimilarOption.clicked.connect(self.refreshInitialEstimatesTab)
        self.ChiRankOption.clicked.connect(self.refreshInitialEstimatesTab)
        self.ManualSelectionOption.clicked.connect(self.refreshInitialEstimatesTab)
        self.NumberSpeciesSpinner.valueChanged.connect(self.refreshInitialEstimatesTab)
        self.KnownSpeciesSpinner.valueChanged.connect(self.refreshInitialEstimatesTab)
        self.SelectKnownSpeciesButton.clicked.connect(self.toggleKnownSpecies)
        self.SelectKnownSpeciesButton.clicked.connect(self.refreshInitialEstimatesTab)
        self.PreviewSelectedCurvesButton.clicked.connect(self.previewAllCurves)
        self.DeleteSelectedCurvesButton.clicked.connect(self.promptDeleteSelectedCurves)

        self.RunMcralsButton.clicked.connect(self.onFirstRunMCRALS)
        self.AmyloidFilibrationPresetOption.clicked.connect(self.refreshConstraintsTab)
        self.TitrationSeriesPresetOption.clicked.connect(self.refreshConstraintsTab)
        self.SecSaxsPresetOption.clicked.connect(self.refreshConstraintsTab)
        self.OtherPresetOption.clicked.connect(self.noConstraintsPreset)
        self.NonnegativeSpectraToggle.clicked.connect(self.noConstraintsPreset)
        self.NonnegativeConcentrationsToggle.clicked.connect(self.noConstraintsPreset)
        self.ClosureCheckBox.clicked.connect(self.noConstraintsPreset)
        self.UnimodalityCheckBox.clicked.connect(self.noConstraintsPreset)
        self.SpectraEqualityCheckBox.clicked.connect(self.noConstraintsPreset)
        self.SetConcentrationProfileButton.clicked.connect(self.importConcentrationProfile)

        self.AcceptSolutionButton.clicked.connect(self.onSelectCombination)
        self.ResultsList.itemClicked.connect(self.refreshMCRALSTab)
        self.RerunMCRALSButton.clicked.connect(self.onRerunMCRALS)

        self.GenerateReportButton.clicked.connect(self.onGenerateReport)
        self.RunErrorEstimationButton.clicked.connect(self.onRunErrorEstimation)
        self.RunErrorEstimationButton.clicked.connect(self.refreshErrorAnalysisTab)
        self.SkipErrorsButton.clicked.connect(self.refreshErrorAnalysisTab)

        self.ExportHTMLReportButton.clicked.connect(self.onHTMLReport)
        self.ExportPDFReportButton.clicked.connect(self.onPDFReport)
        self.SaveCurvesButton.clicked.connect(self.onSaveCurves)

        # Layouts of main tabs
        self.PrepareDataTab.setLayout(self.PrepareDataTabLayout)
        self.InitialEstimatesTab.setLayout(self.InitialEstimatesTabLayout)
        self.ConstraintsTab.setLayout(self.ConstraintsTabLayout)
        self.MCRALSTab.setLayout(self.MCRALSTabLayout)
        self.ErrorAnalysisTab.setLayout(self.ErrorAnalysisTabLayout)
        self.ReportTab.setLayout(self.ReportTabLayout)

        # Input validators
        CutInputValidator = QDoubleValidator(bottom=0, top=float('inf'), decimals=const.MAX_NUMBER_INPUT_DECIMALS)
        self.AbsoluteCutInput.setValidator(CutInputValidator)
        self.HoltzerCutInput.setValidator(CutInputValidator)
        self.KratkyCutInput.setValidator(CutInputValidator)
        self.PorodCutInput.setValidator(CutInputValidator)

        self.ConvergenceCriterionInput.setValidator(QDoubleValidator(bottom=0, top=100.0, decimals=const.MAX_NUMBER_INPUT_DECIMALS))
        self.MaxIterationsInput.setValidator(QIntValidator(bottom=1, top=const.MAX_MCRALS_ITERATIONS))

        self.ErrorIterationsInput.setValidator(QIntValidator(bottom=1, top=const.MAX_ERROR_ITERATIONS))

        # Progression handling
        self.MainTabs.currentChanged.connect(self.refreshTab)

        # Render CurveList
        self.CurveList.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.CurveList.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        for column, width in enumerate(const.CURVE_LIST_COLUMN_WIDTHS):
            self.CurveList.setColumnWidth(column, width)

        self.CurveList.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        self.CurveList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.CurveList.customContextMenuRequested.connect(self.customCurveListContextMenu)

        # Render OutlierTable
        self.OutlierTable.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.OutlierTable.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        for column, width in enumerate(const.OUTLIER_TABLE_COLUMN_WIDTHS):
            self.OutlierTable.setColumnWidth(column, width)

        self.OutlierTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # Render ConcentrationErrorsList and SpectraErrorsList
        self.ConcentrationErrorsList.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.ConcentrationErrorsList.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.SpectraErrorsList.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.SpectraErrorsList.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        for column, width in enumerate(const.ERRORS_LIST_COLUMN_WIDTHS):
            self.ConcentrationErrorsList.setColumnWidth(column, width)
            self.SpectraErrorsList.setColumnWidth(column, width)

        self.ConcentrationErrorsList.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.SpectraErrorsList.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # Begin
        self.updateTabProgression(0)

    """ Main progression, ordered by Tab origin """

    def onRunPCA(self):

        # Collect preprocessing parameters
        self.MCRprocess.n_curves      = self.curve_item_container.countActiveCurves()
        self.MCRprocess.n_tot_curves  = len(self.curves)
        self.MCRprocess.unused_curves = self.MCRprocess.n_tot_curves - self.MCRprocess.n_curves

        self.MCRprocess.a_cut, self.MCRprocess.h_cut, self.MCRprocess.k_cut, self.MCRprocess.p_cut = self.getQCuts()

        # Preprocess curves
        resample_checked = self.ResampleCheckedOption.isChecked()
        scale_checked    = self.ScaleCheckedOption.isChecked()

        for curve_item in self.curve_items.values():
            curve = curve_item.curve
            curve.is_removed = not curve_item.active
            if not curve.is_removed:
                curve.setUnits(curve_item.units)
                curve.is_resampled = (resample_checked == curve_item.resample_checked)
                curve.is_auto_scaled = (scale_checked == curve_item.scale_checked)

        # Run PCA
        figure = MCRALSLib.PCA(self.MCRprocess)

        # Render 'PCA & initial estimates' tab
        self.NumberSpeciesSpinner.setMaximum(min(self.MCRprocess.n_curves - 1, const.MAX_NUMBER_SPECIES))
        self.KnownSpeciesSpinner.setMaximum(min(self.MCRprocess.n_curves - 1, const.MAX_NUMBER_SPECIES))

        # Render Scree plot and eigenvectors
        self.EigenvalueScreeLabel.setText(f"Heuristic on Scree plot suggests {self.MCRprocess.pca_significant_components} significant components\n(elbow at PC{self.MCRprocess.pca_significant_components}, explains {self.MCRprocess.pca_sc_variance:.5%} of variance)")

        self.EigenvalueScreeBox.layout().removeWidget(self.EigenvalueScreePlot)
        self.EigenvalueScreePlot.close()
        self.EigenvalueScreePlot = FigureCanvas(figure)
        self.EigenvalueScreePlot.draw()
        self.EigenvalueScreeBox.layout().insertWidget(0, self.EigenvalueScreePlot, 1, Qt.AlignCenter)
        self.EigenvalueScreeBox.layout().update()

        # Render InitialEstimatesList and SelectPreviewEstimateOption
        self.SelectPreviewEstimateOption.clear()
        self.SelectPreviewEstimateOption.addItem("Select curve")
        self.InitialEstimatesList.clear()
        for curve in self.curves.values():
            if not curve.is_removed:
                self.SelectPreviewEstimateOption.addItem(curve.name)
                item = QListWidgetItem(curve.name)
                item.setCheckState(Qt.Unchecked)
                self.InitialEstimatesList.addItem(item)

        self.InitialEstimatesList.itemChanged.connect(self.refreshInitialEstimatesTab)

        # Go to 'PCA & initial estimates' tab
        self.updateTabProgression(1)

    def onNextFromInitialEstimates(self):

        # Collect parameters
        self.MCRprocess.n_species = int(self.NumberSpeciesSpinner.text())
        self.MCRprocess.n_pure_spectra = int(self.KnownSpeciesSpinner.text())
        self.MCRprocess.pure_spectra = self.selected_known_species

        self.MCRprocess.initial_estimates = self.MCRprocess.pure_spectra.copy()
        for i in range(self.InitialEstimatesList.count()):
            item = self.InitialEstimatesList.item(i)
            if item.checkState() == Qt.Checked:
                self.MCRprocess.initial_estimates.append(self.curve_container.getIdFromName(item.text()))

        # Get initial estimates
        self.MCRprocess.initial_estimate_method = self.getInitialEstimatesMethod()

        MCRALSLib.InitialEstimates(
            process=self.MCRprocess,
            mode=const.INITIAL_ESTIMATE_MODE[self.MCRprocess.initial_estimate_method]
        )

        # Render 'Constraints' tab

        # Render ConstraintsBox and ConstraintsPresetBox
        self.AmyloidFilibrationPresetOption.setChecked(True) # Default option
        if self.MCRprocess.n_pure_spectra == 0:
            self.SecSaxsPresetOption.setEnabled(False)
            self.SpectraEqualityCheckBox.setEnabled(False)
            self.SpectraEqualityLabel.setEnabled(False)
        else:
            self.SecSaxsPresetOption.setEnabled(True)
            self.SpectraEqualityCheckBox.setEnabled(True)
            self.SpectraEqualityLabel.setEnabled(True)
        self.SpectraEqualityLabel.setText(f"Fix spectra profile(s) of {self.MCRprocess.n_pure_spectra} known species:")

        # Render ChosenInitialEstimatesList
        self.ChosenInitialEstimatesList.clear()
        for idx, curve_ID in enumerate(self.MCRprocess.initial_estimates):
            self.ChosenInitialEstimatesList.addItem(f"{idx + 1}. {self.curves[curve_ID].name}" + (" (known)" if curve_ID in self.MCRprocess.pure_spectra else ""))

        # Go to 'Constraints' tab
        self.updateTabProgression(2)
        self.refreshConstraintsTab()

    def onFirstRunMCRALS(self):

        if not self.popupPrompt(header="Run MCRALS", msg="Running MCR-ALS might take a moment.\nDo you want to run it?"):
            return

        # Collect contraints parameters
        if self.AmyloidFilibrationPresetOption.isChecked():
            self.MCRprocess.constraints_preset = "Amyloid filibration"
        elif self.TitrationSeriesPresetOption.isChecked():
            self.MCRprocess.constraints_preset = "Titration series"
        elif self.SecSaxsPresetOption.isChecked():
            self.MCRprocess.constraints_preset = "SEC-SAXS"
        else:
            self.MCRprocess.constraints_preset = "Other"

        self.MCRprocess.convergence_criterion = stringToFloatWithCommas(self.ConvergenceCriterionInput.text())
        self.MCRprocess.max_iterations = int(self.MaxIterationsInput.text())

        self.MCRprocess.constraints.clear()
        if self.NonnegativeConcentrationsToggle.isChecked():
            self.MCRprocess.constraints.append(1)
        if self.NonnegativeSpectraToggle.isChecked():
            self.MCRprocess.constraints.append(2)
        if self.UnimodalityCheckBox.isChecked():
            self.MCRprocess.constraints.append(3)
        if self.ClosureCheckBox.isChecked():
            self.MCRprocess.constraints.append(4)
            closure = stringToFloatWithCommas(self.ClosureInput.text())
        if self.imported_concentration_profile_flag:
            self.MCRprocess.constraints.append(5)
        if self.SpectraEqualityCheckBox.isChecked():
            self.MCRprocess.constraints.append(6)

        self.runMCRALS()

    def runMCRALS(self):

        # Run MCRALS with constraints
        MCRALSLib.MCRLAS(self.MCRprocess)

        # Render 'MCR-ALS' Tab

        # Render RecoveredProfilesPlot
        figure = MCRALSLib.plot_recovered_profiles(self.MCRprocess)

        self.RecoveredProfilesBox.layout().removeWidget(self.RecoveredProfilesPlot)
        self.RecoveredProfilesPlot.close()
        self.RecoveredProfilesPlot = FigureCanvas(figure)
        self.RecoveredProfilesPlot.draw()
        self.RecoveredProfilesBox.layout().insertWidget(0, self.RecoveredProfilesPlot, 1, Qt.AlignCenter)
        self.RecoveredProfilesBox.layout().update()

        # Render ResultsList
        self.ResultsList.clear()

        width_hint = 0
        height_hint = 0
        for tag in const.RESULTS_LIST_COMBINATION_LABELS:
            avg_chi = random.random() * 2
            avg_coeff_deter = random.random()
            radio_button = QRadioButton(f"{tag}\n<χ²>={avg_chi: 1.2f}    ·    <R²>={avg_coeff_deter: 2.1%}")
            list_item = QListWidgetItem()
            list_item.setSizeHint(radio_button.sizeHint())
            width_hint = max(width_hint, radio_button.sizeHint().width())
            height_hint += radio_button.sizeHint().height()
            self.ResultsList.addItem(list_item)
            self.ResultsList.setItemWidget(list_item, radio_button)

        self.ResultsList.itemWidget(self.ResultsList.item(0)).setChecked(True)

        self.ResultsList.setMinimumWidth(width_hint + const.RESULTS_LIST_EXTRA_SIZE[0])
        self.ResultsList.setMinimumHeight(height_hint + const.RESULTS_LIST_EXTRA_SIZE[1])

        # Render OutlierTable
        self.OutlierTable.setRowCount(0)

        for curve in self.curves.values():
            if curve.is_removed: continue

            row = self.OutlierTable.rowCount()
            self.OutlierTable.insertRow(row)

            active_checkbox_widget = QWidget()
            active_checkbox = ActiveCheckBox(active_checkbox_widget, curve.ID)
            active_checkbox_widget.setProperty("active_checkbox", active_checkbox)
            active_checkbox.setCheckState(Qt.Unchecked if (curve.ID in self.MCRprocess.eliminated_curves) else Qt.Checked)
            active_checkbox_layout = QHBoxLayout(active_checkbox_widget)
            active_checkbox_layout.addWidget(active_checkbox)
            active_checkbox_layout.setAlignment(Qt.AlignCenter)
            active_checkbox_layout.setContentsMargins(1, 1, 0, 0)
            self.OutlierTable.setCellWidget(row, 0, active_checkbox_widget)
            active_checkbox.onToggleSignal.connect(self.toggleOutlierItem)

            if curve.ID in self.MCRprocess.eliminated_curves:
                name_label = QLabel(curve.name + const.REMOVED_TAG)
                name_label.setEnabled(False)
            else:
                name_label = QLabel(curve.name)
            name_label.setContentsMargins(5, 0, 0, 0)
            name_label.setEnabled(curve.ID not in self.MCRprocess.eliminated_curves)
            self.OutlierTable.setCellWidget(row, 1, name_label)

            chi_value = float(str(random.random() * 2)[:random.randint(3, 6)])
            chi_label = QLabel(const.CHI_TAG + str(chi_value))
            chi_item = ChiItem(chi_value)
            chi_label.setEnabled(curve.ID not in self.MCRprocess.eliminated_curves)
            self.OutlierTable.setCellWidget(row, 2, chi_label)
            self.OutlierTable.setItem(row, 2, chi_item)

        self.OutlierTable.sortItems(2, Qt.DescendingOrder)

        self.OutlierRemovalLabel.setText(f"{self.MCRprocess.n_eliminated_curves} outlier(s) removed in total")

        # Go to 'MCR-ALS' tab
        self.updateTabProgression(3)

    def onRerunMCRALS(self):

        if not self.popupPrompt(header="Run MCRALS", msg="Rerunning MCR-ALS might take a moment.\nDo you want to rerun it?"):
            return

        # collect selected outliers
        outliers = []
        for row in range(self.OutlierTable.rowCount()):
            if self.OutlierTable.cellWidget(row, 0).property("active_checkbox").checkState() == Qt.Unchecked:
                name = self.OutlierTable.cellWidget(row, 1).text()
                if name.endswith(const.REMOVED_TAG):
                    name = name[:-len(const.REMOVED_TAG)]
                ID = self.curve_container.getIdFromName(name)
                outliers.append(ID)

        # remove outliers
        if  MCRALSLib.remove_outliers(self.MCRprocess, outliers):
            # Run MCRALS
            self.runMCRALS()

    def onSelectCombination(self):

        # Collect parameters
        for i in range(self.ResultsList.count()):
            radio_button = self.ResultsList.itemWidget(self.ResultsList.item(i))
            if radio_button.isChecked():
                self.MCRprocess.combination = radio_button.text().split("\n")[0]

        # Reset 'Error estimation' Tab
        self.MCRprocess.done_error_estimation = False

        # Go to 'Error analysis' tab
        self.updateTabProgression(4)
        self.refreshErrorAnalysisTab()

    plot_conc_errors_mask: list[bool]
    plot_abss_errors_mask: list[bool]

    def onRunErrorEstimation(self):

        if not self.popupPrompt(header="Run Monte Carlo", msg=f"Running {self.ErrorIterationsInput.text()} Monte Carlo simulations might take a moment.\nDo you want to run them?"):
            return

        # Collect parameters
        self.MCRprocess.done_error_estimation = True
        self.MCRprocess.error_iterations = int(self.ErrorIterationsInput.text())
        self.MCRprocess.error_noise = self.NoiseModelCombobox.currentText()

        # Run error estimation
        MCRALSLib.MonteCarlo(self.MCRprocess)

        self.plot_conc_errors_mask = [True] * self.MCRprocess.n_species
        self.plot_abss_errors_mask = [True] * self.MCRprocess.n_species

        # Render ConcentrationErrorsList and SpectraErrorsList
        self.ConcentrationErrorsList.setRowCount(0)
        self.SpectraErrorsList.setRowCount(0)

        for idx, curve_ID in enumerate(self.MCRprocess.initial_estimates):
            row = self.ConcentrationErrorsList.rowCount()
            self.ConcentrationErrorsList.insertRow(row)
            self.SpectraErrorsList.insertRow(row)

            # Show / hide button
            conc_button = ShowHideButton(self.ConcentrationErrorsList.cellWidget(row, 0), idx)
            abss_button = ShowHideButton(self.SpectraErrorsList.cellWidget(row, 0), idx)
            self.ConcentrationErrorsList.setCellWidget(row, 0, conc_button)
            self.SpectraErrorsList.setCellWidget(row, 0, abss_button)
            conc_button.onClickSignal.connect(self.updateConcentrationErrorsPlot)
            abss_button.onClickSignal.connect(self.updateSpectraErrorsPlot)

            # Name
            conc_label = QLabel(self.curves[curve_ID].name)
            abss_label = QLabel(self.curves[curve_ID].name)
            conc_label.setContentsMargins(5, 0, 0, 0)
            abss_label.setContentsMargins(5, 0, 0, 0)
            self.ConcentrationErrorsList.setCellWidget(row, 1, conc_label)
            self.SpectraErrorsList.setCellWidget(row, 1, abss_label)

        # Render ConcentrationErrorsPlot and SpectraErrorsPlot
        self.renderErrorsPlots()

    def onGenerateReport(self):

        # Prepare MCRALS-analysis data for saving
        MCRALSLib.GenerateReport(self.MCRprocess)

        # Render 'Report' Tab
        self.CombinationUsedLabel.setText(self.MCRprocess.combination)
        self.SpeciesSearchedForLabel.setText(f"{self.MCRprocess.n_species} ({self.MCRprocess.n_pure_spectra} fixed)")
        self.NumberCurvesUsedLabel.setText(f"{self.MCRprocess.n_curves} of {self.MCRprocess.n_tot_curves} ({self.MCRprocess.n_eliminated_curves} outlier(s) removed)")
        self.CurvesReconstructedLabel.setText(f"({self.MCRprocess.n_species} species x {self.MCRprocess.n_curves} curves)")

        # Go to 'Report' Tab
        self.updateTabProgression(5)

    def updateTabProgression(self, tab: int):
        """ For actions that update progression """
        for i in range(tab + 1):
            self.MainTabs.setTabEnabled(i, True)
        for i in range(tab + 1, 6):
            self.MainTabs.setTabEnabled(i, False)
        self.MainTabs.setCurrentIndex(tab)


    """ 'refreshTab' functions responsible for the workflow and interactive UI """

    def refreshPrepareDataTab(self, *_):
        units_defined   = self.curve_item_container.checkUnitsDefined()
        selected_curves = self.curve_item_container.countActiveCurves()
        units_changed   = self.curve_item_container.checkUnitsChanged()
        self.SelectCurvesButton.setEnabled(         units_defined and (selected_curves >= 2))
        self.PreviewSelectedCurvesButton.setEnabled(units_defined and (selected_curves > 0))
        self.ResetUnitsButton.setEnabled(           selected_curves > 0)

    def refreshInitialEstimatesTab(self, *_):
        n_species = int(self.NumberSpeciesSpinner.value())
        n_known   = int(self.KnownSpeciesSpinner.value())
        selected  = self.countInitialEstimatesListSelected()
        # self.selected_known_species

        if n_species < n_known:
            self.NumberSpeciesSpinner.setValue(n_known)
            n_species = n_known

        if (n_known != len(self.selected_known_species)):
            self.resetInitialEstimatesListFromKnownSelected()

        if (n_known == len(self.selected_known_species)) and (n_known > 0):
            self.SelectKnownSpeciesButton.setText("Reset known species")
        else:
            self.SelectKnownSpeciesButton.setText("Select known species")

        self.SelectKnownSpeciesButton.setEnabled(
            (n_known > 0) and ((n_known == selected) or (len(self.selected_known_species) > 0))
        )

        method = self.getInitialEstimatesMethod()
        target = const.INITIAL_ESTIMATE_METHOD_CURVE_REQUIREMENTS[method]
        if target == -1:
            target = n_species
        self.InitialEstimatesNextButton.setEnabled(
            ((n_known == 0) or (len(self.selected_known_species) > 0))
            and
            ((target <= selected + n_known) and (target <= n_species))
        )

    def refreshConstraintsTab(self, *_) -> None:
        if self.OtherPresetOption.isChecked():
            self.NonnegativityBox.setEnabled(True)
            self.ClosureBox.setEnabled(True)
            self.UnimodalityBox.setEnabled(True)
            self.EqualityBox.setEnabled(True)
        else:
            if self.AmyloidFilibrationPresetOption.isChecked(): preset_name = "Amyloid filibration"
            if self.TitrationSeriesPresetOption.isChecked(): preset_name = "Titration series"
            if self.SecSaxsPresetOption.isChecked(): preset_name = "SEC-SAXS"

            preset = const.CONSTRAINTS_PRESETS[preset_name]

            self.NonnegativityBox.setEnabled(preset[0] or preset[1])
            self.NonnegativeSpectraToggle.setChecked(preset[0])
            self.NonnegativeConcentrationsToggle.setChecked(preset[1])

            self.ClosureBox.setEnabled(preset[2])
            self.ClosureCheckBox.setChecked(preset[2])

            self.UnimodalityBox.setEnabled(preset[3])
            self.UnimodalityCheckBox.setChecked(preset[3])

            self.EqualityBox.setEnabled(preset[4] or preset[5])
            self.SpectraEqualityCheckBox.setChecked(preset[4])

    def refreshMCRALSTab(self, *_):
        # (Re-)render OutlierTable
        pass

    def refreshErrorAnalysisTab(self, *_):
        if self.SkipErrorsButton.isChecked():
            self.ErrorEstimationBox.setEnabled(False)
            self.GenerateReportButton.setEnabled(True)
        else:
            self.ErrorEstimationBox.setEnabled(True)
            self.GenerateReportButton.setEnabled(self.MCRprocess.done_error_estimation)

    def refreshReportTab(self, *_):
        pass

    def refreshTab(self, tab: int):
        """ For actions that update UI """
        if   tab == 0: self.refreshPrepareDataTab()
        elif tab == 1: self.refreshInitialEstimatesTab()
        elif tab == 2: self.refreshConstraintsTab()
        elif tab == 3: self.refreshMCRALSTab()
        elif tab == 4: self.refreshErrorAnalysisTab()
        elif tab == 5: self.refreshReportTab()

    """ Other functionality, in order of Tab affected """

    """ Import & prepare data Tab """

    def onImportData(self):

        units_mode = self.ImportDataUnitsOption.currentIndex()
        if units_mode == 1: units = "A"
        elif units_mode == 2: units = "N"
        else: units = ""

        directory = MCRALSLib.directory_popup()

        imported_curves = MCRALSLib.import_curve_files(
            process=self.MCRprocess,
            input_directory=directory
        )

        if imported_curves is not None:
            for exp in range(len(imported_curves)):

                self.MCRprocess.experiments.append([])

                for curve in imported_curves[exp]:

                    self.MCRprocess.experiments[-1].append(curve.ID)

                    if units != "":
                        curve.setUnits(units)

                    self.addCurveItem(curve)

    def addCurveItem(self, curve: Curve) -> int:
        """ Add the imported curve to the list of curves """

        curve_item = self.curve_item_container.addItem(curve)

        row = self.CurveList.rowCount()
        self.CurveList.insertRow(row)

        # Active checkbox
        active_checkbox_widget = QWidget()
        active_checkbox = ActiveCheckBox(active_checkbox_widget, curve.ID)
        active_checkbox.setCheckState(Qt.Checked)
        active_checkbox_layout = QHBoxLayout(active_checkbox_widget)
        active_checkbox_layout.addWidget(active_checkbox)
        active_checkbox_layout.setAlignment(Qt.AlignCenter)
        active_checkbox_layout.setContentsMargins(1, 1, 0, 0)
        self.CurveList.setCellWidget(row, 0, active_checkbox_widget)

        curve_item.linkActiveCheckbox(active_checkbox)
        active_checkbox.onToggleSignal.connect(self.toggleCurveItem)
        active_checkbox.toggled.connect(self.refreshPrepareDataTab)

        # Name
        name_label = QLabel(curve.name)
        name_label.setContentsMargins(5, 0, 0, 0)
        self.CurveList.setCellWidget(row, 1, name_label)

        # Units
        unit_button = UnitsToggleButton(self.CurveList.cellWidget(row, 2), curve.ID, curve.units)
        self.CurveList.setCellWidget(row, 2, unit_button)

        curve_item.linkUnitsToggleButton(unit_button)
        unit_button.clicked.connect(self.refreshPrepareDataTab)

        # Fixes
        fixes_widget = QWidget()
        resample_checkbox = QCheckBox("R")
        scale_checkbox = QCheckBox("S")
        fixes_layout = QHBoxLayout(fixes_widget)
        fixes_layout.addWidget(resample_checkbox)
        fixes_layout.addWidget(scale_checkbox)
        fixes_layout.setAlignment(Qt.AlignCenter)
        fixes_layout.setContentsMargins(1, 1, 0, 0)
        self.CurveList.setCellWidget(row, 3, fixes_widget)

        curve_item.linkFixesCheckboxes(resample_checkbox, scale_checkbox)

        # View button
        view_button = ViewCurveButton(self.CurveList.cellWidget(row, 4), curve.ID)
        self.CurveList.setCellWidget(row, 4, view_button)

        view_button.onClickSignal.connect(self.previewCurve)

    def toggleCurveItem(self, curve_ID: int, active: bool):
        # Toggle in CurveList
        name = self.curves[curve_ID].name
        row = 0
        while (self.CurveList.cellWidget(row, 1).text() != name):
            row += 1
        for column in range(1, 5):
            self.CurveList.cellWidget(row, column).setEnabled(active)

    def getQCuts(self) -> tuple[float]:
        a_cut = stringToFloatWithCommas(self.AbsoluteCutInput.text())
        h_cut = stringToFloatWithCommas(self.HoltzerCutInput.text())
        k_cut = stringToFloatWithCommas(self.KratkyCutInput.text())
        p_cut = stringToFloatWithCommas(self.PorodCutInput.text())
        if a_cut == 0: a_cut = float('inf')
        if h_cut == 0: h_cut = float('inf')
        if k_cut == 0: k_cut = float('inf')
        if p_cut == 0: p_cut = float('inf')
        return a_cut, h_cut, k_cut, p_cut

    def preparePreviewProcess(self) -> ProcessContainer:
        process = deepcopy(self.MCRprocess)
        process.a_cut, process.h_cut, process.k_cut, process.p_cut = self.getQCuts()

        resample_checked = self.ResampleCheckedOption.isChecked()
        scale_checked    = self.ScaleCheckedOption.isChecked()

        for curve_item in self.curve_items.values():
            curve = process.curve_container.curves[curve_item.curve.ID]
            curve.is_removed = not curve_item.active
            if not curve.is_removed:
                curve.setUnits(curve_item.units)
                curve.is_resampled = (resample_checked == curve_item.resample_checked)
                curve.is_auto_scaled = (scale_checked == curve_item.scale_checked)

        return process

    def previewCurve(self, curve_ID: int):
        figure = MCRALSLib.preview_curve_all_reps(self.preparePreviewProcess(), curve_ID)

        if figure is not None:
            canvas = FigureCanvas(figure)
            canvas.draw()
            item = QListWidgetItem()
            item.setSizeHint(QSize(200, 1200))
            self.GraphsViewList.insertItem(0, item)
            self.GraphsViewList.setItemWidget(item, canvas)

    def previewAllCurves(self):
        figure = MCRALSLib.preview_data(self.preparePreviewProcess())

        if figure is not None:
            canvas = FigureCanvas(figure)
            canvas.draw()
            item = QListWidgetItem()
            item.setSizeHint(QSize(200, 1200))
            self.GraphsViewList.insertItem(0, item)
            self.GraphsViewList.setItemWidget(item, canvas)

    def promptDeleteSelectedCurves(self):
        if self.popupPrompt(header="Confirm deletion", msg=f"Are you sure you want to delete {self.curve_item_container.countActiveCurves()} curves?"):
            for row in reversed(range(self.CurveList.rowCount())):

                name = self.CurveList.cellWidget(row, 1).text()
                ID = self.curve_container.getIdFromName(name)
                curve_item = self.curve_items[ID]

                if curve_item.active:
                    if self.MCRprocess.deleteCurve(curve_item.curve):
                        self.curve_item_container.deleteCurve(ID)
                        self.CurveList.removeRow(row)

            self.updateTabProgression(0)
            self.refreshPrepareDataTab()

    selected_row_in_curve_list: int = -1

    def customCurveListContextMenu(self):
        self.selected_row_in_curve_list = self.CurveList.rowAt(self.CurveList.viewport().mapFromGlobal(QCursor.pos()).y())
        popup = QMenu()
        delete_curve = QAction("Delete curve")
        delete_curve.triggered.connect(self.promptDeleteClickedCurve)
        popup.addAction(delete_curve)
        popup.exec_(QCursor.pos())

    def promptDeleteClickedCurve(self, *_):
        row = self.selected_row_in_curve_list
        ID = self.curve_container.getIdFromName(self.CurveList.cellWidget(row, 1).text())
        curve = self.curves[ID]

        if self.popupPrompt(header="Confirm deletion", msg=f"Are you sure you want to delete the curve \"{curve.name}\"?"):
            if self.MCRprocess.deleteCurve(curve):
                self.curve_item_container.deleteCurve(ID)
                self.CurveList.removeRow(row)

            self.updateTabProgression(0)
            self.refreshPrepareDataTab()

    """ PCA & initial estimation Tab """

    def previewInitialEstimateCurve(self) -> None:
        if self.SelectPreviewEstimateOption.currentIndex() == 0:
            return

        name = self.SelectPreviewEstimateOption.currentText()
        curve_ID = self.curve_container.getIdFromName(name)

        figure = MCRALSLib.plot_curve(self.MCRprocess, curve_ID)

        self.PreviewInitialEstimatesBox.layout().removeWidget(self.PreviewEstimatePlot)
        self.PreviewEstimatePlot.close()
        self.PreviewEstimatePlot = FigureCanvas(figure)
        self.PreviewEstimatePlot.draw()
        self.PreviewInitialEstimatesBox.layout().insertWidget(0, self.PreviewEstimatePlot, 1, Qt.AlignCenter)
        self.PreviewInitialEstimatesBox.layout().update()

    def getInitialEstimatesMethod(self) -> str:
        if self.MostDissimilarOption.isChecked():
            return "Most dissimilar"
        elif self.ChiRankOption.isChecked():
            return "Chi-rank"
        else:
            return "Manual selection"

    def countInitialEstimatesListSelected(self) -> int:
        count = 0
        for i in range(self.InitialEstimatesList.count()):
            if self.InitialEstimatesList.item(i).checkState() == Qt.Checked:
                count += 1
        return count

    def toggleKnownSpecies(self):
        if len(self.selected_known_species) == 0:
            for row in range(self.InitialEstimatesList.count()):
                item = self.InitialEstimatesList.item(row)
                if item.checkState() == Qt.Checked:
                    ID = self.curve_container.getIdFromName(item.text())
                    self.selected_known_species.append(ID)

            for row in range(self.InitialEstimatesList.count()):
                item = self.InitialEstimatesList.item(row)
                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                    item.setHidden(True)
        else:
            self.resetInitialEstimatesListFromKnownSelected()

    def resetInitialEstimatesListFromKnownSelected(self) -> None:
        if len(self.selected_known_species) == 0:
            return

        self.InitialEstimatesList.itemChanged.disconnect()

        for row in range(self.InitialEstimatesList.count()):
            if self.InitialEstimatesList.isRowHidden(row):
                self.InitialEstimatesList.item(row).setHidden(False)
                self.InitialEstimatesList.item(row).setCheckState(Qt.Checked)
        self.selected_known_species.clear()

        self.InitialEstimatesList.itemChanged.connect(self.refreshInitialEstimatesTab)

    """ Constraints Tab """

    def noConstraintsPreset(self):
        self.OtherPresetOption.setChecked(True)
        self.refreshConstraintsTab()

    imported_concentration_profile_flag: bool = False

    def importConcentrationProfile(self):
        if self.imported_concentration_profile_flag:
            self.SetConcentrationProfileFile.setText("")

            self.SetConcentrationProfileButton.setText("Import profile")

            self.imported_concentration_profile_flag = False
        else:
            if MCRALSLib.import_concentration_file(self.MCRprocess):
                self.SetConcentrationProfileFile.setText(self.MCRprocess.conc_file_name)

                self.SetConcentrationProfileButton.setText("Clear")

                self.imported_concentration_profile_flag = True

    """ MCRALS Tab """

    def toggleOutlierItem(self, curve_ID: int, active: bool):
        # Toggle outlier item in OutlierTable
        name = self.curves[curve_ID].name
        row = 0
        while (self.OutlierTable.cellWidget(row, 1).text() not in [name, name + const.REMOVED_TAG]):
            row += 1
        for column in range(1, 3):
            self.OutlierTable.cellWidget(row, column).setEnabled(active)

    def removeCurveItemOnRerun(self, ID: int):
        pass

    """ Error estimation Tab """

    def renderErrorsPlots(self):
        # Render ConcentrationErrorsPlot and SpectraErrorsPlot
        conc_fig, abss_fig = MCRALSLib.plot_monte_carlo(
            self.MCRprocess,
            self.plot_conc_errors_mask,
            self.plot_abss_errors_mask
        )

        self.ConcentrationErrorsBox.layout().removeWidget(self.ConcentrationErrorsPlot)
        self.ConcentrationErrorsPlot.close()
        self.ConcentrationErrorsPlot = FigureCanvas(conc_fig)
        self.ConcentrationErrorsPlot.draw()
        self.ConcentrationErrorsBox.layout().insertWidget(0, self.ConcentrationErrorsPlot, 3, Qt.AlignCenter)
        self.ConcentrationErrorsBox.layout().update()

        self.SpectraErrorsBox.layout().removeWidget(self.SpectraErrorsPlot)
        self.SpectraErrorsPlot.close()
        self.SpectraErrorsPlot = FigureCanvas(abss_fig)
        self.SpectraErrorsPlot.draw()
        self.SpectraErrorsBox.layout().insertWidget(0, self.SpectraErrorsPlot, 3, Qt.AlignCenter)

    def updateConcentrationErrorsPlot(self, mask_idx: int, state: bool):
        self.plot_conc_errors_mask[mask_idx] = state
        self.renderErrorsPlots()

    def updateSpectraErrorsPlot(self, mask_idx: int, state: bool):
        self.plot_abss_errors_mask[mask_idx] = state
        self.renderErrorsPlots()

    """ Report Tab """

    def onHTMLReport(self):
        directory = MCRALSLib.directory_popup()

        if directory != None:
            MCRALSLib.SaveHTML(self.MCRprocess, directory)

    def onPDFReport(self):
        pass

    def onSaveCurves(self):

        # Collect save options
        format = self.SaveFormatOption.currentText()
        metadata = self.IncludeMetadataCheckBox.isChecked()

        # Add metadata
        if metadata:
            pass

        # Reconstructed curves

        # Save folder
        directory = MCRALSLib.directory_popup()
        if directory is not None:
            print(format + " " + str(metadata))

    """ Other utilities """

    def popupPrompt(self, header: str, msg: str = "") -> bool:
        return QMessageBox.question(self, header, msg, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes

""" UI functionality classes """

class ActiveCheckBox(QCheckBox):
    """ Activates / deactivates curve when pressed """

    curve_ID: int
    onToggleSignal = Signal(int, bool)

    def __init__(self, parent: QWidget, curve_ID: int):
        super(ActiveCheckBox, self).__init__()
        self.setParent(parent)

        self.curve_ID = curve_ID
        self.toggled.connect(self.onToggle)

    def onToggle(self):
        self.onToggleSignal.emit(self.curve_ID, self.isChecked())


class UnitsToggleButton(QPushButton):
    """ Cycles units of curve when pressed """

    curve_ID: int
    onClickSignal = Signal(int)

    def __init__(self, parent: QWidget, curve_ID: int, unit: str = ""):
        super(UnitsToggleButton, self).__init__()
        self.setParent(parent)

        self.curve_ID = curve_ID

        self.updateUnits(unit)
        self.clicked.connect(self.onClick)

    def updateUnits(self, units: str):
        self.setText(const.DISPLAY_UNITS_TEXT[units])

    def onClick(self):
        self.onClickSignal.emit(self.curve_ID)


class ViewCurveButton(QPushButton):
    """ Plots curve in GraphsViewList when pressed """

    curve_ID: int
    onClickSignal = Signal(int)

    def __init__(self, parent: QWidget, curve_ID: int):
        super(ViewCurveButton, self).__init__()
        self.setParent(parent)

        self.setText("View")

        self.curve_ID = curve_ID

        self.clicked.connect(self.onClick)

    def onClick(self):
        self.onClickSignal.emit(self.curve_ID)


class ChiItem(QTableWidgetItem):
    """ Displays chi-values for curves, can be used for sorting """

    def __init__(self, chi_value: float):
        super(ChiItem, self).__init__()

        self.setData(Qt.UserRole, chi_value)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        try:
            return self.data(Qt.UserRole) < other.data(Qt.UserRole)
        except ValueError:
            return super().__lt__(other)


class ShowHideButton(QPushButton):
    """ Show or hide curve button """

    mask_idx: int

    onClickSignal = Signal(int, bool)

    def __init__(self, parent: QWidget, mask_idx: int):
        super(ShowHideButton, self).__init__()
        self.setParent(parent)

        self.setText("Hide")
        self.mask_idx = mask_idx

        self.clicked.connect(self.onClick)

    def onClick(self):
        if self.text() == "Hide":
            self.setText("Show")
            self.onClickSignal.emit(self.mask_idx, False)
        else:
            self.setText("Hide")
            self.onClickSignal.emit(self.mask_idx, True)


""" UI data classes """

class CurveItem:
    """ UI for each curve in CurveList """

    curve: Curve

    units_toggle_button: UnitsToggleButton

    units: str
    resample_checked: bool = False
    scale_checked: bool = False
    active: bool = True
    is_removed: bool = False

    def __init__(self, curve: Curve):
        self.curve = curve
        self.units = curve.units

    def linkActiveCheckbox(self, active_checkbox: ActiveCheckBox):
        active_checkbox.toggled.connect(self.toggleActiveOption)

    def linkUnitsToggleButton(self, button: UnitsToggleButton):
        button.clicked.connect(self.cycleUnits)
        self.units_toggle_button = button

    def linkFixesCheckboxes(self, resample_checkbox: QCheckBox, scale_checkbox: QCheckBox):
        resample_checkbox.toggled.connect(self.toggleResampleOption)
        scale_checkbox.toggled.connect(self.toggleScaleOption)

    def toggleActiveOption(self, flag: bool):
        self.active = flag

    def cycleUnits(self):
        self.updateUnits(const.CYCLE_UNITS[self.units])

    def resetUnits(self):
        self.updateUnits(self.curve.default_units)

    def updateUnits(self, units: str):
        self.units = units
        self.units_toggle_button.updateUnits(self.units)

    def toggleResampleOption(self, flag: bool):
        self.resample_checked = flag

    def toggleScaleOption(self, flag: bool):
        self.scale_checked = flag


class CurveItemContainer:
    """ Handles all CurveItems """

    curve_items: dict[int, CurveItem]
    curve_container: CurveContainer

    def __init__(self, curve_container: CurveContainer):
        self.curve_items = {}
        self.curve_container = curve_container

    def addItem(self, curve: Curve) -> CurveItem:
        self.curve_items[curve.ID] = CurveItem(curve)
        return self.curve_items[curve.ID]

    def countActiveCurves(self) -> int:
        count = 0
        for curve_item in self.curve_items.values():
            if curve_item.active:
                count += 1
        return count

    def checkUnitsDefined(self) -> bool:
        units_defined = True
        for curve_item in self.curve_items.values():
            if curve_item.active:
                units_defined &= (curve_item.units in const.UNITS)
        return units_defined

    def checkUnitsChanged(self) -> bool:
        units_changed = False
        for curve_item in self.curve_items.values():
            if curve_item.active:
                units_changed |= (curve_item.units != curve_item.curve.default_units)
        return units_changed

    def resetUnits(self):
        for curve_item in self.curve_items.values():
            if curve_item.active:
                curve_item.resetUnits()

    def deleteCurve(self, curve_ID: int):
        self.curve_items.pop(curve_ID)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MCRTool()
    widget.show()
    sys.exit(app.exec())

# https://stackoverflow.com/questions/64417775/pyqt-clear-outstanding-user-input

"""
Signals & Slots (https://doc.qt.io/qt-6/signalsandslots.html):
If several slots are connected to one signal, the slots will be executed one after the other, in the order they have been connected, when the signal is emitted.
"""

# Crash, that debugger skips: https://github.com/python/cpython/issues/127352, https://qt-project.atlassian.net/jira/software/c/projects/PYSIDE/list?filter=allissues&selectedIssue=PYSIDE-2877&jql=project%20%3D%20%22PYSIDE%22%20ORDER%20BY%20created%20DESC
