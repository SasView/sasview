import os
import logging
import wx
from wx import Frame
import webbrowser
wx_supports_html2 = float(wx.__version__[:3]) >= 2.9
if wx_supports_html2:
    import wx.html2 as html
else:
    import wx.html as html
from gui_manager import get_app_dir

PATH_APP = get_app_dir() 

class DocumentationWindow(Frame):
    def __init__(self, parent, id, path, title, size=(850, 540)):
        Frame.__init__(self, parent, id, title, size=size)

        SPHINX_DOC_ENV = "SASVIEW_DOC_PATH"
        if SPHINX_DOC_ENV in os.environ:
            docs_path = os.path.join(os.environ[SPHINX_DOC_ENV])
        else:
            # For the installer, docs are in a top-level directory.  We're not
            # bothering to worry about docs when running using the old
            # (non - run.py) way.
            docs_path = os.path.join(PATH_APP, "doc")

        if not os.path.exists(docs_path):
            logging.error("Could not find Sphinx documentation at %s \
            -- has it been built?", docs_path)

        elif wx_supports_html2:
            # Complete HTML/CSS support!
            self.view = html.WebView.New(self)
            self.view.LoadURL("file://" + docs_path + '\\' + path)
            self.Show()
        else: 
            #For cases that do not build against current version dependency
            # Wx 3.0 we provide a webbrowser call - this is particularly for 
            #Red hat used at SNS for which Wx 3.0 is not available.  This
            #does not deal with issue of math in docs of course. 

            webbrowser.open_new_tab("file:///" + docs_path + "/" + path)
            print ("file:///" + docs_path + "/" + path)

 
