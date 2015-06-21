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
import sys
import os
import logging
import wx
import webbrowser
import urllib

SPHINX_DOC_ENV = "SASVIEW_DOC_PATH"
WX_SUPPORTS_HTML2 = True
try:
    import wx.html2 as html
except:
    WX_SUPPORTS_HTML2 = False
if sys.platform.count("win32") > 0:
    #this is a PC
    WX_SUPPORTS_HTML2 = True
else:
    #this is a MAC
    WX_SUPPORTS_HTML2 = False

from gui_manager import get_app_dir


class DocumentationWindow(wx.Frame):
    def __init__(self, parent, dummy_id, path, url_instruction, title, size=(850, 540)):
        wx.Frame.__init__(self, parent, dummy_id, title, size=size)

        if SPHINX_DOC_ENV in os.environ:
            docs_path = os.path.join(os.environ[SPHINX_DOC_ENV])
        else:
            # For the installer, docs are in a top-level directory.  We're not
            # bothering to worry about docs when running using the old
            # (non - run.py) way.
            docs_path = os.path.join(get_app_dir(), "doc")

        file_path = os.path.join(docs_path, path)
        url = "file:///" + urllib.quote(file_path, '/\:')+ url_instruction

        if not os.path.exists(file_path):
            logging.error("Could not find Sphinx documentation at %s \
            -- has it been built?", file_path)
        elif WX_SUPPORTS_HTML2:
            # Complete HTML/CSS support!
            self.view = html.WebView.New(self)
            self.view.LoadURL(url)
            self.Show()
        else:
            logging.error("No html2 support, popping up a web browser")
            #For cases that do not build against current version dependency
            # Wx 3.0 we provide a webbrowser call - this is particularly for
            #Red hat used at SNS for which Wx 3.0 is not available.  This
            #does not deal with issue of math in docs of course.
            webbrowser.open_new_tab(url)

def main():
    app = wx.App()
    DocumentationWindow(None, -1, "index.html", "", "Documentation",)
    app.MainLoop()

if __name__ == '__main__':
    main()
