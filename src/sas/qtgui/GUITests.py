import unittest

from UnitTesting import AboutBoxTest
from UnitTesting import DataExplorerTest
from UnitTesting import WelcomePanelTest
from UnitTesting import DroppableDataLoadWidgetTest
from UnitTesting import GuiManagerTest
from UnitTesting import GuiUtilsTest
from UnitTesting import MainWindowTest
from UnitTesting import TestUtilsTest

def suite():
    suites = (
        unittest.makeSuite(AboutBoxTest.AboutBoxTest,         'test'),
        unittest.makeSuite(DataExplorerTest.DataExplorerTest, 'test'),
        unittest.makeSuite(WelcomePanelTest.WelcomePanelTest, 'test'),
        unittest.makeSuite(DroppableDataLoadWidgetTest.DroppableDataLoadWidgetTest, 'test'),
        unittest.makeSuite(GuiManagerTest.GuiManagerTest,     'test'),
        unittest.makeSuite(GuiUtilsTest.GuiUtilsTest,         'test'),
        unittest.makeSuite(MainWindowTest.MainWindowTest,     'test'),
        unittest.makeSuite(TestUtilsTest.TestUtilsTest,       'test'),
    )
    return unittest.TestSuite(suites)

if __name__ == "__main__":
    unittest.main(defaultTest="suite")

