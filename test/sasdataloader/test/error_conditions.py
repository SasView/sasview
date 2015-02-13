from sas.dataloader.loader import Loader
import unittest

class testLoader(unittest.TestCase):
    def setUp(self):
        self.s = Loader()

    def test_load_unknown(self):
        """
            self.s.load('blah.mat') on an unknown type
            should raise a ValueError exception (thrown by data_util.registry)
        """
        self.assertRaises(ValueError, self.s.load, 'angles_flat.mat')
        
    def test_corrupt(self):
        """
            Loading a corrupted file with a known extension
            should raise a runtime exception.
            The error condition is similar to an unknown 
            type (file extension). When a reader is identified as
            knowing the file extension, it tries to load. If it
            raises an exception, the system should try to identify
            another reader that knows about that file extension.
            If they all fail, we raise a runtime exception stating
            that no reader was found for this file.
        """
        self.assertRaises(RuntimeError, self.s.load, 'corrupt.png')


if __name__ == '__main__':
    unittest.main()
