import sys
import unittest

from PyQt4.QtGui import QApplication
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
from new_invariant import InvariantWindow

app = QApplication(sys.argv)

class InvariantTest(unittest.TestCase):
    '''Test the invariant GUI'''
    def setUp(self):
        '''Create the GUI'''
        self.form = InvariantWindow()

    def test_defaults(self):
        '''Test the GUI in its default state'''
        self.assertEqual(self.form.lineEdit_4.text(), "0.0")
        self.assertEqual(self.form.lineEdit_6.text(), "1.0")
        self.assertEqual(self.form.pushButton.text(), "Calculate")

        # Class is in the default state even without pressing OK
        self.assertEqual(self.form._background, 0.0)
        self.assertEqual(self.form._scale, 1.0)
        
        # Push OK with the left mouse button
        helpButton = self.form.pushButton_3
        QTest.mouseClick(helpButton, Qt.LeftButton)

if __name__ == "__main__":
    unittest.main()
