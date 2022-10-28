from __future__ import print_function

import logging
import logging.config
import os
import sys
import os.path

import importlib.resources

'''
Module that manages the global logging
'''


class SetupLogger(object):
    '''
    Called at the beginning of run.py or sasview.py
    '''

    def __init__(self, logger_name):
        self._config_file = None
        self._find_config_file()
        self.name = logger_name

    def config_production(self):
        logger = logging.getLogger(self.name)
        if not logger.root.handlers:
            self._read_config_file()
            logging.captureWarnings(True)
            logger = logging.getLogger(self.name)
        logging.getLogger('matplotlib').setLevel(logging.WARN)
        logging.getLogger('numba').setLevel(logging.WARN)
        return logger

    def config_development(self):
        '''
        '''
        self._read_config_file()
        logger = logging.getLogger(self.name)
        self._update_all_logs_to_debug(logger)
        logging.captureWarnings(True)
        logging.getLogger('matplotlib').setLevel(logging.WARN)
        logging.getLogger('numba').setLevel(logging.WARN)
        return logger

    def _read_config_file(self):
        if self._config_file is not None:
            logging.config.fileConfig(self._config_file)

    def _update_all_logs_to_debug(self, logger):
        '''
        This updates all loggers and respective handlers to DEBUG
        '''
        for handler in logger.handlers or logger.parent.handlers:
            handler.setLevel(logging.DEBUG)
        for name, _ in logging.Logger.manager.loggerDict.items():
            logging.getLogger(name).setLevel(logging.DEBUG)

    def _find_config_file(self, filename="log.ini"):
        '''
        The config file is in:
        Debug ./sasview/
        Packaging: sas/sasview/
        Packaging / production does not work well with absolute paths
        thus importlib is used to find a filehandle to the resource
        wherever it is actually located.

        Returns a TextIO instance that is open for reading the resource.
        '''
        self._config_file = None
        try:
            self._config_file = importlib.resources.open_text('sas.system', filename)
        except FileNotFoundError:
            print(f"ERROR: '{filename}' not found...", file=sys.stderr)

def production():
    return SetupLogger("sasview").config_production()

def development():
    return SetupLogger("sasview").config_development()
