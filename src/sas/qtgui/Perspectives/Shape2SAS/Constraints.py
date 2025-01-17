#Global
import sys
import ast
import traceback
import importlib.util
import re
import warnings

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

#Global SasView
from sas.qtgui.Utilities.ModelEditor import ModelEditor
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor

#Local Perspectives
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
        self.buttonOptions.help.setToolTip("Go to help page")
        self.buttonOptions.closePage.setToolTip("Close Shape2SAS")
        self.buttonOptions.reset.setToolTip("Reset this page to default")

        self.gridLayout_2.addWidget(self.variableTable, 0, 1, 1, 1)
        self.gridLayout_2.addWidget(self.buttonOptions, 1, 0, 1, 0, Qt.AlignmentFlag.AlignRight)

        self.createPlugin = QPushButton("Create Plugin")
        self.createPlugin.setMinimumSize(110, 24)
        self.createPlugin.setMaximumSize(110, 24)
        self.createPlugin.setToolTip("Create and send the plugin model to the Plugin Models Category in Fit panel")

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
model_info = reparameterize("{name}", parameters, translation, __file__)

        ''').lstrip().rstrip())

    def checkPythonSyntax(self, text: str) -> bool:
        """Check if text is valid python syntax"""
        
        try:
            ast.parse(text)
            return True
        
        except SyntaxError as e:
            msg = e.msg
            if "detected at line" in msg:
                msg = msg.split(" (detected at line")[0]
            
            print(f"{msg} at line {e.lineno}:") #Send to GUI output texteditor

            all_lines = traceback.format_exc().split('\n')
            last_lines = all_lines[-4:]
            traceback_to_show = '\n'.join(last_lines)

            if "detected at line" in traceback_to_show:
                traceback_to_show = traceback_to_show.split(" (detected at line")[0]

            print(traceback_to_show) #Send to GUI output texteditor

            return False


    def getConstraints(self, fitPar: list[str], modelName: str) -> tuple[list[str], str, str]:
        """Read inputs from text editor"""

        constraintsStr = self.constraintTextEditor.txtEditor.toPlainText()

        self.checkPythonSyntax(constraintsStr)

        #Get and check import statements
        importStatement = self.getImportStatements(constraintsStr)

        #Get and check parameters
        parameters = self.getParameters(constraintsStr, fitPar)

        #Get and check translation
        translation = self.getTranslation(modelName, constraintsStr, importStatement)

        return importStatement, parameters, translation
    
    def removeFromImport(self, importStatement: list[str], remove: str) -> list[str]:
        """Remove import statement from list"""

        if remove in importStatement:
            importStatement.remove(remove)

    def getTranslation(self, modelName: str, constraintsStr: str, importStatement: list[str]) -> str:
        """Get translation from constraints"""


        #see if translation is in constraints
        if not re.search(r'translation\s*=', constraintsStr):
            warnings.warn("No translation found in constraints")
            self.removeFromImport(importStatement, "from sasmodels.sasmodels.core import reparameterize")
            return ""
        
        translation = re.search(r'translation\s*=\s*"""(.*\n(?:.*\n)*?)"""', constraintsStr, re.DOTALL)
        translationInput = translation.group(1) if translation else ""

        #Check if translation is empty
        if not translationInput:
            self.removeFromImport(importStatement, "from sasmodels.sasmodels.core import reparameterize")
            return ""
        
        #Check if translation is only whitespace
        if not translationInput.strip():
            self.removeFromImport(importStatement, "from sasmodels.sasmodels.core import reparameterize")
            return ""
        
        #Check if reparameterize is imported
        if not re.search(r'from sasmodels.core import reparameterize', constraintsStr):
            raise ValueError("Could not find from sasmodels.sasmodels.core import reparameterize in constraints")

        #Check if translation is set
        model_infoDescription = fr'model_info\s*=\s*reparameterize\(\s*"{modelName}"\s*,\s*parameters\s*,\s*translation\s*,\s*__file__\s*\)'
        model_info = re.search(model_infoDescription, constraintsStr)
        model_info = model_info.group(0) if model_info else ""

        if not model_info:
            raise ValueError("Could not find model_info in constraints")

        translationText = translation.group(0) + "\n" + "\n" + model_info

        return translationText
    
    def getParameters(self, constraintsStr: str, fitPar: list[str]) -> str:
        """Get parameters from constraints"""

        #see if name parameter is in constraints
        if not re.search(r'parameters\s*=', constraintsStr):
            raise ValueError("No parameter found in constraints")

        parameterObject = re.search(r'parameters\s*=\s*\[(.*\n(?:.*\n)*?)\]', constraintsStr, re.DOTALL)
        if not parameterObject:
            raise ValueError("No valid parameters list found in constraints")

        parameters = parameterObject.group(1)
        parametersNames = re.findall(r'\[\s*\'(.*?)\'', parameters)

        #Check parameters in constraints
        if len(parametersNames) != len(fitPar):
            raise ValueError("Number of parameters in constraints does not match checked parameters")

        for name in parametersNames:
            if name not in fitPar:
                raise ValueError(f"{name} does not exists in checked parameters")

        return parameterObject.group(0)

    @staticmethod
    def isImportFromStatement(node: ast.ImportFrom) -> list[str]:
        """Return list of ImportFrom statements"""

        print("TEST", node.module)
        #Check if library exists
        if not importlib.util.find_spec(node.module):
            raise ModuleNotFoundError(f"No module named {node.module}")

        imports = []
        module = importlib.import_module(node.module)

        for alias in node.names:
            #check if library has the attribute
            if not hasattr(module, f"{alias.name}"):
                raise AttributeError(f"module {node.module} has no attribute {alias.name}")

            if alias.asname:
                imports.append(f"{alias.name} as {alias.asname}")
            else:
                imports.append(f"{alias.name}")
        
        return [f"from {node.module} import {', '.join(imports)}"]

    @staticmethod
    def isImportStatement(node: ast.Import) -> list[str]:
        """Return list of Import statements"""

        imports = []
        for alias in node.names:
            #check if library exists
            if not importlib.util.find_spec(alias.name):
                raise ModuleNotFoundError(f"No module named {alias.name}")

            if alias.asname:
                imports.append(f"{alias.name} as {alias.asname}")
            else:
                imports.append(f"{alias.name}")

        return [f"import {', '.join(imports)}"]
    
    def getImportStatements(self, text: str) -> list[str]:
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
        
        except SyntaxError as e: #TODO: should be send to the GUI text editor output
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