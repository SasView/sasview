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
        self.createPlugin.setToolTip("Create the plugin model. It will be available in the Plugin Models category in the Fit panel.")
        self.createPlugin.setEnabled(False)
        self.variableTable.on_item_changed_callback = lambda _: self.createPlugin.setEnabled(True)

        self.buttonOptions.horizontalLayout_5.insertWidget(1, self.createPlugin)
        self.buttonOptions.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)

        #Setup default logbook text
        defaultText = "<span><b>Shape2SAS plugin constraints log</b></p></span>"
        self.textEdit_2.append(defaultText)


    def getConstraintText(self, fit_params: str) -> str:
        """Get the default text for the constraints editor"""
    
        self.constraintText = (
            "# Write libraries to be imported here.\n"
            "from numpy import inf\n"
            "\n"
            "# Modify fit parameters here.\n"
            f"parameters = {fit_params}\n"
            "\n"
            "# Define your constraints here.\n"
            "# Both absolute and relative parameters can be used.\n"
            "# Example: dCOMX2 = dCOMX1 will make COMX2 track changes in COMX1\n"
        )

        return self.constraintText

    def setConstraints(self, fit_params: str):
        """Insert the text into the constraints editor"""

        constraints = self.getConstraintText(fit_params)
        self.constraintTextEditor.txtEditor.setPlainText(constraints)
        self.createPlugin.setEnabled(True)

    @staticmethod
    def parseConstraintsText(
        text: str, fitPar: list[str], modelPars: list[str], modelVals: list[list[float]], checkedPars: list[str]
    ) -> tuple[list[str], str, str, list[list[bool]]]:
        """Parse the text in the constraints editor and return a dictionary of parameters"""

        print("Parsing constraints text.")
        print("Received input:")
        print(f"fitPar: {fitPar}")
        print(f"modelPars: {modelPars}")
        print(f"modelVals: {modelVals}")
        print(f"checkedPars: {checkedPars}")

        def as_ast(text: str):
            try:
                return ast.parse(text)
            except SyntaxError as e:
                # log most recent traceback error
                all_lines = traceback.format_exc().split('\n')
                last_lines = all_lines[-1:]
                traceback_to_show = '\n'.join(last_lines)
                logger.error(traceback_to_show)
                return None
        
        def parse_ast(tree: ast.AST):
            params = None
            imports = []
            constraints = []

            for node in ast.walk(tree):
                match node:
                    case ast.ImportFrom() | ast.Import():
                        imports.append(node)
                    
                    case ast.Assign():
                        if node.targets[0].id == 'parameters':
                            params = node
                        else:
                            constraints.append(node)

            # params must be defined
            if params is None:
                logger.error("No parameters found in constraints text.")
                return None, None, None

            # ensure imports are valid
            #! not implemented yet

            return [
                ast.unparse(params),
                [ast.unparse(imp) for imp in imports],
                [ast.unparse(constraint) for constraint in constraints]
            ]

        tree = as_ast(text)
        if tree is None:
            return None

        params, imports, constraints = parse_ast(tree)
        print("Finished parsing constraints text.")
        print(f"Parsed parameters: {params}")
        print(f"Parsed imports: {imports}")
        print(f"Parsed constraints: {constraints}")
        return imports, params, constraints, checkedPars

    @staticmethod
    def getPosition(item: VAL_TYPE, itemLists: list[list[VAL_TYPE]]) -> tuple[int, int]:
        """Find position of an item in lists"""

        for i, sublist in enumerate(itemLists):
            if item in sublist:
                return i, sublist.index(item)

    @staticmethod
    def removeFromList(listItems: list[VAL_TYPE], listToCompare: list[VAL_TYPE]):
        """Remove items from a list if in another list"""

        finalpars = []
        for item in listItems:
            for statement in listToCompare:
                if item not in statement:
                    #NOTE: library names, "from" and "import" will also be removeds
                    finalpars.append(item)
        # Explicilty modify list sent to the method
        listItems = finalpars

    def ifParameterExists(self, lineNames: list[str], modelPars: list[list[str]]) -> bool:
        """Check if parameter exists in model parameters"""

        for par in lineNames:
            boolPar = any(par in sublist for sublist in modelPars)
            if not boolPar:
                logger.error(f"{par} does not exist in parameter table")

        return False

    def clearConstraints(self):
        """Clear text editor containing constraints"""
        self.constraintTextEditor.txtEditor.clear()
        self.textEdit_2.clear()

    def onClosingConstraints(self):
        """Close constraints page"""
        self.close()
