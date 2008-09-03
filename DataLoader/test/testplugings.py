"""
    Unit tests for DataLoader module 
"""

import unittest
from DataLoader.loader import  Loader, Registry
class testLoader(unittest.TestCase):
    
    def setUp(self):
        self.L=Loader()
        self.L.find_plugins('../plugins')
            
    def testplugin(self):
        """ 
            test loading with a test reader only 
            found in the plugins directory
        """
        output = self.L.load('test_data.test')
        self.assertEqual(output.x[0], 1234.)
        
class testRegistry(unittest.TestCase):
    
    def setUp(self):
        self.L=Registry()
        self.L.find_plugins('../plugins')
            
    def testplugin(self):
        """ 
            test loading with a test reader only 
            found in the plugins directory
        """
        output = self.L.load('test_data.test')
        self.assertEqual(output.x[0], 1234.)
        self.assertTrue(self.L.loaders.has_key('.test'))
        
if __name__ == '__main__':
    unittest.main()
