#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib.request, urllib.error, urllib.parse
import sys
import json
import logging
import re

'''
HTTP Proxy parser and Connection

connect() function:
    - auto detects proxy in windows, osx
    - in ux systems, the http_proxy enviroment variable must be set
    - if it fails, try to find the proxy.pac address.
      - parses the file, and looks up for all possible proxies
'''


class ConnectionProxy(object):

    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout

    def _get_addresses_of_proxy_pac(self):
        """
        Return a list of possible auto proxy .pac files being used,
        based on the system registry (win32) or system preferences (OSX).
        @return: list of urls
        """
        pac_files = []
        if sys.platform == 'win32':
            try:
                import winreg as winreg  # used from python 2.0-2.6
            except:
                import winreg  # used from python 2.7 onwards
            net = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
            )
            n_subs, n_vals, last_mod = winreg.QueryInfoKey(net)
            subkeys = {}
            for i in range(n_vals):
                this_name, this_val, this_type = winreg.EnumValue(net, i)
                subkeys[this_name] = this_val
            if 'AutoConfigURL' in list(subkeys.keys()) and len(subkeys['AutoConfigURL']) > 0:
                pac_files.append(subkeys['AutoConfigURL'])
        elif sys.platform == 'darwin':
            import plistlib
            sys_prefs = plistlib.readPlist(
                '/Library/Preferences/SystemConfiguration/preferences.plist')
            networks = sys_prefs['NetworkServices']
            # loop through each possible network (e.g. Ethernet, Airport...)
            for network in list(networks.items()):
                # the first part is a long identifier
                net_key, network = network
                if 'ProxyAutoConfigURLString' in list(network['Proxies'].keys()):
                    pac_files.append(
                        network['Proxies']['ProxyAutoConfigURLString'])
        return list(set(pac_files))  # remove redundant ones

    def _parse_proxy_pac(self, pac_urls_list):
        '''
        For every pac file url in pac_urls_list, it tryes to connect.
        If the connection is successful parses the file in search for
        http proxies.
        @param pac_urls_list: List with urls for the pac files
        @return: list with all found http proxies
        '''
        proxy_url_list = []
        for this_pac_url in pac_urls_list:
            logging.debug('Trying pac file (%s)...' % this_pac_url)
            try:
                response = urllib.request.urlopen(
                    this_pac_url, timeout=self.timeout)
                logging.debug('Succeeded (%s)...' % this_pac_url)
            except Exception:
                logging.debug('Failled (%s)...' % this_pac_url)
                continue
            pacStr = response.read()
            possProxies = re.findall(
                r"PROXY\s([^\s;,:]+:[0-9]{1,5})[^0-9]", pacStr + '\n')
            for thisPoss in possProxies:
                prox_url = 'http://' + thisPoss
                proxy_dic = {'http': prox_url}
                proxy_url_list.append(proxy_dic)
        return proxy_url_list

    def _set_proxy(self,proxy_dic=None):
        '''
        Sets connection proxy.
        if proxy_dic is None get's teh proxy from the system.
        To disable autodetected proxy pass an empty dictionary: {}
        @param proxy_dic: format: {'http': 'http://www.example.com:3128/'}               
        '''
        if proxy_dic is None:
            # The default is to read the list of proxies from the environment variables <protocol>_proxy.
            # If no proxy environment variables are set, then in a Windows environment proxy settings are
            # obtained from the registry's Internet Settings section, and in a Mac OS X environment proxy
            # information is retrieved from the OS X System Configuration
            # Framework.
            proxy = urllib.request.ProxyHandler()
        else:
            # If proxies is given, it must be a dictionary mapping protocol names to
            # URLs of proxies.
            proxy = urllib.request.ProxyHandler(proxy_dic)
        opener = urllib.request.build_opener(proxy)
        urllib.request.install_opener(opener)

    def connect(self):
        '''
        Performs the request and gets a response from self.url
        @return: response object from urllib2.urlopen
        '''
        req = urllib.request.Request(self.url)
        response = None
        try:
            logging.debug("Trying Direct connection to %s..."%self.url)
            response = urllib.request.urlopen(req, timeout=self.timeout)
        except Exception as e:
            logging.debug("Failed!")
            logging.debug(e)
            try:
                logging.debug("Trying to use system proxy if it exists...")
                self._set_proxy()
                response = urllib.request.urlopen(req, timeout=self.timeout)
            except Exception as e:
                logging.debug("Failed!")
                logging.debug(e)
                pac_urls = self._get_addresses_of_proxy_pac()
                proxy_urls = self._parse_proxy_pac(pac_urls)
                for proxy in proxy_urls:
                    try:
                        logging.debug("Trying to use the proxy %s found in proxy.pac configuration"%proxy)
                        self._set_proxy(proxy)
                        response = urllib.request.urlopen(req, timeout=self.timeout)
                    except Exception as e:
                        logging.debug("Failed!")
                        logging.debug(e)
        if response is not None:
            logging.debug("The connection to %s was successful."%self.url)
        else:
            logging.warning("Connection to %s failed..."%self.url)
        return response


if __name__ == "__main__":
    from pprint import pprint
    c = Connection()
    response = c.connect()
    if response is not None:
        print(50 * '-')
        content = json.loads(response.read().strip())
        pprint(content)

