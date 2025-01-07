# This Python file uses the following encoding: utf-8
import sys
import ast

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QPushButton

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from sas.qtgui.Utilities.ModelEditor import ModelEditor
from UI.ConstraintsUI import Ui_Constraints
from Tables.variableTable import VariableTable
from ButtonOptions import ButtonOptions



class Constraints(QWidget, Ui_Constraints):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        #Setup variableTable and ButtonOptions here

        #Setup GUI for Constraints
        self.constraintTextEditor = ModelEditor() #SasView's standard text editor
        self.constraintTextEditor.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.constraintTextEditor.gridLayout_16.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout.insertWidget(0, self.constraintTextEditor)
        self.variableTable = VariableTable()
        self.buttonOptions = ButtonOptions()

        self.gridLayout_2.addWidget(self.variableTable, 0, 1, 1, 1)
        self.gridLayout_2.addWidget(self.buttonOptions, 1, 0, 1, 0, Qt.AlignmentFlag.AlignRight)

        self.createPlugin = QPushButton("Create Plugin")
        self.createPlugin.setMinimumSize(110, 24)
        self.createPlugin.setMaximumSize(110, 24)

        self.buttonOptions.horizontalLayout_5.insertWidget(1, self.createPlugin)
        self.buttonOptions.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)

        
        #self.createPlugin.clicked.connect(self.getPluginModel)

    def setConstraints(self, constraints: str, name: str):
        """Set text to QTextEdit containing constraints"""


        self.constraintTextEditor.txtEditor.setPlainText((f'''
#Write libraries to be imported here.
from numpy import inf
from sasmodels.core import reparameterize

#Modify fit parameteres here.
parameters = {constraints}

#Set constraints here.
translation = """

"""
model_info = reparameterize({name}, parameters, translation, __file__)

        ''').lstrip().rstrip())


    def getConstraints(self):
        """Read inputs from text editor"""
        constraints_text = self.constraintTextEditor.txtEditor.toPlainText()
        print(self.checkImportStatement(constraints_text))

        #TODO: Check if constraint button have been clicked. 
        # otherwise return default constraints to checked parameters
        # and return

        # if constraint button is clicked
        #TODO: Check names

        #TODO: Check python syntax

        # return

        return constraints_text
    

    def isImportFromStatement(self, node: ast.ImportFrom) -> list[str]:
        """Return list of ImportFrom statements"""

        imports = []

        for alias in node.names:
            if alias.asname:
                imports.append(f"{alias.name} as {alias.asname}")
            else:
                imports.append(f"{alias.name}")
        
        return [f"from {node.module} import {', '.join(imports)}"]

    def isImportStatement(self, node: ast.Import) -> list[str]:
        """Return list of Import statements"""

        imports = []

        for alias in node.names:
            if alias.asname:
                imports.append(f"{alias.name} as {alias.asname}")
            else:
                imports.append(f"{alias.name}")

        return [f"import {', '.join(imports)}"]
    

    def checkImportStatement(self, text: str) -> list[str]:
        """return all import statements that were 
        written in the text editor"""

        importStatements = []

        try:
            tree = ast.parse(text)
            #look for import statements
            for node in ast.walk(tree):
                #check statement type
                if isinstance(node, ast.ImportFrom):
                    importStatements.extend(self.isImportFromStatement(node))

                elif isinstance(node, ast.Import):
                    importStatements.extend(self.isImportStatement(node))
            
            return importStatements
        
        except SyntaxError as e: #should be send to the GUI text editor output
            error_line = text.splitlines()[e.lineno - 1]
            print(f"Syntax error: {e.msg} at line {e.lineno}: {error_line}")
            return

    
    def clearConstraints(self):
        """Clear text editor containing constraints"""

        self.constraintTextEditor.txtEditor.clear()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Constraints()
    widget.show()
    sys.exit(app.exec())