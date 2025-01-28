#Global
import sys
import ast
import traceback
import importlib.util
import re
import warnings
from typing import Union

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

#Global SasView
from sas.qtgui.Utilities.ModelEditor import ModelEditor

#Local Perspectives
from UI.ConstraintsUI import Ui_Constraints
from Tables.variableTable import VariableTable
from ButtonOptions import ButtonOptions

class PythonEditor():
    def __init__(self, parent=None):
        super().__init__(parent)

        self.constraintTextEditor = ModelEditor() #SasView's standard text editor
        self.constraintTextEditor.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.constraintTextEditor.gridLayout_16.setContentsMargins(5, 5, 5, 5)

    


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

    def getConstraintText(self, constraints: str) -> str:
        """Get default text for constraints"""
    
        self.constraintText = (f'''
#Write libraries to be imported here.
from numpy import inf

#Modify fit parameteres here.
parameters = {constraints}

#Set constraints here.
translation = """

"""

        ''').lstrip().rstrip()

        return self.constraintText

 
    def setConstraints(self, constraints: str):
        """Set text to QTextEdit"""

        constraints = self.getConstraintText(constraints)
        self.constraintTextEditor.txtEditor.setPlainText(constraints)


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


    def getConstraints(self, constraintsStr: str, fitPar: list[str], modelPars: list[str], 
                       modelVals: list[list[float]], checkedPars: list[str]) -> tuple[list[str], str, str, list[list[bool]]]:
        """Read inputs from text editor"""

        self.checkPythonSyntax(constraintsStr)

        #Get and check import statements
        importStatement = self.getImportStatements(constraintsStr)

        #Get and check parameters
        parameters = self.getParameters(constraintsStr, fitPar)

        #Get and check translation
        translation, checkedPars = self.getTranslation(constraintsStr, importStatement, modelPars, modelVals, checkedPars)

        return importStatement, parameters, translation, checkedPars

    @staticmethod
    def getPosition(item: Union[str, float, int], itemLists: list[list[Union[str, float, int]]]) -> tuple[int, int]:
        """Find position of an item in lists"""

        for i, sublist in enumerate(itemLists):
            if item in sublist:
                return i, sublist.index(item)

    @staticmethod
    def removeFromList(listItems: list[Union[str, float, int]], listToCompare: list[Union[str, float, int]]) -> list[str]:
        """Remove items from a list if in another list"""

        removedPars = []
        for item in listItems:
            for statement in listToCompare:
                if item in statement:
                    #NOTE: library names, "from" and "import" will also be removeds
                    removedPars.append(item)

        for remove in removedPars:
            if remove in listItems:
                listItems.remove(remove)

    @staticmethod
    def ifParameterExists(lineNames: list[str], modelPars: list[list[str]]) -> bool:
        """Check if parameter exists in model parameters"""

        for par in lineNames:
            boolPar = any(par in sublist for sublist in modelPars)
            if not boolPar:
                raise ValueError(f"{par} does not exist in model parameters")

        return False

    def getTranslation(self, constraintsStr: str, 
                       importStatement: list[str], 
                       modelPars: list[list[str]], 
                       modelVals: list[list[float]], 
                       checkedPars: list[list[str]]) -> tuple[str, list[list[bool]]]:
        """Get translation from constraints"""

        #see if translation is in constraints
        if not re.search(r'translation\s*=', constraintsStr):
            raise ValueError("No translation found in constraints")

        translation = re.search(r'translation\s*=\s*"""(.*\n(?:.*\n)*?)"""', constraintsStr, re.DOTALL)
        translationInput = translation.group(1) if translation else ""

        #Check syntax
        self.checkPythonSyntax(translationInput) #TODO: fix wrong line number output for translation
        lines = translationInput.split('\n')

        #remove empty lines
        lines = [line for line in lines if line.strip()]

        #Check parameters and update checkedPars
        for i in range(len(lines)):
            
            if '=' not in lines[i]:
                raise ValueError("No '=' found in translation line")

            if lines[i].count('=') > 1:
                raise ValueError("More than one '=' found in translation line")
            
            leftLine, rightLine = lines[i].split('=')

            #unicode greek letters: \u0370-\u03FF
            rightPars = re.findall(r'(?<=)[a-zA-Z_\u0370-\u03FF]\w*\b', rightLine)
            leftPars = re.findall(r'(?<=)[a-zA-Z_\u0370-\u03FF]\w*\b', leftLine)

            #check for import statements (I can't imagine a case where it would be to the left)
            self.removeFromList(rightPars, importStatement)

            #check if parameters exist in model parameters
            self.ifParameterExists(rightPars + leftPars, modelPars)
            
            #Translate
            notes = ""
            for par in rightPars:
                j, k = self.getPosition(par, modelPars)
                if checkedPars[j][k]:
                    #if parameter is a fit parameter, don't remove it
                    continue
                else:
                    #if parameter is a constant, set inputted value
                    inputVal = modelVals[j][k]

                    #update line with input value
                    rightLine = re.sub(r'\b' + re.escape(par) + r'\b', str(inputVal), rightLine)
                    notes += f"{par} = {inputVal},"
            
            #any constants added to notes?
            if notes:
                notes = f" #{notes}"

            for par in leftPars:
                j, k = self.getPosition(par, modelPars)
                #check if paramater are to be set in ModelProfile
                checkedPars[j][k] = True
            
            lines[i] = leftLine + '=' + rightLine + notes

        #return lines to string
        translationInput = '\n'.join(lines)

        return translationInput, checkedPars
    

    def getParameters(self, constraintsStr: str, fitPar: list[str]) -> str:
        """Get parameters from constraints"""

        #see if name parameter is in constraints
        if not re.search(r'parameters\s*=', constraintsStr):
            raise ValueError("No parameter found in constraints")

        parameterObject = re.search(r'parameters\s*=\s*\[(.*\n(?:.*\n)*?)\]', constraintsStr, re.DOTALL)
        if not parameterObject:
            raise ValueError("No valid parameters list found in constraints")

        parameters = parameterObject.group(1)
        parametersNames = re.findall(r'\[\s*\'(.*?)\'', parameters) #Get first element in list

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
            #get name and asname
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


    def onClosingConstraints(self):
        """Close constraints page"""

        self.close()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Constraints()
    widget.show()
    sys.exit(app.exec())