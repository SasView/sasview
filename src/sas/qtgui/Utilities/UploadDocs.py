"""
Utilities for uploading documentation to GitHub and PatchUploader dialog
"""
import difflib
import gzip # Use gzip to compress data and make unreadable, better chance of causing errors rather than unnessary PRs if corrupted
import json # Use json to process data to avoid security vulnerabilities of pickle
import logging
import os

from hashlib import sha224 # Use hashlib to create hashes of files to compare
from pathlib import Path
from PySide6 import QtWidgets, QtCore, QtGui

from sas.qtgui.Utilities.UI.PatchUploaderUI import Ui_PatchUploader

from sas.sascalc.fit import models
from sas.sascalc.data_util.calcthread import CalcThread

from sas.sascalc.doc_regen.makedocumentation import USER_DOC_BASE, MAIN_DOC_SRC

from sas.system.version import __version__

SAVE_DATA_DIRECTORY = USER_DOC_BASE / __version__ / "data"
SAVE_DATA_FILE = SAVE_DATA_DIRECTORY / "docdata.dat"

logger = logging.getLogger(__name__)

def TEMPORARY():
    """
    Create temporary data file if it doesn't already exist.
    Will be removed in future commit--data file should be created by SasView the first time it is run.
    """
    if not os.path.exists(SAVE_DATA_FILE):
        createDat()
        saveToDat(getCurrentState(), 'active')
        saveToDat(getCurrentState(), 'base')

def updateHash(filepath: Path):
    """
    Update the hash value of a given file stored in docdata.dat
    :param filepath: os.path.Path object of the file to update
    """
    # Generate new hash
    new_hash = getHash(filepath)

    # Retrieve active data and update hash
    active_data = readFromDat()['active']
    try:
        active_data[str(filepath)] = new_hash
    except KeyError:
        logger.warning(f"Could not find hash for {filepath} in active data. Documentation may be impossible to upload.")
    
    # Save active data
    saveToDat(active_data, 'active')

def checkDiffs():
    """
    Determinine if documentation has been modified.
    Return list of modified files or None if no changes.
    """

    TEMPORARY()

    if not os.path.exists(SAVE_DATA_FILE):
        raise FileNotFoundError("No previous documentation state found. Uploading capabilities not available.")
        #TODO: Replace with some sort of popup message

    json_data = readFromDat()
    cur_docstate = json_data['active']
    prev_state = json_data['base']
    
    # Compare current state to previous state
    dif_dict = {}
    difs = [dif_dict for _ in cur_docstate.items()]
    cur_items = list(cur_docstate.items())
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


def createDat():
    """
    Create .dat file to store data with JSON template
    WARNING: Will overwrite existing data if it exists
    """
    if not os.path.exists(SAVE_DATA_DIRECTORY):
        os.mkdir(SAVE_DATA_DIRECTORY)

    structure = {'active': {}, 'base': {}, 'static': {}}

    # Create json file
    with gzip.open(SAVE_DATA_FILE, 'wt', encoding="utf-8") as f:
        f.write(json.dumps(structure, ensure_ascii=False, indent=4))


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
    

def saveToDat(data: dict, library: str):
    """
    Save data to JSON file.
    :param data: data to save
    :param library: One of: 'active' or 'base'
    """
    if not os.path.exists(SAVE_DATA_FILE):
        # If data file does not exist, create it
        createDat()
        logger.warning("Documentation from last upload not found! Created new data file.")
        #TODO: Compare active to static and if they are not the same, you have a more serious problem!
        
    json_data = readFromDat()
    json_data[library] = data

    with gzip.open(SAVE_DATA_FILE, 'wt', encoding="utf-8") as f:
        f.write(json.dumps(json_data))

def readFromDat():
    """
    Open data file and return data as a dict.
    'active': current filenames and hashes
    'base': filenames and hashes from last upload to GitHub
    """
    with gzip.open(SAVE_DATA_FILE, 'rt', encoding="utf-8") as f:
            raw = f.read()
            json_data = json.loads(raw)
    return json_data

class PatchUploader(QtWidgets.QDialog, Ui_PatchUploader):
    """
    Dialog for uploading documentation to GitHub
    """

    def __init__(self, parent=None):
        super(PatchUploader, self).__init__(parent._parent)
        self.setupUi(self)

        self.model = QtGui.QStandardItemModel()

        for file in self.getDiffItems():
            basename = os.path.basename(file)
            self.addItemToModel(basename)

        self.lstFiles.setModel(self.model)
        self.lstFiles.setItemDelegate(CheckBoxTextDelegate())

        self.addSignals()
    
    def addSignals(self):
        """
        Connect signals to slots.
        """
        self.cmdSubmit.clicked.connect(self.upload)
    
    def upload(self):
        """
        Upload documentation to GitHub
        """
        files_to_upload = []

        for file in self.getDiffItems():
            if self.isChecked(os.path.basename(file)):
                files_to_upload.append(file)

        # Prepare json information for upload to API
        author_name = self.txtName.text()
        change_msg = self.txtChanges.toPlainText()

        #TODO: Implement upload to GitHub API
    
    def isChecked(self, basename):
        """
        Return True if the checkbox for the given file is checked.
        Assume no duplicate names.
        """
        for i in range(self.model.rowCount()):
            if self.model.item(i, 1).text() == basename:
                return self.model.item(i, 0).checkState() == QtCore.Qt.Checked
        raise ValueError(f"File {basename} not found in model.")

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
    
    def getDiffItems(self):
        """
        Returns a list of files that have been modified.
        """
        diff_dict = checkDiffs()
        diff_list = [filename for filename in diff_dict.keys()]
        return diff_list

class CheckBoxTextDelegate(QtWidgets.QStyledItemDelegate):
    """
    Delegate for the PatchUploader dialog that draws a checkbox and text in the same row.
    """
    def paint(self, painter, option, index):
        model = index.model()

        # Get the checkbox item and the text item from the model
        checkbox_item = model.item(index.row(), 0)
        text_item = model.item(index.row(), 1)

        # Draw the checkbox
        if checkbox_item:
            checkbox_rect = QtWidgets.QStyle.alignedRect(option.direction, QtCore.Qt.AlignLeft,
                                                         QtCore.QSize(20, 20), option.rect)
            check_state = QtWidgets.QStyle.State_Off
            if checkbox_item.checkState() == QtCore.Qt.Checked:
                check_state = QtWidgets.QStyle.State_On

            checkbox_option = QtWidgets.QStyleOptionButton()
            checkbox_option.rect = checkbox_rect
            checkbox_option.state = QtWidgets.QStyle.State_Enabled | check_state

            QtWidgets.QApplication.style().drawPrimitive(QtWidgets.QStyle.PE_IndicatorCheckBox,
                                                         checkbox_option, painter)

        # Draw the text
        if text_item:
            text_rect = option.rect
            text_rect.setLeft(checkbox_rect.right() + 5)
            painter.drawText(text_rect, QtCore.Qt.AlignVCenter, text_item.text())

    def editorEvent(self, event, model, option, index):
        # Check if the event is a mouse button press or release
        if event.type() == QtCore.QEvent.MouseButtonPress or event.type() == QtCore.QEvent.MouseButtonRelease:
            # Get the checkbox item from the model
            checkbox_item = model.item(index.row(), 0)
            if checkbox_item:
                 # Toggle the checkbox state on mouse button press
                if event.type() == QtCore.QEvent.MouseButtonPress:
                    if checkbox_item.checkState() == QtCore.Qt.Checked:
                        checkbox_item.setCheckState(QtCore.Qt.Unchecked)
                    else:
                        checkbox_item.setCheckState(QtCore.Qt.Checked)
                # Indicate that the event has been handled
                return True
        # Pass the event on if it's not handled
        return False
    