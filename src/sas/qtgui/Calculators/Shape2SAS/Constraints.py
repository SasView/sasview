#Global
import ast
import importlib.util
import logging
import re
import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QWidget

from sas.qtgui.Calculators.Shape2SAS.ButtonOptions import ButtonOptions
from sas.qtgui.Calculators.Shape2SAS.Tables.variableTable import VariableTable

#Local Perspectives
from sas.qtgui.Calculators.Shape2SAS.UI.ConstraintsUI import Ui_Constraints

#Global SasView
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.ModelEditor import ModelEditor

logger = logging.getLogger(__name__)

VAL_TYPE = str | int | float


class Constraints(QWidget, Ui_Constraints):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        #Setup GUI for Constraints
        self.constraintTextEditor = ModelEditor() #SasView's standard text editor
        self.constraintTextEditor.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.constraintTextEditor.gridLayout_16.setContentsMargins(5, 5, 5, 5)
        self.constraintTextEditor.groupBox_13.setTitle("Constraints") #override title
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
        self.createPlugin.setEnabled(False)

        self.buttonOptions.horizontalLayout_5.insertWidget(1, self.createPlugin)
        self.buttonOptions.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)

        #Setup default logbook text
        defaultText = "<span><b>Shape2SAS plugin constraints log</b></p></span>"
        self.textEdit_2.append(defaultText)


    def getConstraintText(self, constraints: str) -> str:
        """Get default text for constraints"""

        self.constraintText = (f'''
#Write libraries to be imported here.
from numpy import inf

#Modify fit parameters here.
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
        self.createPlugin.setEnabled(True)

    def checkPythonSyntax(self, text: str):
        """Check if text is valid python syntax"""

        try:
            ast.parse(text)

        except SyntaxError:
            #Get last line of traceback
            all_lines = traceback.format_exc().split('\n')
            last_lines = all_lines[-1:]
            traceback_to_show = '\n'.join(last_lines)

            #send to log
            logger.error(traceback_to_show)

    def getConstraints(self, constraintsStr: str, fitPar: [str], modelPars: [str], modelVals: [[float]],
                       checkedPars: [str]) -> ([str], str, str, [[bool]]):
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
    def getPosition(item: VAL_TYPE, itemLists: [[VAL_TYPE]]) -> (int, int):
        """Find position of an item in lists"""

        for i, sublist in enumerate(itemLists):
            if item in sublist:
                return i, sublist.index(item)

    @staticmethod
    def removeFromList(listItems: [VAL_TYPE], listToCompare: [VAL_TYPE]):
        """Remove items from a list if in another list"""

        finalpars = []
        for item in listItems:
            for statement in listToCompare:
                if item not in statement:
                    #NOTE: library names, "from" and "import" will also be removeds
                    finalpars.append(item)
        # Explicilty modify list sent to the method
        listItems = finalpars

    def ifParameterExists(self, lineNames: [str], modelPars: [[str]]) -> bool:
        """Check if parameter exists in model parameters"""

        for par in lineNames:
            boolPar = any(par in sublist for sublist in modelPars)
            if not boolPar:
                logger.error(f"{par} does not exist in parameter table")

        return False

    def getTranslation(self, constraintsStr: str, importStatement: [str], modelPars: [[str]], modelVals: [[float]],
                       checkedPars: [[str]]) -> (str, [[bool]]):
        """Get translation from constraints"""

        #see if translation is in constraints
        if not re.search(r'translation\s*=', constraintsStr):
            logger.warn("No variable translation found in constraints")

        #TODO: make getParametersFromConstraints general, so translation can be inputted
        #NOTE: re.search() a bit slow, ast faster
        translation = re.search(r'translation\s*=\s*"""(.*\n(?:.*\n)*?)"""', constraintsStr, re.DOTALL)
        translationInput = translation.group(1) if translation else ""

        #Check syntax
        self.checkPythonSyntax(translationInput) #TODO: fix wrong line number output for translation
        lines = translationInput.split('\n')

        #remove empty lines and tabs
        lines = [line.replace('\t', '').strip() for line in lines if line.strip()]
        translationInput = ''

        #Check parameters and update checkedPars
        for line in lines:
            if line.count('=') != 1:
                logger.warn(f"Constraints may only have a single '=' sign in them. Please fix {line}.")

            #split line
            leftLine, rightLine = line.split('=')

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
                if not checkedPars[j][k]:
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
            line = leftLine + '=' + rightLine + notes
            translationInput += line + "\n"

        return translationInput, checkedPars

    def extractValues(self, elt: ast.AST) -> VAL_TYPE:
        if isinstance(elt, ast.Constant):
            return elt.value
        elif isinstance(elt, ast.List):
            return [self.extractValues(elt) for elt in elt.elts]
        #statements for the the boundary list:
        elif isinstance(elt, ast.Name) and elt.id == 'inf':
            return float('inf')
        elif isinstance(elt, ast.Name):
            return elt.id
        #check for negative values in boundary list
        elif isinstance(elt.op, ast.USub) and self.extractValues(elt.operand) == float('inf'):
            return float('-inf')
        elif isinstance(elt.op, ast.USub) and isinstance(self.extractValues(elt.operand), (int, float)):
            return -1*self.extractValues(elt.operand)
        return None

    def getParametersFromConstraints(self, constraints_str: str, targetName: str) -> []:
        """Extract parameters from constraints string"""
        tree = ast.parse(constraints_str) #get abstract syntax tree

        parametersNode = None
        for node in ast.walk(tree):
            #is the node an assignment and does it have the target name?
            if isinstance(node, ast.Assign) and node.targets[0].id == targetName:
                parametersNode = node.value
                parameters = [self.extractValues(elt) for elt in parametersNode.elts]
                return parameters

        logger.warn(f"No {targetName} variable found in constraints")

    def getParameters(self, constraintsStr: str, fitPar: [str]) -> str:
        """Get parameters from constraints"""

        #Is anything in parameters?
        parameters = self.getParametersFromConstraints(constraintsStr, 'parameters')
        names = [parameter[0] for parameter in parameters]

        #Check parameters in constraints
        if len(names) != len(fitPar):
            logger.error("Number of parameters in variable parameters does not match checked parameters in table")

        #Check if parameter exists in checked parameters
        for name in names:
            if name not in fitPar:
                logger.error(f"{name} does not exists in checked parameters")

        description = 'parameters =' + '[' + '\n' + '# name, units, default, [min, max], type, description,' + '\n'
        parameters_str = description  + ',\n'.join(str(sublist) for sublist in parameters) + "\n]"

        return parameters_str

    def isImportFromStatement(self, node: ast.ImportFrom) -> [str]:
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

    def isImportStatement(self, node: ast.Import) -> [str]:
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

    def getImportStatements(self, text: str) -> [str]:
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

        except SyntaxError as e:
            error_line = text.splitlines()[e.lineno - 1]
            raise SyntaxError(f"Syntax error: {e.msg} at line {e.lineno}: {error_line}")

    def clearConstraints(self):
        """Clear text editor containing constraints"""
        self.constraintTextEditor.txtEditor.clear()
        self.textEdit_2.clear()

    def onClosingConstraints(self):
        """Close constraints page"""
        self.close()
