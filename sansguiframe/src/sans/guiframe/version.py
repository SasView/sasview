
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2010, University of Tennessee
################################################################################


import sys
import time
import subprocess
import urllib
import re
import os
import getopt
from threading import Thread

## Maximum number of seconds to wait for an answer from the server
MAX_WAIT_TIME = 20
## Local storage file name
VERSION_FILE  = '.current_version'

DEFAULT_VERSION = '0.0.0'

class VersionChecker(object):
    """
    Class of objects used to obtain the current version of an application
    from the deployment server. 
    A sub process is started to read the URL associated with the version number.
    The version number is written on file locally before the reading process
    ends, then read when the version number is requested.    
    
    The reading of the URL is put in a separate process so that it doesn't 
    affect the performance of the application and can be managed and stopped at any time.
    """
    ## Process used to obtain the current application version from the server
    _process = None
    ## Start time of the process of obtaining a version number
    _t_0 = None
    
    def __init__(self, version_url):
        """
        Start the sub-process used to read the version URL
        """
        self._process = subprocess.Popen([sys.executable, __file__,
                                          '-g', '-u%s' % version_url])
        self._t_0 = time.time()
        
    def is_complete(self):
        """
        Method used to poll the reading process. The process will be killed
        if the wait time is longer than a predefined maximum.
        This method should always be called before get_version() to ensure
        accuracy of the version number that is returned.
        """
        if(time.time() - self._t_0 < MAX_WAIT_TIME):
            if self._process.poll() is not None:
                return True
            return False
        else:
            return False
            #self._process.kill()
        return True
    
    def get_version(self):
        """
        Returns the last version number that was read from the server.
        """
        try:
            f = open(VERSION_FILE, 'r')
            return f.read()
        except:
            return DEFAULT_VERSION

class VersionThread(Thread):
    """
    Thread used to start the process of reading the current version of an
    application from the deployment server. 
   
    The VersionChecker is user in a Thread to allow the main application
    to continue dealing with UI requests from the user. The main application
    provides a call-back method for when the version number is obtained. 
    """
    def __init__ (self, url, call_back=None, baggage=None):
        Thread.__init__(self)
        self._url = url
        self._call_back = call_back
        self._baggage = baggage
      
    def run(self):
        """
        Execute the process of reading the current application version number.
        """
        checker = VersionChecker(self._url)
        while(not checker.is_complete()):
            time.sleep(1)
        self._call_back(checker.get_version(), self._baggage)
        
  
def get_version(url, q=None):
    """
    """
    h = urllib.urlopen(url)
    for line in h.readlines():
        version = line.strip()
        if len(re.findall('\d+\.\d+\.\d+$', version)) > 0:
            if q is not None:
                q.put(version)
            return version
    if q is not None:
        q.put(DEFAULT_VERSION)
    return DEFAULT_VERSION
      
class VersionThread2(Thread):
    """
    Thread used to start the process of reading the current version of an
    application from the deployment server. 
   
    The VersionChecker is user in a Thread to allow the main application
    to continue dealing with UI requests from the user. The main application
    provides a call-back method for when the version number is obtained. 
    """
    def __init__ (self, url, call_back=None, baggage=None):
        Thread.__init__(self)
        self._url = url
        self._call_back = call_back
        self._baggage = baggage
        self._t_0 = time.time()
      
    def run(self):
        """
        Execute the process of reading the current application version number.
        """
        def is_complete(p):
            """
            """
            if(time.time() - self._t_0 < MAX_WAIT_TIME):
                if p.is_alive():
                    return True
                return False
            else:
                return False
            
        from multiprocessing import Process, Queue
        q = Queue()
        p = Process(target=get_version, args=(self._url, q,))
        p.start()
        while(not is_complete(p)):
            time.sleep(1)
        version = q.get()
        p.join()
        p.terminate()
        self._call_back(version, self._baggage)
    
            
def write_version(version, filename=VERSION_FILE):
    """
    Store the version number
    This could be put into a DB if the application has one.
    """
    f = open(filename, 'w')
    f.write(version)
    f.close()
        
def _get_version_from_server(url):
    """
    Method executed in the independent process used to read the 
    current version number from the server.
    
    :param url: URL to read the version number from
    
    """
    try: 
        version = _get_version(url)
        write_version(version)
    except:
        write_version(DEFAULT_VERSION)
        
        
        
if __name__ == "__main__": 
    _get_version = False
    _url = 'http://danse.chem.utk.edu/prview_version.php'
    
    opts, args = getopt.getopt(sys.argv[1:], "gu:", ["get", "url="])
    for opt, arg in opts:
        if opt in ("-u", "--url"):
            _url = arg
        elif opt in ("-g", "--get"):
            _get_version = True
            
    if _get_version:
        # Get the version number from the URL.
        _get_version_from_server(_url)
    else: 
        # Test execution of the reading process
        def _process(version, baggage=None):
            print "Received:", version    
        checker = VersionThread(_url, _process)
        checker.start()
        
