import sys
import unittest

from PyQt4 import QtGui
from PyQt4 import QtTest
from PyQt4 import QtCore
from mock import MagicMock

# Local
from FittingPerspective import FittingWindow

app = QtGui.QApplication(sys.argv)

class FittingPerspectiveTest(unittest.TestCase):
    """Test the Main Window GUI"""
    def setUp(self):
        """Create the GUI"""

        self.widget = FittingWindow(None)

    def tearDown(self):
        """Destroy the GUI"""
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        """Test the GUI in its default state"""
        self.assertIsInstance(self.widget, QtGui.QWidget)
        self.assertEqual(self.widget.windowTitle(), "Fitting")
        self.assertEqual(self.widget.sizePolicy().Policy(), QtGui.QSizePolicy.Fixed)

    def testSelectCategory(self):
        """
        Test if categories have been load properly
        :return:
        """
        fittingWindow =  FittingWindow(None)

        #Test loading from json categories
        category_list = fittingWindow.master_category_dict.keys()
        self.assertTrue("Cylinder" in category_list)
        self.assertTrue("Ellipsoid" in category_list)
        self.assertTrue("Lamellae" in category_list)
        self.assertTrue("Paracrystal" in category_list)
        self.assertTrue("Parallelepiped" in category_list)
        self.assertTrue("Shape Independent" in category_list)
        self.assertTrue("Sphere" in category_list)

        #Test for existence in combobox
        self.assertNotEqual(fittingWindow.cbCategory.findText("Cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbCategory.findText("Ellipsoid"),-1)
        self.assertNotEqual(fittingWindow.cbCategory.findText("Lamellae"),-1)
        self.assertNotEqual(fittingWindow.cbCategory.findText("Paracrystal"),-1)
        self.assertNotEqual(fittingWindow.cbCategory.findText("Parallelepiped"),-1)
        self.assertNotEqual(fittingWindow.cbCategory.findText("Shape Independent"),-1)
        self.assertNotEqual(fittingWindow.cbCategory.findText("Sphere"),-1)

        #Test what is current text in the combobox
        self.assertTrue(fittingWindow.cbCategory.currentText(), "Cylinder")

    def testSelectModel(self):
        """
        Test if models have been loaded properly
        :return:
        """
        fittingWindow =  FittingWindow(None)

        #Test loading from json categories
        model_list = fittingWindow.master_category_dict["Cylinder"]
        self.assertTrue(['cylinder', True] in model_list)
        self.assertTrue(['core_shell_cylinder', True] in model_list)
        self.assertTrue(['barbell', True] in model_list)
        self.assertTrue(['core_shell_bicelle', True] in model_list)
        self.assertTrue(['flexible_cylinder', True] in model_list)
        self.assertTrue(['flexible_cylinder_elliptical', True] in model_list)
        self.assertTrue(['pearl_necklace', True] in model_list)
        self.assertTrue(['capped_cylinder', True] in model_list)
        self.assertTrue(['elliptical_cylinder', True] in model_list)
        self.assertTrue(['pringle', True] in model_list)
        self.assertTrue(['hollow_cylinder', True] in model_list)
        self.assertTrue(['core_shell_bicelle_elliptical', True] in model_list)
        self.assertTrue(['stacked_disks', True] in model_list)

        #Test for existence in combobox
        self.assertNotEqual(fittingWindow.cbModel.findText("cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("core_shell_cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("barbell"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("core_shell_bicelle"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("flexible_cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("flexible_cylinder_elliptical"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("pearl_necklace"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("capped_cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("elliptical_cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("pringle"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("hollow_cylinder"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("core_shell_bicelle_elliptical"),-1)
        self.assertNotEqual(fittingWindow.cbModel.findText("stacked_disks"),-1)


    def testSelectStructureFactor(self):
        """
        Test if structure factors have been loaded properly
        :return:
        """
        fittingWindow =  FittingWindow(None)

        #Test for existence in combobox
        self.assertNotEqual(fittingWindow.cbStructureFactor.findText("stickyhardsphere"),-1)
        self.assertNotEqual(fittingWindow.cbStructureFactor.findText("hayter_msa"),-1)
        self.assertNotEqual(fittingWindow.cbStructureFactor.findText("squarewell"),-1)
        self.assertNotEqual(fittingWindow.cbStructureFactor.findText("hardsphere"),-1)

        #Test what is current text in the combobox
        self.assertTrue(fittingWindow.cbCategory.currentText(), "None")

if __name__ == "__main__":
    unittest.main()
