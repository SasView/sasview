"""
This is the base file reader class all file readers should inherit from.
All generic functionality required for a file loader/reader is built into this
class
"""

import os
import logging
from abc import abstractmethod
from loader_exceptions import NoKnownLoaderException, FileContentsException,\
    DataReaderException
from data_info import Data1D, Data2D, DataInfo, plottable_1D, plottable_2D,\
    combine_data_info_with_plottable

logger = logging.getLogger(__name__)


class FileReader(object):
    # List of Data1D and Data2D objects to be sent back to data_loader
    output = []
    # Current plottable1D/2D object being loaded in
    current_dataset = None
    # Current DataInfo objecct being loaded in
    current_datainfo = None
    # Wildcards
    type = ["Text files (*.txt)"]
    # List of allowed extensions
    ext = ['.txt']
    # Bypass extension check and try to load anyway
    allow_all = False

    def read(self, filepath):
        """
        Basic file reader 
        
        :param filepath: The full or relative path to a file to be loaded
        """
        if os.path.isfile(filepath):
            basename, extension = os.path.splitext(os.path.basename(filepath))
            # If the file type is not allowed, return nothing
            if extension in self.ext or self.allow_all:
                # Try to load the file, but raise an error if unable to.
                try:
                    input_f = open(filepath, 'rb')
                    self.get_file_contents(input_f)
                except RuntimeError:
                    pass
                except OSError as e:
                    msg = "Unable to open file: {}\n".format(filepath)
                    msg += e.message
                    self.handle_error_message(msg)
                except Exception as e:
                    self.handle_error_message(e.message)
        else:
            msg = "Unable to find file at: {}\n".format(filepath)
            msg += "Please check your file path and try again."
            self.handle_error_message(msg)
        # Return a list of parsed entries that dataloader can manage
        return self.output

    def handle_error_message(self, msg):
        """
        Generic error handler to add an error to the current datainfo to
        propogate the error up the error chain.
        :param msg: Error message
        """
        if isinstance(self.current_datainfo, DataInfo):
            self.current_datainfo.errors.append(msg)
        else:
            logger.warning(msg)

    def send_to_output(self):
        """
        Helper that automatically combines the info and set and then appends it
        to output
        """
        data_obj = combine_data_info_with_plottable(self.current_dataset,
                                                    self.current_datainfo)
        self.output.append(data_obj)

    @abstractmethod
    def get_file_contents(self, contents):
        """
        All reader classes that inherit from here should implement
        :param contents: 
        """
        pass
