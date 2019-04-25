import os
import sys
import io

import wx.py.document

def patch_py_editor():
    """
    Monkeypatch wx.py.document.Document with py2/3 compatible file I/O.

    Tested on py2 and py3 with wx 4.0.1.  It works well enough for loading
    and saving from wx.py.editor, but it changes the interface to Document
    to only support unicode text, whereas the old version of Document in
    python 2.7 only supports bytes.
    """
    wx.py.document.Document.read = read
    wx.py.document.Document.write = write

def read(self):
    """Return contents of file."""
    if self.filepath and os.path.exists(self.filepath):
        with io.open(self.filepath, mode='r', encoding='utf8') as f:
            return f.read()
    else:
        return ''

def write(self, text):
    """Write text to file."""
    with io.open(self.filepath, mode='w', encoding='utf8') as f:
        f.write(text)
