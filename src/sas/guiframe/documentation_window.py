import os
import logging
import wx
import webbrowser
import urllib

wx_supports_html2 = True
try:
    import wx.html2 as html
except:
    wx_supports_html2 = False

from gui_manager import get_app_dir


class DocumentationWindow(wx.Frame):
    def __init__(self, parent, id, path, url_instruction, title, size=(850, 540)):
        wx.Frame.__init__(self, parent, id, title, size=size)

        SPHINX_DOC_ENV = "SASVIEW_DOC_PATH"
        if SPHINX_DOC_ENV in os.environ:
            docs_path = os.path.join(os.environ[SPHINX_DOC_ENV])
        else:
            # For the installer, docs are in a top-level directory.  We're not
            # bothering to worry about docs when running using the old
            # (non - run.py) way.
            docs_path = os.path.join(get_app_dir(), "doc")

        file_path = os.path.join(docs_path, path)
        url = "file:///" + urllib.quote(file_path,'\:')+ url_instruction

        if not os.path.exists(file_path):
            logging.error("Could not find Sphinx documentation at %s \
            -- has it been built?", file_path)
        elif wx_supports_html2:
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
