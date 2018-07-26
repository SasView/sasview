import unittest
import sys
from PyQt5 import QtGui
from PyQt5 import QtWidgets

"""
Unit tests for the QT GUI
=========================

In order to run the tests, first install SasView and sasmodels to site-packages
by running ``python setup.py install`` in both repositories.

The tests can be run with ``python GUITests.py``, or
``python GUITests.py suiteName1 suiteName2 ...`` for a subset of tests.

To get more verbose console output (recommended), use ``python GUITests.py -v``
or modify tge VERBOSITY module variable.
"""

# Llist of all suite names. Every time a new suite is added, its name should
# also be added here
ALL_SUITES = [
    'calculatorsSuite',
    'mainSuite',
    'fittingSuite',
    'plottingSuite',
    'utilitiesSuite',
    'perspectivesSuite',
    ]

# Define output verbosity
#VERBOSITY = 0 # quiet - just the total number of tests run and global result
VERBOSITY = 1 # default - quiet + a dot for every successful test or a F for failure
#VERBOSITY = 2 # verbose - default + help string of every test and the result

# Prepare the general QApplication instance
app = QtWidgets.QApplication(sys.argv)

# Main Window
from MainWindow.UnitTesting import AboutBoxTest
from MainWindow.UnitTesting import DataExplorerTest
from MainWindow.UnitTesting import WelcomePanelTest
from MainWindow.UnitTesting import DroppableDataLoadWidgetTest
from MainWindow.UnitTesting import GuiManagerTest
from MainWindow.UnitTesting import MainWindowTest

## Plotting
from Plotting.UnitTesting import AddTextTest
from Plotting.UnitTesting import PlotHelperTest
from Plotting.UnitTesting import WindowTitleTest
from Plotting.UnitTesting import ScalePropertiesTest
from Plotting.UnitTesting import SetGraphRangeTest
from Plotting.UnitTesting import LinearFitTest
from Plotting.UnitTesting import PlotPropertiesTest
from Plotting.UnitTesting import PlotUtilitiesTest
from Plotting.UnitTesting import ColorMapTest
from Plotting.UnitTesting import BoxSumTest
from Plotting.UnitTesting import SlicerModelTest
from Plotting.UnitTesting import SlicerParametersTest
from Plotting.UnitTesting import PlotterBaseTest
from Plotting.UnitTesting import PlotterTest
from Plotting.UnitTesting import Plotter2DTest

# Calculators
from Calculators.UnitTesting import KiessigCalculatorTest
from Calculators.UnitTesting import DensityCalculatorTest
from Calculators.UnitTesting import GenericScatteringCalculatorTest
from Calculators.UnitTesting import SLDCalculatorTest
from Calculators.UnitTesting import SlitSizeCalculatorTest
from Calculators.UnitTesting import ResolutionCalculatorPanelTest
from Calculators.UnitTesting import DataOperationUtilityTest

# Utilities
from Utilities.UnitTesting import GuiUtilsTest
from Utilities.UnitTesting import SasviewLoggerTest
from Utilities.UnitTesting import GridPanelTest
from Utilities.UnitTesting import ModelEditorTest
from Utilities.UnitTesting import PluginDefinitionTest
from Utilities.UnitTesting import TabbedModelEditorTest
from Utilities.UnitTesting import AddMultEditorTest
from Utilities.UnitTesting import ReportDialogTest

# Unit Testing
from UnitTesting import TestUtilsTest

# Perspectives
#  Fitting
from Perspectives.Fitting.UnitTesting import FittingWidgetTest
from Perspectives.Fitting.UnitTesting import FittingPerspectiveTest
from Perspectives.Fitting.UnitTesting import FittingLogicTest
from Perspectives.Fitting.UnitTesting import FittingUtilitiesTest
from Perspectives.Fitting.UnitTesting import FitPageTest
from Perspectives.Fitting.UnitTesting import FittingOptionsTest
from Perspectives.Fitting.UnitTesting import MultiConstraintTest
from Perspectives.Fitting.UnitTesting import ComplexConstraintTest
from Perspectives.Fitting.UnitTesting import ConstraintWidgetTest

#  Invariant
from Perspectives.Invariant.UnitTesting import InvariantPerspectiveTest

#  Inversion
from Perspectives.Inversion.UnitTesting import InversionPerspectiveTest

def plottingSuite():
    suites = (
        # Plotting
        unittest.makeSuite(Plotter2DTest.Plotter2DTest,               'test'),
        unittest.makeSuite(PlotHelperTest.PlotHelperTest,             'test'),
        unittest.makeSuite(AddTextTest.AddTextTest,                   'test'),
        unittest.makeSuite(WindowTitleTest.WindowTitleTest,           'test'),
        unittest.makeSuite(ScalePropertiesTest.ScalePropertiesTest,   'test'),
        unittest.makeSuite(SetGraphRangeTest.SetGraphRangeTest,       'test'),
        unittest.makeSuite(LinearFitTest.LinearFitTest,               'test'),
        unittest.makeSuite(PlotPropertiesTest.PlotPropertiesTest,     'test'),
        unittest.makeSuite(PlotUtilitiesTest.PlotUtilitiesTest,       'test'),
        unittest.makeSuite(ColorMapTest.ColorMapTest,                 'test'),
        unittest.makeSuite(BoxSumTest.BoxSumTest,                     'test'),
        unittest.makeSuite(SlicerModelTest.SlicerModelTest,           'test'),
        unittest.makeSuite(SlicerParametersTest.SlicerParametersTest, 'test'),
        unittest.makeSuite(PlotterBaseTest.PlotterBaseTest,           'test'),
        unittest.makeSuite(PlotterTest.PlotterTest,                   'test'),
        )
    return unittest.TestSuite(suites)

def mainSuite():
    suites = (
        # Main window
        unittest.makeSuite(DataExplorerTest.DataExplorerTest,  'test'),
        unittest.makeSuite(DroppableDataLoadWidgetTest.DroppableDataLoadWidgetTest, 'test'),
        unittest.makeSuite(MainWindowTest.MainWindowTest,      'test'),
        unittest.makeSuite(GuiManagerTest.GuiManagerTest,      'test'),
        unittest.makeSuite(AboutBoxTest.AboutBoxTest,          'test'),
        unittest.makeSuite(WelcomePanelTest.WelcomePanelTest,  'test'),
        )
    return unittest.TestSuite(suites)

def utilitiesSuite():
    suites = (
        ## Utilities
        unittest.makeSuite(TestUtilsTest.TestUtilsTest,           'test'),
        unittest.makeSuite(SasviewLoggerTest.SasviewLoggerTest,   'test'),
        unittest.makeSuite(GuiUtilsTest.GuiUtilsTest,             'test'),
        unittest.makeSuite(GuiUtilsTest.DoubleValidatorTest,      'test'),
        unittest.makeSuite(GuiUtilsTest.HashableStandardItemTest, 'test'),
        unittest.makeSuite(GridPanelTest.BatchOutputPanelTest,    'test'),
        unittest.makeSuite(ModelEditorTest.ModelEditorTest,            'test'),
        unittest.makeSuite(PluginDefinitionTest.PluginDefinitionTest,  'test'),
        unittest.makeSuite(TabbedModelEditorTest.TabbedModelEditorTest,'test'),
        unittest.makeSuite(AddMultEditorTest.AddMultEditorTest, 'test'),
        unittest.makeSuite(ReportDialogTest.ReportDialogTest,     'test'),
        )
    return unittest.TestSuite(suites)

def calculatorsSuite():
    suites = (
        # Calculators
        unittest.makeSuite(KiessigCalculatorTest.KiessigCalculatorTest,                     'test'),
        unittest.makeSuite(DensityCalculatorTest.DensityCalculatorTest,                     'test'),
        unittest.makeSuite(GenericScatteringCalculatorTest.GenericScatteringCalculatorTest, 'test'),
        unittest.makeSuite(SLDCalculatorTest.SLDCalculatorTest, 'test'),
        unittest.makeSuite(SlitSizeCalculatorTest.SlitSizeCalculatorTest, 'test'),
        unittest.makeSuite(ResolutionCalculatorPanelTest.ResolutionCalculatorPanelTest, 'test'),
        unittest.makeSuite(DataOperationUtilityTest.DataOperationUtilityTest, 'test'),
        )
    return unittest.TestSuite(suites)

def fittingSuite():
    suites = (
        # Perspectives
        #  Fitting
        unittest.makeSuite(FittingPerspectiveTest.FittingPerspectiveTest, 'test'),
        unittest.makeSuite(FittingWidgetTest.FittingWidgetTest,           'test'),
        unittest.makeSuite(FittingLogicTest.FittingLogicTest,             'test'),
        unittest.makeSuite(FittingUtilitiesTest.FittingUtilitiesTest,     'test'),
        unittest.makeSuite(FitPageTest.FitPageTest,                       'test'),
        unittest.makeSuite(FittingOptionsTest.FittingOptionsTest,         'test'),
        unittest.makeSuite(MultiConstraintTest.MultiConstraintTest,       'test'),
        unittest.makeSuite(ConstraintWidgetTest.ConstraintWidgetTest,     'test'),
        unittest.makeSuite(ComplexConstraintTest.ComplexConstraintTest,   'test'),
        )
    return unittest.TestSuite(suites)

def perspectivesSuite():
    suites = (
        #  Invariant
        unittest.makeSuite(InvariantPerspectiveTest.InvariantPerspectiveTest,  'test'),
        #  Inversion
        #unittest.makeSuite(InversionPerspectiveTest.InversionTest,  'test'),
        )
    return unittest.TestSuite(suites)

if __name__ == "__main__":

    user_suites = ALL_SUITES
    # Check if user asked for specific suites:
    if len(sys.argv) > 1:
        user_suites = sys.argv[1:]

    runner = unittest.TextTestRunner(verbosity=VERBOSITY)
    for suite in user_suites:
        # create the suite object from name
        try:
            suite_instance = globals()[suite]()
            results = runner.run(suite_instance)
        except KeyError:
            print("ERROR: Incorrect suite name: %s " % suite)
            pass
