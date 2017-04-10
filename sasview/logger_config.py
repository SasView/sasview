from __future__ import print_function

'''
Module that manages the global logging
'''

import logging
import logging.config
import os
import os.path
import pkg_resources

class SetupLogger(object):
    '''
    Called at the beginning of run.py or sasview.py
    '''

    def __init__(self, logger_name):
        self._find_config_file()
        self.name = logger_name

    def config_production(self):
        '''
        '''
        logger = logging.getLogger(self.name)
        if not logger.root.handlers:
            self._read_config_file()
            logging.captureWarnings(True)
            logger = logging.getLogger(self.name)
        return logger

    def config_development(self):
        '''
        '''
        self._read_config_file()
        logger = logging.getLogger(self.name)
        self._update_all_logs_to_debug(logger)
        logging.captureWarnings(True)
        return logger

    def _read_config_file(self):
        '''
        '''
        logging.config.fileConfig(self.config_file)

    def _update_all_logs_to_debug(self, logger):
        '''
        This updates all loggers and respective handlers to DEBUG
        '''
        for handler in logger.handlers or logger.parent.handlers:
            handler.setLevel(logging.DEBUG)
        for name, _ in logging.Logger.manager.loggerDict.items():
            logging.getLogger(name).setLevel(logging.DEBUG)

    def _find_config_file(self, filename="logging.ini"):
        '''
        '''
        for filepath in [
                os.path.join(os.path.abspath(os.path.dirname(__file__)), filename),
                pkg_resources.resource_filename(__name__, filename),
            ]:
            if os.path.exists(filepath):
                self.config_file = filepath
                return
        raise Exception("%s not found...", filename)

