"""
Utilities for uploading documentation to GitHub and PatchUploader dialog
"""
import difflib
import gzip # Use gzip to compress data and make unreadable, better chance of causing errors rather than unnessary PRs if corrupted
import json # Use json to process data to avoid security vulnerabilities of pickle
import os

from hashlib import sha224 # Use hashlib to create hashes of files to compare
from pathlib import Path
from PySide6 import QtWidgets, QtCore, QtGui

from sas.qtgui.Utilities.UI.PatchUploaderUI import Ui_PatchUploader

from sas.sascalc.fit import models
from sas.sascalc.data_util.calcthread import CalcThread

from sas.sascalc.doc_regen.makedocumentation import USER_DOC_BASE, MAIN_DOC_SRC

SAVE_DATA_DIRECTORY = USER_DOC_BASE / "data"
SAVE_DATA_FILE = SAVE_DATA_DIRECTORY / "docdata.dat"


def checkDiffs():
    """
    Determinine if documentation has been modified.
    Return list of modified files or None if no changes.
    """
    cur_state = getCurrentState()

    if not os.path.exists(SAVE_DATA_FILE):
        createJson()
        saveToJson(cur_state)
        raise FileNotFoundError("No previous documentation state found. Uploading capabilities not available.") #TODO: Replace with some sort of popup message
    
    with gzip.open(SAVE_DATA_FILE, 'rt', encoding="utf-8") as f:
        prev_state = json.load(f)
    
    # Compare current state to previous state
    dif_dict = {}
    difs = [dif_dict for _ in cur_state.items()]
    cur_items = list(cur_state.items())
    prev_items = list(prev_state.items())
    synchedLists, extraneous = syncLists(cur_items, prev_items)
    for new_file, old_file in synchedLists:
        checkIfUpdated(new_file, old_file, dif_dict)
    
    return dif_dict

def syncLists(list1, list2):
    """
    Synchronize two lists by removing impurities.
    """
    output = []
    extraneous = list2[:]
    for item_1 in list1:
        for item_2 in list2:
            if item_1[0] == item_2[0]:
                output.append((item_1, item_2))
                extraneous.remove(item_2)
                break
        extraneous.append(item_1)
    
    return output, extraneous



def checkIfUpdated(new_file, old_file, dif_dict):
    """
    Helper function that checks if a file has been updated since the last upload.
    :param tuple: (tuple(str, str), tuple(str, str), dict) - tuple of tuples containing file path and last modified date;
    dictionary of files that have been updated since last upload.
    """

    if new_file[0] != old_file[0]:
        # If the file paths do not match, raise
        return Exception("File paths do not match.")
    elif new_file[1] == old_file[1]:
        # Files are the same and have not been modified
        return None
    else:
        dif_dict.update({new_file[0]: new_file[1]})
        return None


def createJson():
    """
    Create JSON file to store data.
    """
    if not os.path.exists(SAVE_DATA_DIRECTORY):
        os.mkdir(SAVE_DATA_DIRECTORY)

    # Create json file
    with open(SAVE_DATA_FILE, 'x', encoding="utf-8"):
        pass


def getCurrentState():
    """
    Get current state of documentation as a dict of file paths and hashes
    """

    cur_state = {}

    # Get all files in the documentation directory
    if not os.path.exists(MAIN_DOC_SRC):
        raise FileNotFoundError("Documentation directory not found. Please try generating documentation before continuing.")

    for root, dirs, files in os.walk(MAIN_DOC_SRC):
        # Filter out 'img' directories before walking into them
        dirs[:] = [d for d in dirs if d not in ('img', 'src')]

        for file in files:
            if file.endswith('.rst'):
                file_path = os.path.join(root, file)
                cur_state[file_path] = getHash(file_path)
    
    return cur_state

def getHash(file_path):
    """
    Returns the hash of the text of file at
    :param file_path: path to file
    """
    with open(file_path, 'r', encoding="utf-8") as f:
        file_text = f.read()
    
    return sha224(file_text.encode()).hexdigest()
    

def saveToJson(data: dict):
    """
    Save data to JSON file.
    """
    if not os.path.exists(SAVE_DATA_FILE):
        createJson()

    json_text = json.dumps(data, ensure_ascii=False, indent=4)
    with gzip.open(SAVE_DATA_FILE, 'wt', encoding="utf-8") as f:
        f.write(json_text)

class PatchUploader(QtWidgets.QDialog, Ui_PatchUploader):
    """
    Dialog for uploading documentation to GitHub
    """

    def __init__(self, parent=None):
        super(PatchUploader, self).__init__(parent._parent)
        self.setupUi(self)

        self.model = QtGui.QStandardItemModel()
        self.model.setColumnCount(2)

        for file in self.getDiffItems():
            self.addItemToModel(file)
            print(file)

        self.lstFiles.setModel(self.model)
    
    def addItemToModel(self, text):
        """
        Add an item to the lstFiles model.
        """
        # Create the checkbox item
        checkbox_item = QtGui.QStandardItem()
        checkbox_item.setCheckable(True)
        checkbox_item.setEditable(False)

        # Create the text item with the Courier New font
        text_item = QtGui.QStandardItem(text)
        text_font = QtGui.QFont("Courier New", pointSize=10, weight=QtGui.QFont.Normal)
        text_item.setFont(text_font)
        text_item.setEditable(False)

        # Add the items to the model
        self.model.appendRow([checkbox_item, text_item])
        print(self.model.item(0, 1).text())
    
    def getDiffItems(self):
        """
        Returns a list of files that have been modified.
        """
        diff_dict = checkDiffs()
        diff_list = [filename for filename in diff_dict.keys()]
        return diff_list
    


