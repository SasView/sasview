"""
documentation module provides a simple means to add help throughout the
application. It checks for the existence of html2 package needed to support
fully html panel which supports css.  The class defined here takes a title for
the particular help panel, a pointer to the html documentation file of interest
within the documentation tree along with a 'command' string such as a page
anchor or a query string etc.  The path to the doc directory is retrieved
automatically by the class itself.  Thus with these three pieces of information
the class generates a panel with the appropriate title bar and help file
formatted according the style sheets called in the html file.  Finally, if an
old version of Python is running and the html2 package is not available the
class brings up the default browser and passes the file:/// string to it.  In
this case however the instruction portion is usually not passed for security
reasons.
"""
import os
import logging
import webbrowser
import urllib
import sys

import wx
try:
    import wx.html2 as html
    WX_SUPPORTS_HTML2 = True
except ImportError:
    WX_SUPPORTS_HTML2 = False

from sas import get_app_dir

# Don't use wx html renderer on windows.
if os.name == 'nt':
    WX_SUPPORTS_HTML2 = False

logger = logging.getLogger(__name__)

SPHINX_DOC_ENV = "SASVIEW_DOC_PATH"

THREAD_STARTED = False
def start_documentation_server(doc_root, port):
    import thread
    global THREAD_STARTED
    if not THREAD_STARTED:
        thread.start_new_thread(_documentation_server, (doc_root, port))
        THREAD_STARTED = True

def _documentation_server(doc_root, port):
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from SocketServer import TCPServer

    os.chdir(doc_root)
    httpd = TCPServer(("127.0.0.1", port), SimpleHTTPRequestHandler, bind_and_activate=False)
    httpd.allow_reuse_address = True
    try:
        httpd.server_bind()
        httpd.server_activate()
        httpd.serve_forever()
    finally:
        httpd.server_close()

class DocumentationWindow(wx.Frame):
    """
    DocumentationWindow inherits from wx.Frame and provides a centralized
    coherent framework for all help documentation.  Help files must be html
    files stored in an properly organized tree below the top 'doc' folder.  In
    order to display the appropriate help file from anywhere in the gui, the
    code simply needs to know the location below the top level where the
    help file resides along with the name of the help file.
    called
    (self, parent, dummy_id, path, url_instruction, title, size=(850, 540))

    :param path: path to html file beginning AFTER /doc/ and ending in the\
    file.html.
    :param url_instructions: anchor string or other query e.g. '#MyAnchor'
    :param title: text to place in the title bar of the help panel
    """
    def __init__(self, parent, dummy_id, path, url_instruction, title, size=(850, 540)):
        wx.Frame.__init__(self, parent, dummy_id, title, size=size)

        if SPHINX_DOC_ENV in os.environ:
            docs_path = os.path.join(os.environ[SPHINX_DOC_ENV])
        else:
            # For the installer, docs are in a top-level directory.  We're not
            # bothering to worry about docs when running using the old
            # (non - run.py) way.
            docs_path = os.path.join(get_app_dir(), "doc")

        #note that filepath for mac OS, at least in bundle starts with a
        #forward slash as /Application, while the PC string begins C:\
        #It seems that mac OS is happy with four slashes as in file:////App...
        #Two slashes is not sufficient to indicate path from root.  Thus for now
        #we use "file:///" +... If the mac behavior changes may need to make the
        #file:/// be another constant at the beginning that yields // for Mac
        #and /// for PC.
        #Note added June 21, 2015     PDB
        file_path = os.path.join(docs_path, path)
        if path.startswith('http'):
            url = path
        elif not os.path.exists(file_path):
            url = "index.html"
            logger.error("Could not find Sphinx documentation at %s -- has it been built?",
                         file_path)
        elif False:
            start_documentation_server(docs_path, port=7999)
            url = "http://127.0.0.1:7999/" + path.replace('\\', '/') + url_instruction
        else:
            url = "file:///" + urllib.quote(file_path, r'/\:')+ url_instruction

        #logger.info("showing url " + url)
        if WX_SUPPORTS_HTML2:
            # Complete HTML/CSS support!
            self.view = html.WebView.New(self)
            self.view.LoadURL(url)
            self.Bind(html.EVT_WEBVIEW_ERROR, self.OnError, self.view)
            self.Show()
        else:
            logger.error("No html2 support, popping up a web browser")
            #For cases that do not build against current version dependency
            # Wx 3.0 we provide a webbrowser call - this is particularly for
            #Red hat used at SNS for which Wx 3.0 is not available.  This
            #does not deal with issue of math in docs of course.
            webbrowser.open_new_tab(url)

    def OnError(self, evt):
        logger.error("%d: %s", evt.GetInt(), evt.GetString())

def main():
    """
    main loop function if running alone for testing.
    """
    url = "index.html" if len(sys.argv) <= 1 else sys.argv[1]
    app = wx.App()
    DocumentationWindow(None, -1, url, "", "Documentation",)
    app.MainLoop()

if __name__ == '__main__':
    main()
