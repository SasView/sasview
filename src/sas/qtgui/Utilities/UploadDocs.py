"""
Utilities for uploading documentation to GitHub and PatchUploader dialog
"""
import difflib
import gzip # Use gzip to compress data and make unreadable, better chance of causing errors rather than unnessary PRs if corrupted
import json # Use json to process data to avoid security vulnerabilities of pickle
import logging
import os
import requests
import time

from hashlib import sha224 # Use hashlib to create hashes of files to compare
from pathlib import Path
from PySide6 import QtWidgets, QtCore, QtGui
from twisted.internet import threads

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
    
    if not os.path.exists(SAVE_DATA_DIRECTORY / 'static.dat'):
        if not os.path.exists(SAVE_DATA_DIRECTORY):
            os.mkdir(SAVE_DATA_DIRECTORY)

        structure = {'static': {}}

        # Create json file
        with gzip.open(SAVE_DATA_DIRECTORY / 'static.dat', 'wt', encoding="utf-8") as f:
            f.write(json.dumps(structure, ensure_ascii=False, indent=4))
        
        json_data = readFromDat(SAVE_DATA_DIRECTORY / 'static.dat')
        json_data['static'] = getCurrentState()

        with gzip.open(SAVE_DATA_DIRECTORY / 'static.dat', 'wt', encoding="utf-8") as f:
            f.write(json.dumps(json_data, ensure_ascii=False, indent=4))

def updateHash(filepath: Path):
    """
    Update the hash value of a given file stored in docdata.dat
    :param filepath: os.path.Path object of the file to update
    """
    # Generate new hash
    new_hash = getHash(filepath)

    # Retrieve active data and update hash
    active_data = readFromDat(SAVE_DATA_FILE)['active']
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

    json_data = readFromDat(SAVE_DATA_FILE)
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
    :param new_file: tuple(str, str) - tuple containing file path and hash of current state
    :param old_file: tuple(str, str) - tuple containing file path and hash of previous state
    :param dif_dict: dictionary of files that have been updated since last upload.
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

    structure = {'active': {}, 'base': {}}

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
        
    json_data = readFromDat(SAVE_DATA_FILE)
    json_data[library] = data

    with gzip.open(SAVE_DATA_FILE, 'wt', encoding="utf-8") as f:
        f.write(json.dumps(json_data))

def readFromDat(path: Path):
    """
    Open data file and return data as a dict.
    'active': current filenames and hashes
    'base': filenames and hashes from last upload to GitHub
    """
    with gzip.open(path, 'rt', encoding="utf-8") as f:
            raw = f.read()
            json_data = json.loads(raw)
    return json_data

def getHashes(file_path: Path):
    """
    Compare the hashes of a file accross all databases. Effectivly tells you the status of the file edits.
    :param file_path: path to file
    :return: dictionary of hashes from each database
    """
    save_data_json = readFromDat(SAVE_DATA_FILE)
    static_path = [SAVE_DATA_DIRECTORY / file for file in os.listdir(SAVE_DATA_DIRECTORY) if file.endswith('.dat') and file != os.path.basename(SAVE_DATA_FILE)] # Should just be one file
    static_json = readFromDat(static_path[0])

    # Add static database to save_data database
    save_data_json['static'] = static_json['static']

    hash_dict = {}

    for database in save_data_json:
        if file_path in save_data_json[database]:
            hash_dict[database] = save_data_json[database][file_path]

    return hash_dict

class PatchUploader(QtWidgets.QDialog, Ui_PatchUploader):
    """
    Dialog for uploading documentation to GitHub
    """

    docsUploadingSignal = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super(PatchUploader, self).__init__(parent._parent)
        self.setupUi(self)

        self.uploadURL = "http://127.0.0.1:5000/post" # Test server for development, TODO replace later
        self.parent = parent

        self.model = QtGui.QStandardItemModel()

        self.lstFiles.setModel(self.model)
        self.delegate = CheckBoxTextDelegate(self.lstFiles)

        self.lstFiles.setDelegate(self.delegate) # NOTE: Use setDelegate() instead of setItemDelegate()

        self.addSignals()
        self.refresh() # Populate lstFiles with changed files
    
    def addSignals(self):
        """
        Connect signals to slots.
        """
        self.cmdSubmit.clicked.connect(self.apiInteraction)
        self.docsUploadingSignal.connect(self.setWidgetEnabled)
    
    def apiInteraction(self):
        """
        Upload documentation to DANSE API and handle response.
        """
        files = self.genPostRequest()
        self.createThread(files)
        # TODO: Handle response
    
    def refresh(self):
        """
        Check for updated diffs and update lstFiles
        """
        changed_files = self.getDiffItems()
        self.model.clear()

        for file in changed_files:
            basename = os.path.basename(file)
            self.addItemToModel(basename)
        
        if self.model.rowCount() == 0:
            self.cmdSubmit.setEnabled(False)
            self.txtChanges.setEnabled(False)
            self.txtName.setEnabled(False)
            self.delegate.disableTable(True, "No changes to upload")
        else:
            self.cmdSubmit.setEnabled(True)
            self.txtChanges.setEnabled(True)
            self.txtName.setEnabled(True)
            self.delegate.disableTable(False, "")
    
    def genPostRequest(self):
        """
        Format POST request
        """
        files_to_upload = []

        for file in self.getDiffItems():
            if self.isChecked(os.path.basename(file)):
                files_to_upload.append(file)

        # Prepare json information for upload to API
        author_name = self.txtName.text()
        change_msg = self.txtChanges.toPlainText()

        # Check to see if the user has already submitted the file to a branch
        branches_exist = {}
        for file in files_to_upload:
            hashes = getHashes(file)
            if hashes['static'] != hashes['base']:
                # User's submission is already submitted to a branch
                branches_exist[file] = True
            else:
                branches_exist[file] = False
        
        # Format files into a dictionary and open them as binary packets for upload
        rst_content = {}
        for file in files_to_upload:
            rst_content[file] = open(file, 'rb')

        #Format into a json request to send to DANSE-2 API
        json_packet = {'sasview_version': __version__,
                       'author': author_name,
                       'changes': change_msg,
                       'branches_exist': branches_exist
                    }

        files = {'json': (None, json.dumps(json_packet), 'application/json')}
        for key, value in rst_content.items():
            files[key] = (key, value, 'application/octet-stream')

        return files
    
    def createThread(self, files):
        """
        Create a thread to send the request to the API
        """
        self.parent.communicate.statusBarUpdateSignal.emit('Beginning documentation upload...')
        self.docsUploadingSignal.emit(True)
        d = threads.deferToThread(self.sendRequest, self.uploadURL, files)
        d.addCallback(self.docUploadComplete)
        
    @staticmethod
    def sendRequest(url, files):
        """
        Send the request to the API in separate thread
        """
        thread = DocsUploadThread(url, files)

        return thread.response
    
    def docUploadComplete(self, response):
        """
        Handle the response from the API
        """
        if response.status_code == 200:
            self.docsUploadingSignal.emit(False) # Trigger the signal to re-enable the dialog
            self.parent.communicate.statusBarUpdateSignal.emit('Documentation uploaded successfully.')

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

    def setWidgetEnabled(self, uploading: bool):
        """
        Enable/disable the PatchUploader dialog during upload.
        """
        enabled = not uploading # If uploading, dialog is DISabled
        self.cmdSubmit.setEnabled(enabled)
        self.txtChanges.setEnabled(enabled)
        self.txtName.setEnabled(enabled)
        if uploading:
            self.cmdSubmit.setText("Uploading...")
            self.cmdSubmit.setStyleSheet("color: red")
            self.delegate.disableTable(True, "Upload in progress...")
        else:
            self.cmdSubmit.setText("Submit")
            self.cmdSubmit.setStyleSheet("color: black")
            self.delegate.disableTable(False, "")


class CheckBoxTextDelegate(QtWidgets.QStyledItemDelegate):
    """
    Delegate for the PatchUploader dialog that draws a checkbox and text in the same row.
    Includes functionality for "disabling" the table
    """
    def __init__(self, parent=None):
        super(CheckBoxTextDelegate, self).__init__(parent)
        self.disabled = False  # Flag to track if the table is disabled
        self.disabled_text = "Table is disabled"  # Default text for disabled state

    def paint(self, painter, option, index):
        if self.disabled:
            # First, paint the items normally
            self.paintEnabled(painter, option, index)

            # Then, trigger a repaint of the entire table
            self.paintDisabledOverlay(painter)
        else:
            # Paint the items normally
            self.paintEnabled(painter, option, index)

    def paintDisabledOverlay(self, painter):
        # Get the dimensions of the entire table view
        table_rect = self.parent().viewport().rect()

        # Set the painter to use a semi-transparent light gray color
        semi_transparent_gray = QtGui.QColor(200, 200, 200, 150)
        painter.fillRect(table_rect, semi_transparent_gray)

        # Set the pen and font for drawing the italic text
        painter.setPen(QtGui.QColor(100, 100, 100))
        font = painter.font()
        font.setItalic(True)
        painter.setFont(font)

        # Draw the italic text in the center of the table
        painter.drawText(table_rect, QtCore.Qt.AlignCenter, self.disabled_text)

    def paintEnabled(self, painter, option, index):
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

    def disableTable(self, disable, text="Table is disabled"):
        """
        Function to enable or disable the table rendering.
        When disabled, the table is painted with a semi-transparent overlay and text.
        """
        self.disabled = disable
        self.disabled_text = text
        self.parent().viewport().update()  # Trigger a repaint of the table

    def editorEvent(self, event, model, option, index):
        if self.disabled:
            return False  # Ignore events when the table is disabled

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

class DocsUploadThread():
    """Thread performing a request to GitHub
    NOTE: Not using CalcThread because it created weird heisenbugs that interfered with callbacks (also overkill)
    """

    def __init__(self,
                 upload_url,
                 files,):
        self.url = upload_url
        self.files = files
        self.response = None
        self.compute()

    def compute(self):
        """
        Upload the docs in a separate thread
        """
        try:
            response = requests.post(self.url, files=self.files)

            # Close the file bytestreams after the request is sent
            for key, file in self.files.items():
                if file[1] is not None and key != 'json':
                    file[1].close()
                
            self.response = response
            return
        except KeyboardInterrupt as msg:
            logging.log(0, msg)
