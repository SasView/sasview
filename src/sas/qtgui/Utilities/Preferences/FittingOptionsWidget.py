import os
import types
import webbrowser

from bumps.options import FIT_CONFIG, FIT_FIELDS, ChoiceList

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.system import config

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.Preferences.PreferencesWidget import PreferencesWidget, set_config_value


class FittingOptions(PreferencesWidget):
    """
    Hard-coded version of the fit options dialog available from BUMPS.
    bumps.options.FIT_FIELDS gives mapping between parameter names, parameter strings and field type
    (double line edit, integer line edit, combo box etc.), e.g.::

        FIT_FIELDS = dict(
            samples = ("Samples", parse_int),
            xtol = ("x tolerance", float),
        )

    bumps.fitters.<algorithm>.settings gives mapping between algorithm, parameter name and default value, e.g.::

        >>> settings = [('steps', 1000), ('starts', 1), ('radius', 0.15), ('xtol', 1e-6), ('ftol', 1e-8)]
    """
    fit_option_changed = QtCore.pyqtSignal(str)

    name = "Fitting Optimizers"

    def __init__(self):
        super(FittingOptions, self).__init__(self.name)

    def _addAllWidgets(self):
        # Add default fit algorithm widget
        self.config = FIT_CONFIG
        active_names = [name for fit_id, name in self.config.names.items() if fit_id in self.config.active_ids]
        default_id = config.DEFAULT_FITTING_OPTIMIZER
        algorithm = self.config.names[default_id]
        self.addHeaderText("Values to persist between SasView sessions:")
        self.defaultOptimizer = self.addComboBox("Default Fit Algorithm",
                                                 active_names,
                                                 self.setDefaultOptimizer,
                                                 algorithm)
        self.addHorizontalLine()

        # Add all other widgets
        self.addHeaderText("Fitting options for this session only:")
        self.cbAlgorithm = self.addComboBox("Active Fit Algorithm",
                                            active_names,
                                            self.setActiveOptimizer,
                                            algorithm)
        self._addFittingOptionsWidgets()
        self.verticalLayout.addWidget(self.stackedWidget)
        self.onAlgorithmChange(self.cbAlgorithm.currentIndex())

    def _addFittingOptionsWidgets(self):
        """This is a direct copy from teh python file generated from the old UI file."""
        self.stackedWidget = QtWidgets.QStackedWidget()
        self.stackedWidget.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.stackedWidget.setObjectName("stackedWidget")
        self.page_dream = QtWidgets.QWidget()
        self.page_dream.setObjectName("page_dream")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.page_dream)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.groupBox_2 = QtWidgets.QGroupBox(self.page_dream)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                           QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.samples_dream = QtWidgets.QLineEdit(self.groupBox_2)
        self.samples_dream.setObjectName("samples_dream")
        self.gridLayout.addWidget(self.samples_dream, 0, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox_2)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.burn_dream = QtWidgets.QLineEdit(self.groupBox_2)
        self.burn_dream.setObjectName("burn_dream")
        self.gridLayout.addWidget(self.burn_dream, 1, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.pop_dream = QtWidgets.QLineEdit(self.groupBox_2)
        self.pop_dream.setObjectName("pop_dream")
        self.gridLayout.addWidget(self.pop_dream, 2, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.init_dream = QtWidgets.QComboBox(self.groupBox_2)
        self.init_dream.setObjectName("init_dream")
        self.init_dream.addItem("")
        self.init_dream.addItem("")
        self.init_dream.addItem("")
        self.init_dream.addItem("")
        self.gridLayout.addWidget(self.init_dream, 3, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.groupBox_2)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 4, 0, 1, 1)
        self.thin_dream = QtWidgets.QLineEdit(self.groupBox_2)
        self.thin_dream.setObjectName("thin_dream")
        self.gridLayout.addWidget(self.thin_dream, 4, 1, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.groupBox_2)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 5, 0, 1, 1)
        self.steps_dream = QtWidgets.QLineEdit(self.groupBox_2)
        self.steps_dream.setObjectName("steps_dream")
        self.gridLayout.addWidget(self.steps_dream, 5, 1, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox_2, 0, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 268, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem, 1, 0, 1, 1)
        self.stackedWidget.addWidget(self.page_dream)
        self.page_lm = QtWidgets.QWidget()
        self.page_lm.setObjectName("page_lm")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.page_lm)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.groupBox_3 = QtWidgets.QGroupBox(self.page_lm)
        self.groupBox_3.setObjectName("groupBox_3")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.groupBox_3)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label_7 = QtWidgets.QLabel(self.groupBox_3)
        self.label_7.setObjectName("label_7")
        self.gridLayout_3.addWidget(self.label_7, 0, 0, 1, 1)
        self.steps_lm = QtWidgets.QLineEdit(self.groupBox_3)
        self.steps_lm.setObjectName("steps_lm")
        self.gridLayout_3.addWidget(self.steps_lm, 0, 1, 1, 1)
        self.label_8 = QtWidgets.QLabel(self.groupBox_3)
        self.label_8.setObjectName("label_8")
        self.gridLayout_3.addWidget(self.label_8, 1, 0, 1, 1)
        self.ftol_lm = QtWidgets.QLineEdit(self.groupBox_3)
        self.ftol_lm.setObjectName("ftol_lm")
        self.gridLayout_3.addWidget(self.ftol_lm, 1, 1, 1, 1)
        self.label_9 = QtWidgets.QLabel(self.groupBox_3)
        self.label_9.setObjectName("label_9")
        self.gridLayout_3.addWidget(self.label_9, 2, 0, 1, 1)
        self.xtol_lm = QtWidgets.QLineEdit(self.groupBox_3)
        self.xtol_lm.setObjectName("xtol_lm")
        self.gridLayout_3.addWidget(self.xtol_lm, 2, 1, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox_3, 0, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 434, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_4.addItem(spacerItem1, 1, 0, 1, 1)
        self.stackedWidget.addWidget(self.page_lm)
        self.page_newton = QtWidgets.QWidget()
        self.page_newton.setObjectName("page_newton")
        self.gridLayout_7 = QtWidgets.QGridLayout(self.page_newton)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.groupBox_5 = QtWidgets.QGroupBox(self.page_newton)
        self.groupBox_5.setObjectName("groupBox_5")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.groupBox_5)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.label_10 = QtWidgets.QLabel(self.groupBox_5)
        self.label_10.setObjectName("label_10")
        self.gridLayout_5.addWidget(self.label_10, 0, 0, 1, 1)
        self.steps_newton = QtWidgets.QLineEdit(self.groupBox_5)
        self.steps_newton.setObjectName("steps_newton")
        self.gridLayout_5.addWidget(self.steps_newton, 0, 1, 1, 1)
        self.label_13 = QtWidgets.QLabel(self.groupBox_5)
        self.label_13.setObjectName("label_13")
        self.gridLayout_5.addWidget(self.label_13, 1, 0, 1, 1)
        self.starts_newton = QtWidgets.QLineEdit(self.groupBox_5)
        self.starts_newton.setObjectName("starts_newton")
        self.gridLayout_5.addWidget(self.starts_newton, 1, 1, 1, 1)
        self.label_11 = QtWidgets.QLabel(self.groupBox_5)
        self.label_11.setObjectName("label_11")
        self.gridLayout_5.addWidget(self.label_11, 2, 0, 1, 1)
        self.ftol_newton = QtWidgets.QLineEdit(self.groupBox_5)
        self.ftol_newton.setObjectName("ftol_newton")
        self.gridLayout_5.addWidget(self.ftol_newton, 2, 1, 1, 1)
        self.label_12 = QtWidgets.QLabel(self.groupBox_5)
        self.label_12.setObjectName("label_12")
        self.gridLayout_5.addWidget(self.label_12, 3, 0, 1, 1)
        self.xtol_newton = QtWidgets.QLineEdit(self.groupBox_5)
        self.xtol_newton.setObjectName("xtol_newton")
        self.gridLayout_5.addWidget(self.xtol_newton, 3, 1, 1, 1)
        self.gridLayout_7.addWidget(self.groupBox_5, 0, 0, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 68, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_7.addItem(spacerItem2, 1, 0, 1, 1)
        self.stackedWidget.addWidget(self.page_newton)
        self.page_de = QtWidgets.QWidget()
        self.page_de.setObjectName("page_de")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.page_de)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.groupBox_6 = QtWidgets.QGroupBox(self.page_de)
        self.groupBox_6.setObjectName("groupBox_6")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.groupBox_6)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.label_14 = QtWidgets.QLabel(self.groupBox_6)
        self.label_14.setObjectName("label_14")
        self.gridLayout_6.addWidget(self.label_14, 0, 0, 1, 1)
        self.steps_de = QtWidgets.QLineEdit(self.groupBox_6)
        self.steps_de.setObjectName("steps_de")
        self.gridLayout_6.addWidget(self.steps_de, 0, 1, 1, 1)
        self.label_15 = QtWidgets.QLabel(self.groupBox_6)
        self.label_15.setObjectName("label_15")
        self.gridLayout_6.addWidget(self.label_15, 1, 0, 1, 1)
        self.pop_de = QtWidgets.QLineEdit(self.groupBox_6)
        self.pop_de.setObjectName("pop_de")
        self.gridLayout_6.addWidget(self.pop_de, 1, 1, 1, 1)
        self.label_18 = QtWidgets.QLabel(self.groupBox_6)
        self.label_18.setObjectName("label_18")
        self.gridLayout_6.addWidget(self.label_18, 2, 0, 1, 1)
        self.CR_de = QtWidgets.QLineEdit(self.groupBox_6)
        self.CR_de.setObjectName("CR_de")
        self.gridLayout_6.addWidget(self.CR_de, 2, 1, 1, 1)
        self.label_19 = QtWidgets.QLabel(self.groupBox_6)
        self.label_19.setObjectName("label_19")
        self.gridLayout_6.addWidget(self.label_19, 3, 0, 1, 1)
        self.F_de = QtWidgets.QLineEdit(self.groupBox_6)
        self.F_de.setObjectName("F_de")
        self.gridLayout_6.addWidget(self.F_de, 3, 1, 1, 1)
        self.label_16 = QtWidgets.QLabel(self.groupBox_6)
        self.label_16.setObjectName("label_16")
        self.gridLayout_6.addWidget(self.label_16, 4, 0, 1, 1)
        self.ftol_de = QtWidgets.QLineEdit(self.groupBox_6)
        self.ftol_de.setObjectName("ftol_de")
        self.gridLayout_6.addWidget(self.ftol_de, 4, 1, 1, 1)
        self.label_17 = QtWidgets.QLabel(self.groupBox_6)
        self.label_17.setObjectName("label_17")
        self.gridLayout_6.addWidget(self.label_17, 5, 0, 1, 1)
        self.xtol_de = QtWidgets.QLineEdit(self.groupBox_6)
        self.xtol_de.setObjectName("xtol_de")
        self.gridLayout_6.addWidget(self.xtol_de, 5, 1, 1, 1)
        self.gridLayout_8.addWidget(self.groupBox_6, 0, 0, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(20, 356, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_8.addItem(spacerItem3, 1, 0, 1, 1)
        self.stackedWidget.addWidget(self.page_de)
        self.page_amoeba = QtWidgets.QWidget()
        self.page_amoeba.setObjectName("page_amoeba")
        self.gridLayout_10 = QtWidgets.QGridLayout(self.page_amoeba)
        self.gridLayout_10.setObjectName("gridLayout_10")
        self.groupBox_7 = QtWidgets.QGroupBox(self.page_amoeba)
        self.groupBox_7.setObjectName("groupBox_7")
        self.gridLayout_11 = QtWidgets.QGridLayout(self.groupBox_7)
        self.gridLayout_11.setObjectName("gridLayout_11")
        self.label_20 = QtWidgets.QLabel(self.groupBox_7)
        self.label_20.setObjectName("label_20")
        self.gridLayout_11.addWidget(self.label_20, 0, 0, 1, 1)
        self.steps_amoeba = QtWidgets.QLineEdit(self.groupBox_7)
        self.steps_amoeba.setObjectName("steps_amoeba")
        self.gridLayout_11.addWidget(self.steps_amoeba, 0, 1, 1, 1)
        self.label_21 = QtWidgets.QLabel(self.groupBox_7)
        self.label_21.setObjectName("label_21")
        self.gridLayout_11.addWidget(self.label_21, 1, 0, 1, 1)
        self.starts_amoeba = QtWidgets.QLineEdit(self.groupBox_7)
        self.starts_amoeba.setObjectName("starts_amoeba")
        self.gridLayout_11.addWidget(self.starts_amoeba, 1, 1, 1, 1)
        self.label_22 = QtWidgets.QLabel(self.groupBox_7)
        self.label_22.setObjectName("label_22")
        self.gridLayout_11.addWidget(self.label_22, 2, 0, 1, 1)
        self.radius_amoeba = QtWidgets.QLineEdit(self.groupBox_7)
        self.radius_amoeba.setObjectName("radius_amoeba")
        self.gridLayout_11.addWidget(self.radius_amoeba, 2, 1, 1, 1)
        self.label_24 = QtWidgets.QLabel(self.groupBox_7)
        self.label_24.setObjectName("label_24")
        self.gridLayout_11.addWidget(self.label_24, 3, 0, 1, 1)
        self.ftol_amoeba = QtWidgets.QLineEdit(self.groupBox_7)
        self.ftol_amoeba.setObjectName("ftol_amoeba")
        self.gridLayout_11.addWidget(self.ftol_amoeba, 3, 1, 1, 1)
        self.label_25 = QtWidgets.QLabel(self.groupBox_7)
        self.label_25.setObjectName("label_25")
        self.gridLayout_11.addWidget(self.label_25, 4, 0, 1, 1)
        self.xtol_amoeba = QtWidgets.QLineEdit(self.groupBox_7)
        self.xtol_amoeba.setObjectName("xtol_amoeba")
        self.gridLayout_11.addWidget(self.xtol_amoeba, 4, 1, 1, 1)
        self.gridLayout_10.addWidget(self.groupBox_7, 0, 0, 1, 1)
        spacerItem4 = QtWidgets.QSpacerItem(20, 382, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_10.addItem(spacerItem4, 1, 0, 1, 1)
        self.stackedWidget.addWidget(self.page_amoeba)

        self.retranslateUi()
        self.stackedWidget.setCurrentIndex(0)

    def retranslateUi(self, ):
        _translate = QtCore.QCoreApplication.translate
        self.groupBox_2.setTitle(_translate("FittingOptions", "DREAM"))
        self.label.setText(_translate("FittingOptions", "Samples:"))
        self.samples_dream.setToolTip(_translate("FittingOptions",
                                                 "<html><head/><body><p>Number of points to be drawn from the Markov chain.</p></body></html>"))
        self.label_2.setText(_translate("FittingOptions", "Burn-in Steps:"))
        self.burn_dream.setToolTip(_translate("FittingOptions",
                                              "<html><head/><body><p>The number of iterations to required for the Markov chain to converge to the equilibrium distribution.</p></body></html>"))
        self.label_3.setText(_translate("FittingOptions", "Population:"))
        self.pop_dream.setToolTip(
            _translate("FittingOptions", "<html><head/><body><p>The size of the population.</p></body></html>"))
        self.label_4.setText(_translate("FittingOptions", "Initializer:"))
        self.init_dream.setToolTip(_translate("FittingOptions",
                                              "<html><head/><body><p><span style=\" font-style:italic;\">Initializer</span> determines how the population will be initialized. The options are as follows:</p><p><span style=\" font-style:italic;\">eps</span> (epsilon ball), in which the entire initial population is chosen at random from within a tiny hypersphere centered about the initial point</p><p><span style=\" font-style:italic;\">lhs</span> (latin hypersquare), which chops the bounds within each dimension in <span style=\" font-weight:600;\">k</span> equal sized chunks where <span style=\" font-weight:600;\">k</span> is the size of the population and makes sure that each parameter has at least one value within each chunk across the population.</p><p><span style=\" font-style:italic;\">cov</span> (covariance matrix), in which the uncertainty is estimated using the covariance matrix at the initial point, and points are selected at random from the corresponding gaussian ellipsoid</p><p><span style=\" font-style:italic;\">random</span> (uniform random), in which the points are selected at random within the bounds of the parameters</p></body></html>"))
        self.init_dream.setItemText(0, _translate("FittingOptions", "eps"))
        self.init_dream.setItemText(1, _translate("FittingOptions", "lhs"))
        self.init_dream.setItemText(2, _translate("FittingOptions", "cov"))
        self.init_dream.setItemText(3, _translate("FittingOptions", "random"))
        self.label_5.setText(_translate("FittingOptions", "Thinning:"))
        self.thin_dream.setToolTip(_translate("FittingOptions",
                                              "<html><head/><body><p>The amount of thinning to use when collecting the population.</p></body></html>"))
        self.label_6.setText(_translate("FittingOptions", "Steps:"))
        self.steps_dream.setToolTip(_translate("FittingOptions",
                                               "<html><head/><body><p>Determines the number of iterations to use for drawing samples after burn in.</p></body></html>"))
        self.groupBox_3.setTitle(_translate("FittingOptions", "Levenberg"))
        self.label_7.setText(_translate("FittingOptions", "Steps:"))
        self.steps_lm.setToolTip(_translate("FittingOptions",
                                            "<html><head/><body><p>The number of gradient steps to take.</p></body></html>"))
        self.label_8.setText(_translate("FittingOptions", "f(x) tolerance:"))
        self.ftol_lm.setToolTip(_translate("FittingOptions",
                                           "<html><head/><body><p>Used to determine when the fit has reached the point where no significant improvement is expected.</p></body></html>"))
        self.label_9.setText(_translate("FittingOptions", "x tolerance:"))
        self.xtol_lm.setToolTip(_translate("FittingOptions",
                                           "<html><head/><body><p>Used to determine when the fit has reached the point where no significant improvement is expected.</p></body></html>"))
        self.groupBox_5.setTitle(_translate("FittingOptions", "Quasi-Newton BFGS "))
        self.label_10.setText(_translate("FittingOptions", "Steps:"))
        self.steps_newton.setToolTip(_translate("FittingOptions",
                                                "<html><head/><body><p>The number of gradient steps to take.</p></body></html>"))
        self.label_13.setText(_translate("FittingOptions", "Starts:"))
        self.starts_newton.setToolTip(_translate("FittingOptions",
                                                 "<html><head/><body><p>Value thattells the optimizer to restart a given number of times. Each time it restarts it uses a random starting point.</p></body></html>"))
        self.label_11.setText(_translate("FittingOptions", "f(x) tolerance:"))
        self.ftol_newton.setToolTip(_translate("FittingOptions",
                                               "<html><head/><body><p>Used to determine when the fit has reached the point where no significant improvement is expected.</p></body></html>"))
        self.label_12.setText(_translate("FittingOptions", "x tolerance:"))
        self.xtol_newton.setToolTip(_translate("FittingOptions",
                                               "<html><head/><body><p>Used to determine when the fit has reached the point where no significant improvement is expected.</p></body></html>"))
        self.groupBox_6.setTitle(_translate("FittingOptions", "Differential Evolution"))
        self.label_14.setText(_translate("FittingOptions", "Steps:"))
        self.steps_de.setToolTip(
            _translate("FittingOptions", "<html><head/><body><p>The number of iterations.</p></body></html>"))
        self.label_15.setText(_translate("FittingOptions", "Population:"))
        self.label_18.setText(_translate("FittingOptions", "Crossover ratio:"))
        self.CR_de.setToolTip(
            _translate("FittingOptions", "<html><head/><body><p>The size of the population.</p></body></html>"))
        self.label_19.setText(_translate("FittingOptions", "Scale:"))
        self.F_de.setToolTip(_translate("FittingOptions",
                                        "<html><head/><body><p>Determines how much to scale each difference vector before adding it to the candidate point.</p></body></html>"))
        self.label_16.setText(_translate("FittingOptions", "f(x) tolerance:"))
        self.ftol_de.setToolTip(_translate("FittingOptions",
                                           "<html><head/><body><p>Used to determine when the fit has reached the point where no significant improvement is expected.</p></body></html>"))
        self.label_17.setText(_translate("FittingOptions", "x tolerance:"))
        self.xtol_de.setToolTip(_translate("FittingOptions",
                                           "<html><head/><body><p>Used to determine when the fit has reached the point where no significant improvement is expected.</p></body></html>"))
        self.groupBox_7.setTitle(_translate("FittingOptions", "Nelder-Mead Simplex"))
        self.label_20.setText(_translate("FittingOptions", "Steps:"))
        self.steps_amoeba.setToolTip(_translate("FittingOptions",
                                                "<html><head/><body><p>The number of simplex update iterations to perform.</p></body></html>"))
        self.label_21.setText(_translate("FittingOptions", "Starts:"))
        self.starts_amoeba.setToolTip(_translate("FittingOptions",
                                                 "<html><head/><body><p>Tells the optimizer to restart a given number of times. Each time it restarts it uses a random starting point.</p></body></html>"))
        self.label_22.setText(_translate("FittingOptions", "Simplex radius:"))
        self.radius_amoeba.setToolTip(_translate("FittingOptions",
                                                 "<html><head/><body><p>The initial size of the simplex, as a portion of the bounds defining the parameter space.</p></body></html>"))
        self.label_24.setText(_translate("FittingOptions", "f(x) tolerance:"))
        self.ftol_amoeba.setToolTip(_translate("FittingOptions",
                                               "<html><head/><body><p>Used to determine when the fit has reached the point where no significant improvement is expected. </p></body></html>"))
        self.label_25.setText(_translate("FittingOptions", "x tolerance:"))
        self.xtol_amoeba.setToolTip(_translate("FittingOptions",
                                               "<html><head/><body><p>Used to determine when the fit has reached the point where no significant improvement is expected. </p></body></html>"))

    def setDefaultOptimizer(self):
        """Capture the default optimizer value in the and set it in the config file"""
        text = self.defaultOptimizer.currentText()
        id = dict((new_val, new_k) for new_k, new_val in FIT_CONFIG.names.items()).get(text)
        set_config_value(id, 'DEFAULT_FITTING_OPTIMIZER')
        self.cbAlgorithm.setCurrentIndex(self.defaultOptimizer.currentIndex())
        self.setActiveOptimizer()

    def setActiveOptimizer(self):
        """Grab the optimizer value and set it in the config file"""
        if self.parent is not None:
            self.parent.guiManager.loadedPerspectives["Fitting"].onFittingOptionsChange(self.cbAlgorithm.currentText())
        self.onAlgorithmChange(self.cbAlgorithm.currentIndex())

    def assignValidators(self):
        """
        Use options.FIT_FIELDS to assert which line edit gets what validator
        """
        for option in FIT_FIELDS.keys():
            (f_name, f_type) = FIT_FIELDS[option]
            validator = None
            if type(f_type) == types.FunctionType:
                validator = QtGui.QIntValidator()
                validator.setBottom(0)
            elif f_type == float:
                validator = GuiUtils.DoubleValidator()
                validator.setBottom(0)
            else:
                continue
            for fitter_id in FIT_CONFIG.active_ids:
                line_edit = self.widgetFromOption(str(option), current_fitter=str(fitter_id))
                if hasattr(line_edit, 'setValidator') and validator is not None:
                    line_edit.setValidator(validator)
                    line_edit.textChanged.emit(line_edit.text())

    def onAlgorithmChange(self, index):
        """
        Change the page in response to combo box index
        """
        # Find the algorithm ID from name
        self.current_fitter_id = \
            [n.id for n in FIT_CONFIG.fitters.values() if n.name == str(self.cbAlgorithm.currentText())][0]

        # find the right stacked widget
        widget_name = "self.page_"+str(self.current_fitter_id)

        # Convert the name into widget instance
        try:
            widget_to_activate = eval(widget_name)
        except AttributeError:
            # We don't yet have this optimizer.
            # Show message
            msg = "This algorithm has not yet been implemented in SasView.\n"
            msg += "Please choose a different algorithm"
            QtWidgets.QMessageBox.warning(self,
                                        'Warning',
                                        msg,
                                        QtWidgets.QMessageBox.Ok)
            # Move the index to previous position
            self.cbAlgorithm.setCurrentIndex(self.previous_index)
            return

        index_for_this_id = self.stackedWidget.indexOf(widget_to_activate)

        # Select the requested widget
        self.stackedWidget.setCurrentIndex(index_for_this_id)

        self.updateWidgetFromBumps(self.current_fitter_id)

        self.assignValidators()

        # keep reference
        self.previous_index = index

    def onApply(self):
        """
        Update the fitter object
        """
        options = self.config.values[self.current_fitter_id]
        for option in options.keys():
            # Find the widget name of the option
            # e.g. 'samples' for 'dream' is 'self.samples_dream'
            widget_name = 'self.'+option+'_'+self.current_fitter_id
            try:
                line_edit = eval(widget_name)
            except AttributeError:
                # Skip bumps monitors
                continue
            if line_edit is None or not isinstance(line_edit, QtWidgets.QLineEdit):
                continue
            color = line_edit.palette().color(QtGui.QPalette.Background).name()
            if color == '#fff79a':
                # Show a custom tooltip and return
                tooltip = "<html><b>Please enter valid values in all fields.</html>"
                QtWidgets.QToolTip.showText(line_edit.mapToGlobal(
                    QtCore.QPoint(line_edit.rect().right(), line_edit.rect().bottom() + 2)), tooltip)
                return

        # Notify the perspective, so the window title is updated
        self.fit_option_changed.emit(self.cbAlgorithm.currentText())

        def bumpsUpdate(option):
            """
            Utility method for bumps state update
            """
            widget = self.widgetFromOption(option)
            if widget is None:
                return
            try:
                if isinstance(widget, QtWidgets.QComboBox):
                    new_value = widget.currentText()
                else:
                    try:
                        new_value = int(widget.text())
                    except ValueError:
                        new_value = float(widget.text())
                #new_value = widget.currentText() if isinstance(widget, QtWidgets.QComboBox) \
                #    else float(widget.text())
                self.config.values[self.current_fitter_id][option] = new_value
            except ValueError:
                # Don't update bumps if widget has bad data
                self.reject

        # Update the BUMPS singleton
        [bumpsUpdate(o) for o in self.config.values[self.current_fitter_id].keys()]
        self.close()

    def onHelp(self):
        """
        Show the "Fitting options" section of help
        """
        tree_location = GuiUtils.HELP_DIRECTORY_LOCATION
        tree_location += "/user/qtgui/Perspectives/Fitting/"

        # Actual file anchor will depend on the combo box index
        # Note that we can be clusmy here, since bad current_fitter_id
        # will just make the page displayed from the top
        helpfile = "optimizer.html#fit-" + self.current_fitter_id
        help_location = tree_location + helpfile
        webbrowser.open('file://' + os.path.realpath(help_location))

    def widgetFromOption(self, option_id, current_fitter=None):
        """
        returns widget's element linked to the given option_id
        """
        if current_fitter is None:
            current_fitter = self.current_fitter_id
        if option_id not in list(FIT_FIELDS.keys()): return None
        option = option_id + '_' + current_fitter
        if not hasattr(self, option): return None
        return eval('self.' + option)

    def getResults(self):
        """
        Sends back the current choice of parameters
        """
        algorithm = self.cbAlgorithm.currentText()
        return algorithm

    def updateWidgetFromBumps(self, fitter_id):
        """
        Given the ID of the current optimizer, fetch the values
        and update the widget
        """
        options = self.config.values[fitter_id]
        for option in options.keys():
            # Find the widget name of the option
            # e.g. 'samples' for 'dream' is 'self.samples_dream'
            attribute = option + '_' + fitter_id
            if not hasattr(self, attribute):
                continue
            widget_name = 'self.'+attribute
            if option not in FIT_FIELDS:
                return
            if isinstance(FIT_FIELDS[option][1], ChoiceList):
                control = eval(widget_name)
                control.setCurrentIndex(control.findText(str(options[option])))
            else:
                eval(widget_name).setText(str(options[option]))

        pass
