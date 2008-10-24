import abs_reader
import cansas_reader
import ascii_reader
import cansas_reader
import danse_reader
import hfir1d_reader
import IgorReader
import tiff_reader

def register_readers(registry_function):
    """
        Function called by the registry/loader object to register
        all default readers using a call back function.
    
        @param registry_function: function to be called to register each reader
    """
    registry_function(abs_reader)
    registry_function(cansas_reader)
    registry_function(ascii_reader)
    registry_function(cansas_reader)
    registry_function(danse_reader)
    registry_function(hfir1d_reader)
    registry_function(IgorReader)
    registry_function(tiff_reader)
    